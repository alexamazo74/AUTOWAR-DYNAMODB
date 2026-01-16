#!/usr/bin/env node
import * as cdk from 'aws-cdk-lib';
import { AutoWarStack } from '../lib/cdk-stack';

const app = new cdk.App();
new AutoWarStack(app, 'AutoWarStack', {
  env: {
    account: process.env.CDK_DEFAULT_ACCOUNT,
    region: process.env.CDK_DEFAULT_REGION,
  },
});
