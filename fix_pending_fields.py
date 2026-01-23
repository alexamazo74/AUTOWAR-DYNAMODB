import re

with open('src/app/security_evaluator.py', 'r') as f:
    content = f.read()

# Pattern 1: PENDING_REVIEW findings without risk/remediation/evidence
# findings.append({\n    'bp': 'XXX',\n    'status': 'PENDING_REVIEW',\n    'finding': 'XXX',\n    'severity': 'XXX'\n})

pattern1 = r"(\s+)findings\.append\(\{\s*'bp':\s*'([^']+)',\s*'status':\s*'PENDING_REVIEW',\s*'finding':\s*'([^']+)',\s*'severity':\s*'([^']+)'\s*\}\)"

def fix_missing_fields_1(match):
    indent = match.group(1)
    bp = match.group(2)
    finding = match.group(3)
    severity = match.group(4)
    return f"""{indent}pending_count += 1
{indent}findings.append(self._create_pending_finding(
{indent}    '{bp}',
{indent}    '{finding}',
{indent}    '{severity}'
{indent}))"""

content = re.sub(pattern1, fix_missing_fields_1, content, flags=re.MULTILINE)

# Pattern 2: findings.append with longer multi-line structure missing fields
pattern2 = r"(\s+)findings\.append\(\{\s*'bp':\s*'([^']+)',\s*'status':\s*'PENDING_REVIEW',\s*'finding':\s*'([^']+)',\s*'severity':\s*'([^']+)',?\s*(?:'risk':|'remediation':|'evidence':)?[^\}]*\}\)"

# This is too complex, let's be more manual

# Find and manually fix the ones in SEC02-SEC11
# Just add risk, remediation, evidence fields when they're missing

lines = content.split('\n')
new_lines = []
i = 0
while i < len(lines):
    line = lines[i]
    # Check if this is a PENDING_REVIEW without all fields
    if "'status': 'PENDING_REVIEW'" in line and i > 0:
        # Look ahead to see if risk/remediation/evidence are missing
        block_start = i
        while i < len(lines) and '}' not in lines[i]:
            i += 1
        
        # Check the block (from block_start to i)
        block = '\n'.join(lines[block_start:i+1])
        
        if "'risk':" not in block or "'remediation':" not in block or "'evidence':" not in block:
            # Missing fields - reconstruct with defaults
            # Extract bp, finding, severity
            bp_match = re.search(r"'bp':\s*'([^']+)'", block)
            finding_match = re.search(r"'finding':\s*'([^']+)'", block)
            severity_match = re.search(r"'severity':\s*'([^']+)'", block)
            
            if bp_match and finding_match and severity_match:
                bp = bp_match.group(1)
                finding = finding_match.group(1)
                severity = severity_match.group(1)
                
                new_lines.append("        pending_count += 1")
                new_lines.append("        findings.append(self._create_pending_finding(")
                new_lines.append(f"            '{bp}',")
                new_lines.append(f"            '{finding}',")
                new_lines.append(f"            '{severity}'")
                new_lines.append("        ))")
                i += 1
                continue
    
    new_lines.append(line)
    i += 1

with open('src/app/security_evaluator.py', 'w') as f:
    f.write('\n'.join(new_lines))

print("✓ Fixed PENDING_REVIEW fields")
