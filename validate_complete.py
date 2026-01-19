#!/usr/bin/env python3
"""
End-to-End Validation Script
Tests complete flow from backend mock data to expected BP coverage
"""

import sys
sys.path.insert(0, 'src/app')

from mock_security_evaluator import MockSecurityEvaluator

# Expected BP distribution across 11 questions
EXPECTED_BPS = {
    'SEC01': 9,
    'SEC02': 7,
    'SEC03': 8,
    'SEC04': 6,
    'SEC05': 6,
    'SEC06': 6,
    'SEC07': 6,
    'SEC08': 5,
    'SEC09': 5,
    'SEC10': 4,
    'SEC11': 1
}

def validate_mock_evaluator():
    """Validate that MockSecurityEvaluator returns complete BP data"""
    print("=" * 80)
    print("END-TO-END VALIDATION - AutoWAR Security Pillar")
    print("=" * 80)
    
    evaluator = MockSecurityEvaluator()
    result = evaluator.evaluate_all()
    
    # Validate overall structure
    assert 'overall_score' in result, "Missing overall_score"
    assert 'total_best_practices' in result, "Missing total_best_practices"
    assert 'questions' in result, "Missing questions array"
    assert result['total_best_practices'] == 63, f"Expected 63 BPs, got {result['total_best_practices']}"
    
    print(f"\n✓ Overall Score: {result['overall_score']}%")
    print(f"✓ Total BPs: {result['total_best_practices']}")
    print(f"✓ Questions: {len(result['questions'])}")
    
    # Validate each question
    all_pass = True
    total_bps_found = 0
    issues = []
    
    for question in result['questions']:
        q_id = question['question_id']
        expected_count = EXPECTED_BPS.get(q_id, 0)
        findings = question.get('findings', [])
        actual_count = len(findings)
        total_bps_found += actual_count
        
        # Check BP count
        if actual_count != expected_count:
            all_pass = False
            issues.append(f"{q_id}: Expected {expected_count} BPs, found {actual_count}")
            print(f"\n✗ {q_id}: {question['title']}")
            print(f"  Expected: {expected_count}, Found: {actual_count} ❌")
        else:
            print(f"\n✓ {q_id}: {question['title']}")
            print(f"  BPs: {actual_count}/{expected_count} ✅")
        
        # Validate each finding has required fields
        for finding in findings:
            required_fields = ['bp', 'status', 'severity', 'finding', 'evidence', 'risk', 'remediation']
            missing_fields = [f for f in required_fields if f not in finding or not finding[f]]
            
            if missing_fields:
                all_pass = False
                issues.append(f"{finding.get('bp', 'UNKNOWN')}: Missing fields: {missing_fields}")
    
    print("\n" + "=" * 80)
    print(f"TOTAL BPs VALIDATED: {total_bps_found}/63")
    print("=" * 80)
    
    if all_pass and total_bps_found == 63:
        print("\n✅ ALL VALIDATIONS PASSED")
        print("   ✓ All 63 BPs present")
        print("   ✓ All BPs have required fields (bp, status, severity, finding, evidence, risk, remediation)")
        print("   ✓ Mock evaluator ready for production")
        return True
    else:
        print("\n❌ VALIDATION FAILED")
        if issues:
            print("\nIssues found:")
            for issue in issues:
                print(f"  - {issue}")
        return False

if __name__ == "__main__":
    success = validate_mock_evaluator()
    sys.exit(0 if success else 1)
