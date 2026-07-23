# Contributing to transitbus

Thanks for taking the time to contribute! This project uses
[uv](https://docs.astral.sh/uv/) for everything.

## Installing with uv

Add `transitbus` to another project:

```bash
# from PyPI (once published)
uv add transitbus

# straight from the git repo
uv add "git+https://github.com/<user>/transitbus"

# as a local, editable checkout — handy when developing alongside it
uv add --editable C:\code\transitbus
```

## Working on transitbus itself

```bash
uv sync            # create .venv and install deps (incl. the dev group)
uv run pytest      # run the tests
uv run ruff check  # lint
```

`uv sync` reads `pyproject.toml`, creates a virtual environment, and installs
`pydantic` along with the dev dependencies (`pytest`, `pytest-asyncio`).

## Python version

`pyproject.toml` sets `requires-python = ">=3.14"`, so uv needs a Python 3.14
available. If you don't have one, let uv fetch it:

```bash
uv python install 3.14
```

## Before opening a pull request

- `uv run pytest` passes.
- `uv run ruff check` is clean.
- New behaviour has a test and, where it's user-facing, a note in the README.
