#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Read-only pairwise SS dashboard. Standard library only; no torch imports."""
import argparse
import csv
from datetime import datetime, timedelta, timezone
import math
from pathlib import Path
import re
import subprocess
import sys
import time

ROOT = Path('/nas/liziyan103/seatrack/training_runs/20261103_pairwise_ss')
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
                   'Loss/ss_template', 'Loss/ss_search', 'FPS', 'TotalTime')}}
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
        return None
    value = path.read_text().strip()
    try:
        return int(value) if value else None
    except ValueError:
        return '无效内容'


def snapshots(run, config):
    saved = []
    directory = run / 'checkpoints' / config
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


def screen(run, epochs, config, session, gpu=None, now=None):
    now = time.time() if now is None else now
    log = run / 'train.log'
    text = tail(log)
    state = parse(text)
    train, validation, last = state['train'], state['val'], state['last']
    saved = snapshots(run, config)
    highest = max(saved, default=0)
    exitcode = read_exit(run)
    done = exitcode == 0 and state['finished'] and highest >= epochs
    metrics_invalid = last and any(v is not None and not math.isfinite(v) for v in last['metrics'].values())
    if exitcode is not None and exitcode != 0:
        label = '失败 / 已退出，退出码：{}'.format(exitcode)
    elif done:
        label = '已完成（退出码 0，末轮权重文件存在）'
    elif exitcode == 0:
        label = '已退出（退出码 0，完整完成证据尚不足）'
    elif state['error_after_progress']:
        label = '日志出现错误，等待退出状态'
    elif metrics_invalid:
        label = '日志出现非有限指标，请检查训练窗口'
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
    if exitcode is not None or state['error_after_progress'] or metrics_invalid or (age is not None and age > 600):
        remaining = None
    lines = [
        'SEATrack · Pairwise SS 训练进度',
        datetime.fromtimestamp(now, timezone(timedelta(hours=8))).strftime('%Y-%m-%d %H:%M:%S 北京时间'),
        '=' * 72,
        '状态：' + label,
        '训练会话：{}  |  每批 4 · 累积 16 · 有效 batch 64'.format(session),
        '实验：' + str(run),
        '日志距今：{}（面板读取的是最近记录，不检测训练进程存活）'.format(duration(age)),
        '-' * 72,
        '总体训练批次 {} {:6.2f}%'.format(bar(overall), overall * 100),
    ]
    if train:
        lines += ['训练：第 {}/{} 轮  |  第 {:,}/{:,} 小批次'.format(train['epoch'], epochs, train['batch'], train['batches']),
                  '本轮 {} {:6.2f}%'.format(bar(fraction), fraction * 100),
                  '参数更新：最近训练记录对应约 {:,}/{:,} 次（按累积16推算）'.format(train['batch']//16, train['batches']//16)]
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
    lines.append('已保存权重：{} 份；最高第 {} 轮（仅检查非空文件，不加载权重）'.format(len(saved), highest))
    if gpu is not None:
        lines += ['-' * 72, gpu]
    lines += ['-' * 72,
              '总体百分比只统计训练批次；到 100% 后可能仍在验证或保存。',
              '正式配置通常每 160 个训练小批次写一条日志，面板不会逐批跳动。',
              'Ctrl+C 只退出面板；Ctrl+B 然后 D 离开 tmux，保留面板运行。',
              '返回训练：tmux attach -t {}（已在 tmux 内用 switch-client -t {}）'.format(session, session)]
    if state['error_after_progress'] or (exitcode is not None and exitcode != 0):
        lines += ['', '最近日志：'] + text.splitlines()[-10:]
    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--run-dir', type=Path)
    parser.add_argument('--config', default='rgbt_ss')
    parser.add_argument('--epochs', type=int)
    parser.add_argument('--session', default='1', help='Display only; never controls tmux')
    parser.add_argument('--gpu', type=int, default=1, help='Read-only physical GPU query; -1 disables')
    parser.add_argument('--interval', type=float, default=10)
    parser.add_argument('--once', action='store_true')
    args = parser.parse_args()
    if args.interval < 1 or (args.epochs is not None and args.epochs < 1):
        parser.error('interval must be >=1 and epochs >=1')
    try:
        run = select_run(args.root, args.run_dir)
        epochs = args.epochs or training_epochs(args.root, args.config)
        while True:
            if run is None:
                run = select_run(args.root, args.run_dir)
            if run is None:
                output = '尚未发现正式 full_* 实验目录：{}\n等待训练启动；不会读取 smoke 试跑。'.format(args.root)
            else:
                gpu = gpu_status(args.gpu) if args.gpu >= 0 else None
                output = screen(run, epochs, args.config, args.session, gpu)
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
