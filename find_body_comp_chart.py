#!/usr/bin/env python
import os
import re

# Find relevant templates
template_dir = 'templates'
search_patterns = [
    'bodyCompositionChart',
    '\[31.9',
    'body[_-]?(fat|composition)',
    'data: \[\d+\.\d+, \d+\.\d+\]',
]

def search_file(file_path, patterns):
    print(f"Searching in {file_path}...")
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
    for pattern in patterns:
        matches = re.finditer(pattern, content, re.IGNORECASE)
        for match in matches:
            line_number = content[:match.start()].count('\n') + 1
            line_content = content.splitlines()[line_number-1]
            print(f"  Line {line_number}: {line_content}")

for filename in os.listdir(template_dir):
    if filename.endswith('.html'):
        file_path = os.path.join(template_dir, filename)
        search_file(file_path, search_patterns)