from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
import os
from .aws_connector import get_table
from .models import EvaluationIn, EvaluationOut
from .evaluation_service import (
    create_evaluation,
    get_evaluation,
    list_evaluations_for_client,
)
from .credentials_manager import (
    assume_role,
    store_secret_for_keys,
    validate_keys,
    register_credential_record,
)
from .auth import require_api_key
from .cognito_auth import require_cognito_auth
from pydantic import BaseModel
from typing import Optional
import uuid
from datetime import datetime
from .scores_service import create_score, get_score, list_scores_for_evaluation
from .security_service import SecurityService

APP_TABLES = {
    'clients': 'autowar-clients',
    'evaluations': 'autowar-evaluations',
    'scores': 'autowar-scores',
}

app = FastAPI(title='AutoWAR API')


class ClientIn(BaseModel):
    id: str
    name: str
    industry: str | None = None


@app.get('/health')
async def health():
    return {'status': 'ok'}


@app.get('/clients')
def list_clients():
    table = get_table(APP_TABLES['clients'])
    resp = table.scan()
    items = resp.get('Items', [])
    return {'count': len(items), 'items': items}


@app.post('/clients', status_code=201)
def create_client(client: ClientIn, claims: dict = Depends(require_cognito_auth)):
    table = get_table(APP_TABLES['clients'])
    item = client.dict()
    try:
        table.put_item(Item=item)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return {'ok': True, 'item': item}


# Evaluations endpoints
@app.post('/evaluations', status_code=201, response_model=EvaluationOut)
def api_create_evaluation(evaluation: EvaluationIn, claims: dict = Depends(require_cognito_auth)):
    try:
        item = create_evaluation(evaluation)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return item


@app.get('/evaluations/{evaluation_id}')
def api_get_evaluation(evaluation_id: str):
    item = get_evaluation(evaluation_id)
    if not item:
        raise HTTPException(status_code=404, detail='Evaluation not found')
    return item


@app.get('/clients/{client_id}/evaluations')
def api_list_evaluations_for_client(client_id: str, limit: int = 50):
    items = list_evaluations_for_client(client_id, limit=limit)
    return {'count': len(items), 'items': items}


# Credentials management
class CredentialsIn(BaseModel):
    client_id: str
    role_arn: Optional[str] = None
    external_id: Optional[str] = None
    access_key_id: Optional[str] = None
    secret_access_key: Optional[str] = None
    session_token: Optional[str] = None
    region: Optional[str] = None
    save_secret: Optional[bool] = True


@app.post('/credentials', status_code=201, dependencies=[Depends(require_api_key)])
def api_create_credentials(payload: CredentialsIn):
    # Prefer AssumeRole when role_arn is provided
    if payload.role_arn:
        session_name = f"autowar-{uuid.uuid4()}"
        try:
            resp = assume_role(payload.role_arn, session_name, external_id=payload.external_id, region=payload.region)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"AssumeRole failed: {e}")
        # register metadata (do not store secrets)
        rec = {
            'type': 'role',
            'role_arn': payload.role_arn,
            'caller_identity': resp.get('caller_identity'),
            'status': 'ACTIVE',
        }
        saved = register_credential_record(payload.client_id, rec)
        return {'ok': True, 'record': saved}

    # Fallback: keys provided
    if payload.access_key_id and payload.secret_access_key:
        try:
            identity = validate_keys(payload.access_key_id, payload.secret_access_key, payload.session_token, payload.region)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Credential validation failed: {e}")
        secret_arn = None
        if payload.save_secret:
            try:
                secret_arn = store_secret_for_keys(payload.client_id, payload.access_key_id, payload.secret_access_key, payload.session_token, payload.region)
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Secrets Manager error: {e}")
        rec = {
            'type': 'keys',
            'caller_identity': identity,
            'secret_arn': secret_arn,
            'status': 'ACTIVE',
        }
        saved = register_credential_record(payload.client_id, rec)
        return {'ok': True, 'record': saved}

    raise HTTPException(status_code=400, detail='Provide either role_arn or access_key_id+secret_access_key')


# Per-BP scoring
class ScoreIn(BaseModel):
    evaluation_id: str
    bp_id: str
    scores: dict


class ScoreOut(ScoreIn):
    id: str
    total: float
    created_at: str


@app.post('/scores', status_code=201, response_model=ScoreOut)
def api_create_score(payload: ScoreIn, claims: dict = Depends(require_cognito_auth)):
    try:
        item = create_score(payload)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return item


@app.get('/scores/{score_id}')
def api_get_score(score_id: str):
    item = get_score(score_id)
    if not item:
        raise HTTPException(status_code=404, detail='Score not found')
    return item


@app.get('/evaluations/{evaluation_id}/scores')
def api_list_scores_for_evaluation(evaluation_id: str, limit: int = 50):
    items = list_scores_for_evaluation(evaluation_id, limit=limit)
    return {'count': len(items), 'items': items}


# Security Service Routes
@app.post('/security/evaluate/{question_id}', dependencies=[Depends(require_cognito_auth)])
async def evaluate_security_question(evaluation_id: str, question_id: str):
    """Evaluate a specific security question"""
    dynamodb = get_table('autowar-waf-questions')  # Get resource
    service = SecurityService(dynamodb, 'autowar-waf-questions')
    result = await service.evaluate_security_question(evaluation_id, question_id)
    return result


@app.get('/security/evaluations/{evaluation_id}/{question_id}', dependencies=[Depends(require_cognito_auth)])
def get_security_evaluation(evaluation_id: str, question_id: str):
    """Get security evaluation for specific question"""
    dynamodb = get_table('autowar-waf-questions')
    service = SecurityService(dynamodb, 'autowar-waf-questions')
    result = service.get_security_evaluation(evaluation_id, question_id)
    if not result:
        raise HTTPException(status_code=404, detail='Security evaluation not found')
    return result


@app.get('/security/evaluations/{evaluation_id}', dependencies=[Depends(require_cognito_auth)])
def list_security_evaluations(evaluation_id: str):
    """List all security evaluations for an evaluation"""
    dynamodb = get_table('autowar-waf-questions')
    service = SecurityService(dynamodb, 'autowar-waf-questions')
    items = service.list_security_evaluations_for_evaluation(evaluation_id)
    return {'count': len(items), 'items': items}
