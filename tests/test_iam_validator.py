def test_iam_password_policy_and_root_mfa(monkeypatch):
    class FakeIAM:
        def get_account_password_policy(self):
            return {
                "PasswordPolicy": {
                    "MinimumPasswordLength": 14,
                    "RequireSymbols": True,
                    "RequireNumbers": True,
                    "RequireUppercaseCharacters": True,
                    "RequireLowercaseCharacters": True,
                }
            }

        def get_account_summary(self):
            return {"SummaryMap": {"AccountMFAEnabled": 1}}

    import src.app.validators.iam_validators as imod

    monkeypatch.setattr(
        imod, "boto3", type("B", (), {"client": lambda service_name: FakeIAM()})
    )

    pwd_validator = imod.IAMPasswordPolicyValidator()
    res1 = pwd_validator.run(name=None)
    assert res1["status"] == "PASS"

    mfa_validator = imod.RootMFAValidator()
    res2 = mfa_validator.run(name=None)
    assert res2["status"] == "PASS"
