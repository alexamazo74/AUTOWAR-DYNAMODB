import requests
import json

BASE = "https://k9yu787voe.execute-api.us-east-1.amazonaws.com/prod"

payload = {
    'evaluation_id': 'int-test-eval-1',
    'bp_id': 'bp-int-001',
    'scores': {'s1': 3, 's2': 4.5, 's3': 2}
}

print('POST', BASE + '/public-scores')
try:
    r = requests.post(BASE + '/public-scores', json=payload, timeout=10)
    print(r.status_code)
    try:
        print(json.dumps(r.json(), indent=2))
    except Exception:
        print(r.text)
except Exception as e:
    print('Error:', e)
