#!/usr/bin/env python3
"""
Script to update SEC02-SEC11 to use BP-based scoring instead of point deductions
"""

import re

# Map of SEC sections to BP counts
SEC_BP_COUNTS = {
    'SEC02': 6,
    'SEC03': 9,
    'SEC04': 4,
    'SEC05': 4,
    'SEC06': 5,
    'SEC07': 4,
    'SEC08': 4,
    'SEC09': 3,
    'SEC10': 8,
    'SEC11': 8,
}

def update_sec_function(content, sec_num):
    """Update a SEC function to use BP-based scoring"""
    bp_count = SEC_BP_COUNTS.get(sec_num, 0)
    if bp_count == 0:
        return content
    
    func_name = f'evaluate_{sec_num.lower()}'
    
    # Find the function
    pattern = rf'(def {func_name}\(self\).*?"""[^"]*""")\s+findings = \[\]\s+score = 100'
    replacement = rf'\1\n        findings = []\n        compliant_count = 0\n        non_compliant_count = 0\n        pending_count = 0\n        total_bps = {bp_count}'
    
    content = re.sub(pattern, replacement, content, flags=re.DOTALL)
    
    # Replace score -= X with non_compliant_count += 1 and add _create_pending_finding
    # This is done at the end of the function
    
    # Find the return statement and replace score calculation
    pattern = rf'(def {func_name}.*?)(return \{{\s*\'question_id\': \'{sec_num.upper()}\',.*?\'score\': max\(0, score\),)'
    
    def replace_return(match):
        func_content = match.group(1)
        
        # Replace score deductions
        func_content = re.sub(r'\s*score\s*-=\s*(\d+)', '', func_content)
        
        # Add compliant_count tracking after COMPLIANT findings
        func_content = re.sub(
            r"(\{\s*'bp':\s*'[^']+',\s*'status':\s*'COMPLIANT',",
            r"compliant_count += 1\n                findings.append({\n                    'bp': '\1',\n                    'status': 'COMPLIANT',",
            func_content
        )
        
        # Add non_compliant_count tracking after NON_COMPLIANT findings  
        func_content = re.sub(
            r"(\{\s*'bp':\s*'[^']+',\s*'status':\s*'NON_COMPLIANT',",
            r"non_compliant_count += 1\n                findings.append({\n                    'bp': '\1',\n                    'status': 'NON_COMPLIANT',",
            func_content
        )
        
        # Add pending_count for PENDING_REVIEW
        func_content = re.sub(
            r"findings\.append\(\{\s*'bp':\s*'([^']+)',\s*'status':\s*'PENDING_REVIEW',\s*'finding':\s*'([^']+)',",
            r"pending_count += 1\n                findings.append(self._create_pending_finding(\n                    '\1',\n                    '\2',",
            func_content
        )
        
        # Calculate score at the end
        return_section = f"        # Calculate score based on compliant BPs\n        score = self._calculate_section_score(total_bps, compliant_count)\n        \n        return {{\n            'question_id': '{sec_num.upper()}', "
        
        return func_content + return_section
    
    return content


if __name__ == '__main__':
    with open('src/app/security_evaluator.py', 'r') as f:
        content = f.read()
    
    for sec_num in ['SEC02', 'SEC03', 'SEC04', 'SEC05', 'SEC06', 'SEC07', 'SEC08', 'SEC09', 'SEC10', 'SEC11']:
        content = update_sec_function(content, sec_num)
    
    with open('src/app/security_evaluator.py', 'w') as f:
        f.write(content)
    
    print("✓ Updated SEC02-SEC11 with BP-based scoring")
