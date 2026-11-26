#!/usr/bin/env python3
"""Start or resume the two ALFWorld arms in order, with credentials in memory."""
from pathlib import Path
import fcntl
import getpass
import json
import os
import sqlite3
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
OUT = HERE.parent / 'alfworld-9b-oneshot-alternate'
PYTHON = os.environ.get('ALFWORLD_PYTHON', str(Path.home() / 'state-audit-pilot/.venv/bin/python'))
SPLIT = os.environ.get('ALFWORLD_VALID_SEEN', str(Path.home() / 'state-audit-pilot/data/alfworld/json_2.1.1/valid_seen'))

def finished(arm):
    paths = sorted(OUT.glob(f'game*/episode_start/{arm}.json'))
    return [p.parents[1].name for p in paths] == [f'game{i:02d}' for i in range(1, 13)]

def ledger_marks():
    marks = {}
    for path in OUT.glob('game*/calls.sqlite'):
        with sqlite3.connect(path.resolve().as_uri() + '?mode=ro', uri=True) as conn:
            if conn.execute("SELECT 1 FROM sqlite_master WHERE name='requests'").fetchone():
                marks[path] = conn.execute('SELECT COALESCE(MAX(id),0) FROM requests').fetchone()[0]
    return marks

def errors_since(marks):
    statuses = []
    for path in OUT.glob('game*/calls.sqlite'):
        with sqlite3.connect(path.resolve().as_uri() + '?mode=ro', uri=True) as conn:
            for raw, in conn.execute('SELECT transport FROM requests WHERE ok=0 AND id>?', (marks.get(path, 0),)):
                calls = json.loads(raw)
                statuses.append(calls[-1].get('last_http_status') if calls and not calls[-1].get('ok') else None)
    return statuses

def run():
    for arm in ('direct', 'llm_eda'):
        attempts = 0
        limited = 0
        while not finished(arm):
            before = len(list(OUT.glob(f'game*/episode_start/{arm}.json')))
            marks = ledger_marks()
            args = [PYTHON, '-B', str(HERE / 'paired.py'), '--provider', 'openrouter',
                    '--design', 'episode', '--workers', '1', '--arms', arm, '--split-dir', SPLIT, '--out', str(OUT)]
            code = subprocess.call(args)
            subprocess.run([PYTHON, '-B', str(HERE / 'trajectories.py'), str(OUT)], check=True)
            if code == 0 and finished(arm):
                break
            statuses = errors_since(marks)
            if statuses and all(s == 429 for s in statuses):
                limited += 1
                delay = min(900, 60 * 2 ** min(limited - 1, 4))
                print(f'HTTP 429; waiting {delay} seconds, then resuming {arm}.', flush=True)
                time.sleep(delay)
                continue
            if any(s in (401, 402, 403) for s in statuses):
                raise SystemExit(f'Authentication, balance or account access requires attention: {statuses}')
            after = len(list(OUT.glob(f'game*/episode_start/{arm}.json')))
            attempts = 1 if after > before else attempts + 1
            if attempts == 3 or code == 0:
                raise SystemExit(f'{arm} paused after {attempts} incomplete attempt(s).')
            time.sleep(20 * attempts)
        subprocess.run([PYTHON, '-B', str(HERE / 'trajectories.py'), str(OUT)], check=True)
        print(f'{arm} finished; trajectories exported.', flush=True)
    print('Both arms complete.', flush=True)

def main():
    OUT.mkdir(exist_ok=True)
    if sys.argv[1:] == ['--worker']:
        return run()
    with (OUT / '.supervisor.lock').open('a') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            print('实验已经在后台运行。')
            return
        if finished('direct') and finished('llm_eda'):
            print('两组均已完成。')
            return
        key = os.environ.get('OPENROUTER_API_KEY') or getpass.getpass('OpenRouter API key (hidden): ').strip()
        if not key:
            raise SystemExit('缺少 key，实验未启动。')
        with (OUT / 'console.log').open('ab') as log:
            subprocess.Popen([sys.executable, str(Path(__file__).resolve()), '--worker'],
                             stdin=subprocess.DEVNULL, stdout=log, stderr=log, start_new_session=True,
                             pass_fds=(lock.fileno(),), env=dict(os.environ, OPENROUTER_API_KEY=key))
        print('已交给后台，可以关闭终端。完成 baseline 后自动跑方法组。', flush=True)

if __name__ == '__main__':
    main()
