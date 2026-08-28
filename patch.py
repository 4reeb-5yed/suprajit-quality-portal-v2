import os

with open('.github/workflows/ci.yml', 'r', encoding='utf-8') as f:
    ci = f.read()

ci = ci.replace('python -m pytest tests/test_ultimate.py tests/test_sync_engine_dimensions.py -v --cov=app --cov-report=term', 
                'python -c "import tomllib; tomllib.load(open(\'pyproject.toml\',\'rb\'))"\n        python -m pytest tests/ -v --cov=app --cov-report=term')
ci = ci.replace('python tests/test_compiled_binary.py', 'python tests/smoke_test_binary.py')

with open('.github/workflows/ci.yml', 'w', encoding='utf-8') as f:
    f.write(ci)

with open('app/__init__.py', 'r', encoding='utf-8') as f:
    init = f.read()

init = init.replace('def create_app():', 'def create_app(test_config=None):')
init = init.replace('app.config.from_object(cfg)\n    setup_logging(app)', 'app.config.from_object(cfg)\n    if test_config:\n        app.config.update(test_config)\n    setup_logging(app)')

with open('app/__init__.py', 'w', encoding='utf-8') as f:
    f.write(init)

with open('tests/conftest.py', 'r', encoding='utf-8') as f:
    conftest = f.read()

conftest = conftest.replace('app = create_app()\n    app.config.update({', 'test_config = {\n        "TESTING": True,\n        "WTF_CSRF_ENABLED": False,\n        "RATELIMIT_ENABLED": False,\n        "DATABASE_PATH": db_path,\n        "STORAGE_FOLDER": storage_dir\n    }\n    app = create_app(test_config)\n    app.config.update({')

with open('tests/conftest.py', 'w', encoding='utf-8') as f:
    f.write(conftest)
