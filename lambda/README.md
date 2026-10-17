# AutoWAR Lambda Functions

Serverless backend for AWS Well-Architected Framework evaluation.

## Structure

```
lambda/
├── layers/
│   └── common/              # Shared code (boto3, utils)
├── credential_validator/    # Validates AWS credentials
├── orchestrator/            # Orchestrates single pillar evaluation
├── evaluators/
│   ├── security/           # Security pillar evaluator
│   ├── reliability/        # Reliability pillar evaluator
│   ├── performance/        # Performance pillar evaluator
│   ├── cost/              # Cost pillar evaluator
│   ├── operational/       # Operational Excellence evaluator
│   └── sustainability/    # Sustainability pillar evaluator
├── scoring_calculator/     # Calculates scores
├── results_storer/        # Stores results in DynamoDB
└── session_cleanup/       # Cleans up expired sessions
```

## Deployment

Deploy using AWS CDK from `/cdk` directory.
