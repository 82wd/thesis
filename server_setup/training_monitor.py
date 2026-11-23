#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Read-only SEATrack training dashboard. Standard library only; no torch imports."""
import argparse
import csv
from datetime import datetime, timedelta, timezone
import math
from pathlib import Path
import re
import subprocess
import sys
import time

ROOT = Path('/nas/liziyan103/seatrack/training_runs/20261116_ss_search')
STATS = re.compile(r'^\[(train|val):\s*(\d+),\s*(\d+)\s*/\s*(\d+)\](.*)$', re.M)
VALUE = r'([-+]?\d+(?:\.\d*)?(?:[eE][-+]?\d+)?|nan|inf|-inf)'


def tail(path, limit=524288):
    try:
        with path.open('rb') as stream:
            stream.seek(0, 2)
            stream.seek(max(0, stream.tell() - limit))
            return stream.read().decode('utf-8', errors='replace')
    except FileNotFoundError:
        return ''


def metric(text, key):
    match = re.search(r'(?<![\w/])' + re.escape(key) + r':\s*' + VALUE, text, re.I)
    return float(match.group(1)) if match else None


def parse(text):
    result = {'train': None, 'val': None, 'last': None}
    for match in STATS.finditer(text):
        phase, epoch, batch, batches, values = match.groups()
        row = {'phase': phase, 'epoch': int(epoch), 'batch': int(batch),
               'batches': int(batches), 'position': match.start(),
               'metrics': {key: metric(values, key) for key in (
                   'Loss/total', 'IoU', 'Loss/ss', 'Loss/ss_weighted',
                   'Loss/ss_template', 'Loss/ss_search', 'Register/register_norm',
                   'Register/patch_norm', 'FPS', 'TotalTime')}}
        result[phase] = result['last'] = row
    error_positions = [text.rfind(token) for token in
                       ('Traceback (most recent call last):', 'Training crashed at epoch',
                        'CUDA out of memory', 'torch.OutOfMemoryError')]
    result['error_after_progress'] = max(error_positions) > (result['last']['position'] if result['last'] else -1)
    result['finished'] = 'Finished training!' in text
    return result


def duration(seconds):
    if seconds is None or not math.isfinite(seconds) or seconds < 0:
        return '暂无'
    minutes = int(seconds) // 60
    days, hours, mins = minutes // 1440, minutes // 60 % 24, minutes % 60
    if days:
        return '{}天 {}小时 {}分'.format(days, hours, mins)
    if hours:
        return '{}小时 {}分'.format(hours, mins)
    return '{}分 {}秒'.format(mins, int(seconds) % 60)


def bar(fraction, width=28):
    filled = int(max(0, min(1, fraction)) * width)
    return '[' + '#' * filled + '-' * (width - filled) + ']'


def select_run(root, explicit):
    if explicit is not None:
        require = explicit.resolve()
        if not require.is_dir():
            raise ValueError('指定目录不存在：' + str(require))
        return require
    candidates = sorted(p for p in root.glob('full_*') if p.is_dir())
    if not candidates:
        return None
    if len(candidates) > 1:
        raise ValueError('发现多个正式实验，请使用 --run-dir 指定一个：\n' +
                         '\n'.join(str(p) for p in candidates))
    return candidates[0]


def read_exit(run):
    path = run / 'exitcode.txt'
    if not path.exists():
        status = tail(run / 'status')
        if status.strip() == 'TRAIN_COMPLETE':
            return 0
        match = re.search(r'(?:FINISHED|FAILED) exit=(-?\d+)', status)
        return int(match.group(1)) if match else None
    value = path.read_text().strip()
    try:
        return int(value) if value else None
    except ValueError:
        return '无效内容'


def snapshots(run, config):
    saved = []
    directory = run / 'output' / 'checkpoints' / config
    if not directory.exists():
        directory = run / 'checkpoints' / config
    if not directory.exists():
        directory = run / 'full' / 'checkpoints' / config
    for path in directory.glob('SEATrack_ep*.pth.tar'):
        match = re.fullmatch(r'SEATrack_ep(\d+)\.pth\.tar', path.name)
        try:
            if match and path.stat().st_size > 0:
                saved.append(int(match.group(1)))
        except FileNotFoundError:
            pass
    return sorted(set(saved))


def gpu_status(index):
    try:
        command = ['nvidia-smi', '-i', str(index),
                   '--query-gpu=index,name,memory.used,memory.total,utilization.gpu',
                   '--format=csv,noheader,nounits']
        output = subprocess.run(command, capture_output=True, text=True, timeout=3)
        if output.returncode:
            return 'GPU 查询不可用（不影响读取训练日志）'
        fields = next(csv.reader(output.stdout.splitlines()))
        number, name, used, total, util = (field.strip() for field in fields)
        return 'GPU {} · {} | 显存 {}/{} MiB | 利用率 {}%（整卡）'.format(number, name, used, total, util)
    except (OSError, subprocess.TimeoutExpired, ValueError, StopIteration):
        return 'GPU 查询不可用（不影响读取训练日志）'


def training_epochs(root, config):
    # Read this project's flat TRAIN section without needing a YAML dependency.
    path = root / 'code/experiments/seatrack' / (config + '.yaml')
    text = tail(path)
    section = re.search(r'^TRAIN:\s*\n(.*?)(?=^\S|\Z)', text, re.M | re.S)
    match = re.search(r'^\s+EPOCH:\s*(\d+)\b', section.group(1), re.M) if section else None
    return int(match.group(1)) if match else 60


def screen(run, epochs, config, session, gpu=None, now=None, stale_seconds=300, log_path=None):
    now = time.time() if now is None else now
    log = log_path or run / 'train.log'
    text = tail(log, limit=4194304)
    state = parse(text)
    train, validation, last = state['train'], state['val'], state['last']
    saved = snapshots(run, config)
    highest = max(saved, default=0)
    exitcode = read_exit(run)
    pipeline_done = 'HALF_TRAIN_AND_EVAL_COMPLETE' in text
    evaluation = list(re.finditer(r'^PROGRESS (LasHeR|RGBT234) (\d+) (\d+)', text, re.M))
    done = (exitcode == 0 and state['finished'] and highest >= epochs) or pipeline_done
    metrics_invalid = last and any(v is not None and not math.isfinite(v) for v in last['metrics'].values())
    if exitcode is not None and exitcode != 0:
        label = '失败 / 已退出，退出码：{}'.format(exitcode)
    elif pipeline_done:
        label = '训练与两套全量测评均已完成（完成标记）'
    elif done:
        label = '已完成（退出码 0，末轮权重文件存在）'
    elif exitcode == 0:
        label = '已退出（退出码 0，完整完成证据尚不足）'
    elif state['error_after_progress']:
        label = '日志出现错误，等待退出状态'
    elif metrics_invalid:
        label = '日志出现非有限指标，请检查训练窗口'
    elif evaluation:
        label = '正在全量测评（最近进度记录）'
    elif state['finished']:
        label = '训练已报告结束，等待退出码'
    elif last:
        label = '最近记录：' + ('训练' if last['phase'] == 'train' else '验证')
    else:
        label = '等待首条训练记录'
    try:
        age = max(0, now - log.stat().st_mtime)
    except FileNotFoundError:
        age = None
    stale = age is not None and age > stale_seconds and exitcode is None
    if stale and not state['error_after_progress'] and not done:
        label = '警告：日志长期未更新，疑似停滞（也可能在加载/保存）'
    queue_status = tail(run / 'status').strip()
    if not last and queue_status.startswith('WAITING_GPU'):
        label = '等待空闲 GPU'
    fraction = train['batch'] / train['batches'] if train and train['batches'] else 0
    completed = max(highest, train['epoch'] - 1 + fraction if train else 0)
    if last:
        completed = max(completed, last['epoch'] - 1)
        if last['phase'] == 'val':
            completed = max(completed, last['epoch'])
    overall = min(1, completed / epochs)
    speed = train['metrics']['TotalTime'] if train else None
    remaining = None
    if speed is not None and math.isfinite(speed) and speed > 0 and train:
        remaining = max(0, epochs - completed) * train['batches'] * speed
    if exitcode is not None or state['error_after_progress'] or metrics_invalid or stale or evaluation or pipeline_done:
        remaining = None
    lines = [
        'SEATrack · 训练进度监控',
        datetime.fromtimestamp(now, timezone(timedelta(hours=8))).strftime('%Y-%m-%d %H:%M:%S 北京时间'),
        '=' * 72,
        '状态：' + label,
        '训练会话：{}  |  配置：{}'.format(session, config),
        '实验：' + str(run),
        '日志距今：{} | 停更阈值 {} 秒'.format(duration(age), stale_seconds),
        '队列记录：' + (queue_status or '无状态文件'),
        '-' * 72,
        '总体训练批次 {} {:6.2f}%'.format(bar(overall), overall * 100),
    ]
    if train:
        lines += ['训练：第 {}/{} 轮  |  第 {:,}/{:,} 小批次'.format(train['epoch'], epochs, train['batch'], train['batches']),
                  '本轮 {} {:6.2f}%'.format(bar(fraction), fraction * 100)]
        fps = train['metrics']['FPS']
        if fps is not None:
            lines.append('本轮平均速度：{:.1f} 样本/秒'.format(fps))
    if validation:
        lines.append('最近验证：第 {} 轮，{:,}/{:,} 批'.format(validation['epoch'], validation['batch'], validation['batches']))
    lines.append('剩余训练阶段时间估算：{}（不含后续验证、保存与停顿）'.format(duration(remaining)))
    lines.append('-' * 72)
    for title, row in [('训练', train), ('验证', validation)]:
        if not row:
            continue
        fields = []
        for key, name in [('Loss/total', '总损失'), ('IoU', 'IoU'), ('Loss/ss', 'SS'), ('Loss/ss_weighted', '加权SS')]:
            value = row['metrics'][key]
            if value is not None:
                fields.append('{} {:.5f}'.format(name, value))
        lines.append('{} 第{}轮：{}'.format(title, row['epoch'], ' | '.join(fields)))
        template, search = row['metrics']['Loss/ss_template'], row['metrics']['Loss/ss_search']
        if template is not None and search is not None:
            lines.append('  模板 SS {:.5f}  |  搜索 SS {:.5f}'.format(template, search))
        register = row['metrics']['Register/register_norm']
        patch = row['metrics']['Register/patch_norm']
        if register is not None and patch is not None:
            lines.append('  寄存器范数 {:.5f}  |  patch 范数 {:.5f}（LayerNorm前）'.format(register, patch))
    lines.append('已保存权重：{} 份；最高第 {} 轮（仅检查非空文件，不加载权重）'.format(len(saved), highest))
    if evaluation:
        for dataset in ('LasHeR', 'RGBT234'):
            records = [m for m in evaluation if m.group(1) == dataset]
            if records:
                item = records[-1]
                lines.append('全量测评 {}：{}/{} 条序列'.format(dataset, item.group(2), item.group(3)))
    if gpu is not None:
        lines += ['-' * 72, gpu]
    lines += ['-' * 72,
              '总体百分比只统计训练批次；到 100% 后可能仍在验证或保存。',
              '只读日志与 GPU；不自动重启训练，不将队列状态当作存活证明。',
              'Ctrl+C 只退出面板；Ctrl+B 然后 D 离开 tmux，保留面板运行。',
              '返回训练：tmux attach -t {}（已在 tmux 内用 switch-client -t {}）'.format(session, session)]
    if state['error_after_progress'] or (exitcode is not None and exitcode != 0):
        lines += ['', '最近日志：'] + text.splitlines()[-10:]
    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--run-dir', type=Path)
    parser.add_argument('--log', type=Path, help='Override training/pipeline log path')
    parser.add_argument('--config', default='rgbt_ss_search')
    parser.add_argument('--epochs', type=int)
    parser.add_argument('--session', default='ss_search_20261116', help='Display only; never controls tmux')
    parser.add_argument('--gpu', type=int, default=5, help='Read-only physical GPU query; -1 disables')
    parser.add_argument('--interval', type=float, default=10)
    parser.add_argument('--stale-seconds', type=int, default=300)
    parser.add_argument('--once', action='store_true')
    args = parser.parse_args()
    if args.stale_seconds < 1 or args.interval < 1 or (args.epochs is not None and args.epochs < 1):
        parser.error('interval must be >=1 and epochs >=1')
    try:
        run = select_run(args.root, args.run_dir or args.root)
        epochs = args.epochs or training_epochs(args.root, args.config)
        while True:
            if run is None:
                run = select_run(args.root, args.run_dir or args.root)
            if run is None:
                output = '尚未发现正式 full_* 实验目录：{}\n等待训练启动；不会读取 smoke 试跑。'.format(args.root)
            else:
                gpu = gpu_status(args.gpu) if args.gpu >= 0 else None
                output = screen(run, epochs, args.config, args.session, gpu, stale_seconds=args.stale_seconds, log_path=args.log)
            if sys.stdout.isatty() and not args.once:
                sys.stdout.write('\033[2J\033[H')
            print(output, flush=True)
            if args.once:
                return
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print('\n已退出进度面板，未操作训练进程。')
    except (OSError, ValueError) as error:
        print('面板读取失败：' + str(error), file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
