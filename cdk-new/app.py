#!/usr/bin/env python3
"""
AutoWAR CDK App - Serverless Architecture
"""

import aws_cdk as cdk
from stacks.autowar_stack import AutoWARStack

app = cdk.App()

AutoWARStack(
    app,
    "AutoWARStack",
    env=cdk.Environment(
        account="102080400524",
        region="us-east-1"
    ),
    description="AutoWAR - AWS Well-Architected Framework Evaluation Platform (Serverless)"
)

app.synth()
