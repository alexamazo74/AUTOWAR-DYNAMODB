#!/usr/bin/env python3
import re

with open('src/app/security_evaluator.py', 'r', encoding='utf-8') as f:
    code = f.read()

# Find SEC05 line
lines = [l for l in code.split('\n') if 'SEC05' in l and 'Protección' in l]
print("SEC05 lines found:", len(lines))
for line in lines[:3]:
    print(f"  {line.strip()}")

# Check for 4 BPs near SEC05
sec05_start = code.find('def evaluate_sec05')
sec05_section = code[sec05_start:sec05_start+500]
print("\nSEC05 docstring:")
print(sec05_section[:300])
