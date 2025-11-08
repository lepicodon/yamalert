# Yamalert

A lightweight toolkit for validating, linting and alerting on YAML files. Yamalert helps you catch common YAML mistakes, enforce conventions, and integrate YAML checks into CI pipelines.

> NOTE: This is a generic, friendly README template. If you want me to tailor it to the project's real usage (language, install method, CLI flags, examples), tell me which language/build system the project uses or point me to key source files and I'll update the README accordingly.

## Features
- Validate YAML syntax and report clear, file/line-specific errors.
- Lint for common issues (tabs vs spaces, duplicate keys, inconsistent indentation).
- Provide configurable rules and presets.
- CI-friendly output (machine-readable and human-readable formats).
- Can be used as a CLI tool or as a library in your projects.

## Quick start

1. Clone the repository

```bash
git clone https://github.com/lepicodon/yamalert.git
cd yamalert
```

2. Build or install

Because I don't have information about the project's language/tooling, here are a few common ways — pick the one that matches this repository and I can update this section:

- Python (pip editable install):

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

- Node.js (npm/yarn):

```bash
npm install
# or
yarn install
```

- Go:

```bash
go build ./...
```

- Generic build (if there is a Makefile):

```bash
make
```

## Usage

As a CLI (example):

```bash
# Run yamalert on a single file
yamalert check path/to/config.yml

# Check all YAML files in a repo
yamalert check . --ext yml --ext yaml

# Output machine-readable results (JSON)
yamalert check . --format json > yamalert-results.json
```

As a library (pseudo-code):

```python
from yamalert import Runner

r = Runner(config=".yamalertrc")
results = r.run("./configs")
for res in results:
    print(res)
```

## CI integration (GitHub Actions example)

```yaml
name: yamalert
on: [push, pull_request]

jobs:
  yamalert:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python 3.x
        uses: actions/setup-python@v4
        with:
          python-version: '3.x'
      - name: Install
        run: |
          python -m pip install --upgrade pip
          pip install -e .
      - name: Run Yamalert
        run: yamalert check . --format github
```

## Configuration

Add a .yamalertrc (YAML or JSON) to the project root to configure rules, ignore patterns, and output preferences. Example:

```yaml
rules:
  no-tabs: error
  duplicate-keys: warn
ignore:
  - "tests/fixtures/**"
```

## Contributing

Contributions are very welcome — thanks!

- Fork the repo and create a feature branch (git checkout -b feat/my-feature).
- Run tests and linters before opening a PR.
- Open a clear, focused pull request describing the change and why it is needed.

If you'd like help writing issues or splitting work into small tasks, mention me in an issue and I can help create the tasks.

## Roadmap ideas

- Add official presets for common CI providers.
- Provide GitHub/GitLab fast-fail action integrations.
- Add an auto-fixer for trivial problems (e.g., convert tabs to spaces).

## License

Specify the license used for this project (e.g., MIT, Apache-2.0). If you haven't chosen one yet, consider adding a LICENSE file.

## Maintainers

- lepicodon (owner)

## Acknowledgements

Inspired by many YAML linters and validators — thank you to all open-source contributors.
