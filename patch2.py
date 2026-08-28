import os

with open('tests/conftest.py', 'r', encoding='utf-8') as f:
    conftest = f.read()

if 'limiter.enabled = False' not in conftest:
    conftest = conftest.replace('app = create_app(test_config)', 'app = create_app(test_config)\n    from app import limiter\n    limiter.enabled = False')

with open('tests/conftest.py', 'w', encoding='utf-8') as f:
    f.write(conftest)
