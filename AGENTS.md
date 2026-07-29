# GlossWise Agent Guide

GlossWise is a standalone Python application, SDK, HeavenBase extension, and
MCP server. Keep changes modular and preserve the short user workflow described
in canonical `README.en.md`; `README.md` is its generated projection.

## Authority

Read in this order:

1. `README.en.md` for public behavior and supported workflows.
2. `pyproject.toml` for package, environment, and test policy.
3. GitHub issues and pull requests for active work.
4. `docs/heavenbase-feedback.md`, when present, for local HeavenBase evidence.

Git history owns completed work. Do not create a second task queue in repository
notes.

## Project Rules

- Use public HeavenBase APIs and import the package as `import heavenbase as
  hb`.
- Put workspace behavior on `workspace.glosswise`; keep CLI and MCP functions
  as thin adapters.
- Namespace every MCP tool with `glosswise_`.
- Keep translation-model selection in the client. GlossWise retrieves and
  validates context; it does not conceal an LLM.
- Keep the captured `src/glosswise` module root free of repository,
  environment, test, and build artifacts.
- Record reproducible HeavenBase integration difficulties in the ignored local
  `docs/heavenbase-feedback.md`, including evidence, the project response, and
  the desired upstream improvement. Do not commit or link this local notebook
  from release documentation.
- Do not commit credentials, local workspaces, databases, or generated test
  state.

## Verification

Use the checked-in wrappers:

```console
bash scripts/sync-env.bash
bash scripts/flake.bash --ci
bash scripts/test.bash
bash scripts/test.bash -m full
uv build
```

Run commands through the environment wrapper supplied by the current harness
when one is required.
