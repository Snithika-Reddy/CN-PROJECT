import json
import re

with open('documentation/chatgpt_extracted.txt', 'r', encoding='utf-8') as f:
    text = f.read()

# Look for MASTER PROMPT FOR ANTIGRAVITY
pos = text.find('MASTER PROMPT FOR ANTIGRAVITY')
if pos != -1:
    print(f'Found MASTER PROMPT at {pos}')
    # find where the prompt text starts and ends
    # The prompt starts around pos and ends before the next json token or triple backticks
    prompt_chunk = text[pos:pos+50000]
    # Clean escaped chars
    prompt_clean = prompt_chunk.encode('utf-8').decode('unicode_escape', errors='ignore')
    with open('documentation/master_specification_full.md', 'w', encoding='utf-8') as f_out:
        f_out.write(prompt_clean)
    print(f'Wrote full prompt ({len(prompt_clean)} chars) to documentation/master_specification_full.md')
else:
    print('Not found directly, searching...')
