"""Optional full emitted-project tests: networkx, pybind11, CMake and C++17 required.

No packages are installed by this test. No benchmark or network is used.
"""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SOURCE = Path(os.environ.get('PYTOCPP_SOURCE', Path(__file__).resolve().parents[1]))


class EmittedStringValues(unittest.TestCase):
    def check_values(self, values):
        with tempfile.TemporaryDirectory(prefix='pytocpp-strings-') as td:
            root = Path(td)
            source = root / 'input.py'
            source.write_text('\n\n'.join(
                f'def value_{i}() -> str:\n    return {value!r}'
                for i, value in enumerate(values)
            ) + '\n')
            out, build = root / 'generated', root / 'build'
            env = dict(os.environ, PYTHONPATH=str(SOURCE), PYTHONDONTWRITEBYTECODE='1')
            def run(command, stage, **kwargs):
                result = subprocess.run(command, cwd=root, env=env, text=True,
                                        capture_output=True, timeout=120, **kwargs)
                self.assertEqual(result.returncode, 0,
                                 f'{stage}\n{result.stdout}\n{result.stderr}')
                return result
            bind = run([sys.executable, '-m', 'pybind11', '--cmakedir'], 'pybind directory').stdout.strip()
            run([sys.executable, '-m', 'src.main', str(source), '--output-dir', str(out),
                 '--skip-benchmarks'], 'complete CLI generation')
            run(['cmake', '-S', str(out), '-B', str(build), '-Dpybind11_DIR=' + bind,
                 '-DPYTHON_EXECUTABLE=' + sys.executable], 'configure emitted project')
            run(['cmake', '--build', str(build), '--parallel', '2'], 'build emitted executable and module')
            run([str(build / 'pytocpp_generated')], 'run emitted executable')
            script = (
                'import sys,json;sys.path.insert(0,sys.argv[1]);import cpp_impl;'
                'print(json.dumps([getattr(cpp_impl,"value_"+str(i))()'
                ' for i in range(int(sys.argv[2]))]))'
            )
            called = run([sys.executable, '-c', script, str(build), str(len(values))],
                         'call compiled module')
            self.assertEqual(json.loads(called.stdout), values)

    def test_ordinary_and_quote_controls(self):
        self.check_values(['Hello World', 'He said "Hello"', ''])

    def test_decoded_line_feed(self):
        self.check_values(['Hello\nWorld', '\n\n'])

    def test_literal_backslash_sequences(self):
        self.check_values(['C:\\new\\folder', '\\n is not a newline'])

    def test_mixed_line_feed_backslash_quote_and_trailing_backslash(self):
        self.check_values(['first\n"quoted" \\second\\', '\\"\n'])
