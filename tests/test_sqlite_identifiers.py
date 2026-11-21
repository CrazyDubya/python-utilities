"""Exercise the complete scanner CLI on disposable SQLite fixtures."""
from pathlib import Path
import hashlib
import os
import sqlite3
import subprocess
import sys
import tempfile
import unittest

SOURCE = Path(os.environ.get('SCANNER_SOURCE', Path(__file__).resolve().parents[1] / 'utilities/directory_scanner.py'))

class SQLiteIdentifierTests(unittest.TestCase):
    def check_identifier(self, name):
        with tempfile.TemporaryDirectory(prefix='scanner-regression-') as directory:
            db = Path(directory) / 'fixture.db'
            quoted = '"' + name.replace('"', '""') + '"'
            with sqlite3.connect(db) as conn:
                conn.execute(f'CREATE TABLE {quoted} (id INTEGER, note TEXT)')
                conn.executemany(f'INSERT INTO {quoted} VALUES (?, ?)', [(1, 'first'), (2, 'second')])
                conn.execute('CREATE TABLE tail_control (value TEXT)')
            before = hashlib.sha256(db.read_bytes()).hexdigest()
            result = subprocess.run([sys.executable, str(SOURCE), directory],
                                    text=True, capture_output=True, timeout=10)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertNotIn('Error reading database:', result.stdout)
            self.assertIn(f'Table: {name}\n  id INTEGER\n  note TEXT\n  Rows: 2', result.stdout)
            self.assertIn('Table: tail_control\n  value TEXT\n  Rows: 0', result.stdout)
            self.assertIn('Tables: 2', result.stdout)
            self.assertIn('Processed 1 files.', result.stdout)
            self.assertEqual(hashlib.sha256(db.read_bytes()).hexdigest(), before)
            self.assertEqual(sorted(p.name for p in Path(directory).iterdir()), ['fixture.db'])

    def test_ordinary_table(self):
        self.check_identifier('ordinary')

    def test_spaced_table(self):
        self.check_identifier('order items')

    def test_keyword_table(self):
        self.check_identifier('select')

    def test_double_quote_in_table_name(self):
        self.check_identifier('embedded"quote')

if __name__ == '__main__':
    unittest.main()
