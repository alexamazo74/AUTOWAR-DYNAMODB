#!/usr/bin/env python3
"""Test script to validate mock evaluator has all 63 BPs"""

import sys
sys.path.insert(0, 'src/app')

from mock_security_evaluator import MockSecurityEvaluator

# Initialize evaluator
evaluator = MockSecurityEvaluator()
result = evaluator.evaluate_all()

print("=" * 80)
print("MOCK SECURITY EVALUATOR - BP VALIDATION")
print("=" * 80)

# Count total BPs
total_bps = 0
for question in result['questions']:
    question_id = question['question_id']
    num_findings = len(question['findings'])
    bps_expected = question['bps_evaluated']
    status = "✓" if num_findings == bps_expected else "✗"
    
    print(f"\n{status} {question_id}: {question['title']}")
    print(f"   Expected BPs: {bps_expected}, Found: {num_findings}")
    
    # Show BP details
    for finding in question['findings']:
        bp_id = finding['bp']
        status_val = finding['status']
        severity = finding['severity']
        has_risk = 'risk' in finding and finding['risk']
        has_remediation = 'remediation' in finding and finding['remediation']
        
        print(f"   - {bp_id}: {status_val} [{severity}] Risk: {'✓' if has_risk else '✗'} Rem: {'✓' if has_remediation else '✗'}")
    
    total_bps += len(question['findings'])

print(f"\n{'=' * 80}")
print(f"TOTAL BPs FOUND: {total_bps}/63")
print(f"STATUS: {'✓ COMPLETE' if total_bps == 63 else '✗ INCOMPLETE'}")
print(f"{'=' * 80}")
