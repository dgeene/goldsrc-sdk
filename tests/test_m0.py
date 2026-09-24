"""Boundary tests for M0's launcher and source-archive guard."""
import importlib.util
import io
import json
import os
from pathlib import Path
import struct
import subprocess
import tempfile
import unittest
from unittest.mock import patch
import zipfile

SPEC = importlib.util.spec_from_file_location('m0', Path(__file__).resolve().parents[1] / 'tools/m0.py')
m0 = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(m0)


class LauncherTests(unittest.TestCase):
    def test_directory_spaces_unicode_cwd_and_arguments(self):
        with tempfile.TemporaryDirectory(prefix='JACK spaces ü ') as tmp:
            root = Path(tmp)
            binary = root / 'Jack'
            binary.write_text('#!/usr/bin/env python3\nimport os,sys,json\nprint(json.dumps([os.getcwd(),sys.argv[1:],os.environ["LD_LIBRARY_PATH"]]))\n')
            binary.chmod(0o755)
            source = root / 'map ; $(ignored).map'
            source.touch()
            env = dict(os.environ, LD_LIBRARY_PATH='/existing::')
            argv, cwd, env = m0.editor_command(root, source, env)
            result = subprocess.run(argv, cwd=cwd, env=env, capture_output=True, text=True, check=True)
            self.assertEqual(json.loads(result.stdout), [str(root), [str(source)], str(root) + ':/existing'])

    def test_symlink_uses_actual_install_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            binary = root / 'install/Jack'
            binary.parent.mkdir()
            binary.touch(); binary.chmod(0o755)
            link = root / 'launcher'
            link.symlink_to(binary)
            argv, cwd, _ = m0.editor_command(link, environ={})
            self.assertEqual(cwd, binary.parent)
            self.assertEqual(argv, [str(binary)])

    def test_reject_non_executable_and_loop(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'Jack').touch()
            with self.assertRaises(ValueError):
                m0.editor_command(root)
            (root / 'loop').symlink_to('loop')
            with self.assertRaises((RuntimeError, OSError)):
                m0.editor_command(root / 'loop')

    def test_override_precedence_and_custom_library(self):
        with tempfile.TemporaryDirectory() as tmp:
            cfg = Path(tmp) / 'user.toml'
            cfg.write_text('[paths]\nhalf_life_dir="/config/library"\nsteam_root="/config/Steam"\n')
            args = m0.parser().parse_args(['probe', '--config', str(cfg), '--half-life-dir', tmp])
            with patch.dict(os.environ, {'GOLDSRC_HALF_LIFE_DIR': '/env/library', 'GOLDSRC_STEAM_ROOT': '/env/Steam'}):
                values = m0.settings(args)
            steam, game = m0.game_paths(values)
            self.assertEqual(game, Path(tmp))
            self.assertEqual(steam, Path('/env/Steam'))

    def test_steam_directory_is_not_an_executable(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                m0.executable(tmp)


class BspTests(unittest.TestCase):
    @staticmethod
    def bsp():
        # Synthetic nonempty lumps test container validation, not engine semantics.
        return struct.pack('<i', 30) + b''.join(struct.pack('<ii', 124 + i * 4, 4) for i in range(15)) + b'\0' * 60

    def inspect(self, data):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'test.bsp'
            path.write_bytes(data)
            return m0.inspect_bsp(path)

    def test_plain_bsp_accepted(self):
        self.assertFalse(self.inspect(self.bsp())['embedded_source'])

    def test_appended_source_zip_rejected(self):
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, 'w') as archive:
            archive.writestr('source.map', '{ "classname" "worldspawn" }')
        with self.assertRaisesRegex(ValueError, 'appended'):
            self.inspect(self.bsp() + buf.getvalue())

    def test_corruption_rejected(self):
        for data in (b'bad', struct.pack('<i', 29) + self.bsp()[4:], self.bsp()[:-1],
                     self.bsp() + b'unexpected tail', self.bsp()[:4] + struct.pack('<ii', 120, 4) + self.bsp()[12:]):
            with self.subTest(data=data[:12]), self.assertRaises(ValueError):
                self.inspect(data)

    def test_overlap_rejected(self):
        data = self.bsp()[:12] + struct.pack('<ii', 124, 4) + self.bsp()[20:]
        with self.assertRaisesRegex(ValueError, 'Overlapping'):
            self.inspect(data)


if __name__ == '__main__':
    unittest.main()
