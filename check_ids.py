import os
import re

frontend_dir = os.path.abspath('frontend')
for fname in os.listdir(frontend_dir):
    if fname.endswith('.html'):
        fpath = os.path.join(frontend_dir, fname)
        content = open(fpath, encoding='utf-8').read()
        ids_called = set(re.findall(r'getElementById\([\'"]([^\'"]+)[\'"]\)', content))
        ids_in_dom = set(re.findall(r'id=[\'"]([^\'"]+)[\'"]', content))
        missing = ids_called - ids_in_dom
        if missing:
            print(f"File {fname} has missing DOM IDs:")
            for m in sorted(missing):
                print(f"  - {m}")
