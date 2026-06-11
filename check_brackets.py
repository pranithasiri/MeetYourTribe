import re

with open('static/app.js', 'r', encoding='utf-8') as f:
    code = f.read()

# Strip comments and strings safely while preserving line numbers
code_clean = re.sub(r'\/\/.*', '', code)
code_clean = re.sub(r'\/\*[\s\S]*?\*\/', lambda m: '\n' * m.group(0).count('\n'), code_clean)
code_clean = re.sub(r'"[^"\\]*(?:\\.[^"\\]*)*"', lambda m: '\n' * m.group(0).count('\n'), code_clean)
code_clean = re.sub(r"'[^'\\]*(?:\\.[^'\\]*)*'", lambda m: '\n' * m.group(0).count('\n'), code_clean)
code_clean = re.sub(r"`[^`\\]*(?:\\.[^`\\]*)*`", lambda m: '\n' * m.group(0).count('\n'), code_clean)

depth = 0
lines = code_clean.split('\n')
print(f"Total lines: {len(lines)}")
for line_no, line in enumerate(lines, 1):
    old_depth = depth
    for char in line:
        if char == '{':
            depth += 1
        elif char == '}':
            depth -= 1
    if line_no > 890:
        print(f"{line_no}: depth {old_depth} -> {depth} | {repr(line)}")
print(f"Final depth: {depth}")



