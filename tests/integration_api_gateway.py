import requests
import json

BASE = "https://k9yu787voe.execute-api.us-east-1.amazonaws.com/prod"

def pretty(resp):
    try:
        return json.dumps(resp.json(), indent=2)
    except Exception:
        return resp.text

payload = {
    'evaluation_id': 'int-test-eval-1',
    'bp_id': 'bp-int-001',
    'scores': {'s1': 3, 's2': 4.5, 's3': 2}
}

print('POST', BASE + '/scores')
try:
    r = requests.post(BASE + '/scores', json=payload, timeout=10)
    print(r.status_code)
    print(pretty(r))
    if r.status_code in (200,201):
        item = r.json()
        sid = item.get('id')
        if sid:
            print('\nGET /scores/{id}')
            r2 = requests.get(BASE + f'/scores/{sid}', timeout=10)
            print(r2.status_code)
            print(pretty(r2))

            print('\nGET /evaluations/int-test-eval-1/scores')
            r3 = requests.get(BASE + '/evaluations/int-test-eval-1/scores', timeout=10)
            print(r3.status_code)
            print(pretty(r3))
    else:
        print('POST failed; skipping GETs')
except Exception as e:
    print('Error:', e)
