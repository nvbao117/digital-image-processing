import re

file_path = 'app/processors/builtin.py'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

param_str = '        "display_mode": {"label": "Display", "type": "choice", "choices": ["Result Only", "Grid View"], "default": 0},\n    }'
content = re.sub(r'    \}\n\n    def apply', param_str + '\n\n    def apply', content)

content = content.replace('return _apply_freq_filter_multichannel(img, mask)', 
                          'display_mode = int(kwargs.get("display_mode", 0))\n        return _apply_freq_filter_multichannel(img, mask, display_mode)')

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
