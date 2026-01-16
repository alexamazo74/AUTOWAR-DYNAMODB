import json


def test_evaluation_worker_processes_message(monkeypatch):
    # Fake event with one SQS record
    evaluation_item = {
        "id": "ev-1",
        "evaluationId": "ev-1",
        "client_id": "c1",
        "targets": [{"type": "s3", "name": "my-bucket"}],
        "region": "us-east-1",
    }

    event = {
        "Records": [
            {"body": json.dumps({"evaluationId": "ev-1", "item": evaluation_item})}
        ]
    }

    # Fake dynamo tables
    class FakeTable:
        def __init__(self):
            self.items = {}

        def update_item(
            self,
            Key=None,
            UpdateExpression=None,
            ExpressionAttributeNames=None,
            ExpressionAttributeValues=None,
        ):
            self.items[Key["id"]] = ExpressionAttributeValues

        def put_item(self, Item=None):
            self.items[Item["id"]] = Item

    fake_eval_table = FakeTable()
    fake_evidence_table = FakeTable()

    import src.lambdas.evaluation_worker as worker

    monkeypatch.setattr(
        worker,
        "dynamo",
        type(
            "D",
            (),
            {
                "Table": lambda name: (
                    fake_eval_table
                    if name == "autowar-evaluations"
                    else fake_evidence_table
                )
            },
        ),
    )

    # monkeypatch validators runner to return a sample result
    def fake_run_validators(targets, region=None, account_id=None):
        return [
            {
                "name": "s3-public-access",
                "resource": "my-bucket",
                "status": "PASS",
                "details": {"public_block": True},
            }
        ]

    import src.app.validators.manager as vm

    monkeypatch.setattr(vm, "run_validators_for_evaluation", fake_run_validators)

    res = worker.handler(event, {})
    assert res["processed"] == 1
    # verify evaluation table got updated
    assert "ev-1" in fake_eval_table.items
