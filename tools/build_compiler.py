#!/usr/bin/env python3
"""Build the M0 compiler pin into ignored .local storage. Python 3.11+."""
import argparse
import hashlib
import json
from pathlib import Path
import shlex
import subprocess
import sys
import tomllib

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--jobs', type=int, default=4)
    args = parser.parse_args()
    if args.jobs < 1:
        parser.error('--jobs must be positive')
    with (ROOT / 'tools/versions.lock.toml').open('rb') as stream:
        pin = tomllib.load(stream)['hltools']
    source = ROOT / '.local/src/hltools'
    logs = ROOT / 'build/m0'
    logs.mkdir(parents=True, exist_ok=True)

    def run(argv, name):
        print(shlex.join(map(str, argv)), flush=True)
        with (logs / name).open('w') as log:
            result = subprocess.run(argv, stdout=log, stderr=subprocess.STDOUT)
        if result.returncode:
            raise ValueError(f'Exit {result.returncode}; see {logs / name}')

    if not source.exists():
        source.parent.mkdir(parents=True, exist_ok=True)
        run(['git', 'clone', '--no-checkout', pin['repository'], str(source)], 'clone.log')
        run(['git', '-C', str(source), 'checkout', '--detach', pin['revision']], 'checkout.log')
    revision = subprocess.check_output(['git', '-C', str(source), 'rev-parse', 'HEAD'], text=True).strip()
    dirty = subprocess.check_output(['git', '-C', str(source), 'status', '--porcelain', '--untracked-files=no'], text=True)
    if revision != pin['revision'] or dirty:
        raise ValueError(f'{source} must be clean and at {pin["revision"]}; existing source was left intact')
    run(['cmake', '-S', str(source), '-B', str(source / 'build'), *pin['cmake_options']], 'cmake-configure.log')
    run(['cmake', '--build', str(source / 'build'), '--target', pin['target'], '--parallel', str(args.jobs)], 'cmake-build.log')
    binary = source / pin['binary']
    record = {'revision': revision, 'binary': str(binary),
              'sha256': hashlib.sha256(binary.read_bytes()).hexdigest(), 'cmake_options': pin['cmake_options']}
    (logs / 'compiler-build.json').write_text(json.dumps(record, indent=2) + '\n')
    print(json.dumps(record, indent=2))


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, subprocess.CalledProcessError) as exc:
        print(f'error: {exc}', file=sys.stderr)
        sys.exit(1)
