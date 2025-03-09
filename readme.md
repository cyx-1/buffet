![release](./images/version_badge.svg) ![Coverage Status](./images/coverage_badge.svg) 

# Setup
- This project assumes that uv is the python package/project manager already installed via pipx
- Run ```uv run .\scripts\generate_coverage_badge.py``` to generate a new badge
- Run ```uv run ptw``` to run tests and watch for changes
- Run ```uv add pandas``` to add package pandas into the uv-managed virtual environment, and update pyproject.toml
- Note: to debug pytest, remember to turn off pycov via pytest.ini