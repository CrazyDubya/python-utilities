"""Actual app imports in fresh processes; synthetic in-memory queues only."""
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest

PROJECT = Path(os.environ.get('QUEUE_APP_SOURCE', Path(__file__).resolve().parents[1]))
PROGRAM = '''
import json,socket
attempts=[]
def deny(*args,**kwargs):
 attempts.append(1)
 raise RuntimeError('No network')
socket.create_connection=deny
from app import app
from app import routes
from app.config import Config
routes.queue[:]=['seed']
routes.queue_position.clear();routes.queue_position['seed']=1
client=app.test_client();rows=[]
for label,headers in [('missing',{}),('incorrect',{'X-API-Key':'wrong'}),('correct',{'X-API-Key':'synthetic-key'})]:
 for method,path,data in [('GET','/queue/seed',None),('POST','/queue',{'name':'fixture-'+label}),('POST','/queue/next',{})]:
  before=[list(routes.queue),dict(routes.queue_position)]
  result=client.open(path,method=method,json=data,headers=headers)
  after=[list(routes.queue),dict(routes.queue_position)]
  rows.append({'key':label,'method':method,'path':path,'status':result.status_code,'body':result.get_json(),'unchanged':before==after})
print(json.dumps({'required':Config.REQUIRE_API_KEY,'rows':rows,'network_attempts':attempts}))
'''

class BasicAuthToggleTests(unittest.TestCase):
    def run_app(self, required=None, keys='synthetic-key'):
        env = {**os.environ, 'API_KEYS': keys, 'PYTHONPATH': str(PROJECT)}
        env.pop('REQUIRE_API_KEY', None)
        if required is not None:
            env['REQUIRE_API_KEY'] = required
        result = subprocess.run([sys.executable, '-c', PROGRAM], cwd=PROJECT,
                                env=env, text=True, capture_output=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    def test_required_rejects_missing_wrong_before_state_changes(self):
        data = self.run_app('true')
        self.assertTrue(data['required'])
        self.assertEqual(data['network_attempts'], [])
        for row in data['rows']:
            if row['key'] == 'correct':
                self.assertEqual(row['status'], 200, row)
            else:
                self.assertEqual(row['status'], 401, row)
                self.assertTrue(row['unchanged'], row)
                self.assertEqual(row['body']['error'], 'Unauthorized')

    def test_default_off_keeps_basic_api_compatibility(self):
        data = self.run_app()
        self.assertFalse(data['required'])
        self.assertTrue(all(row['status'] == 200 for row in data['rows']))
        self.assertEqual(data['network_attempts'], [])

    def test_required_without_configured_keys_rejects_every_key(self):
        data = self.run_app('true', '')
        self.assertTrue(all(row['status'] == 401 and row['unchanged'] for row in data['rows']))
        self.assertEqual(data['network_attempts'], [])

if __name__ == '__main__':
    unittest.main()
