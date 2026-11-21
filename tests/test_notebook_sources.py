from pathlib import Path
import json
import os
import subprocess
import sys
import tempfile
import unittest

SOURCE = Path(os.environ.get('CODE_SCANNER_SOURCE', Path(__file__).resolve().parents[1] / 'utilities/code_scanner.py'))
CODE = 'def example():\n    value = "α"\n\n    return value\n'
MARKDOWN = '# Example\n\nIndented content:\n    literal\n'

class NotebookSourceTests(unittest.TestCase):
    def scan(self, files):
        with tempfile.TemporaryDirectory(prefix='code-scanner-regression-') as temp:
            directory = Path(temp)
            for name, body in files.items():
                (directory / name).write_text(body, encoding='utf-8')
            result = subprocess.run([sys.executable, str(SOURCE)], cwd=directory,
                                    text=True, capture_output=True, timeout=10)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertNotIn('Error reading', result.stdout)
            self.assertEqual({p.name: p.read_text(encoding='utf-8') for p in directory.iterdir()}, files)
            return result.stdout

    def notebook(self, convert):
        return json.dumps({'nbformat':4, 'nbformat_minor':4, 'metadata':{}, 'cells':[
            {'cell_type':'markdown', 'metadata':{}, 'source':convert(MARKDOWN)},
            {'cell_type':'code', 'metadata':{}, 'source':convert(CODE), 'outputs':[], 'execution_count':None}]})

    def expected(self, markdown, code):
        return '\n' + '=' * 80 + '\nFILE: ./fixture.ipynb\n' + '=' * 80 + '\n' + markdown + '\nCODE:\n' + code + '\n'

    def test_string_source_preserves_exact_text(self):
        self.assertEqual(self.scan({'fixture.ipynb':self.notebook(lambda x:x)}), self.expected(MARKDOWN,CODE))

    def test_list_source_preserves_exact_text(self):
        self.assertEqual(self.scan({'fixture.ipynb':self.notebook(lambda x:x.splitlines(keepends=True))}), self.expected(MARKDOWN,CODE))

    def test_chunks_need_not_end_with_newline(self):
        self.assertEqual(self.scan({'fixture.ipynb':self.notebook(lambda x:[x[:3],x[3:]])}), self.expected(MARKDOWN,CODE))

    def test_empty_and_missing_source(self):
        for source in ['', [], None]:
            cells=[{'cell_type':t,'metadata':{}} for t in ['markdown','code']]
            if source is not None:
                for cell in cells:cell['source']=source
            text=json.dumps({'nbformat':4,'nbformat_minor':4,'metadata':{},'cells':cells})
            self.assertEqual(self.scan({'fixture.ipynb':text}), self.expected('',''))

    def test_plain_python_and_config_content_unchanged(self):
        for name,body in [('fixture.py', CODE),('config.ini','[fixture]\nvalue = yes\n'),('requirements.txt','example==1.0\n')]:
            output=self.scan({name:body})
            self.assertEqual(output,'\n'+'='*80+'\nFILE: ./'+name+'\n'+'='*80+'\n'+body+'\n')

if __name__ == '__main__':
    unittest.main()
