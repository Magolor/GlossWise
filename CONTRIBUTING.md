# Contributing to GlossWise

Thank you for helping improve GlossWise. Bug reports, focused feature proposals,
documentation fixes, tests, and HeavenBase integration findings are welcome.

## Development setup

GlossWise supports Python 3.10 through 3.13 and uses `uv` for its reproducible
development environment:

```console
git clone https://github.com/Magolor/GlossWise.git
cd GlossWise
uv sync --extra dev --locked
uv run pre-commit install
bash scripts/test.bash
bash scripts/flake.bash --ci
```

Use the repository scripts rather than invoking pytest, Black, or Flake8
directly. `scripts/test.bash` owns the test-marker policy.
The local pre-commit hooks regenerate the reviewable root `SKILL.md` from the
packaged source and copy canonical `README.en.md` to `README.md`. CI checks both
projections without modifying the worktree. Edit `README.en.md`, never the
generated `README.md`; update locale READMEs when its user-facing content
changes.

## Making a change

1. Open or reference a GitHub issue when the change needs design discussion.
2. Keep the public path short: interfaces call the API layer, which owns
   application behavior.
3. Add focused tests for behavior changes.
4. Update `README.en.md` and affected translations when installation, CLI,
   MCP, SDK, or user workflows change.
5. Record reproducible framework friction in the ignored local
   `docs/heavenbase-feedback.md`; do not commit the notebook or add private
   framework workarounds.
6. Run the fast tests and lint checks before opening a pull request.

Run the full release and packaging checks for changes to installation,
HeavenBase integration, MCP transport, packaging, or workspace lifecycle:

```console
bash scripts/test.bash -m full
uv build
```

## Pull requests

Keep pull requests focused and explain the user or developer impact. Include
the checks you ran and call out any compatibility or migration concern. By
participating, you agree to follow the [Code of Conduct](CODE_OF_CONDUCT.md).
