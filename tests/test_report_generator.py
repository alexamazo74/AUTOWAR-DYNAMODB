import json

def test_report_generator_puts_report_and_updates_table(monkeypatch):
    # Fake event
    event = {'Records': [{'body': json.dumps({'evaluationId': 'ev-1'})}]}

    class FakeTable:
        def __init__(self):
            self.items = {}

        def get_item(self, Key=None):
            return {'Item': {'id': Key['id'], 'evaluationId': Key['id'], 'created_at': 1, 'results': []}}

        def update_item(self, Key=None, UpdateExpression=None, ExpressionAttributeValues=None):
            self.items[Key['id']] = ExpressionAttributeValues

    class FakeS3:
        def __init__(self):
            self.objects = {}

        def put_object(self, Bucket, Key, Body):
            self.objects[Key] = Body

    fake_table = FakeTable()
    fake_reports_table = FakeTable()
    fake_s3 = FakeS3()

    import src.lambdas.report_generator as rg

    monkeypatch.setenv('REPORTS_BUCKET', 'my-bucket')
    monkeypatch.setenv('RENDERER_URL', 'https://fake-renderer.local/render')
    monkeypatch.setattr(rg, 'dynamo', type('D', (), {'Table': lambda name: fake_table if name == 'autowar-evaluations' else fake_reports_table}))
    monkeypatch.setattr(rg, 's3', fake_s3)

    # mock httpx.post to return bytes (PDF)
    class FakeResp:
        def __init__(self, content):
            self.content = content

        def raise_for_status(self):
            return None

    monkeypatch.setattr(rg, 'httpx', type('H', (), {'post': lambda url, json, timeout: FakeResp(b'%PDF-1.4 fakepdf')}))

    res = rg.handler(event, {})
    assert res['processed'] == 1
    # verify reports table updated
    assert 'ev-1' in fake_reports_table.items
