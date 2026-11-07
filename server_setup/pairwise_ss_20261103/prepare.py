"""Create an isolated SS experiment from the previously trained single-GPU code.

Run with the existing seatrack Python environment. Never launches training.
"""
import argparse
import ast
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import re
import shutil
import sys

import yaml

PACKAGE = Path(__file__).resolve().parent
DEFAULT_ROOT = Path('/nas/liziyan103/seatrack')
REPLACED = [
    'lib/config/seatrack/config.py',
    'lib/models/seatrack/vit_ci.py',
    'lib/models/seatrack/seatrack.py',
    'lib/train/actors/seatrack.py',
    'lib/models/layers/patch_embed.py',
]
PRESERVED = [
    'lib/train/dataset/lasher.py',
    'lib/train/trainers/accumulation.py',
    'lib/train/trainers/ltr_trainer.py',
    'lib/train/train_script.py',
    'lib/train/run_training.py',
    'lib/train/base_functions.py',
]
SS = dict(ENABLED=True, LAYERS=[3, 5, 7, 9, 11],
          TEMPLATE_WEIGHT=0.5, SEARCH_WEIGHT=0.5)


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def syntax(text):
    return ast.dump(ast.parse(text), include_attributes=False)


def server_patch_embed_syntax(text):
    """The user-confirmed variant places flatten after num_patches.

    Accept only this exact assignment relocation; retain all other AST checks.
    """
    assignment = '        self.flatten = flatten\n'
    after = '        self.num_patches = self.grid_size[0] * self.grid_size[1]\n'
    require(text.count(assignment) == 1 and text.count(after) == 1,
            'Unexpected packaged PatchEmbed layout')
    return syntax(text.replace(assignment, '').replace(after, after + assignment))


def timestamp():
    return datetime.now(timezone(timedelta(hours=8))).isoformat(timespec='seconds')


def prepare(source, run):
    require(source.is_dir(), 'Missing source: ' + str(source))
    require(not run.exists(), 'Run directory already exists; refusing to overwrite: ' + str(run))
    require(source != run and source not in run.parents and run not in source.parents,
            'Source and destination must be separate directories')

    # Check every payload against the manifest before copying anything.
    manifest = json.loads((PACKAGE / 'package_manifest.json').read_text())
    for relative, expected in manifest.items():
        require(digest(PACKAGE / relative) == expected, 'Package checksum mismatch: ' + relative)

    # Compare syntax in this Python version: comments, CRLF, and 3.8/3.9 AST
    # representation differences do not cause false mismatches.
    keep_existing = []
    for relative in REPLACED:
        actual = syntax((source / relative).read_text())
        expected = syntax((PACKAGE / 'reference' / relative).read_text())
        updated_text = (PACKAGE / 'payload' / relative).read_text()
        updated = syntax(updated_text)
        accepted = [expected, updated]
        if relative == 'lib/models/layers/patch_embed.py':
            fixed_versions = [updated, server_patch_embed_syntax(updated_text)]
            accepted.extend(fixed_versions)
            if actual in fixed_versions:
                keep_existing.append(relative)
        require(actual in accepted,
                'Unrecognized server changes in ' + relative + '; no files were changed')
    require(not (source / 'lib/models/layers/semantic_alignment.py').exists(),
            'Source already contains an SS module; inspect its version first')
    require('_frame_cache' in (source / PRESERVED[0]).read_text(),
            'Source lacks the validated LasHeR frame matching fix')
    require('accumulator.backward(loss)' in (source / PRESERVED[2]).read_text(),
            'Source lacks the gradient accumulation integration')
    require(re.search(r'settings\.accumulation_steps\s*=\s*16\b',
                      (source / PRESERVED[3]).read_text()), 'Expected accumulation_steps=16')
    require('fail_safe=False' in (source / PRESERVED[3]).read_text(),
            'Expected fail_safe=False so errors are not silently retried')
    original = yaml.safe_load((source / 'experiments/seatrack/rgbt.yaml').read_text())
    require(original['TRAIN']['BATCH_SIZE'] == 4, 'Expected microbatch=4')
    require(original['TRAIN']['EPOCH'] == 60, 'Expected 60 training epochs')
    require(original['DATA']['TRAIN']['SAMPLE_PER_EPOCH'] == 59968,
            'Expected 59968 training samples per epoch for 937 accumulation groups')
    require(original['TRAIN']['PEFT'] and not original['TRAIN']['AMP'],
            'Expected PEFT=True and AMP=False')
    require(all(r == 1 for r in original['MODEL']['BACKBONE']['CE_KEEP_RATIO']),
            'SS requires CE_KEEP_RATIO=1')
    weight = Path(original['MODEL']['PRETRAIN_FILE'])
    if not weight.is_absolute():
        weight = (source / weight).resolve()
    require(weight.is_file(), 'Missing initialization checkpoint: ' + str(weight))

    # The old files and outputs are never modified. Only source code directories
    # are copied; datasets, weights and old training results are not duplicated.
    before = {name: digest(source / name) for name in PRESERVED + REPLACED}
    run.mkdir(parents=True)
    log = run / 'setup.log'

    def record(message):
        line = timestamp() + ' ' + message
        print(line, flush=True)
        with log.open('a') as stream:
            stream.write(line + '\n')

    try:
        record('SOURCE ' + str(source))
        record('Copy lib/experiments/tracking; preserve data-loader fixes and accumulation=16')
        code = run / 'code'
        code.mkdir()
        for name in ('lib', 'experiments', 'tracking'):
            shutil.copytree(source / name, code / name,
                            ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
        for p in (PACKAGE / 'payload').rglob('*'):
            if p.is_file():
                relative = p.relative_to(PACKAGE / 'payload')
                if str(relative) in keep_existing:
                    record('Preserve verified existing fix byte-for-byte: ' + str(relative))
                    continue
                target = code / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(p, target)
        record('Install full pairwise SS module, backbone/Actor integration, config and tests')

        local = code / 'lib/train/admin/local.py'
        text = local.read_text()
        for key, value in {'workspace_dir': code, 'tensorboard_dir': run / 'tensorboard'}.items():
            text, count = re.subn(r'(self\.' + key + r'\s*=\s*)[^\n]+',
                                 lambda match: match.group(1) + repr(str(value)), text)
            require(count == 1, 'Expected one local setting: ' + key)
        local.write_text(text)
        (run / 'tensorboard').mkdir()
        record('Isolate workspace/TensorBoard paths; retain existing dataset paths')

        config_dir = code / 'experiments/seatrack'
        full = deepcopy(original)
        full['MODEL']['PRETRAIN_FILE'] = str(weight)
        full['MODEL']['SS'] = deepcopy(SS)
        full['TRAIN']['SS_WEIGHT'] = 0.1
        baseline = deepcopy(full)
        baseline['MODEL']['SS']['ENABLED'] = False
        smoke = deepcopy(full)
        smoke['DATA']['TRAIN']['SAMPLE_PER_EPOCH'] = 128
        smoke['DATA']['VAL']['SAMPLE_PER_EPOCH'] = 16
        smoke['TRAIN'].update(EPOCH=1, NUM_WORKER=0, PRINT_INTERVAL=16,
                              VAL_EPOCH_INTERVAL=1, SAVE_EPOCH_INTERVAL=1,
                              SAVE_LAST_N_EPOCH=1)
        smoke['TEST']['EPOCH'] = 1
        for name, config in [('rgbt_ss', full), ('rgbt_ss_baseline', baseline),
                             ('rgbt_ss_smoke', smoke)]:
            (config_dir / (name + '.yaml')).write_text(yaml.safe_dump(config, sort_keys=False))
        record('Full SS and baseline share batch4 x accumulation16, 60 epochs and all other settings')
        record('Smoke: 128 train samples/32 microbatches/2 optimizer updates; 16 val samples; 1 epoch')

        for relative, expected in before.items():
            require(digest(source / relative) == expected, 'Source changed during setup: ' + relative)
        for relative in PRESERVED + keep_existing:
            require(digest(code / relative) == before[relative], 'Preserved file changed: ' + relative)
        for p in code.rglob('*.py'):
            ast.parse(p.read_text(), filename=str(p), feature_version=8)
        state = {
            'created_at': timestamp(), 'source': str(source), 'code': str(code),
            'initialization_checkpoint': str(weight), 'source_sha256': before,
            'preserved_files': PRESERVED + keep_existing, 'microbatch': 4, 'accumulation_steps': 16,
            'effective_batch': 64, 'ss': SS, 'ss_weight': 0.1,
            'smoke_optimizer_updates': 2,
            'code_sha256': {str(p.relative_to(code)): digest(p) for p in code.rglob('*')
                            if p.is_file() and '__pycache__' not in p.parts},
            'training_started': False,
        }
        (run / 'setup_manifest.json').write_text(json.dumps(state, indent=2))
        record('PREPARE_OK; original code unchanged; training has NOT started')
        print('CODE=' + str(code))
        print('NEXT: cd ' + str(code))
        print('NEXT: ' + sys.executable + ' -m unittest discover -s tests -p test_semantic_alignment.py -v')
    except Exception as error:
        record('FAILED ' + repr(error) + '; partial directory retained for inspection')
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path,
                        default=DEFAULT_ROOT / 'training_runs/20261011_remaining/code_single')
    parser.add_argument('--run-dir', type=Path,
                        default=DEFAULT_ROOT / 'training_runs/20261103_pairwise_ss')
    args = parser.parse_args()
    prepare(args.source.resolve(), args.run_dir.resolve())
