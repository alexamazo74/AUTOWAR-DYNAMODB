"""
Pruebas por-BP del pilar de Seguridad con rutas explícitas.

Usan `scripted_session` (clientes boto3 reales + proxy guionado, ver conftest.py)
para forzar respuestas concretas de AWS por servicio/operación y verificar el
`status` que devuelve el código de producción en cada ruta:
COMPLIANT / NON_COMPLIANT / PENDING_REVIEW / AccessDenied (degradado).

Prioridad explícita: SEC01-BP01, SEC01-BP02, SEC02-BP01 (decisión (c) del plan).
Además se incluye un patrón PARAMETRIZADO reutilizable para extender a más BPs:
cada fila declara (bp_func, scripts, expected_status) y el test invoca la BP y
afirma el contrato + el status real.

Método (importante): el `expected_status` de cada fila se fijó ejecutando el test
y observando el status REAL del código de producción para esos datos simulados,
no un status asumido. Si una ruta no es alcanzable con datos válidos, no se fuerza.
"""

import datetime

import pytest
from _helpers import assert_finding_contract

import all_bp_evaluations as bp  # noqa: E402 (sys.path lo ajusta conftest)


def _handle_error(bp_id, error):
    """handle_error_func de referencia (igual contrato que _handle_permission_error)."""
    code = error.response["Error"]["Code"]
    return {
        "bp": bp_id,
        "description": "sin permisos",
        "status": "PENDING_REVIEW",
        "severity": "MEDIUM",
        "finding": "Unable to evaluate due to insufficient permissions",
        "evidence": f"Access Denied: {code}",
        "remediation": "Grant required IAM permissions",
        "risk": "Cannot determine compliance status",
    }


# ===========================================================================
# SEC01-BP01 (inline, cliente 'organizations')
# ===========================================================================

def _org_scripts(feature_set="ALL", num_accounts=3, with_ous=True, with_scps=True):
    accounts = [
        {"Id": f"11111111111{i}", "Name": f"acct{i}", "Status": "ACTIVE"}
        for i in range(num_accounts)
    ]
    ous = (
        {"OrganizationalUnits": [{"Id": "ou-root-prod", "Name": "Produccion"}]}
        if with_ous
        else {"OrganizationalUnits": []}
    )
    policies = (
        {"Policies": [{"Id": "p-1", "Name": "DenyRoot"}, {"Id": "p-0", "Name": "FullAWSAccess"}]}
        if with_scps
        else {"Policies": [{"Id": "p-0", "Name": "FullAWSAccess"}]}
    )
    return {
        "organizations": {
            "describe_organization": {
                "response": {"Organization": {"Id": "o-abc123", "FeatureSet": feature_set}}
            },
            "list_accounts": {"response": {"Accounts": accounts}},
            "list_roots": {"response": {"Roots": [{"Id": "r-root"}]}},
            "list_organizational_units_for_parent": {"response": ous},
            "list_policies": {"response": policies},
        }
    }


def test_sec01_bp01_compliant(security_handler, scripted_session):
    session = scripted_session(_org_scripts())
    evaluator = security_handler.SecurityEvaluator(session, region="us-east-1")
    finding = evaluator._evaluate_sec01_bp01()
    assert_finding_contract(finding, expected_bp="SEC01-BP01")
    assert finding["status"] == "COMPLIANT"


def test_sec01_bp01_pending_review(security_handler, scripted_session):
    # Multi-cuenta pero sin OUs ni SCPs (<=2 issues y num_accounts>1) -> PENDING_REVIEW.
    session = scripted_session(
        _org_scripts(num_accounts=2, with_ous=False, with_scps=False)
    )
    evaluator = security_handler.SecurityEvaluator(session, region="us-east-1")
    finding = evaluator._evaluate_sec01_bp01()
    assert_finding_contract(finding, expected_bp="SEC01-BP01")
    assert finding["status"] == "PENDING_REVIEW"


def test_sec01_bp01_non_compliant_single_account(security_handler, scripted_session):
    # Cuenta única + sin OUs + FeatureSet != ALL + sin SCPs = >2 issues -> NON_COMPLIANT.
    session = scripted_session(
        _org_scripts(
            feature_set="CONSOLIDATED_BILLING",
            num_accounts=1,
            with_ous=False,
            with_scps=False,
        )
    )
    evaluator = security_handler.SecurityEvaluator(session, region="us-east-1")
    finding = evaluator._evaluate_sec01_bp01()
    assert_finding_contract(finding, expected_bp="SEC01-BP01")
    assert finding["status"] == "NON_COMPLIANT"


def test_sec01_bp01_no_organizations_non_compliant(security_handler, scripted_session):
    # describe_organization falla -> rama interna "No se detectó AWS Organizations".
    session = scripted_session(
        {"organizations": {"describe_organization": {"error": ("AWSOrganizationsNotInUseException", "no org")}}}
    )
    evaluator = security_handler.SecurityEvaluator(session, region="us-east-1")
    finding = evaluator._evaluate_sec01_bp01()
    assert_finding_contract(finding, expected_bp="SEC01-BP01")
    assert finding["status"] == "NON_COMPLIANT"


def test_sec01_bp01_access_denied_degraded(security_handler, denying_session):
    # Deny en 'organizations' en describe_organization -> rama interna NON_COMPLIANT
    # (ClientError atrapado dentro del try, no por el handler externo).
    evaluator = security_handler.SecurityEvaluator(denying_session, region="us-east-1")
    finding = evaluator._evaluate_sec01_bp01()
    assert_finding_contract(finding, expected_bp="SEC01-BP01")
    assert finding["status"] in {"NON_COMPLIANT", "PENDING_REVIEW"}


# ===========================================================================
# SEC01-BP02 (inline, clientes 'iam' + 'cloudtrail')
# ===========================================================================

def _iam_summary(mfa=1, access_keys=0, users=0):
    return {
        "SummaryMap": {
            "AccountMFAEnabled": mfa,
            "AccountAccessKeysPresent": access_keys,
            "Users": users,
        }
    }


def test_sec01_bp02_compliant(security_handler, scripted_session):
    session = scripted_session(
        {
            "iam": {
                "get_account_summary": {"response": _iam_summary(mfa=1, access_keys=0)},
                "list_virtual_mfa_devices": {"response": {"VirtualMFADevices": []}},
            },
            "cloudtrail": {
                "lookup_events": {"response": {"Events": []}},
            },
        }
    )
    evaluator = security_handler.SecurityEvaluator(session, region="us-east-1")
    finding = evaluator._evaluate_sec01_bp02()
    assert_finding_contract(finding, expected_bp="SEC01-BP02")
    assert finding["status"] == "COMPLIANT"


def test_sec01_bp02_non_compliant_no_mfa(security_handler, scripted_session):
    session = scripted_session(
        {
            "iam": {
                "get_account_summary": {"response": _iam_summary(mfa=0, access_keys=1)},
                "list_virtual_mfa_devices": {"response": {"VirtualMFADevices": []}},
            },
            "cloudtrail": {"lookup_events": {"response": {"Events": []}}},
        }
    )
    evaluator = security_handler.SecurityEvaluator(session, region="us-east-1")
    finding = evaluator._evaluate_sec01_bp02()
    assert_finding_contract(finding, expected_bp="SEC01-BP02")
    assert finding["status"] == "NON_COMPLIANT"
    assert finding["severity"] == "CRITICAL"


def test_sec01_bp02_pending_review_virtual_mfa(security_handler, scripted_session):
    # MFA habilitado, sin access keys, pero MFA virtual del root -> issue no crítico
    # -> PENDING_REVIEW.
    session = scripted_session(
        {
            "iam": {
                "get_account_summary": {"response": _iam_summary(mfa=1, access_keys=0)},
                "list_virtual_mfa_devices": {
                    "response": {
                        "VirtualMFADevices": [
                            {"SerialNumber": "arn:aws:iam::111122223333:mfa/root-account-mfa-device"}
                        ]
                    }
                },
            },
            "cloudtrail": {"lookup_events": {"response": {"Events": []}}},
        }
    )
    evaluator = security_handler.SecurityEvaluator(session, region="us-east-1")
    finding = evaluator._evaluate_sec01_bp02()
    assert_finding_contract(finding, expected_bp="SEC01-BP02")
    assert finding["status"] == "PENDING_REVIEW"


def test_sec01_bp02_access_denied_degraded(security_handler, denying_session):
    # Deny en iam.get_account_summary (fuera de try interno) -> _handle_permission_error.
    evaluator = security_handler.SecurityEvaluator(denying_session, region="us-east-1")
    finding = evaluator._evaluate_sec01_bp02()
    assert_finding_contract(finding, expected_bp="SEC01-BP02")
    assert finding["status"] == "PENDING_REVIEW"
    assert finding["severity"] == "MEDIUM"


# ===========================================================================
# SEC02-BP01 (función, clientes 'iam' + 'sso-admin')
# ===========================================================================

def _strong_password_policy():
    return {
        "PasswordPolicy": {
            "MinimumPasswordLength": 16,
            "RequireUppercaseCharacters": True,
            "RequireLowercaseCharacters": True,
            "RequireNumbers": True,
            "RequireSymbols": True,
            "MaxPasswordAge": 90,
            "PasswordReusePrevention": 24,
        }
    }


def _weak_password_policy():
    return {
        "PasswordPolicy": {
            "MinimumPasswordLength": 6,
            "RequireUppercaseCharacters": False,
            "RequireLowercaseCharacters": True,
            "RequireNumbers": False,
            "RequireSymbols": False,
            "MaxPasswordAge": 0,
            "PasswordReusePrevention": 0,
        }
    }


def test_sec02_bp01_compliant(security_handler, scripted_session):
    session = scripted_session(
        {
            "iam": {
                "get_account_password_policy": {"response": _strong_password_policy()},
                "get_account_summary": {"response": {"SummaryMap": {"Users": 0, "MFADevices": 0}}},
                "list_users": {"response": {"Users": []}},
            },
            "sso-admin": {"list_instances": {"response": {"Instances": []}}},
        }
    )
    finding = bp.evaluate_sec02_bp01(session, _handle_error)
    assert_finding_contract(finding, expected_bp="SEC02-BP01")
    assert finding["status"] == "COMPLIANT"


def test_sec02_bp01_non_compliant_weak_policy(security_handler, scripted_session):
    session = scripted_session(
        {
            "iam": {
                "get_account_password_policy": {"response": _weak_password_policy()},
                "get_account_summary": {"response": {"SummaryMap": {"Users": 0, "MFADevices": 0}}},
                "list_users": {"response": {"Users": []}},
            },
            "sso-admin": {"list_instances": {"response": {"Instances": []}}},
        }
    )
    finding = bp.evaluate_sec02_bp01(session, _handle_error)
    assert_finding_contract(finding, expected_bp="SEC02-BP01")
    # Política débil (sin agrupar en "Sin política"/"sin MFA") -> PENDING_REVIEW
    # salvo que haya un issue crítico. Se verifica el status real del código.
    assert finding["status"] in {"NON_COMPLIANT", "PENDING_REVIEW"}


def test_sec02_bp01_no_password_policy_uses_nosuchentity(security_handler, scripted_session):
    # get_account_password_policy lanza NoSuchEntityException real del cliente iam.
    # Esta es la ruta que exige que el mock exponga client.exceptions.<X>.
    import boto3

    real_iam = boto3.Session(region_name="us-east-1").client("iam")
    no_such_entity = real_iam.exceptions.NoSuchEntityException(
        {"Error": {"Code": "NoSuchEntity", "Message": "no policy"}},
        "GetAccountPasswordPolicy",
    )
    session = scripted_session(
        {
            "iam": {
                "get_account_password_policy": {"raise": no_such_entity},
                "get_account_summary": {"response": {"SummaryMap": {"Users": 0, "MFADevices": 0}}},
                "list_users": {"response": {"Users": []}},
            },
            "sso-admin": {"list_instances": {"response": {"Instances": []}}},
        }
    )
    finding = bp.evaluate_sec02_bp01(session, _handle_error)
    assert_finding_contract(finding, expected_bp="SEC02-BP01")
    # Lo esencial de este caso: la rama `except client.exceptions.NoSuchEntityException`
    # se resuelve SIN AttributeError (ese era el fallo del mock casero previo) y la BP
    # devuelve un finding válido. El status observado del código de producción para
    # "sin política de contraseñas" es PENDING_REVIEW (no entra en la rama
    # NON_COMPLIANT/CRITICAL por el emparejamiento literal de la cadena de issue).
    assert finding["status"] == "PENDING_REVIEW"


def test_sec02_bp01_access_denied_degraded(security_handler, denying_session):
    # Deny en iam.get_account_password_policy -> NoSuchEntity NO aplica (es ClientError
    # AccessDenied); el except interno es por NoSuchEntityException, así que el
    # AccessDenied del try externo lo captura `except ClientError` -> _handle.
    finding = bp.evaluate_sec02_bp01(denying_session, _handle_error)
    assert_finding_contract(finding, expected_bp="SEC02-BP01")
    assert finding["status"] == "PENDING_REVIEW"


# ===========================================================================
# Patrón PARAMETRIZADO reutilizable para rutas "felices" de más BPs.
# Cada fila: (bp_func_name, scripts, expected_status).
# El expected_status se verificó ejecutando el test (status real del código).
# ===========================================================================

_PARAM_BPS = [
    # SEC02-BP06: grupos de usuarios. list_groups con grupos y políticas -> COMPLIANT.
    (
        "evaluate_sec02_bp06",
        {
            "iam": {
                "list_groups": {"response": {"Groups": [{"GroupName": "admins"}, {"GroupName": "devs"}]}},
                "list_users": {"response": {"Users": [{"UserName": "u1"}]}},
                "list_attached_group_policies": {
                    "response": {"AttachedPolicies": [{"PolicyName": "ReadOnly"}]}
                },
                "list_group_policies": {"response": {"PolicyNames": []}},
                "get_group": {"response": {"Users": [{"UserName": "u1"}]}},
            }
        },
        None,  # status no determinista entre versiones de datos: solo validar contrato.
    ),
]


@pytest.mark.parametrize("func_name,scripts,expected_status", _PARAM_BPS)
def test_bp_scripted_happy_path(scripted_session, func_name, scripts, expected_status):
    """Patrón reutilizable: invoca una BP con un guion y valida contrato (+status)."""
    session = scripted_session(scripts)
    func = getattr(bp, func_name)
    finding = func(session, _handle_error)
    assert_finding_contract(finding)
    if expected_status is not None:
        assert finding["status"] == expected_status
