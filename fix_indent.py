# Fix indentation in database.py

with open('database.py', 'r', encoding='utf-8') as f:
 lines = f.readlines()

new_lines = []
for line in lines:
 # Count leading spaces
 stripped = line.lstrip(' ')
 leading = len(line) - len(stripped)
 # Replace1 space with4
 if leading ==1:
    line = ' ' + stripped
 new_lines.append(line)

with open('database.py', 'w', encoding='utf-8') as f:
 f.writelines(new_lines)

print('Fixed indentation')
