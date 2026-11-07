"""Read-only monitor for an RGB-E + SS training run."""
import argparse
from datetime import datetime, timedelta, timezone
from pathlib import Path
import re
import sys
import time

ROOT = Path('/nas/liziyan103/seatrack/training_runs/rgbe_pairwise_ss')
BATCH = re.compile(r'\[train:\s*(\d+),\s*(\d+)\s*/\s*(\d+)\]')
WEIGHT = re.compile(r'SEATrack_ep(\d+)\.pth\.tar$')


def tail(path):
    try:
        with path.open('rb') as src:
            src.seek(max(0, path.stat().st_size - 262144))
            return src.read().decode(errors='replace')
    except FileNotFoundError:
        return ''


def process_running(folder):
    needle = str(folder).encode()
    for cmd in Path('/proc').glob('[0-9]*/cmdline'):
        try:
            args = cmd.read_bytes().split(b'\0')
        except OSError:
            continue
        if needle in args and any(a.endswith(b'/run_training.py') for a in args):
            return True
    return False


def panel(run):
    smoke = tail(run / 'smoke/train.log')
    formal = (run / 'full/train.log').exists()
    stage = 'full' if formal else 'smoke'
    folder = run / stage
    log = tail(folder / 'train.log')
    records = [line for line in log.splitlines() if BATCH.search(line)]
    weights = sorted(p for p in folder.glob('checkpoints/*/SEATrack_ep*.pth.tar')
                     if WEIGHT.fullmatch(p.name) and p.stat().st_size > 0)
    limit = 45 if formal else 1
    finished = ('Finished training!' in log and weights and
                int(WEIGHT.fullmatch(weights[-1].name)[1]) == limit)
    active = process_running(folder)
    status = '已完成' if finished else ('运行中' if active else '未检测到训练进程')
    timestamp = datetime.now(timezone(timedelta(hours=8))).strftime('%H:%M:%S')
    rows = [f'RGB-E + SS ｜ VisEvent ｜ {timestamp} 北京时间', str(run),
            '试跑：' + ('已通过' if formal else '已结束' if 'Finished training!' in smoke else '待完成'),
            ('正式训练' if formal else '试跑阶段') + '：' + status]
    if records:
        line = records[-1]
        epoch, batch, count = map(int, BATCH.search(line).groups())
        progress = (epoch - 1 + batch / count) / limit
        rows.append(f'第 {epoch}/{limit} 轮 ｜ 本轮 {batch}/{count} 批（{batch/count:.1%}） ｜ 阶段总进度 {progress:.2%}')
        for label, key in [('总损失','Loss/total'), ('SS 损失','Loss/ss'), ('IoU','IoU')]:
            m = re.search(r'(?:^|,\s*)' + re.escape(key) + r':\s*([^,\s]+)', line)
            if m:
                rows.append(f'{label}  {m[1]}')
    else:
        rows.append('等待首次批次日志')
    rows.append('最近权重  ' + (weights[-1].name if weights else '尚未保存'))
    if log and not finished and not active:
        rows.extend(log.splitlines()[-3:])
    rows.append('每 10 秒刷新 ｜ Ctrl+C 退出面板')
    return '\n'.join(rows)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-dir', type=Path)
    parser.add_argument('--once', action='store_true')
    args = parser.parse_args()
    run = args.run_dir
    try:
        while True:
            try:
                if run is None:
                    runs = sorted(ROOT.glob('run_*'), key=lambda x: x.stat().st_mtime)
                    run = runs[-1] if runs else None
                output = panel(run) if run else '等待创建 RGB-E 训练目录'
            except OSError as exc:
                output = f'读取训练状态失败：{exc}'
            print(('\033[2J\033[H' if sys.stdout.isatty() and not args.once else '') + output, flush=True)
            if args.once:
                break
            time.sleep(10)
    except KeyboardInterrupt:
        pass
