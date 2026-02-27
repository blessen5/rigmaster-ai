from app import app
import sys

with open('endpoints.txt', 'w', encoding='utf-8') as f:
    for rule in app.url_map.iter_rules():
        f.write(f"{rule.endpoint}\n")
    
    f.write(f"\nSEARCH 'group_planning': {'group_planning' in app.view_functions}\n")
    f.write(f"SEARCH 'group_builder': {'group_builder' in app.view_functions}\n")
    f.write(f"SEARCH 'group_builder_page': {'group_builder_page' in app.view_functions}\n")
