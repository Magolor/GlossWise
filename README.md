# GlossWise

<p align="center">
  <strong>English</strong> ·
  <a href="README.ar.md">العربية</a> ·
  <a href="README.zh.md">中文</a> ·
  <a href="README.fr.md">Français</a> ·
  <a href="README.ru.md">Русский</a> ·
  <a href="README.es.md">Español</a> ·
  <a href="README.de.md">Deutsch</a> ·
  <a href="README.ja.md">日本語</a>
</p>

<p align="center">
  <img src="docs/assets/glosswise-banner.png" alt="GlossWise — terminology-safe translation for AI agents" width="100%">
</p>

<p align="center">
  <a href="https://github.com/Magolor/GlossWise/actions/workflows/ci.yml"><img src="https://github.com/Magolor/GlossWise/actions/workflows/ci.yml/badge.svg?branch=master" alt="Continuous integration"></a>
  <a href="https://www.python.org/"><img src="https://img.shields.io/badge/Python-3.10–3.13-3776AB" alt="Python 3.10 through 3.13"></a>
  <a href="https://ahvn.top"><img src="https://img.shields.io/badge/HeavenBase-0.1.2.1-6957E5" alt="HeavenBase 0.1.2.1"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-green.svg" alt="MIT License"></a>
</p>

<p align="center">
  <a href="#install">Install</a> ·
  <a href="#connect-an-agent">Connect an agent</a> ·
  <a href="#try-it-teach-once-translate-consistently">Try the demo</a> ·
  <a href="#everyday-prompts">Everyday prompts</a> ·
  <a href="#mcp-server">MCP tools</a> ·
  <a href="#python-sdk">Python SDK</a>
</p>

GlossWise stores approved terms, translation rules, and examples, then prepares
a compact brief for the calling agent or application. Host agents translate
with their own model; the direct CLI uses a visible HeavenBase LLM preset.

GlossWise is available as a CLI, MCP server, and Python SDK. Version `0.1.0.5`
supports `heavenbase>=0.1.2.1`.

## Install

GlossWise requires Python 3.10–3.13. Install the current source directly from
GitHub. Before installing, you can [review the exact agent Skill](SKILL.md):

```console
python -m pip install "git+https://github.com/Magolor/GlossWise.git"
glosswise setup -l en -l zh
```

To inspect or contribute to the source:

```console
git clone https://github.com/Magolor/GlossWise.git
cd GlossWise
python -m pip install .
glosswise setup -l en -l zh
```

`setup` requires the languages you normally translate between, saves them as
global defaults, creates and activates the `default` workspace with those
languages, then installs the GlossWise agent Skill at:

- `~/.agents/skills/glosswise`
- `~/.claude/skills/glosswise`

The public root Skill and the packaged copy installed by `setup` are kept
byte-for-byte identical.

Workspace data is managed automatically under `~/.glosswise/`. You do not need
to choose or expose a database. New workspaces inherit the global language
defaults; use `glosswise config lang -l en -l <language>` to change them.

Check the installation:

```console
glosswise ws ls
glosswise ws get
```

## Connect an agent

`glosswise setup` has already installed the common and Claude GlossWise Skills.
Connect the same global MCP server from any supported host:

| Host | One-time setup |
| --- | --- |
| [Claude Code](https://code.claude.com/docs/en/mcp) | `claude mcp add --scope user glosswise -- glosswise mcp` |
| [Codex](https://developers.openai.com/codex/mcp/) | `codex mcp add glosswise -- glosswise mcp` |
| [Cursor](https://docs.cursor.com/context/model-context-protocol) | Save `glosswise mcp --json` as `~/.cursor/mcp.json`. |
| [VS Code / Copilot](https://code.visualstudio.com/docs/copilot/chat/mcp-servers) | Add `.vscode/mcp.json` with a `servers.glosswise` stdio entry using command `glosswise` and args `["mcp"]`. |
| [OpenCode](https://opencode.ai/docs/mcp-servers/) | Add the local MCP entry below to `~/.config/opencode/opencode.json`. |
| [OpenClaw](https://ahvn.top/quickstart/heavenbase-mcp#3-connect-your-agent) | Run `glosswise mcp --transport http`, then set `mcp.servers.glosswise` to `http://127.0.0.1:61055/mcp` with transport `streamable-http`. |
| [Hermes](https://ahvn.top/quickstart/heavenbase-mcp#3-connect-your-agent) | Run `glosswise mcp --transport http`, then add its URL under `mcp_servers.glosswise` in `~/.hermes/config.yaml`. |
| [LM Studio](https://lmstudio.ai/docs/app/mcp) | Open **Program/Developer → Install → Edit mcp.json**, then paste the output of `glosswise mcp --json`. |
| [Qwen Code](https://qwenlm.github.io/qwen-code-docs/en/users/features/mcp/) | `qwen mcp add --scope user glosswise glosswise mcp` |
| [HeavenBase](https://ahvn.top/quickstart/heavenbase-mcp#3-connect-your-agent) | Run `glosswise mcp --transport http`, then `hb llm session --mcp http://127.0.0.1:61055/mcp`. |

For [OpenCode](https://opencode.ai/docs/mcp-servers/), add this to the global
`~/.config/opencode/opencode.json`:

```json
{
  "$schema": "https://opencode.ai/config.json",
  "mcp": {
    "glosswise": {
      "type": "local",
      "command": ["glosswise", "mcp"],
      "enabled": true
    }
  }
}
```

Verify the connection with the host's MCP list command, then restart the agent
when its documentation requires it.

Start a new chat and say:

```text
/glosswise List my workspaces and tell me which one is active.
```

The agent can now create workspaces, curate terminology, search it, and prepare
translation briefs on your behalf. You do not need to write JSON or manage a
database. One Skill and one MCP connection work across all GlossWise
workspaces.

For another stdio-capable MCP client, print the portable profile:

```console
glosswise mcp --json
```

## Try it: teach once, translate consistently

This demo starts with an ordinary model translation, teaches GlossWise two
terminology decisions in natural language, then repeats the original request
in a clean agent session. The excerpt is from
[Mary Shelley’s *Frankenstein*](https://www.gutenberg.org/cache/epub/42324/pg42324-images.html),
an early work of science fiction in the public domain.

### 1. Start a workspace

Ask your agent:

```text
/glosswise Create and select a GlossWise workspace named `frankenstein-lab`.
Set its default languages to English, Chinese, French, German, Russian, and Japanese.
```

Or use the two short CLI commands:

```console
glosswise ws create frankenstein-lab
glosswise ws lang -l en -l zh -l fr -l de -l ru -l ja
```

`ws create` selects the new workspace automatically. Repeat `-l/--lang` for
each ordered language. The set is a curation hint that reminds agents to
collect all six preferred forms without turning languages into a hard restriction.

### 2. Translate before teaching GlossWise

Send this paragraph to the agent:

```text
/glosswise Use the `frankenstein-lab` workspace. Translate the paragraph below
into Chinese, French, German, Russian, and Japanese. First check GlossWise for
relevant guidance, then identify the model or host that performed the translation.

“It was on a dreary night of November, that I beheld the accomplishment of my
toils. With an anxiety that almost amounted to agony, I collected the
instruments of life around me, that I might infuse a spark of being into the
lifeless thing that lay at my feet.”
```

The first wording depends on the agent's translation model. It may choose
literal phrases such as “spark of being” → `存在的火花`,
`étincelle de vie`, `Lebensfunken`, `искра жизни`, or `命の火花`.

### 3. Teach two decisions by conversation

Send one more message:

```text
/glosswise Save these as active preferred terms in the `frankenstein-lab`
workspace. The target forms are my project terminology decisions, not claims
about the novel's official translations.

1. “instruments of life” means the apparatus used in the experiment:
   Chinese 生命仪器; French instruments de vie;
   German Instrumente des Lebens; Russian орудия жизни;
   Japanese 生命の器具.

2. “spark of being” means the animating essence imparted to lifeless matter:
   Chinese 生命之火; French étincelle d'existence;
   German Funke des Seins; Russian искра бытия;
   Japanese 存在の火花.

Keep the English source forms too. Use the preferred terminology exactly when
target-language grammar permits; otherwise inflect it without changing the
approved concept. Tell me when both records are stored.
```

The agent handles the structured CRUD calls. If a requested workspace language
is missing, the installed Skill tells it to ask, propose a form for
confirmation, or clearly disclose an agent-generated form.

### 4. Start a new session and repeat the same request

End the current chat and start a new agent session. Send the exact prompt from
step 2 again—do not add a reminder about the terms you just stored:

```text
/glosswise Use the `frankenstein-lab` workspace. Translate the paragraph below
into Chinese, French, German, Russian, and Japanese. First check GlossWise for
relevant guidance, then identify the model or host that performed the translation.

“It was on a dreary night of November, that I beheld the accomplishment of my
toils. With an anxiety that almost amounted to agony, I collected the
instruments of life around me, that I might infuse a spark of being into the
lifeless thing that lay at my feet.”
```

The prompt is identical; only the persisted GlossWise workspace has changed.
The new session must retrieve that state rather than rely on chat memory. The
important change is now visible:

| Language | A baseline may use | GlossWise-guided wording |
| --- | --- | --- |
| Chinese | `生命工具` · `存在的火花` | `生命仪器` · `生命之火` |
| French | `instruments de la vie` · `étincelle de vie` | `instruments de vie` · `étincelle d'existence` |
| German | `Werkzeuge des Lebens` · `Lebensfunken` | `Instrumente des Lebens` · `Funken des Seins`¹ |
| Russian | `инструменты жизни` · `искра жизни` | `орудия жизни` · `искру бытия`¹ |
| Japanese | `生命の道具` · `命の火花` | `生命の器具` · `存在の火花` |

¹ The agent inflects the canonical preferred form to fit this sentence.

<details>
<summary>One successful GlossWise-guided result</summary>

**Chinese**

> 那是十一月一个阴沉的夜晚，我目睹了自己辛劳的成果。怀着近乎痛苦的焦虑，我把生命仪器聚集在身边，想把生命之火注入躺在我脚边的无生命之物中。

**French**

> Ce fut par une lugubre nuit de novembre que je contemplai l’accomplissement de mes travaux. Avec une anxiété qui confinait presque à l’agonie, je rassemblai autour de moi les instruments de vie afin d’insuffler une étincelle d'existence à la chose inanimée étendue à mes pieds.

**German**

> Es war in einer trüben Novembernacht, als ich die Vollendung meiner Mühen erblickte. Mit einer Angst, die beinahe an Qual grenzte, versammelte ich die Instrumente des Lebens um mich, um dem leblosen Ding zu meinen Füßen einen Funken des Seins einzuhauchen.

**Russian**

> В мрачную ноябрьскую ночь я увидел завершение своих трудов. С тревогой, почти переходившей в агонию, я собрал вокруг себя орудия жизни, чтобы вдохнуть искру бытия в безжизненное создание, лежавшее у моих ног.

**Japanese**

> 十一月の陰鬱な夜、私は自らの労苦の成就を目の当たりにした。苦悶に近い不安を抱えながら、私は生命の器具を周囲に集め、足元に横たわる生命なきものへ存在の火花を吹き込もうとした。

</details>

GlossWise did not generate these sentences. The connected agent did; GlossWise
made the approved terminology retrievable and inspectable before generation.

### 5. Find and edit it later

No record identifiers are needed:

```text
/glosswise Find the term about a spark in `frankenstein-lab`. Show its preferred
forms in a compact table.
```

Then edit it naturally:

```text
/glosswise Change only the Japanese preferred form for “spark of being” to
`生命の火花`. Keep every other language unchanged and show me the saved record.
```

This complete setup → create → curate → restart → brief → search → edit path is
exercised against an installed wheel and two independent stdio MCP sessions in
[`tests/test_quickstart.py`](https://github.com/Magolor/GlossWise/blob/master/tests/test_quickstart.py).

## Everyday prompts

Once connected, normal work can stay in chat. Management prompts below make
intentional changes; query and translation prompts are read-only unless they
explicitly ask to save something.

### Manage workspaces and terminology

- `/glosswise Create and select a workspace named <name>.`
- `/glosswise In workspace <name>, set the default languages to English, Chinese, and Japanese.`
- `/glosswise In workspace <name>, save “rate limit” as an active preferred term with English “rate limit”, Chinese “速率限制”, and Japanese “レート制限”. Show me the saved record.`
- `/glosswise Find “rate limit” in workspace <name>. Change only its Japanese preferred form to “速度制限”, preserve every other field and form, then show me the updated record.`
- `/glosswise Archive the term “rate limit” in workspace <name> so it is excluded from normal active-term lookup. Ask me before making the change.`

### Look up guidance and translate

- `/glosswise In workspace <name>, find active terms related to authentication. Show their preferred and prohibited forms in English, Chinese, and Japanese. Do not modify anything.`
- `/glosswise In workspace <name>, find rules and examples for translating error messages into French. Show priorities, styles, and conflicts. Do not modify anything.`
- `/glosswise Check “Requests over this limit are rejected.” against workspace <name>. List matching terms and rules without translating or saving anything.`
- `/glosswise Use workspace <name>. Translate “The client retries the request after the rate limit resets.” from English into Chinese and Japanese. Prepare a fresh GlossWise brief for each target language, apply active preferred terms and rules, flag conflicts, and identify the model or host that performed the translation.`
- `/glosswise Use workspace <name>. Translate the English passage below into French. First prepare a GlossWise brief, then show the translation followed by a compact table of every stored term, rule, or example you applied: <paste source passage>.`
- `/glosswise Review this French translation against workspace <name>. Report missing preferred terms, prohibited forms, and conflicting rules; do not rewrite or save anything unless I ask: <paste translation>.`

Use `glosswise ws ls`, `glosswise ws use <name>`, and
`glosswise ws get` when a quick terminal check is more convenient than chat.

## Built-in translation, file ranges, and PDF OCR

Direct translation uses a named HeavenBase `LLMSession` preset. Each result
reports the resolved preset, gateway, provider, model, and model id. Select the
preset and uncertainty behavior independently:

```console
glosswise config llm chat
glosswise config mode auto
glosswise translate "Run this query." -sl en -tl ja
glosswise translate "Run this query." -sl en -tl ja --preset chat
```

Modes are `yolo` (translate immediately), `elicit` (ask focused terminology
questions with options), `auto` (adapt to the available evidence), `explain`
(translate and explain every material choice), and `custom` with `--prompt`.
HeavenBase renders the system prompt through `hb.Prompt` and resolves the named
preset. Use `chat` for HeavenBase's current fast-chat choice, or pin a dedicated
preset without duplicating provider credentials inside GlossWise:

```console
hb cfg set heavenbase.llm.presets.glosswise-translate.model deepseek-v4-flash
glosswise config llm glosswise-translate
```

`scan`, `brief`, and `translate` accept inclusive one-based `--start-line` and
`--end-line` ranges for inline text, stdin, and `@file` input. The authorized
local MCP profile adds equivalent file tools.

For a PDF, authorize its directory, OCR only the pages you need through the
configured HeavenBase LLM preset, and browse the retained per-page text by its
short `gw-...` handle:

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

GlossWise renders and OCRs one page at a time and deletes each page image
immediately. Suspicious long repetition is flagged, never silently removed.
Configure the default `ocr-local` with `hb cfg set
heavenbase.llm.presets.ocr-local.<field-or-path> <value>`; settings include
`desc`, `gateway`, `provider`, `model`, and `default_args`; select another preset with `glosswise config ocr <preset>`.

## MCP server

### Local stdio

Most desktop and coding-agent clients should use:

```console
glosswise mcp --json
```

The generated child process starts the full server with read, CRUD, Skill, and
workspace-management tools. The `glosswise` executable must be on the MCP
client's `PATH`.

### Local HTTP

To run a long-lived streamable HTTP server:

```console
glosswise mcp --transport http
```

It binds to `127.0.0.1:61055` by default and serves MCP at
`http://127.0.0.1:61055/mcp`. Print the matching client profile with:

```console
glosswise mcp --json --transport http
```

Choose another local endpoint when needed:

```console
glosswise mcp --transport http --host 127.0.0.1 --port 61056
```

GlossWise does not add network authentication. Keep the server on a loopback
host unless another trusted layer supplies authentication and transport
security.

### MCP tools

Data and context tools accept an optional `workspace_id`. When it is omitted,
GlossWise uses the active workspace and then the managed default.

| Tool | Purpose | `read` | `full` | `local` |
| --- | --- | :---: | :---: | :---: |
| `glosswise_workspace_info` | Show workspace capabilities and language hints. | ✓ | ✓ | ✓ |
| `glosswise_prepare_translation` | Build a translation brief for source text. | ✓ | ✓ | ✓ |
| `glosswise_search_terms` | Search terms. | ✓ | ✓ | ✓ |
| `glosswise_search_rules` | Search rules. | ✓ | ✓ | ✓ |
| `glosswise_search_examples` | Search examples. | ✓ | ✓ | ✓ |
| `glosswise_scan_text` | Scan text for term and rule matches. | ✓ | ✓ | ✓ |
| `glosswise_list_records` | List terms, rules, or examples. | ✓ | ✓ | ✓ |
| `glosswise_get_record` | Get one record by object id. | ✓ | ✓ | ✓ |
| `glosswise_put_term` | Create or update a term and its forms. | — | ✓ | ✓ |
| `glosswise_put_rule` | Create or update a rule. | — | ✓ | ✓ |
| `glosswise_put_example` | Create or update an example. | — | ✓ | ✓ |
| `glosswise_archive` | Archive one record. | — | ✓ | ✓ |
| `glosswise_list_workspaces` | List workspaces. | ✓ | ✓ | ✓ |
| `glosswise_get_workspace` | Get one redacted workspace record. | ✓ | ✓ | ✓ |
| `glosswise_create_workspace` | Create a managed workspace. | — | ✓ | ✓ |
| `glosswise_set_workspace_languages` | Set workspace language hints. | — | ✓ | ✓ |
| `glosswise_activate_workspace` | Select the active workspace. | — | ✓ | ✓ |
| `glosswise_deactivate_workspace` | Clear the active selection. | — | ✓ | ✓ |
| `glosswise_remove_workspace` | Unregister a workspace. | — | ✓ | ✓ |
| `glosswise_open_workspace` | Open a workspace and show its capabilities. | ✓ | ✓ | ✓ |
| `glosswise_health_workspace` | Inspect registry and runtime health. | ✓ | ✓ | ✓ |
| `glosswise_read_skill` | Read the packaged agent instructions. | ✓ | ✓ | ✓ |
| `glosswise_scan_file` | Scan an authorized server-local text file. | — | — | ✓ |
| `glosswise_prepare_file` | Build a brief from an authorized text-file range. | — | — | ✓ |
| `glosswise_ocr_pdf` | OCR authorized PDF pages into a short handle. | — | — | ✓ |
| `glosswise_list_documents` | List temporary OCR document handles. | — | — | ✓ |
| `glosswise_get_document` | Inspect one OCR document manifest. | — | — | ✓ |
| `glosswise_read_document` | Read a bounded line range from one OCR page. | — | — | ✓ |
| `glosswise_remove_document` | Remove one temporary OCR document. | — | — | ✓ |

### MCP profiles

Profiles control tool exposure, not workspace contents or the installed Skill
file:

| Profile | Exact surface | Intended use |
| --- | --- | --- |
| `full` | The 22 tools checked in the `full` column. | Default. It supports lookup, translation briefs, CRUD, Skill inspection, and workspace management. Bare `glosswise mcp` and `glosswise mcp --json` select this profile. |
| `read` | The 13 tools checked in the `read` column. | Read-only terminology/context use and workspace inspection. It cannot curate records, change selection, or manage workspaces. |
| `local` | All 22 `full` tools plus seven authorized local-document tools. | An advanced full-access server for bounded text ranges and PDF OCR. Selecting this profile alone does not grant file access; authorize roots first. |

`glosswise setup` installs one profile-independent Skill. The Skill does not
select a profile: the connected MCP server decides which tools the agent can
call. The normal setup uses `full`, which is the only non-local profile that
supports every management and translation workflow taught by the Skill.

To change an existing installation, keep the installed Skill and change only
the MCP server command in the agent's configuration, then restart or reconnect
the agent:

```console
glosswise mcp                 # full (default)
glosswise mcp --profile read  # read-only
glosswise mcp --profile local # full plus authorized text/PDF tools
```

Use `glosswise mcp --json --profile <profile>` to generate replacement client
JSON. Re-running `glosswise setup` is unnecessary when switching profiles.
Changing back to bare `glosswise mcp` restores the default `full` surface.

Every tool returns a versioned JSON envelope. Agents should inspect `error`,
`warnings`, `conflicts`, and `truncated` before using `items`.

## CLI reference

| Task | Command | Also accepted |
| --- | --- | --- |
| List workspaces | `glosswise ws ls` | `ws list` |
| Inspect a workspace | `glosswise ws get [<name>]` | — |
| Create a workspace | `glosswise ws create [<name>]` | — |
| Select a workspace | `glosswise ws use <name>` | `ws activate`, `ws act` |
| Clear selection | `glosswise ws deact` | `ws deactivate` |
| Unregister a workspace | `glosswise ws rm <name>` | `ws unset`, `ws remove` |
| Show global configuration | `glosswise config get` | — |
| Set global language defaults | `glosswise config lang -l en -l <language>` | `config languages` |
| Set translation behavior | `glosswise config mode <mode>` | — |
| Set the translation LLM preset | `glosswise config llm <preset>` | — |
| Set language hints | `glosswise ws lang -l en -l <language>` | `ws languages` |
| Authorize local roots | `glosswise ws files -r <directory>` | — |
| Create or update data | `glosswise term set @term.json` | `term put` |
| Get one record | `glosswise term get <object-id>` | — |
| List data | `glosswise term ls` | `term list` |
| Search data | `glosswise term search "query"` | — |
| Archive data | `glosswise term archive <object-id>` | — |
| Scan a passage | `glosswise scan "text"` | — |
| Prepare context | `glosswise brief "text"` | — |
| Translate through LLMSession | `glosswise translate "text"` | — |
| OCR PDF pages | `glosswise pdf ocr <path>` | — |
| Browse OCR text | `glosswise doc read <handle> <page>` | — |

Replace `term` with `rule` or `example` for the same
set/get/list/search/archive workflow. Run `glosswise --help` or
`glosswise <group> --help` for the complete command surface.

## Python SDK

```python
import glosswise


with glosswise.GlossWiseApp.open() as app:
    app.configure_default_languages(["en", "zh", "ru"])
    terms = app.list_terms(status="active")
    brief = app.prepare_translation(
        "Use the public API.",
        source_lang="en",
        target_lang="zh",
    )
    translation = app.translate(
        "Use the public API.",
        source_lang="en",
        target_langs=["zh"],
        preset="chat",
    )
```

`GlossWiseApp.open()` uses the active workspace or creates the managed default
after global languages have been configured.
Use `GlossWiseApp.create("<name>")` for an explicitly named managed workspace
and `GlossWiseApp.load()` when absence should be an error. Applications that
already own a HeavenBase workspace may use `workspace.glosswise` directly.

## How it works

1. An agent connects through MCP, the CLI, or the Python SDK.
2. GlossWise resolves the requested workspace, or uses the active/default one.
3. It retrieves relevant terms, rules, and examples.
4. `brief` ranks and packages that evidence with warnings and conflicts.
5. The host agent translates, or `translate` invokes HeavenBase `LLMSession`
   with an `hb.Prompt`-managed contract and a visible preset.
6. The caller can scan the proposed translation, or OCR authorized PDF pages
   into bounded temporary per-page text.

GlossWise keeps storage and terminology policy behind task-focused operations;
agents do not need generic database access.

## For developers

GlossWise is a demo project showing how a clean, standalone application can use
HeavenBase. It demonstrates the practical advantages of:

- a modular extension mounted at `workspace.glosswise`;
- managed workspaces and application-owned defaults;
- Context-level user defaults and visible HeavenBase LLM presets;
- typed entities, queries, and computed retrieval;
- page-wise HeavenBase LLM OCR with bounded document handles;
- one command registry exposed through multiple CLI backends;
- MCP tools generated from a HeavenBase toolkit; and
- a packaged Skill that teaches agents the application workflow.

Direct CLI and Python translation use the configured HeavenBase preset through
`LLMSession`; MCP hosts use their own configured model.

Development checks:

```console
git clone https://github.com/Magolor/GlossWise.git
cd GlossWise
bash scripts/sync-env.bash
bash scripts/flake.bash --ci
bash scripts/test.bash
bash scripts/test.bash -m full
uv build
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for the contribution workflow and
[SECURITY.md](SECURITY.md) for private vulnerability reporting.

Current boundaries: HeavenBase extensions are explicitly installed, enabled
extensions are not disabled, schema migration is not automated, and GlossWise
does not choose or hide a translation model.

## Citation

If GlossWise supports your research or project, cite the software using
[CITATION.cff](CITATION.cff) or:

```bibtex
@software{glosswise_2026,
  author  = {Magolor},
  title   = {GlossWise: Terminology-safe translation for AI agents},
  year    = {2026},
  version = {0.1.0.5},
  url     = {https://github.com/Magolor/GlossWise}
}
```

GlossWise is built on [HeavenBase](https://ahvn.top).

## License

GlossWise is available under the [MIT License](LICENSE).
