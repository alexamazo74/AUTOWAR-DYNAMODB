"""
Evaluation Builder
Builds complete evaluation data structure from pillar results
"""

from typing import Dict, List
from datetime import datetime


def build_evaluation_data(pillar_results: Dict[str, dict], account_id: str) -> dict:
    """
    Build complete evaluation data structure from individual pillar results
    
    Args:
        pillar_results: Dictionary mapping pillar names to their evaluation results
        account_id: AWS account ID
    
    Returns:
        dict: Complete evaluation data ready for storage
    
    Requirements: 1.4, 1.5
    """
    # Extract pillar scores
    pillar_scores = {}
    for pillar_name, pillar_data in pillar_results.items():
        pillar_scores[pillar_name] = pillar_data.get('overall_score', 0.0)
    
    # Extract all best practices
    best_practices = []
    for pillar_name, pillar_data in pillar_results.items():
        for question in pillar_data.get('questions', []):
            question_id = question.get('question_id', '')
            # Handle title as dict {es, en} or string
            question_title_raw = question.get('title', question.get('question_title', ''))
            if isinstance(question_title_raw, dict):
                question_title = question_title_raw.get('es', question_title_raw.get('en', ''))
            else:
                question_title = str(question_title_raw)
            
            for finding in question.get('findings', []):
                best_practices.append({
                    'pilar': pillar_name,
                    'bpId': finding.get('bp', ''),
                    'questionId': question_id,
                    'questionTitle': question_title,
                    'description': finding.get('description', ''),
                    'status': finding.get('status', ''),
                    'severity': finding.get('severity', ''),
                    'finding': finding.get('finding', ''),
                    'evidence': finding.get('evidence', ''),
                    'remediation': finding.get('remediation', ''),
                    'risk': finding.get('risk', '')
                })
    
    # Calculate metadata
    total_best_practices = len(best_practices)
    total_findings = sum(1 for bp in best_practices if bp['status'] == 'NON_COMPLIANT')
    
    # Get region from first pillar (assuming all use same region)
    region = 'unknown'
    for pillar_data in pillar_results.values():
        if 'region' in pillar_data:
            region = pillar_data['region']
            break
    
    # Build complete evaluation data
    evaluation_data = {
        'pillarScores': pillar_scores,
        'bestPractices': best_practices,
        'metadata': {
            'region': region,
            'totalBestPractices': total_best_practices,
            'totalFindings': total_findings,
            'pillarsEvaluated': list(pillar_results.keys())
        }
    }
    
    return evaluation_data
