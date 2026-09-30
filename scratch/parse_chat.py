import json
import re

with open('documentation/chatgpt_extracted.txt', 'r', encoding='utf-8') as f:
    content = f.read()

# Try finding JSON objects or text in this script
matches = re.findall(r'"text"\s*:\s*"(.*?)(?<!\\)"', content)
print(f'Total text matches: {len(matches)}')
with open('documentation/chatgpt_all_texts.txt', 'w', encoding='utf-8') as out:
    for i, m in enumerate(matches):
        if len(m) > 80:
            cleaned = m.encode('utf-8').decode('unicode_escape', errors='ignore')
            out.write(f"\n\n=== MATCH {i} (len {len(m)}) ===\n{cleaned}\n")
print("Saved matches to documentation/chatgpt_all_texts.txt")
