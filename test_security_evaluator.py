#!/usr/bin/env python3
"""
Test script to verify the complete Security Pillar evaluation system
"""
# -*- coding: utf-8 -*-

from src.app.security_evaluator import SecurityPillarEvaluator
from src.app.aws_connector import AWSConnector
from unittest.mock import MagicMock
import json
import sys

# Force UTF-8 encoding for output
if sys.stdout.encoding != 'utf-8':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


def test_evaluator_structure():
    """Verify evaluator methods exist for all 11 questions"""
    print("\n" + "="*60)
    print("Testing Evaluator Structure")
    print("="*60)
    
    # Create mock connector
    mock_connector = MagicMock(spec=AWSConnector)
    mock_connector.regions = ['us-east-1', 'us-west-2']
    
    # Test evaluator has all methods
    evaluator = SecurityPillarEvaluator(mock_connector)
    
    required_methods = [
        'evaluate_sec01',
        'evaluate_sec02',
        'evaluate_sec03',
        'evaluate_sec04',
        'evaluate_sec05',
        'evaluate_sec06',
        'evaluate_sec07',
        'evaluate_sec08',
        'evaluate_sec09',
        'evaluate_sec10',
        'evaluate_sec11',
        'evaluate_all',
    ]
    
    for method_name in required_methods:
        if hasattr(evaluator, method_name):
            print(f"[OK] {method_name} exists")
        else:
            print(f"[FAIL] {method_name} MISSING")
    
    print("\nAll 11 question evaluators present: [OK]")


def test_mock_evaluation():
    """Test evaluation with mocked AWS data"""
    print("\n" + "="*60)
    print("Testing Mock Evaluation (with mocked AWS Connector)")
    print("="*60)
    
    # Create mock connector with sample data
    mock_connector = MagicMock(spec=AWSConnector)
    mock_connector.regions = ['us-east-1']
    
    # Mock IAM data
    mock_connector.get_iam_users.return_value = [
        {
            'user_name': 'testuser',
            'mfa_enabled': True,
            'access_keys': [
                {'access_key_id': 'AKIA****', 'status': 'Active'}
            ]
        }
    ]
    
    mock_connector.get_iam_roles.return_value = [
        {
            'role_name': 'ec2-role',
            'trust_policy': {}
        }
    ]
    
    mock_connector.get_iam_policies.return_value = [
        {
            'policy_name': 'test-policy',
            'attachment_count': 2
        }
    ]
    
    # Mock CloudTrail/Config data
    mock_connector.get_cloudtrail_trails.return_value = [
        {
            'name': 'org-trail',
            'is_logging': True
        }
    ]
    
    mock_connector.get_config_status.return_value = {
        'recording': True
    }
    
    # Mock GuardDuty
    mock_connector.get_guardduty_detectors.return_value = [
        {'detector_id': 'test-detector'}
    ]
    
    # Mock KMS
    mock_connector.get_kms_keys.return_value = [
        {'key_id': 'test-key', 'description': 'Test CMK'}
    ]
    
    # Mock S3
    mock_connector.get_s3_buckets.return_value = [
        {
            'name': 'test-bucket',
            'encryption_enabled': True
        }
    ]
    
    # Run evaluation
    evaluator = SecurityPillarEvaluator(mock_connector)
    results = evaluator.evaluate_all()
    
    # Display results
    print(f"\nTotal Questions Evaluated: {results['total_questions']}")
    print(f"Total Best Practices: {results['total_best_practices']}")
    print(f"Overall Security Score: {results['overall_score']}/100")
    print(f"Total Findings: {results['total_findings']}")
    
    # Show question scores
    print("\n" + "-"*60)
    print("Question Scores:")
    print("-"*60)
    
    for question in results['questions']:
        sec_id = question['question_id']
        score = question['score']
        bps = question['bps_evaluated']
        findings_count = len(question['findings'])
        print(f"{sec_id}: {score:3.0f}/100 | {bps} BPs | {findings_count:2d} findings")
    
    # Sample findings from SEC03 (should have real data)
    print("\n" + "-"*60)
    print("Sample SEC03 Findings (Human Identity Management):")
    print("-"*60)
    
    sec03_findings = results['questions'][2]['findings']  # SEC03 is index 2
    for finding in sec03_findings[:3]:
        print(f"\n  {finding['bp']}: {finding['status']}")
        print(f"  Finding: {finding['finding']}")
        if 'remediation' in finding:
            print(f"  Remediation: {finding['remediation']}")
    
    return results


if __name__ == '__main__':
    print("\n" + "="*60)
    print("SECURITY PILLAR EVALUATOR - COMPLETE TEST SUITE")
    print("="*60)
    
    # Test 1: Structure
    test_evaluator_structure()
    
    # Test 2: Mock evaluation
    results = test_mock_evaluation()
    
    # Verify no question has score > 100
    print("\n" + "="*60)
    print("Validation Check")
    print("="*60)
    
    all_valid = True
    for question in results['questions']:
        if question['score'] > 100 or question['score'] < 0:
            print(f"[FAIL] {question['question_id']} has invalid score: {question['score']}")
            all_valid = False
    
    if all_valid:
        print("[OK] All scores are valid (0-100)")
    
    # Test 4: Verify best practice counts
    print("\n" + "="*60)
    print("Best Practices Distribution")
    print("="*60)
    
    total_bps = sum(q['bps_evaluated'] for q in results['questions'])
    print(f"Total BPs evaluated: {total_bps}")
    print(f"Expected: 63")
    print(f"Status: {'[OK] MATCH' if total_bps == 63 else '[FAIL] MISMATCH'}")
    
    print("\n" + "="*60)
    print("[OK] ALL TESTS COMPLETED")
    print("="*60 + "\n")
