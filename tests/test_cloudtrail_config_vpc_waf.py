def test_cloudtrail_config_vpc_waf(monkeypatch):
    class FakeCT:
        def describe_trails(self):
            return {"trailList": [{"Name": "t1"}]}

        def get_trail_status(self, Name=None):
            return {"IsLogging": True}

    class FakeCFG:
        def describe_configuration_recorders(self):
            return {"ConfigurationRecorders": [{"name": "r1"}]}

        def describe_configuration_recorder_status(self):
            return {"ConfigurationRecordersStatus": [{"name": "r1", "recording": True}]}

    class FakeEC2:
        def describe_flow_logs(self, Filters=None):
            return {"FlowLogs": [{"FlowLogId": "f1"}]}

    class FakeWAF:
        def list_web_acls(self, Scope="REGIONAL"):
            return {"WebACLs": [{"Name": "acl1"}]}

    import src.app.validators.cloudtrail_validators as ctv
    import src.app.validators.config_validators as cfgv
    import src.app.validators.vpc_validators as vpcv
    import src.app.validators.waf_validators as wafv

    monkeypatch.setattr(
        ctv,
        "boto3",
        type("B", (), {"client": lambda service_name, region_name=None: FakeCT()}),
    )
    monkeypatch.setattr(
        cfgv,
        "boto3",
        type("B", (), {"client": lambda service_name, region_name=None: FakeCFG()}),
    )
    monkeypatch.setattr(
        vpcv,
        "boto3",
        type("B", (), {"client": lambda service_name, region_name=None: FakeEC2()}),
    )
    monkeypatch.setattr(
        wafv,
        "boto3",
        type("B", (), {"client": lambda service_name, region_name=None: FakeWAF()}),
    )

    res_ct = ctv.CloudTrailLoggingValidator().run()
    assert res_ct["status"] == "PASS"

    res_cfg = cfgv.ConfigRecorderValidator().run()
    assert res_cfg["status"] == "PASS"

    res_vpc = vpcv.VPCFlowLogsValidator().run(name="vpc-1")
    assert res_vpc["status"] == "PASS"

    res_waf = wafv.WAFWebACLPresenceValidator().run()
    assert res_waf["status"] == "PASS"
