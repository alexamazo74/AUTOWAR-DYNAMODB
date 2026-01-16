import os
import pytest
import requests

# Allow CI to override endpoint. Default matches previous API Gateway endpoint.
BASE = os.getenv(
    "PUBLIC_SCORES_URL",
    "https://k9yu787voe.execute-api.us-east-1.amazonaws.com/prod/public-scores",
)

payload = {
    "evaluation_id": "ci-test-eval-1",
    "bp_id": "bp-ci-001",
    "scores": {"s1": 3, "s2": 4.5, "s3": 2},
}


def test_public_scores_echo():
    r = requests.post(BASE, json=payload, timeout=10)
    assert r.status_code == 200
    # The mock integration returns an empty JSON body by default; at least ensure valid JSON
    try:
        data = r.json()
    except ValueError:
        pytest.fail("Response not JSON")
    assert isinstance(data, dict)
