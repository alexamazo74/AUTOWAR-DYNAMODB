def test_s3_public_access_validator(monkeypatch):
    # fake s3 client responses
    class FakeS3:
        def get_public_access_block(self, Bucket):
            return {
                "PublicAccessBlockConfiguration": {
                    "BlockPublicAcls": True,
                    "IgnorePublicAcls": True,
                    "BlockPublicPolicy": True,
                    "RestrictPublicBuckets": True,
                }
            }

        def get_bucket_acl(self, Bucket):
            return {"Grants": []}

    import src.app.validators.s3_validators as vmod

    monkeypatch.setattr(
        vmod,
        "boto3",
        type("B", (), {"client": lambda service_name, region_name=None: FakeS3()}),
    )

    validator = vmod.S3PublicAccessValidator()
    res = validator.run(name="my-bucket", region="us-east-1")
    assert res["status"] == "PASS"
    assert res["details"]["public_block"] is True
