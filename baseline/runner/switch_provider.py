"""Replacement experiment launched by the existing authenticated CLI on its next retry."""
import fcntl
import os
import time
from pathlib import Path

from paired import EXAMPLES, ROUTES, manifest, resources, select_route
from paired_store import load, save
from run_one_shot import OUT, SPLIT, run
from providers import ProviderError

def main():
    OUT.mkdir(exist_ok=True)
    owner = (OUT / '.supervisor.lock').open('a')
    fcntl.flock(owner, fcntl.LOCK_EX | fcntl.LOCK_NB)
    with (OUT / 'console.log').open('ab') as console:
        os.dup2(console.fileno(), 1)
        os.dup2(console.fileno(), 2)
    save(OUT / 'handoff.json', {'status': 'checking providers', 'model': 'qwen/qwen3.5-9b'})
    games = manifest(Path(SPLIT))
    actor = resources('openrouter')
    actor.action_example = load(EXAMPLES)['examples'][games[0]['family']]
    while True:
        try:
            selected = select_route(OUT, actor, Path(SPLIT) / games[0]['game'], ROUTES)
            break
        except ProviderError as exc:
            print(str(exc), flush=True)
            if '401' in str(exc) or '402' in str(exc):
                raise
            time.sleep(120)
    save(OUT / 'handoff.json', {'status': 'provider verified', 'provider': selected, 'model': actor.model})
    print(f'Alternate provider {selected} passed; starting fresh paired comparison.', flush=True)
    mode = 'both'
    run()
    save(OUT / 'handoff.json', {'status': 'complete', 'mode': mode, 'provider': selected, 'model': actor.model})

if __name__ == '__main__':
    main()
