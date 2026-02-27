#!/usr/bin/env python
# Script to move Group Planning routes to correct location in app.py

with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find the markers
main_block_start = content.find('\nif __name__')
group_module_start = content.find('# GROUP PC BUILD PLANNING MODULE')

if main_block_start > 0 and group_module_start > main_block_start:
    # Routes are after if __name__, need to move them before
    before_main = content[:main_block_start]
    main_and_after = content[main_block_start:group_module_start]
    group_section = content[group_module_start:]
    
    # Reconstruct: before_main + group_section + main_and_after
    new_content = before_main.rstrip() + '\n\n' + group_section.strip() + '\n\n' + main_and_after.lstrip()
    
    with open('app.py', 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print("Successfully moved Group Planning routes before if __name__ block")
else:
    print(f"Could not find markers. main_block_start={main_block_start}, group_module_start={group_module_start}")
