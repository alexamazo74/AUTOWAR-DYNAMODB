"""
Security Service for AutoWAR Platform
Handles evaluation of Security pillar best practices
"""

import json
from decimal import Decimal
from typing import Dict, List, Any, Optional
from datetime import datetime

from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError

from .aws_connector import AWSConnector
from .models import EvaluationRequest, SecurityEvaluation


class SecurityService:
    """Service for Security pillar evaluation"""

    def __init__(self, dynamodb_resource, table_name: str = 'autowar-waf-questions'):
        self.dynamodb = dynamodb_resource
        self.table_name = table_name
        self.table = self.dynamodb.Table(table_name)
        self.aws_connector = AWSConnector()

    def _to_decimal_safe(self, value: Any) -> Decimal:
        """Safely convert to Decimal for DynamoDB"""
        if value is None:
            return Decimal('0')
        if isinstance(value, Decimal):
            return value
        try:
            return Decimal(str(value))
        except (ValueError, TypeError):
            return Decimal('0')

    async def evaluate_security_question(self, evaluation_id: str, question_id: str) -> Dict[str, Any]:
        """
        Evaluate a specific security question
        Returns scoring and compliance status
        """
        try:
            # Get AWS resources for this question
            resources = await self._get_security_resources(question_id)

            # Run validators for this question
            validation_results = await self._run_security_validators(question_id, resources)

            # Calculate scoring
            scoring = self._calculate_security_scoring(validation_results)

            # Store evaluation
            evaluation_data = {
                'id': f"{evaluation_id}#{question_id}",
                'evaluation_id': evaluation_id,
                'question_id': question_id,
                'pillar': 'Security',
                'scoring': scoring,
                'validation_results': validation_results,
                'resources_evaluated': resources,
                'evaluated_at': datetime.utcnow().isoformat(),
                'status': 'completed'
            }

            self.table.put_item(Item=evaluation_data)

            return evaluation_data

        except Exception as e:
            return {
                'id': f"{evaluation_id}#{question_id}",
                'evaluation_id': evaluation_id,
                'question_id': question_id,
                'pillar': 'Security',
                'error': str(e),
                'status': 'failed'
            }

    async def _get_security_resources(self, question_id: str) -> List[Dict[str, Any]]:
        """Get AWS resources relevant to security question"""
        # Map questions to AWS services
        service_mapping = {
            'SEC01': ['iam', 'organizations'],  # Identity and access management
            'SEC02': ['cloudtrail', 'config'],  # Logging and monitoring
            'SEC03': ['kms', 'secretsmanager'],  # Encryption
            'SEC04': ['vpc', 'ec2', 'security-groups'],  # Network security
            'SEC05': ['s3', 'rds', 'lambda'],  # Data protection
        }

        pillar = question_id[:4]  # e.g., SEC01
        services = service_mapping.get(pillar, [])

        resources = []
        for service in services:
            try:
                service_resources = await self.aws_connector.get_resources_by_service(service)
                resources.extend(service_resources)
            except Exception as e:
                print(f"Error getting {service} resources: {e}")

        return resources

    async def _run_security_validators(self, question_id: str, resources: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Run security validators for the question"""
        # Import validators dynamically
        from .validators import security_validators

        results = {}
        for bp_id, validator_func in security_validators.items():
            if bp_id.startswith(question_id):
                try:
                    result = await validator_func(resources)
                    results[bp_id] = result
                except Exception as e:
                    results[bp_id] = {
                        'status': 'error',
                        'error': str(e),
                        'score': 0
                    }

        return results

    def _calculate_security_scoring(self, validation_results: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate overall scoring for security question"""
        total_score = 0
        total_bps = len(validation_results)
        compliant_bps = 0

        for bp_result in validation_results.values():
            score = bp_result.get('score', 0)
            total_score += score
            if score >= 80:  # Consider compliant if score >= 80
                compliant_bps += 1

        avg_score = total_score / total_bps if total_bps > 0 else 0

        return {
            'overall_score': self._to_decimal_safe(avg_score),
            'compliant_bps': compliant_bps,
            'total_bps': total_bps,
            'compliance_percentage': self._to_decimal_safe((compliant_bps / total_bps) * 100 if total_bps > 0 else 0)
        }

    def get_security_evaluation(self, evaluation_id: str, question_id: str) -> Optional[Dict[str, Any]]:
        """Get security evaluation for specific question"""
        try:
            response = self.table.get_item(
                Key={'id': f"{evaluation_id}#{question_id}"}
            )
            return response.get('Item')
        except ClientError as e:
            print(f"Error getting security evaluation: {e}")
            return None

    def list_security_evaluations_for_evaluation(self, evaluation_id: str) -> List[Dict[str, Any]]:
        """List all security evaluations for an evaluation"""
        try:
            response = self.table.query(
                IndexName='evaluationIndex',  # Assuming GSI exists
                KeyConditionExpression=Key('evaluation_id').eq(evaluation_id)
            )
            return response.get('Items', [])
        except ClientError as e:
            print(f"Error listing security evaluations: {e}")
            return []