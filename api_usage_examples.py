#!/usr/bin/env python3
"""
API Usage Examples - Security Pillar Evaluation

Complete examples of how to use the AutoWAR Security evaluation endpoints
"""

import requests
import json
from typing import Dict, Any

# API Base URL
BASE_URL = "http://127.0.0.1:8002"


class SecurityEvaluationClient:
    """Client for AutoWAR Security Pillar evaluation"""
    
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.session = requests.Session()
    
    def validate_credentials(
        self,
        access_key_id: str,
        secret_access_key: str,
        account_id: str,
        regions: list,
        session_token: str = None
    ) -> Dict[str, Any]:
        """
        Validate AWS credentials
        
        Args:
            access_key_id: AWS Access Key ID
            secret_access_key: AWS Secret Access Key
            account_id: AWS Account ID
            regions: List of AWS regions to evaluate
            session_token: Optional session token for MFA/temporary credentials
        
        Returns:
            Response with validation result and account details
        
        Example:
            >>> client = SecurityEvaluationClient()
            >>> response = client.validate_credentials(
            ...     access_key_id="AKIAIOSFODNN7EXAMPLE",
            ...     secret_access_key="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
            ...     account_id="123456789012",
            ...     regions=["us-east-1", "us-west-2"]
            ... )
            >>> print(f"Valid: {response['success']}")
            >>> print(f"Account: {response['account_id']}")
        """
        payload = {
            "access_key_id": access_key_id,
            "secret_access_key": secret_access_key,
            "account_id": account_id,
            "regions": regions,
            "session_token": session_token
        }
        
        response = self.session.post(
            f"{self.base_url}/security/validate-credentials",
            json=payload
        )
        return response.json()
    
    def evaluate_security(
        self,
        access_key_id: str,
        secret_access_key: str,
        account_id: str,
        regions: list,
        session_token: str = None
    ) -> Dict[str, Any]:
        """
        Run complete Security pillar evaluation (all 11 questions, 63 BPs)
        
        Args:
            access_key_id: AWS Access Key ID
            secret_access_key: AWS Secret Access Key
            account_id: AWS Account ID
            regions: List of AWS regions to evaluate
            session_token: Optional session token for MFA/temporary credentials
        
        Returns:
            Complete evaluation with all questions, scores, and findings
        
        Example:
            >>> client = SecurityEvaluationClient()
            >>> response = client.evaluate_security(
            ...     access_key_id="AKIAIOSFODNN7EXAMPLE",
            ...     secret_access_key="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
            ...     account_id="123456789012",
            ...     regions=["us-east-1"]
            ... )
            >>> 
            >>> # Check overall score
            >>> print(f"Security Score: {response['evaluation']['overall_score']}")
            >>> 
            >>> # Count findings by severity
            >>> critical = response['summary']['critical']
            >>> high = response['summary']['high']
            >>> print(f"Critical findings: {critical}, High: {high}")
            >>> 
            >>> # Review SEC03 (Human Identity) findings
            >>> sec03 = response['evaluation']['questions_evaluated'][2]
            >>> print(f"SEC03 Score: {sec03['score']}")
            >>> for finding in sec03['findings']:
            ...     print(f"  {finding['bp']}: {finding['finding']}")
        """
        payload = {
            "access_key_id": access_key_id,
            "secret_access_key": secret_access_key,
            "account_id": account_id,
            "regions": regions,
            "session_token": session_token
        }
        
        response = self.session.post(
            f"{self.base_url}/security/evaluate-real",
            json=payload
        )
        return response.json()
    
    def get_question_score(
        self,
        evaluation_response: Dict[str, Any],
        question_id: str
    ) -> Dict[str, Any]:
        """Get specific question details from evaluation"""
        for question in evaluation_response['evaluation']['questions_evaluated']:
            if question['question_id'] == question_id:
                return question
        return None
    
    def get_critical_findings(
        self,
        evaluation_response: Dict[str, Any]
    ) -> list:
        """Get all CRITICAL severity findings"""
        findings = []
        for question in evaluation_response['evaluation']['questions_evaluated']:
            for finding in question['findings']:
                if finding.get('severity') == 'CRITICAL':
                    findings.append({
                        'question': question['question_id'],
                        'bp': finding['bp'],
                        'finding': finding['finding'],
                        'remediation': finding.get('remediation', 'N/A')
                    })
        return findings


# ============================================================================
# EXAMPLE 1: Basic Validation
# ============================================================================

def example_validate_credentials():
    """Example: Validate AWS credentials"""
    
    print("\n" + "="*70)
    print("EXAMPLE 1: Validate AWS Credentials")
    print("="*70)
    
    client = SecurityEvaluationClient()
    
    # Note: Replace with real AWS credentials
    result = client.validate_credentials(
        access_key_id="AKIAIOSFODNN7EXAMPLE",
        secret_access_key="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
        account_id="123456789012",
        regions=["us-east-1", "us-west-2"]
    )
    
    if result.get('success'):
        print(f"✓ Credentials valid")
        print(f"  Account ID: {result.get('account_id')}")
        print(f"  Caller ARN: {result.get('account_arn')}")
    else:
        print(f"✗ Validation failed: {result.get('error')}")
    
    return result


# ============================================================================
# EXAMPLE 2: Complete Security Evaluation
# ============================================================================

def example_security_evaluation():
    """Example: Run complete Security pillar evaluation"""
    
    print("\n" + "="*70)
    print("EXAMPLE 2: Complete Security Pillar Evaluation")
    print("="*70)
    print("Evaluating: 11 questions, 63 best practices")
    print("Regions: us-east-1, us-west-2\n")
    
    client = SecurityEvaluationClient()
    
    # Run evaluation
    result = client.evaluate_security(
        access_key_id="AKIAIOSFODNN7EXAMPLE",
        secret_access_key="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
        account_id="123456789012",
        regions=["us-east-1", "us-west-2"]
    )
    
    if result.get('success'):
        # Display summary
        summary = result['summary']
        eval_data = result['evaluation']
        
        print("EVALUATION SUMMARY:")
        print("-" * 70)
        print(f"Overall Security Score:    {eval_data['overall_score']}/100")
        print(f"Total Questions Evaluated: {eval_data['total_questions']}")
        print(f"Total Best Practices:      {eval_data['total_best_practices']}")
        print(f"Total Findings:            {summary['total_findings']}")
        print(f"\nFinding Severity Breakdown:")
        print(f"  CRITICAL:                {summary['critical']}")
        print(f"  HIGH:                    {summary['high']}")
        print(f"  MEDIUM:                  {summary['medium']}")
        print(f"\nBest Practices Evaluated:  {summary['bps_evaluated']}/63")
        
        # Display all question scores
        print("\n" + "="*70)
        print("QUESTION SCORES (0-100):")
        print("-" * 70)
        
        questions_data = eval_data['questions_evaluated']
        for q in questions_data:
            print(f"{q['question_id']}: {q['score']:3.0f}/100 | {q['bps_evaluated']} BPs | {len(q['findings']):2d} findings")
        
        return result
    else:
        print(f"✗ Evaluation failed: {result.get('error')}")
        return result


# ============================================================================
# EXAMPLE 3: Analyze Specific Question (SEC03 - Human Identity)
# ============================================================================

def example_analyze_question(evaluation_result):
    """Example: Deep dive into specific question (SEC03)"""
    
    print("\n" + "="*70)
    print("EXAMPLE 3: Detailed Analysis - SEC03 (Human Identity Management)")
    print("="*70)
    
    client = SecurityEvaluationClient()
    sec03 = client.get_question_score(evaluation_result, 'SEC03')
    
    if sec03:
        print(f"\nQuestion: {sec03['question']}")
        print(f"Score: {sec03['score']}/100")
        print(f"Best Practices Evaluated: {sec03['bps_evaluated']}")
        print(f"Findings: {len(sec03['findings'])}\n")
        
        print("FINDINGS BY STATUS:")
        print("-" * 70)
        
        # Group findings by status
        by_status = {}
        for finding in sec03['findings']:
            status = finding['status']
            if status not in by_status:
                by_status[status] = []
            by_status[status].append(finding)
        
        # Display compliant findings
        if 'COMPLIANT' in by_status:
            print(f"\n✓ COMPLIANT ({len(by_status['COMPLIANT'])} findings):")
            for f in by_status['COMPLIANT']:
                print(f"  {f['bp']}: {f['finding']}")
        
        # Display non-compliant findings
        if 'NON_COMPLIANT' in by_status:
            print(f"\n✗ NON_COMPLIANT ({len(by_status['NON_COMPLIANT'])} findings):")
            for f in by_status['NON_COMPLIANT']:
                print(f"  {f['bp']}: {f['finding']}")
                if 'remediation' in f:
                    print(f"    Remediation: {f['remediation']}")
        
        # Display pending review
        if 'PENDING_REVIEW' in by_status:
            print(f"\n⏳ PENDING_REVIEW ({len(by_status['PENDING_REVIEW'])} findings):")
            for f in by_status['PENDING_REVIEW']:
                print(f"  {f['bp']}: {f['finding']}")


# ============================================================================
# EXAMPLE 4: Get Critical Findings
# ============================================================================

def example_critical_findings(evaluation_result):
    """Example: Extract and display critical findings"""
    
    print("\n" + "="*70)
    print("EXAMPLE 4: Critical Findings")
    print("="*70)
    
    client = SecurityEvaluationClient()
    critical = client.get_critical_findings(evaluation_result)
    
    if critical:
        print(f"\nFound {len(critical)} CRITICAL findings that need immediate attention:\n")
        
        for i, finding in enumerate(critical, 1):
            print(f"{i}. {finding['question']} - {finding['bp']}")
            print(f"   Issue: {finding['finding']}")
            print(f"   Fix: {finding['remediation']}\n")
    else:
        print("\n✓ No critical findings detected!")


# ============================================================================
# EXAMPLE 5: AWS Services Coverage
# ============================================================================

def example_aws_services_coverage():
    """Example: Display AWS services evaluated per question"""
    
    print("\n" + "="*70)
    print("EXAMPLE 5: AWS Services Evaluated Per Question")
    print("="*70)
    
    services_map = {
        'SEC01': ['IAM', 'CloudTrail', 'Organizations'],
        'SEC02': ['Organizations', 'IAM', 'STS'],
        'SEC03': ['IAM', 'CloudTrail', 'STS'],
        'SEC04': ['IAM', 'STS', 'SecretsManager'],
        'SEC05': ['IAM', 'Organizations', 'AccessAnalyzer'],
        'SEC06': ['CloudTrail', 'Config', 'GuardDuty', 'SecurityHub'],
        'SEC07': ['VPC', 'SecurityGroups', 'WAF', 'Shield'],
        'SEC08': ['KMS', 'ACM', 'TLS'],
        'SEC09': ['KMS', 'S3', 'RDS', 'DynamoDB'],
        'SEC10': ['Backup', 'RecoveryServices'],
        'SEC11': ['Artifact', 'Config']
    }
    
    print("\nAWS Services Integration Matrix:")
    print("-" * 70)
    
    for question_id, services in services_map.items():
        print(f"{question_id}: {', '.join(services)}")


# ============================================================================
# EXAMPLE 6: Export Results as JSON
# ============================================================================

def example_export_results(evaluation_result):
    """Example: Export evaluation results to file"""
    
    print("\n" + "="*70)
    print("EXAMPLE 6: Export Results to File")
    print("="*70)
    
    # Export to JSON file
    filename = "security_evaluation_result.json"
    
    with open(filename, 'w') as f:
        json.dump(evaluation_result, f, indent=2)
    
    print(f"\n✓ Evaluation results exported to: {filename}")
    print(f"  File size: {len(json.dumps(evaluation_result, indent=2))} bytes")
    print(f"  Contains: {len(evaluation_result.get('evaluation', {}).get('questions_evaluated', []))} questions")


# ============================================================================
# MAIN EXECUTION
# ============================================================================

if __name__ == '__main__':
    print("\n" + "="*70)
    print("AutoWAR Security Pillar Evaluation - API Usage Examples")
    print("="*70)
    
    # Example 1: Validate credentials
    # Note: Skip actual execution as it requires real AWS credentials
    print("\n[EXAMPLE 1] Validating AWS credentials...")
    print("  Would validate: AKIAIOSFODNN7EXAMPLE")
    print("  Account: 123456789012")
    
    # Example 2: Run evaluation
    print("\n[EXAMPLE 2] Running Security Pillar Evaluation...")
    print("  Questions: 11 (SEC01-SEC11)")
    print("  Best Practices: 63")
    print("  Expected duration: 5-10 seconds")
    
    # Example 3: Analyze specific question
    print("\n[EXAMPLE 3] Analyzing SEC03 (Human Identity Management)...")
    print("  BPs: 8")
    print("  Focus: MFA, temporary credentials, identity federation")
    
    # Example 4: Critical findings
    print("\n[EXAMPLE 4] Extracting critical findings...")
    print("  Shows: Issues requiring immediate remediation")
    print("  Action: Prioritize based on security impact")
    
    # Example 5: AWS services coverage
    example_aws_services_coverage()
    
    # Example 6: Export to file
    print("\n[EXAMPLE 6] Exporting results...")
    print("  Format: JSON")
    print("  Location: security_evaluation_result.json")
    
    print("\n" + "="*70)
    print("For live testing, ensure:")
    print("  1. Backend running: python -m uvicorn src.app.main:app --port 8002")
    print("  2. Use real AWS credentials (never commit)")
    print("  3. Update example code with real account details")
    print("="*70 + "\n")
    
    print("\nTo use these examples:")
    print("""
    from api_examples import SecurityEvaluationClient
    
    client = SecurityEvaluationClient()
    
    # Validate credentials
    result = client.validate_credentials(
        access_key_id="YOUR_ACCESS_KEY",
        secret_access_key="YOUR_SECRET_KEY",
        account_id="123456789012",
        regions=["us-east-1", "us-west-2"]
    )
    
    # Run evaluation
    eval_result = client.evaluate_security(
        access_key_id="YOUR_ACCESS_KEY",
        secret_access_key="YOUR_SECRET_KEY",
        account_id="123456789012",
        regions=["us-east-1", "us-west-2"]
    )
    
    # Analyze results
    print(f"Score: {eval_result['evaluation']['overall_score']}")
    print(f"Critical: {eval_result['summary']['critical']}")
    """)
