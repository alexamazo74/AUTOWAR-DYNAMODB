#!/usr/bin/env python3
"""
Display AWS Security Evaluation Results
"""

import json
import sys

def display_results(filename='evaluation_results.json'):
    try:
        with open(filename, 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Error: {filename} not found")
        return
    
    print("\n" + "=" * 100)
    print(f"{'AWS SECURITY EVALUATION RESULTS':^100}")
    print("=" * 100)
    
    # Top level info
    eval_data = data.get('evaluation', {})
    print(f"\n📊 ACCOUNT OVERVIEW")
    print(f"  Account ID: {eval_data.get('account_id')}")
    print(f"  Account ARN: {eval_data.get('account_arn')}")
    print(f"  Region(s): {', '.join(eval_data.get('regions', []))}")
    print(f"  Timestamp: {eval_data.get('timestamp')}")
    print(f"  Evaluation ID: {eval_data.get('id')}")
    
    # Overall score
    overall = eval_data.get('overall_score', 0)
    print(f"\n🎯 OVERALL SECURITY SCORE: {overall}%")
    if overall >= 80:
        rating = "EXCELLENT"
    elif overall >= 60:
        rating = "GOOD"
    elif overall >= 40:
        rating = "FAIR"
    elif overall >= 20:
        rating = "POOR"
    else:
        rating = "CRITICAL"
    print(f"   Rating: {rating}")
    
    # Questions breakdown
    print(f"\n📋 SECURITY QUESTIONS: {eval_data.get('total_questions')} pillar sections")
    print(f"   Total Best Practices: {eval_data.get('total_best_practices')}")
    
    questions = eval_data.get('questions_evaluated', [])
    
    # Create score summary
    sec_scores = {}
    for q in questions:
        sec_id = q.get('question_id', 'Unknown')
        
        # Calculate score for this SEC
        findings = q.get('findings', [])
        compliant = sum(1 for f in findings if f.get('status') == 'COMPLIANT')
        non_compliant = sum(1 for f in findings if f.get('status') == 'NON_COMPLIANT')
        total = compliant + non_compliant
        
        if total > 0:
            score = (compliant / total) * 100
        else:
            score = 0
        
        sec_scores[sec_id] = {
            'score': score,
            'compliant': compliant,
            'non_compliant': non_compliant,
            'total': total,
            'question': q.get('question', '')
        }
    
    # Display SEC scores
    print(f"\n📈 SCORE BY SECTION:")
    for sec_id in sorted(sec_scores.keys()):
        info = sec_scores[sec_id]
        score = info['score']
        bar = "█" * int(score / 5) + "░" * (20 - int(score / 5))
        status = "✓" if score >= 70 else "⚠" if score >= 40 else "✗"
        print(f"  {status} {sec_id}: {score:5.1f}% {bar} ({info['compliant']}/{info['total']} compliant)")
    
    # Critical and High severity findings
    print(f"\n⚠️  CRITICAL & HIGH SEVERITY FINDINGS:")
    critical_findings = []
    high_findings = []
    
    for q in questions:
        sec_id = q.get('question_id')
        for finding in q.get('findings', []):
            if finding.get('severity') == 'CRITICAL':
                critical_findings.append((sec_id, finding))
            elif finding.get('severity') == 'HIGH':
                high_findings.append((sec_id, finding))
    
    if critical_findings:
        print(f"\n  🔴 CRITICAL ({len(critical_findings)}):")
        for sec_id, finding in critical_findings[:10]:
            print(f"    • {sec_id} - {finding.get('bp')}: {finding.get('finding')}")
    
    if high_findings:
        print(f"\n  🟠 HIGH ({len(high_findings)}):")
        for sec_id, finding in high_findings[:10]:
            print(f"    • {sec_id} - {finding.get('bp')}: {finding.get('finding')}")
    
    # SEC04, SEC05, SEC06 specific
    print(f"\n🔒 DETECTION & RESPONSE (SEC04):")
    if 'SEC04' in sec_scores:
        info = sec_scores['SEC04']
        print(f"   Score: {info['score']:.1f}% | Compliant: {info['compliant']}/{info['total']}")
    
    print(f"\n🌐 NETWORK SECURITY (SEC05):")
    if 'SEC05' in sec_scores:
        info = sec_scores['SEC05']
        print(f"   Score: {info['score']:.1f}% | Compliant: {info['compliant']}/{info['total']}")
    
    print(f"\n💻 COMPUTE SECURITY (SEC06):")
    if 'SEC06' in sec_scores:
        info = sec_scores['SEC06']
        print(f"   Score: {info['score']:.1f}% | Compliant: {info['compliant']}/{info['total']}")
    
    # Top remediation items
    print(f"\n🔧 TOP REMEDIATION PRIORITIES (Non-Compliant Items):")
    non_compliant_items = []
    for q in questions:
        sec_id = q.get('question_id')
        for finding in q.get('findings', []):
            if finding.get('status') == 'NON_COMPLIANT':
                non_compliant_items.append({
                    'sec': sec_id,
                    'bp': finding.get('bp'),
                    'issue': finding.get('finding'),
                    'severity': finding.get('severity'),
                    'remediation': finding.get('remediation')
                })
    
    # Sort by severity and show top items
    severity_order = {'CRITICAL': 0, 'HIGH': 1, 'MEDIUM': 2, 'LOW': 3}
    non_compliant_items.sort(key=lambda x: severity_order.get(x['severity'], 999))
    
    for item in non_compliant_items[:15]:
        print(f"\n  [{item['severity']}] {item['sec']}/{item['bp']}")
        print(f"    Issue: {item['issue']}")
        print(f"    Action: {item['remediation']}")
    
    print(f"\n" + "=" * 100)
    print(f"{'END OF REPORT':^100}")
    print("=" * 100 + "\n")

if __name__ == "__main__":
    display_results()
