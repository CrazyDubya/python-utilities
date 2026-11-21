from pathlib import Path
import csv
import json
import os
import subprocess
import sys
import tempfile
import unittest

SOURCE=Path(os.environ.get('CONVERSATION_ANALYZER_SOURCE',Path(__file__).resolve().parents[1]/'data_processing/conversation_analyzer.py'))

class AsyncDefinitionTests(unittest.TestCase):
    def analyze(self, conversations, summary_only=False):
        with tempfile.TemporaryDirectory(prefix='conversation-functions-')as temp:
            root=Path(temp);source=root/'conversations.json';out=root/'result'
            data=[{'mapping':{str(index):{'message':{'author':{'role':'assistant'},'content':{'parts':[text]}}}for index,text in enumerate(messages)}}for messages in conversations]
            text=json.dumps(data);source.write_text(text)
            command=[sys.executable,str(SOURCE),str(source),'--output-dir',str(out)]
            if summary_only:command.append('--summary-only')
            result=subprocess.run(command,capture_output=True,text=True,timeout=15)
            self.assertEqual(result.returncode,0,result.stderr);self.assertNotIn('Analysis error:',result.stdout)
            self.assertEqual(source.read_text(),text)
            if summary_only:
                self.assertFalse(out.exists());return result.stdout,{},{}
            with (out/'function_counts.csv').open(newline='')as f:
                rows=list(csv.DictReader(f))
            functions={(row['Function'],row['Conversation']):int(row['Count'])for row in rows}
            return result.stdout,functions,{p.name:p.read_text()for p in out.iterdir()}

    def test_sync_async_and_nested_definitions_from_full_cli(self):
        code='```python\nraise RuntimeError("Fixture must never execute")\ndef sync_outer():\n    async def async_inner():\n        return 1\n\nasync def async_outer():\n    def sync_inner():\n        return 2\n```'
        summary,functions,files=self.analyze([[code]])
        self.assertEqual(functions,{(name,'conversation_0'):1 for name in ['sync_outer','async_inner','async_outer','sync_inner']})
        self.assertIn('Unique Functions Found: 4',summary)
        self.assertEqual(files['code_block_counts.csv'],'Language,Count\npython,1\n')

    def test_existing_per_conversation_same_name_counts_preserved(self):
        sync='```python\ndef shared():\n    pass\n```';async_code='```python\nasync def shared():\n    pass\n```'
        summary,functions,_=self.analyze([[sync,async_code],[async_code]])
        self.assertEqual(functions,{('shared','conversation_0'):2,('shared','conversation_1'):1})
        self.assertIn('Unique Functions Found: 2',summary)
        self.assertIn('Total Code Blocks: 3',summary)

    def test_sync_invalid_and_nonpython_controls(self):
        code='```python\ndef sync_control():\n    pass\n```\n```python\ndef invalid(:\n```\n```javascript\nasync function ignored() {}\n```'
        summary,functions,files=self.analyze([[code]])
        self.assertEqual(functions,{('sync_control','conversation_0'):1})
        self.assertIn('Unique Functions Found: 1',summary)
        self.assertEqual(files['function_counts.csv'],'Function,Conversation,Count\nsync_control,conversation_0,1\n')
        self.assertEqual(files['code_block_counts.csv'],'Language,Count\npython,2\njavascript,1\n')

    def test_summary_only_reports_async_without_writing_csvs(self):
        summary,_,_=self.analyze([['```python\nasync def only_async():\n    pass\n```']],True)
        self.assertIn('Unique Functions Found: 1',summary)

if __name__=='__main__':
    unittest.main()
