with open('app/sync_engine.py', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace('", "\n".join(error_logs)', '", "\\n".join(error_logs)')
content = content.replace('ALL HISTORICAL"}\n"', 'ALL HISTORICAL"}\\n"')
content = content.replace('trace.append(f"\n--- DRY RUN SUMMARY ---")', 'trace.append(f"\\n--- DRY RUN SUMMARY ---")')
content = content.replace('return "\n".join(trace)', 'return "\\n".join(trace)')

with open('app/sync_engine.py', 'w', encoding='utf-8') as f:
    f.write(content)
