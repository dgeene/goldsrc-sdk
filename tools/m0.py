#!/usr/bin/env python3
"""Linux M0 experiments, not the future goldsrc CLI. Python 3.11+."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import shlex
import shutil
import struct
import subprocess
import sys
import tempfile
import tomllib
import zipfile

ROOT = Path(__file__).resolve().parents[1]
PATH_KEYS = ('editor_path', 'steam_root', 'steam_executable', 'half_life_dir',
             'valve_fgd', 'cstrike_fgd')


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def absolute(value):
    return Path(value).expanduser().resolve()


def executable(value):
    path = absolute(shutil.which(str(value)) or value)
    if not path.is_file() or not os.access(path, os.X_OK):
        raise ValueError(f'Not an executable file: {path}')
    return path


def editor_command(value, map_path=None, environ=None):
    path = absolute(value)
    if path.is_dir():
        path /= 'Jack'
    # Resolve symlinks before deriving cwd, so shared libraries are beside Jack.
    path = executable(path)
    env = dict(os.environ if environ is None else environ)
    env['LD_LIBRARY_PATH'] = os.pathsep.join(
        [str(path.parent)] + [p for p in env.get('LD_LIBRARY_PATH', '').split(os.pathsep) if p])
    argv = [str(path)]
    if map_path:
        source = absolute(map_path)
        if not source.is_file():
            raise ValueError(f'Map does not exist: {source}')
        argv.append(str(source))
    return argv, path.parent, env


def settings(args):
    cfg = absolute(args.config)
    if cfg.exists():
        with cfg.open('rb') as stream:
            values = tomllib.load(stream).get('paths', {})
        if not isinstance(values, dict) or set(values) - set(PATH_KEYS):
            raise ValueError('Config [paths] must contain only documented path keys')
        if any(not isinstance(v, str) for v in values.values()):
            raise ValueError('Config path values must be strings')
    elif cfg != ROOT / '.local/user.toml':
        raise ValueError(f'Config file does not exist: {cfg}')
    else:
        values = {}
    resolved = {key: getattr(args, key, None) or os.environ.get('GOLDSRC_' + key.upper())
                or values.get(key) for key in PATH_KEYS}
    return resolved


def game_paths(values):
    steam_root = values['steam_root']
    if not steam_root:
        candidates = {absolute(p) for p in (
            Path.home() / '.local/share/Steam', Path.home() / '.steam/steam',
            Path.home() / '.var/app/com.valvesoftware.Steam/.local/share/Steam') if p.is_dir()}
        if len(candidates) > 1:
            raise ValueError('Multiple Steam roots; set --steam-root: ' + ', '.join(map(str, sorted(candidates))))
        steam_root = next(iter(candidates), Path.home() / '.local/share/Steam')
    steam_root = absolute(steam_root)
    game = absolute(values['half_life_dir'] or steam_root / 'steamapps/common/Half-Life')
    return steam_root, game


def probe(values):
    steam_root, game = game_paths(values)
    errors = []
    editor = values['editor_path'] or shutil.which('Jack') or shutil.which('jack')
    editor_dir = None
    editor_info = None
    try:
        if not editor:
            raise ValueError('Set --editor-path to your JACK installation directory or executable')
        argv, editor_dir, env = editor_command(editor)
        editor_info = {'argv': argv, 'cwd': str(editor_dir), 'sha256': sha256(argv[0]),
                       'LD_LIBRARY_PATH': env['LD_LIBRARY_PATH']}
    except (ValueError, OSError, RuntimeError) as exc:
        errors.append(str(exc))
    steam = values['steam_executable'] or shutil.which('steam') or steam_root / 'steam.sh'
    try:
        steam = str(executable(steam))
    except (ValueError, OSError, RuntimeError) as exc:
        errors.append(str(exc))
        steam = None
    targets = {}
    for target, dll in [('valve', 'hl.so'), ('cstrike', 'cs.so')]:
        mod = game / target
        fgd_default = (editor_dir / 'halflife/halflife.fgd' if editor_dir else None) if target == 'valve' else mod / 'halflife-cs.fgd'
        fgd_value = values[target + '_fgd'] or fgd_default
        fgd = absolute(fgd_value) if fgd_value else None
        # Baseline for these fixtures, not every possible map or game release.
        required = [game / 'hl.sh', game / 'hl_linux', game / 'valve/halflife.wad',
                    mod / 'liblist.gam', mod / 'dlls' / dll, mod / 'cl_dlls/client.so']
        if target == 'cstrike':
            required += [mod / 'cstrike.wad']
        missing = [str(p) for p in required if not p.is_file()]
        if not fgd or not fgd.is_file():
            missing.append(str(fgd or 'valve FGD: set --valve-fgd'))
        errors.extend(f'{target}: missing {p}' for p in missing)
        targets[target] = {'game_directory': str(mod), 'fgd': str(fgd) if fgd else None,
                           'wads': [str(p) for p in sorted(mod.glob('*.wad'))], 'missing': missing}
    return {'system': platform.system(), 'architecture': platform.machine(),
            'python': platform.python_version(), 'steam_root': str(steam_root),
            'steam_executable': steam, 'half_life_dir': str(game), 'editor': editor_info,
            'targets': targets, 'errors': errors,
            'limitations': ['M0 probe uses explicit game-root override for other Steam libraries; VDF discovery is M1.',
                            'File presence does not verify GUI rendering or game loading.']}


def inspect_bsp(path):
    """Require a compiled BSP30 with no appended source archive or other tail."""
    path = Path(path)
    data = path.read_bytes()
    if len(data) < 124 or struct.unpack_from('<i', data)[0] != 30:
        raise ValueError('Expected a GoldSrc BSP version 30 header')
    lumps = [struct.unpack_from('<ii', data, 4 + i * 8) for i in range(15)]
    for offset, length in lumps:
        if offset < 0 or length < 0 or offset + length > len(data) or (length and offset < 124):
            raise ValueError('BSP lump outside file bounds')
    for index in (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14):
        if not lumps[index][1]:
            raise ValueError(f'Expected nonempty compiled lump {index}')
    occupied = sorted((o, o + n) for o, n in lumps if n)
    if any(end > next_start for (_, end), (next_start, _) in zip(occupied, occupied[1:])):
        raise ValueError('Overlapping BSP lumps')
    end = max(o + n for o, n in lumps)
    tail = data[end:]
    if zipfile.is_zipfile(path) or len(tail) > 3 or any(tail):
        raise ValueError('BSP has appended data (possible embedded MAP source)')
    return {'version': 30, 'bytes': len(data), 'sha256': sha256(path),
            'lump_lengths': [n for _, n in lumps], 'embedded_source': False,
            'trailing_alignment_bytes': len(tail)}


def smoke(values, compiler):
    _, game = game_paths(values)
    wad = game / 'valve/halflife.wad'
    if not wad.is_file():
        raise ValueError(f'Missing fixture WAD: {wad}; set --half-life-dir')
    # The upstream WAD config tokenizer has no quoting escape mechanism.
    if any(c in str(wad) for c in ('"', '\n', '\r')):
        raise ValueError('WAD path cannot contain quotes or newlines')
    compiler = executable(compiler)
    with (ROOT / 'tools/versions.lock.toml').open('rb') as stream:
        pin = tomllib.load(stream)['hltools']
    output_root = ROOT / 'build/m0'
    output_root.mkdir(parents=True, exist_ok=True)
    output = Path(tempfile.mkdtemp(prefix='smoke-', dir=output_root))
    source = ROOT / 'fixtures/m0/sdk_m0_room.map'
    staged = output / source.name
    shutil.copyfile(source, staged)
    wad_config = output / 'wad.cfg'
    wad_config.write_text(f'"{wad}"\n')
    argv = [str(compiler), 'compile', *pin['compile_options'], '-wadcfgfile', str(wad_config), str(staged)]
    print(shlex.join(argv), flush=True)
    with (output / 'compile.log').open('w') as log:
        result = subprocess.run(argv, cwd=output, stdout=log, stderr=subprocess.STDOUT)
    if result.returncode:
        raise ValueError(f'Compile exited {result.returncode}; see {output / "compile.log"}')
    bsp = staged.with_suffix('.bsp')
    report = {'command': argv, 'cwd': str(output), 'compiler_sha256': sha256(compiler),
              'expected_revision': pin['revision'], 'source_sha256': sha256(source),
              'wad_sha256': sha256(wad), 'bsp': inspect_bsp(bsp)}
    # Supplying another compiler is permitted; never pretend its hash proves the pin.
    with (output / 'bsp-info.log').open('w') as log:
        subprocess.run([str(compiler), 'bsp', 'info', str(bsp)], cwd=output,
                       stdout=log, stderr=subprocess.STDOUT, check=True)
    report['outputs'] = sorted(p.name for p in output.iterdir())
    (output / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report['bsp'], indent=2))
    print(f'Artifacts and logs: {output}')
    return 0


def parser():
    top = argparse.ArgumentParser(description=__doc__)
    commands = top.add_subparsers(dest='command', required=True)
    for name in ('probe', 'editor', 'smoke'):
        sub = commands.add_parser(name)
        sub.add_argument('--config', default=str(ROOT / '.local/user.toml'))
        for key in PATH_KEYS:
            sub.add_argument('--' + key.replace('_', '-'))
        if name == 'editor':
            sub.add_argument('--map', help='Optional map to open; resolved before changing cwd')
            sub.add_argument('--dry-run', action='store_true')
        if name == 'smoke':
            sub.add_argument('--compiler', default=str(ROOT / '.local/src/hltools/bin/hltools'))
    inspect = commands.add_parser('inspect')
    inspect.add_argument('bsp', type=Path)
    return top


def main(argv=None):
    args = parser().parse_args(argv)
    try:
        if args.command == 'inspect':
            print(json.dumps(inspect_bsp(args.bsp), indent=2))
            return 0
        values = settings(args)
        if args.command == 'probe':
            report = probe(values)
            print(json.dumps(report, indent=2))
            return 1 if report['errors'] else 0
        if args.command == 'smoke':
            return smoke(values, args.compiler)
        editor = values['editor_path'] or shutil.which('Jack') or shutil.which('jack')
        if not editor:
            raise ValueError('Set --editor-path to the JACK directory or executable')
        argv, cwd, env = editor_command(editor, args.map)
        print(json.dumps({'argv': argv, 'cwd': str(cwd), 'LD_LIBRARY_PATH': env['LD_LIBRARY_PATH']}, indent=2), flush=True)
        if args.dry_run:
            return 0
        return subprocess.run(argv, cwd=cwd, env=env).returncode
    except (OSError, ValueError, RuntimeError, subprocess.CalledProcessError) as exc:
        print(f'error: {exc}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
