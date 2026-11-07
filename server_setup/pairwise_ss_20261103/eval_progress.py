"""Read-only terminal progress for the epoch 60 evaluation (Python 3)."""
import argparse
import datetime
import fcntl
import json
from pathlib import Path
import re
import sys
import time

ROOT = Path('/nas/liziyan103/seatrack/training_runs/20261103_pairwise_ss/full_zCqHZl/eval_ep0060')
DATASETS = [('LasHeR', 245), ('RGBT234', 234)]


def running():
    with (ROOT / 'lock').open('rb') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_SH | fcntl.LOCK_NB)
        except BlockingIOError:
            return True
    return False


def panel():
    active = running()
    log = (ROOT / 'run.log').read_text(errors='replace').splitlines()
    rows = []
    total = 0
    reports = 0
    for name, size in DATASETS:
        count = sum(1 for _ in (ROOT / 'RGBT_workspace/ss' / name).glob('*.txt'))
        total += count
        filled = int(20 * min(count / size, 1))
        bar = '█' * filled + '░' * (20 - filled)
        rows.append(f'{name:8} {bar}  {count:3}/{size}  {100 * count / size:5.1f}%')
        scores = []
        for label, title in [('ss', 'SS'), ('baseline', '基线')]:
            path = ROOT / f'{name}_{label}.json'
            ready = False
            if path.is_file():
                try:
                    data = json.loads(path.read_text())
                    ready = (data.get('sequences') == size if name == 'LasHeR'
                             else data.get('sequence_count') == size)
                except ValueError:
                    pass
            reports += int(ready)
            scores.append(title + ('已完成' if ready else '待出分'))
        rows.append('         ' + ' ｜ '.join(scores))
    complete = 'EVALUATION_COMPLETE' in log and reports == 4 and total == 479
    status = '全部完成' if complete else ('运行中' if active else '已停止，请检查日志')
    detail = log[-1] if log else '等候日志'
    match = re.search(r'Process sequence: (.*?)—+$', detail)
    if active and match:
        detail = '正在跟踪  ' + match.group(1)
    elif active and detail.startswith('PROGRESS'):
        detail = '已写入轨迹  ' + detail[9:]
    now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8)))
    return '\n'.join([f'第 60 轮跟踪测试   {now:%H:%M:%S} 北京时间   {status}',
                      f'轨迹总进度  {total}/479（{total/479:.1%}）   指标报告  {reports}/4',
                      '', *rows, '', detail, '每 10 秒刷新 · Ctrl+C 退出查看'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--once', action='store_true')
    args = parser.parse_args()
    try:
        while True:
            try:
                output = panel()
            except OSError as exc:
                output = f'读取评测目录失败：{exc}'
            if sys.stdout.isatty() and not args.once:
                print('\033[2J\033[H', end='')
            print(output, flush=True)
            if args.once:
                break
            time.sleep(10)
    except KeyboardInterrupt:
        pass
