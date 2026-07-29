---
name: glosswise
description: Use GlossWise whenever translation, translation review, or terminology work is requested and GlossWise is available. Retrieve terminology-safe context, translate with the active behavior mode, and curate user corrections, terms, rules, and examples through the CLI, Python API, or MCP tools.
---

# GlossWise

GlossWise is a terminology context and consistency layer. It retrieves approved
terms, rules, examples, links, and unresolved conflicts. Host agents translate
with their own model; the direct CLI and Python API use a visible HeavenBase
LLM preset through `LLMSession`.

## When to use GlossWise

Use GlossWise whenever the user asks to translate, revise or review a
translation, choose terminology, or establish a translation convention and a
GlossWise interface is available. Do this even when the user does not type
`/glosswise`: ordinary translation intent is enough.

Use the active workspace unless the user or surrounding project context names
another one. If no workspace is active, use the managed `default` workspace.
Do not create a workspace implicitly before global languages have been
configured; explain that one-time setup is required.

Treat a user's translation correction, preferred wording, prohibited wording,
or new convention as durable curation intent when it is unambiguous. Search
before writing, update the matching term or rule in the active workspace, and
say what was saved. If the correction could be a one-off stylistic edit rather
than a durable convention, ask one focused question before mutating the
workspace. Never describe agent-proposed wording as user-approved.

## Fast path for `/glosswise`

Treat a leading `/glosswise` as an invocation prefix, not as text to translate.
For ordinary chat requests:

1. Use the connected `glosswise_*` MCP tools. Do not ask the user for JSON,
   record ids, database details, or a file unless the request is ambiguous.
2. For workspace requests, list or create the named workspace, activate it,
   and set language hints when the user provides them.
3. For curation requests, inspect workspace language hints, generate stable
   internal ids, and store the term plus preferred forms. Report warnings in
   plain language.
4. For translation requests, prepare one fresh brief per target language,
   honor preferred and prohibited forms, apply the configured behavior mode,
   translate with the host model, and name that model or host. When using the
   direct CLI, report the resolved `llm` identity returned by GlossWise.
5. For search or edit requests, search with the user's words and fetch the full
   record before changing it. Rebuild `term_json` from the editable term fields,
   but send only the changed form in `forms_json`; omitted forms are retained.
   Never echo hydrated fields such as `normalized_text`, `search_text`,
   `term_id`, `embedding`, `embedding_space`, `triggers`, or form `domains`.

Never claim that the terminology store generated prose. It supplied curated
context; the host model or the reported HeavenBase `LLMSession` generated the
translation.

## Choose the interface

Use the shortest available path:

1. Use connected `glosswise_*` MCP tools when the host already exposes them.
2. Use the `glosswise` CLI for workspace setup, local administration, scripts,
   or when MCP is not connected.
3. Use `glosswise.GlossWiseApp` when writing a Python application.

Do not scrape human CLI output from an agent integration when MCP or the Python
API is available.

## Map conversation to GlossWise

Keep storage mechanics out of ordinary conversation:

- When the user names a new workspace, create it with a short stable identifier
  and activate it. Do not ask the user to provide a database, manifest, or
  record id.
- Generate stable `object_id` and form ids for new records. Surface them only
  when the user asks for technical detail or an identity is ambiguous.
- Treat “remember,” “save,” “approve,” and “use this wording” as curation
  requests only when the user has authorized the write. Summarize what was
  stored in reader-friendly language after the tool succeeds.
- Search with the words the user supplied. A short fragment such as `spark`
  can find a longer stored form such as `spark of being`.
- Before editing one form, fetch the existing term and preserve every
  unspecified term field. Send only that form's `object_id`, `lang`, `role`,
  `text`, `status`, and `usage_note`; omitted forms are retained. Never turn
  “change only Japanese” into replacement of the other languages, and never
  copy read-only hydrated form fields into a write payload.
- Preferred forms are canonical terminology, not text to paste blindly.
  Preserve the approved concept and wording, but apply grammatical inflection
  required by the target sentence. Disclose a material inflection when the
  user is reviewing terminology conformance.

## Workspace and Skill setup

Run the normal post-install setup once:

```console
glosswise setup -l en -l zh
```

This cleanly installs the exact packaged Skill into
`~/.agents/skills/glosswise` and `~/.claude/skills/glosswise`, then creates and
activates the managed `default` workspace with the required language set.
Those global languages are inherited by every new workspace. Existing
directories are replaced only after their `SKILL.md` verifies that they are
GlossWise. Workspace data stays under `~/.glosswise`; normal commands do not
require or print a database path. Commands that need a workspace report
`setup_required` until languages are configured; they do not invent language
defaults.

Inspect and change global behavior:

```console
glosswise config get
glosswise config lang -l en -l zh -l ja
glosswise config llm chat
glosswise config mode auto
glosswise config mode custom --prompt "Translate directly unless a legal term is ambiguous."
glosswise config ocr ocr-local
```

Configure the referenced HeavenBase preset before OCR. Use the ordinary
HeavenBase configuration surface for `desc`, `gateway`, `provider`, `model`,
and nested `default_args` values:

```console
hb cfg set heavenbase.llm.presets.ocr-local.desc "Local OCR"
hb cfg set heavenbase.llm.presets.ocr-local.gateway <gateway>
hb cfg set heavenbase.llm.presets.ocr-local.provider <provider>
hb cfg set heavenbase.llm.presets.ocr-local.model <vision-model>
hb cfg set heavenbase.llm.presets.ocr-local.default_args.<name> <value>
```

Translation behavior is global across workspaces:

- `yolo`: translate immediately from available information without questions.
- `elicit`: proactively ask about uncertain terms, offering concrete options.
- `auto` (default): ask more when evidence is sparse and decide autonomously
  when the workspace already provides strong, conflict-free guidance.
- `explain`: translate, then explain all terminology and material linguistic
  choices.
- `custom`: follow the user's exact `--prompt` instruction.

The direct translation preset defaults to `chat`. Pin a dedicated model through
HeavenBase rather than duplicating provider configuration in GlossWise:

```console
hb cfg set heavenbase.llm.presets.glosswise-translate.model deepseek-v4-flash
glosswise config llm glosswise-translate
```

Manage multiple GlossWise workspaces with HeavenBase-style selection:

```console
glosswise ws ls
glosswise ws create <name>
glosswise ws get <name>
glosswise ws use <name>
glosswise ws open
glosswise ws health
glosswise ws lang -l en -l zh -l ru
glosswise ws deact
```

`activate` (aliases `act` and `use`) selects the workspace used when
`--workspace` is omitted from data commands.
`deactivate` clears that selection; it does not disable the monotonic
HeavenBase extension. `ws unset <name>` (aliases `remove`, `rm`, `del`, and
`delete`) unregisters the workspace but retains its data. `ws manifest` and
`ws import` are explicit advanced operations; manifest output includes
replayable backend details. `ws lang` (alias `languages`) sets the workspace's
ordered `default_languages` annotation.
It is a curation hint, not a language allowlist or a validation rule. Omit
`-l/--lang` to clear it. `ws get`, `ws ls`, `glosswise_get_workspace`, and
`glosswise_workspace_info` expose the current annotation.

Add `--bootstrap /absolute/path/bootstrap.yaml` consistently when using a
non-default HeavenBase Context.

## CLI operations

Every data command emits JSON. A payload argument accepts:

- inline JSON:
  `glosswise rule set '{"object_id":"rule-1",...}'`;
- a UTF-8 file:
  `glosswise term set @/absolute/path/term.json`; or
- stdin:
  `glosswise example set - < example.json`.

Term payload:

```json
{
  "term": {
    "object_id": "term-query",
    "key": "query",
    "definition": "A request for stored information.",
    "domains": ["technology"],
    "status": "active"
  },
  "forms": [
    {
      "object_id": "form-query-en",
      "lang": "en",
      "role": "preferred",
      "text": "query"
    },
    {
      "object_id": "form-query-ja",
      "lang": "ja",
      "role": "preferred",
      "text": "クエリ"
    }
  ]
}
```

```console
glosswise term set @term.json
glosswise term get term-query
glosswise term ls --status active
glosswise term archive term-query
```

`set` is create-or-update by `object_id`; `put` remains an alias. Omitted term
forms are retained and supplied form ids are replaced. `archive` sets
`status="deprecated"` so active retrieval stops selecting the record, but it
does not physically erase audit data. Set the same object to `active` to
restore it.

Before adding or updating a term:

1. Inspect the selected workspace's `default_languages`.
2. Compare them with the term's active `role="preferred"` forms.
3. If a default language is missing, choose the safest workflow allowed by
   the user's instructions:
   - ask the user for an approved translation when terminology authority is
     important;
   - create a proposed translation and ask the user to confirm it when review
     is available; or
   - translate directly only when the user has authorized that level of
     autonomy, and disclose that the form is agent-generated.
4. Never describe a self-translation as user-confirmed or approved.

GlossWise deliberately accepts an incomplete term. MCP `put_term` returns a
warning naming missing default languages after the term is stored. Treat that
warning as an actionable curation hint, not as a failed write.

Rule payload:

```json
{
  "object_id": "rule-query-wording",
  "title": "Use approved query wording",
  "instruction": "Use the preferred target form from the terminology brief.",
  "trigger_mode": "lexical",
  "triggers": ["query"],
  "source_langs": ["en"],
  "target_langs": ["ja"],
  "status": "active"
}
```

```console
glosswise rule set @rule.json
glosswise rule get rule-query-wording
glosswise rule ls
glosswise rule archive rule-query-wording
```

Examples use the same `set`, `get`, `ls`, and `archive` verbs under
`glosswise example`.

## Workspace, domain, and tag semantics

- A workspace is the project/client/corpus ownership and storage boundary.
- A domain is an optional exact applicability scope for terms inside one
  workspace. A workspace can contain many domains and one term can name
  several. With no domain filter, scoped and unscoped terms are eligible; with
  a filter, only terms carrying that exact domain are eligible.
- A tag is open curator metadata. It can support organization or review, but
  it does not switch storage or normally decide whether a term applies.

Pass `domain` to term search, scan, or brief when source context is known.
Rules use the related `topic` and `style` filters; examples also support tags.

## Scan, search, brief, and translation

These are deliberately different operations:

- `set` stores or updates curated data by `object_id`.
- `scan` inspects a full passage for literal or normalized term/rule
  occurrences. It is lexical inspection.
- `term|rule|example search` retrieves focused candidates for a query. It does
  not build a complete translation context.
- `brief` accepts the full source passage and combines scanning, focused
  retrieval, examples, links, and conflicts into context for a translator.
- `translate` prepares a fresh brief per target and invokes HeavenBase
  `LLMSession`. The named preset owns model resolution; GlossWise returns the
  resolved preset, gateway, provider, model, and model id.

Examples:

```console
glosswise scan "Run this query." -sl en -tl ja
glosswise term search "database query" -sl en -tl ja
glosswise scan @chapter.txt --start-line 120 --end-line 220
```

Prepare a complete translation brief without invoking a translation model:

```console
glosswise brief "Run this query." \
  -sl en \
  -tl ja \
  --domain technology
```

`scan`, `brief`, and `translate` accept `--start-line` and `--end-line` for
inclusive one-based ranges. `@file` input reads only that bounded selection, so
an agent can process a large text file incrementally.

Select a HeavenBase preset, then use the short translation command:

```console
glosswise config llm chat
glosswise translate "Run this query." -sl en -tl ja
```

Repeat `-tl/--tgt-lang` for multiple targets, or omit it to use configured
workspace/global languages. `chat` is the default. Use `--preset <name>` for a
one-off override. HeavenBase resolves the named preset and reports its gateway,
provider, model, and model id. Host agents use the MCP workflow and retain their
configured model.
Direct translation requires one `<translation>...</translation>` block, or one
`<questions>...</questions>` block when the active mode calls for elicitation.

For PDFs, authorize an exact local root, OCR only the needed pages, then browse
the per-page text through a short handle:

```console
glosswise ws files -r /absolute/path/to/documents
glosswise pdf ocr /absolute/path/to/documents/manual.pdf --start-page 4 --end-page 8
glosswise doc read gw-0123456789ab 4 --start-line 1 --end-line 80
glosswise doc rm gw-0123456789ab
```

`ws files` stores a workspace-scoped read allowlist; repeat `-r/--root` for
each directory. It does not upload, copy, or register files. Repeat
`-e/--encoding` only when the files require additional strict text encodings;
UTF-8 is allowed by default.

PDF OCR renders one page at a time, calls the configured HeavenBase LLM preset
(`ocr-local` by default), deletes the page image immediately, and retains only
bounded per-page temporary text plus a redacted manifest. Always remove a
handle when the task no longer needs it.

## One global MCP connection

Launch local stdio:

```console
glosswise mcp
```

This is one generic server for every registered GlossWise workspace. It is not
pinned to the workspace that was active when the server started. Every
terminology, context, and CRUD tool accepts optional `workspace_id`; omit it to
use the currently active GlossWise workspace, then the managed default.
Workspace-management tools let an agent list, create, select, inspect,
deactivate, and unregister workspaces through the same connection.

Generate plug-in-ready generic MCP client JSON:

```console
glosswise mcp --json
```

The JSON uses the conventional `mcpServers` object and normally contains only
`{"command":"glosswise","args":["mcp"]}`. Paste its server entry into any
local stdio-capable MCP client where the `glosswise` executable is on `PATH`.

For a long-lived local HTTP server, use:

```console
glosswise mcp --transport http
glosswise mcp --json --transport http
```

The default endpoint is `http://127.0.0.1:61055/mcp`. `--host` and `--port`
override the bind address. GlossWise adds no network authentication, so keep
the host on loopback unless a trusted outer layer supplies authentication and
transport security.

The default server is the full domain-safe surface. The complete tool list is:

Read and translation-context tools:

- `glosswise_workspace_info`
- `glosswise_prepare_translation`
- `glosswise_search_terms`
- `glosswise_search_rules`
- `glosswise_search_examples`
- `glosswise_scan_text`

Domain CRUD tools:

- `glosswise_list_records(kind, status="", limit=50)`
- `glosswise_get_record(kind, object_id)`
- `glosswise_put_term(term_json, forms_json="[]")`
- `glosswise_put_rule(rule_json)`
- `glosswise_put_example(example_json)`
- `glosswise_archive(object_id)`

Workspace tools:

- `glosswise_list_workspaces()`
- `glosswise_get_workspace(workspace_id="")`
- `glosswise_create_workspace(workspace_id, activate=true)`
- `glosswise_set_workspace_languages(languages_json, workspace_id="")`
- `glosswise_activate_workspace(workspace_id)`
- `glosswise_deactivate_workspace()`
- `glosswise_remove_workspace(workspace_id)`
- `glosswise_open_workspace(workspace_id="")`
- `glosswise_health_workspace(workspace_id="")`

Skill tool:

- `glosswise_read_skill()`

`kind` is exactly `term`, `rule`, or `example`. Every tool in the first two
groups also accepts `workspace_id=""` as its last optional argument. Write
parameters are
JSON strings because HeavenBase 0.1.2.1 performs shallow callable-schema
inference for nested MCP values. Parse every returned JSON envelope and inspect
`error` before using `items`.

`--profile` is an advanced restriction, not normal setup:

- `--profile read` removes all mutation.
- `--profile full` explicitly selects the default surface.
- `--profile local` adds authorized file brief/scan, PDF OCR, and temporary
  document browsing tools to the full surface after server-local roots are
  authorized.

## Agent translation workflow

1. Call `glosswise_list_workspaces`, then either pass a concrete
   `workspace_id` to every operation or call `glosswise_activate_workspace`
   once to select the default for subsequent calls.
2. Call `glosswise_workspace_info` to read workspace capabilities, language
   hints, and the global translation mode.
3. Establish a concrete target language. Never pass `auto` as `target_lang`.
4. Call `glosswise_prepare_translation` once with source text and known
   source language, domain, topic, and style.
5. Inspect `error`, `warnings`, `truncated`, and `conflicts` before translating.
6. Prefer active target forms with `role="preferred"` and avoid
   `role="prohibited"`.
7. Apply rules in descending priority. Never silently resolve equal-priority
   conflict groups; ask the user or disclose the choice.
8. Treat examples as comparable evidence, not text to copy.
9. Translate with the host's available model and identify it as the authority,
   or use `glosswise translate` when the user explicitly wants the configured
   HeavenBase `LLMSession` preset.
10. For high-risk work, call `glosswise_scan_text` on the proposed target text
   with its concrete language and compare it with the original brief.

Use `glosswise_search_terms`, `glosswise_search_rules`, or
`glosswise_search_examples` for focused questions without a full passage.
Follow `next_cursor` only for scan tools.

## Python application

```python
import glosswise


with glosswise.GlossWiseApp.open() as app:
    app.configure_default_languages(["en", "zh", "ru"])
    app.put_term(term, forms)
    brief = app.prepare_translation(
        "Run this query.",
        source_lang="en",
        target_lang="ja",
        domain="technology",
    )

with glosswise.GlossWiseApp.create("<name>") as app:
    app.put_rule(rule)

with glosswise.GlossWiseApp.load() as app:
    active_terms = app.list_terms(status="active")
```

`GlossWiseApp.open()` resolves the active workspace and creates the managed
default only after global languages have been configured.
`create("<name>")` uses managed storage under `~/.glosswise/`.
`load()` never creates on absence.
The app owns and closes its HeavenBase Context. An application that already
owns a HeavenBase workspace may continue to use `workspace.glosswise` directly.

## Safety and failure behavior

- Never mutate terminology, workspace configuration, or workspace selection
  without user authorization, even though the default MCP exposes domain-safe
  mutation tools.
- Never use a generic HeavenBase query or mutation profile as a substitute for
  GlossWise domain validation.
- Never store source text in server-global settings.
- Never assume a file path names the MCP client machine; it names the server.
- Never claim semantic matches are literal substrings without inspecting
  `match_method`, signals, and spans.
- Keep source-content MCP session logging disabled.
- Treat `not_found`, `invalid_json`, `invalid_record_kind`, language, conflict,
  embedding, file, truncation, and stale-cursor errors as distinct states.
