import re

file_path = 'app/processors/builtin.py'
with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find where frequency filters start
freq_idx = 0
for i, line in enumerate(lines):
    if 'FREQUENCY DOMAIN FILTERS' in line:
        freq_idx = i
        break

new_lines = []
for i, line in enumerate(lines):
    # If before frequency domain filters, remove the display_mode param
    if i < freq_idx:
        if '"display_mode": {"label": "Display"' in line:
            continue
    else:
        # If in frequency domain filters, fix missing comma on previous line if needed
        if '"display_mode": {"label": "Display"' in line:
            # Check previous line
            prev = new_lines[-1]
            if prev.strip() and not prev.strip().endswith(',') and prev.strip() != '{':
                new_lines[-1] = prev.rstrip('\n') + ',\n'
                
    new_lines.append(line)

with open(file_path, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)
