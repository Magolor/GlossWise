"""Backend-neutral GlossWise command-line interface."""

from __future__ import annotations

__all__ = ["build_registry", "create_cli", "main"]

from collections.abc import Callable, Mapping, Sequence
import json
from pathlib import Path
import sys
from typing import Any

from heavenbase.cli import (
    ArgumentSpec,
    CLIOutput,
    CLIRegistry,
    CommandGroupSpec,
    CommandSpec,
    OptionSpec,
    PackageCLIContext,
)
from heavenbase.cli.backends import (
    build_argparse,
    build_click,
    build_typer,
    run_argparse,
    run_click,
    run_typer,
)

from .api import (
    DEFAULT_WORKSPACE_ID,
    GlossWiseApp,
    GlossWiseWorkspaces,
)
from .api.workspaces import DEFAULT_MCP_HOST, DEFAULT_MCP_PORT
from .contracts import MAX_FILE_BYTES, MAX_TEXT_CHARS
from .documents import DEFAULT_OCR_DPI, MAX_PDF_BYTES
from .documents.text import read_text, select_text
from .errors import GlossWiseError
from .lifecycle import install_agent_skills
from .mcp import generic_toolkit

_BACKENDS: dict[str, tuple[Callable[..., Any], Callable[..., Any]]] = {
    "typer": (build_typer, run_typer),
    "click": (build_click, run_click),
    "argparse": (build_argparse, run_argparse),
}


def _workspace_options() -> list[OptionSpec]:
    return [
        OptionSpec.from_flags(
            "workspace",
            "--workspace",
            "-w",
            default="",
            help=("GlossWise workspace id; omit for the active workspace or managed default."),
        ),
        OptionSpec.from_flags(
            "bootstrap",
            "--bootstrap",
            default="",
            help="Optional HeavenBase bootstrap YAML.",
        ),
    ]


def _list_options() -> list[OptionSpec]:
    return [
        OptionSpec.from_flags(
            "status",
            "--status",
            default="",
            help="Optional draft, active, or deprecated filter.",
        ),
        OptionSpec.from_flags(
            "limit",
            "--limit",
            type=int,
            default=50,
            help="Maximum records from 1 through 200.",
        ),
        *_workspace_options(),
    ]


def _languages_option(help: str) -> OptionSpec:
    return OptionSpec.from_flags(
        "lang",
        "--lang",
        "-l",
        default=None,
        multiple=True,
        help=help,
    )


def _roots_option(help: str) -> OptionSpec:
    return OptionSpec.from_flags(
        "root",
        "--root",
        "-r",
        default=None,
        multiple=True,
        help=help,
    )


def _encodings_option(help: str) -> OptionSpec:
    return OptionSpec.from_flags(
        "encoding",
        "--encoding",
        "-e",
        default=None,
        multiple=True,
        help=help,
    )


def _source_language_option(
    *,
    default: str = "auto",
    help: str = "Source BCP 47 language or auto.",
) -> OptionSpec:
    return OptionSpec.from_flags(
        "src_lang",
        "--src-lang",
        "-sl",
        default=default,
        help=help,
    )


def _target_language_option(
    *,
    default: object = "",
    multiple: bool = False,
    help: str = "Optional target language.",
) -> OptionSpec:
    return OptionSpec.from_flags(
        "tgt_lang",
        "--tgt-lang",
        "-tl",
        default=default,
        multiple=multiple,
        help=help,
    )


def _load_app(
    workspace: str,
    bootstrap: str,
) -> GlossWiseApp:
    return GlossWiseApp.open(
        workspace or None,
        bootstrap=bootstrap or None,
    )


def _load_json(value: str, name: str) -> object:
    text = _load_text(value)
    try:
        return json.loads(text)
    except json.JSONDecodeError as error:
        raise GlossWiseError(
            "invalid_json",
            f"{name} must contain valid JSON.",
        ) from error


def _load_object(value: str, name: str) -> dict[str, object]:
    decoded = _load_json(value, name)
    if not isinstance(decoded, dict):
        raise GlossWiseError(
            "invalid_json",
            f"{name} must decode to a JSON object.",
        )
    return decoded


def _option_values(values: Sequence[str] | None) -> list[str]:
    if values is None:
        return []
    if isinstance(values, str):
        return [values]
    return [str(value) for value in values]


def _load_text(
    value: str,
    *,
    start_line: int | None = None,
    end_line: int | None = None,
) -> str:
    selected = str(value)
    if selected == "-":
        return select_text(
            sys.stdin.read(),
            start_line=start_line,
            end_line=end_line,
            max_bytes=MAX_FILE_BYTES,
            max_chars=MAX_TEXT_CHARS,
        ).text
    if selected.startswith("@"):
        return read_text(
            Path(selected[1:]).expanduser(),
            start_line=start_line,
            end_line=end_line,
            max_bytes=MAX_FILE_BYTES,
            max_chars=MAX_TEXT_CHARS,
        ).text
    return select_text(
        selected,
        start_line=start_line,
        end_line=end_line,
        max_bytes=MAX_FILE_BYTES,
        max_chars=MAX_TEXT_CHARS,
    ).text


def _optional(value: str) -> str | None:
    selected = str(value).strip()
    return selected or None


def _optional_index(value: int) -> int | None:
    selected = int(value)
    return None if selected == 0 else selected


def _not_found(kind: str, object_id: str) -> GlossWiseError:
    return GlossWiseError(
        "not_found",
        f"GlossWise {kind} {object_id!r} was not found.",
        object_ids=(object_id,),
    )


def _setup(
    context: PackageCLIContext,
    lang: Sequence[str] | None,
    skills_root: str,
    claude_skills_root: str,
    bootstrap: str,
) -> None:
    selected_languages = _option_values(lang)
    if not selected_languages:
        raise GlossWiseError(
            "languages_required",
            "Setup requires at least one default language.",
        )
    selected_roots = [Path(root) for root in (skills_root, claude_skills_root) if str(root).strip()]
    skills = install_agent_skills(
        selected_roots or None,
    )
    with GlossWiseWorkspaces.load(
        bootstrap=bootstrap or None,
    ) as directory:
        canonical = directory.configure_user_languages(selected_languages)
        workspace = directory.ensure_default(activate=True)
        workspace = directory.configure_default_languages(
            canonical,
            DEFAULT_WORKSPACE_ID,
        )
        user_config = directory.user_config()
    context.out.json(
        {
            "skills": [str(skill) for skill in skills],
            "workspace": workspace,
            "user_config": user_config,
        }
    )


def _workspace_list(
    context: PackageCLIContext,
    bootstrap: str,
) -> None:
    with GlossWiseWorkspaces.load(
        bootstrap=bootstrap or None,
    ) as directory:
        context.out.json({"items": directory.list()})


def _workspace_get(
    context: PackageCLIContext,
    workspace: str,
    bootstrap: str,
) -> None:
    with GlossWiseWorkspaces.load(
        bootstrap=bootstrap or None,
    ) as directory:
        context.out.json(
            directory.get(
                workspace or None,
                ensure_default=True,
            )
        )


def _workspace_lang(
    context: PackageCLIContext,
    lang: Sequence[str] | None,
    workspace: str,
    bootstrap: str,
) -> None:
    with GlossWiseWorkspaces.load(
        bootstrap=bootstrap or None,
    ) as directory:
        context.out.json(
            directory.configure_default_languages(
                _option_values(lang),
                workspace or None,
            )
        )


def _workspace_files(
    context: PackageCLIContext,
    root: Sequence[str] | None,
    encoding: Sequence[str] | None,
    max_bytes: int,
    max_pdf_bytes: int,
    workspace: str,
    bootstrap: str,
) -> None:
    selected_roots = _option_values(root)
    if not selected_roots:
        raise GlossWiseError(
            "file_access_denied",
            "At least one --root is required.",
        )
    with _load_app(workspace, bootstrap) as app:
        context.out.json(
            app.configure_file_access(
                selected_roots,
                max_bytes=max_bytes,
                max_pdf_bytes=max_pdf_bytes,
                encodings=_option_values(encoding) or ["utf-8"],
            )
        )


def _config_get(
    context: PackageCLIContext,
    bootstrap: str,
) -> None:
    with GlossWiseWorkspaces.load(
        bootstrap=bootstrap or None,
    ) as directory:
        context.out.json(directory.user_config())


def _config_languages(
    context: PackageCLIContext,
    lang: Sequence[str] | None,
    bootstrap: str,
) -> None:
    with GlossWiseWorkspaces.load(
        bootstrap=bootstrap or None,
    ) as directory:
        configured = directory.configure_user_languages(_option_values(lang))
        context.out.json(
            {
                "default_languages": configured,
            }
        )


def _config_mode(
    context: PackageCLIContext,
    mode: str,
    prompt: str,
    bootstrap: str,
) -> None:
    with GlossWiseWorkspaces.load(
        bootstrap=bootstrap or None,
    ) as directory:
        context.out.json(
            directory.configure_translation(
                mode,
                custom_prompt=_optional(prompt),
            )
        )


def _config_llm(
    context: PackageCLIContext,
    preset: str,
    bootstrap: str,
) -> None:
    with GlossWiseWorkspaces.load(
        bootstrap=bootstrap or None,
    ) as directory:
        context.out.json(
            {
                "preset": directory.configure_translation_preset(preset),
            }
        )


def _config_ocr(
    context: PackageCLIContext,
    preset: str,
    bootstrap: str,
) -> None:
    with GlossWiseWorkspaces.load(
        bootstrap=bootstrap or None,
    ) as directory:
        context.out.json(
            {
                "preset": directory.configure_ocr(preset),
            }
        )


def _workspace_create(
    context: PackageCLIContext,
    workspace: str,
    database: str,
    no_activate: bool,
    bootstrap: str,
) -> None:
    with GlossWiseWorkspaces.load(
        bootstrap=bootstrap or None,
    ) as directory:
        context.out.json(
            directory.create(
                workspace or DEFAULT_WORKSPACE_ID,
                database=database or None,
                activate=not no_activate,
            )
        )


def _workspace_activate(
    context: PackageCLIContext,
    workspace: str,
    bootstrap: str,
) -> None:
    with GlossWiseWorkspaces.load(
        bootstrap=bootstrap or None,
    ) as directory:
        context.out.json(directory.activate(workspace))


def _workspace_deactivate(
    context: PackageCLIContext,
    bootstrap: str,
) -> None:
    with GlossWiseWorkspaces.load(
        bootstrap=bootstrap or None,
    ) as directory:
        context.out.json(directory.deactivate())


def _workspace_remove(
    context: PackageCLIContext,
    workspace: str,
    bootstrap: str,
) -> None:
    with GlossWiseWorkspaces.load(
        bootstrap=bootstrap or None,
    ) as directory:
        context.out.json(directory.remove(workspace))


def _workspace_open(
    context: PackageCLIContext,
    workspace: str,
    bootstrap: str,
) -> None:
    with GlossWiseWorkspaces.load(
        bootstrap=bootstrap or None,
    ) as directory:
        context.out.json(
            directory.info(
                workspace or None,
                ensure_default=True,
            )
        )


def _workspace_health(
    context: PackageCLIContext,
    workspace: str,
    bootstrap: str,
) -> None:
    with GlossWiseWorkspaces.load(
        bootstrap=bootstrap or None,
    ) as directory:
        context.out.json(
            directory.health(
                workspace or None,
                ensure_default=True,
            )
        )


def _workspace_manifest(
    context: PackageCLIContext,
    workspace: str,
    bootstrap: str,
) -> None:
    with GlossWiseWorkspaces.load(
        bootstrap=bootstrap or None,
    ) as directory:
        context.out.json(directory.manifest(workspace or None))


def _workspace_import(
    context: PackageCLIContext,
    path: str,
    no_activate: bool,
    bootstrap: str,
) -> None:
    with GlossWiseWorkspaces.load(
        bootstrap=bootstrap or None,
    ) as directory:
        context.out.json(
            directory.import_manifest(
                path,
                activate=not no_activate,
            )
        )


def _skill_install(
    context: PackageCLIContext,
    root: str,
    claude_root: str,
) -> None:
    selected_roots = [Path(path) for path in (root, claude_root) if str(path).strip()]
    paths = install_agent_skills(
        selected_roots or None,
    )
    context.out.json({"installed": [str(path) for path in paths]})


def _term_set(
    context: PackageCLIContext,
    payload: str,
    workspace: str,
    bootstrap: str,
) -> None:
    data = _load_object(payload, "term payload")
    term = data.get("term")
    forms = data.get("forms", [])
    if not isinstance(term, Mapping):
        raise GlossWiseError(
            "invalid_json",
            "Term payload needs a `term` object.",
        )
    if not isinstance(forms, list) or any(not isinstance(form, Mapping) for form in forms):
        raise GlossWiseError(
            "invalid_json",
            "Term payload `forms` must be an array of objects.",
        )
    with _load_app(workspace, bootstrap) as app:
        context.out.json(app.put_term(term, forms))


def _term_get(
    context: PackageCLIContext,
    object_id: str,
    workspace: str,
    bootstrap: str,
) -> None:
    with _load_app(workspace, bootstrap) as app:
        row = app.get_term(object_id)
        if row is None:
            raise _not_found("term", object_id)
        context.out.json(row)


def _term_list(
    context: PackageCLIContext,
    status: str,
    limit: int,
    workspace: str,
    bootstrap: str,
) -> None:
    with _load_app(workspace, bootstrap) as app:
        context.out.json(
            {
                "items": app.list_terms(
                    status=_optional(status),
                    limit=limit,
                )
            }
        )


def _term_search(
    context: PackageCLIContext,
    query: str,
    src_lang: str,
    tgt_lang: str,
    domain: str,
    limit: int,
    workspace: str,
    bootstrap: str,
) -> None:
    with _load_app(workspace, bootstrap) as app:
        context.out.json(
            app.search_terms(
                _load_text(query),
                query_lang=src_lang,
                target_lang=_optional(tgt_lang),
                domain=_optional(domain),
                limit=limit,
            )
        )


def _rule_set(
    context: PackageCLIContext,
    payload: str,
    workspace: str,
    bootstrap: str,
) -> None:
    with _load_app(workspace, bootstrap) as app:
        context.out.json(app.put_rule(_load_object(payload, "rule payload")))


def _rule_get(
    context: PackageCLIContext,
    object_id: str,
    workspace: str,
    bootstrap: str,
) -> None:
    with _load_app(workspace, bootstrap) as app:
        row = app.get_rule(object_id)
        if row is None:
            raise _not_found("rule", object_id)
        context.out.json(row)


def _rule_list(
    context: PackageCLIContext,
    status: str,
    limit: int,
    workspace: str,
    bootstrap: str,
) -> None:
    with _load_app(workspace, bootstrap) as app:
        context.out.json(
            {
                "items": app.list_rules(
                    status=_optional(status),
                    limit=limit,
                )
            }
        )


def _rule_search(
    context: PackageCLIContext,
    query: str,
    src_lang: str,
    tgt_lang: str,
    topic: str,
    style: str,
    limit: int,
    workspace: str,
    bootstrap: str,
) -> None:
    with _load_app(workspace, bootstrap) as app:
        context.out.json(
            app.search_rules(
                _load_text(query),
                source_lang=src_lang,
                target_lang=_optional(tgt_lang),
                topic=_optional(topic),
                style=_optional(style),
                limit=limit,
            )
        )


def _example_set(
    context: PackageCLIContext,
    payload: str,
    workspace: str,
    bootstrap: str,
) -> None:
    with _load_app(workspace, bootstrap) as app:
        context.out.json(app.put_example(_load_object(payload, "example payload")))


def _example_get(
    context: PackageCLIContext,
    object_id: str,
    workspace: str,
    bootstrap: str,
) -> None:
    with _load_app(workspace, bootstrap) as app:
        row = app.get_example(object_id)
        if row is None:
            raise _not_found("example", object_id)
        context.out.json(row)


def _example_list(
    context: PackageCLIContext,
    status: str,
    limit: int,
    workspace: str,
    bootstrap: str,
) -> None:
    with _load_app(workspace, bootstrap) as app:
        context.out.json(
            {
                "items": app.list_examples(
                    status=_optional(status),
                    limit=limit,
                )
            }
        )


def _example_search(
    context: PackageCLIContext,
    query: str,
    src_lang: str,
    tgt_lang: str,
    topic: str,
    style: str,
    tag: str,
    limit: int,
    workspace: str,
    bootstrap: str,
) -> None:
    with _load_app(workspace, bootstrap) as app:
        context.out.json(
            app.search_examples(
                _load_text(query),
                source_lang=_optional(src_lang),
                target_lang=_optional(tgt_lang),
                topic=_optional(topic),
                style=_optional(style),
                tag=_optional(tag),
                limit=limit,
            )
        )


def _archive(
    context: PackageCLIContext,
    object_id: str,
    workspace: str,
    bootstrap: str,
) -> None:
    with _load_app(workspace, bootstrap) as app:
        context.out.json(app.archive(object_id))


def _scan(
    context: PackageCLIContext,
    text: str,
    src_lang: str,
    tgt_lang: str,
    domain: str,
    topic: str,
    style: str,
    start_line: int,
    end_line: int,
    limit: int,
    cursor: str,
    workspace: str,
    bootstrap: str,
) -> None:
    with _load_app(workspace, bootstrap) as app:
        context.out.json(
            app.scan_text(
                _load_text(
                    text,
                    start_line=_optional_index(start_line),
                    end_line=_optional_index(end_line),
                ),
                text_lang=src_lang,
                target_lang=_optional(tgt_lang),
                domain=_optional(domain),
                topic=_optional(topic),
                style=_optional(style),
                limit=limit,
                cursor=_optional(cursor),
            )
        )


def _brief(
    context: PackageCLIContext,
    text: str,
    tgt_lang: str,
    src_lang: str,
    domain: str,
    topic: str,
    style: str,
    start_line: int,
    end_line: int,
    workspace: str,
    bootstrap: str,
) -> None:
    with _load_app(workspace, bootstrap) as app:
        context.out.json(
            app.prepare_translation(
                _load_text(
                    text,
                    start_line=_optional_index(start_line),
                    end_line=_optional_index(end_line),
                ),
                target_lang=tgt_lang,
                source_lang=src_lang,
                domain=_optional(domain),
                topic=_optional(topic),
                style=_optional(style),
            )
        )


def _pdf_ocr(
    context: PackageCLIContext,
    path: str,
    preset: str,
    start_page: int,
    end_page: int,
    dpi: int,
    workspace: str,
    bootstrap: str,
) -> None:
    with _load_app(workspace, bootstrap) as app:
        context.out.json(
            app.ocr_pdf(
                path,
                preset=_optional(preset),
                start_page=_optional_index(start_page),
                end_page=_optional_index(end_page),
                dpi=dpi,
            )
        )


def _document_list(
    context: PackageCLIContext,
    workspace: str,
    bootstrap: str,
) -> None:
    with _load_app(workspace, bootstrap) as app:
        context.out.json({"items": app.list_documents()})


def _document_get(
    context: PackageCLIContext,
    handle: str,
    workspace: str,
    bootstrap: str,
) -> None:
    with _load_app(workspace, bootstrap) as app:
        context.out.json(app.get_document(handle))


def _document_read(
    context: PackageCLIContext,
    handle: str,
    page: int,
    start_line: int,
    end_line: int,
    workspace: str,
    bootstrap: str,
) -> None:
    with _load_app(workspace, bootstrap) as app:
        context.out.json(
            app.read_document(
                handle,
                page,
                start_line=_optional_index(start_line),
                end_line=_optional_index(end_line),
            )
        )


def _document_remove(
    context: PackageCLIContext,
    handle: str,
    workspace: str,
    bootstrap: str,
) -> None:
    with _load_app(workspace, bootstrap) as app:
        context.out.json(app.remove_document(handle))


def _translate(
    context: PackageCLIContext,
    text: str,
    tgt_lang: Sequence[str] | None,
    src_lang: str,
    preset: str,
    domain: str,
    topic: str,
    style: str,
    start_line: int,
    end_line: int,
    workspace: str,
    bootstrap: str,
) -> None:
    targets = _option_values(tgt_lang) or None
    with _load_app(workspace, bootstrap) as app:
        context.out.json(
            app.translate(
                _load_text(
                    text,
                    start_line=_optional_index(start_line),
                    end_line=_optional_index(end_line),
                ),
                target_langs=targets,
                source_lang=src_lang,
                preset=_optional(preset),
                domain=_optional(domain),
                topic=_optional(topic),
                style=_optional(style),
            )
        )


def _mcp(
    context: PackageCLIContext,
    bootstrap: str,
    profile: str,
    json: bool,
    name: str,
    transport: str,
    host: str,
    port: int,
) -> None:
    selected_profile = _optional(profile)
    selected_transport = str(transport).strip().lower()
    with GlossWiseWorkspaces.load(
        bootstrap=bootstrap or None,
    ) as directory:
        config = directory.mcp_config(
            profile=selected_profile,
            server_name=name,
            transport=selected_transport,
            host=host,
            port=port,
        )
        if json:
            context.out.json(config)
            return
        directory.get(ensure_default=True)
        toolkit = generic_toolkit(
            directory,
            profile=selected_profile or "full",
        )
        serve_options: dict[str, object] = {
            "transport": selected_transport,
            "wait": False,
        }
        if selected_transport != "stdio":
            serve_options.update(
                {
                    "host": host,
                    "port": port,
                }
            )
        server = toolkit.serve(**serve_options)
        server.wait()


def _record_group(
    name: str,
    *,
    set_record: Callable[..., None],
    get: Callable[..., None],
    list_records: Callable[..., None],
    search: Callable[..., None],
    search_options: list[OptionSpec],
) -> CommandGroupSpec:
    return CommandGroupSpec(
        name,
        help=(f"Create, inspect, search, list, and archive GlossWise {name}s."),
        commands=[
            CommandSpec(
                "set",
                set_record,
                help=(f"Create or update one {name} by object id from inline JSON, `@file.json`, or stdin `-`."),
                aliases=["put"],
                args=[
                    ArgumentSpec(
                        "payload",
                        help=f"{name.title()} JSON payload.",
                    )
                ],
                options=_workspace_options(),
            ),
            CommandSpec(
                "get",
                get,
                help=f"Get one {name} by object id.",
                args=[
                    ArgumentSpec(
                        "object_id",
                        help=f"{name.title()} object id.",
                    )
                ],
                options=_workspace_options(),
            ),
            CommandSpec(
                "list",
                list_records,
                help=f"List {name}s in deterministic identity order.",
                options=_list_options(),
                aliases=["ls"],
            ),
            CommandSpec(
                "search",
                search,
                help=(f"Search curated {name}s for focused candidates; this does not prepare a full translation brief."),
                args=[
                    ArgumentSpec(
                        "query",
                        help="Natural-language query, `@file`, or stdin `-`.",
                    )
                ],
                options=[
                    *search_options,
                    OptionSpec.from_flags(
                        "limit",
                        "--limit",
                        type=int,
                        default=10,
                        help="Maximum candidates from 1 through 200.",
                    ),
                    *_workspace_options(),
                ],
            ),
            CommandSpec(
                "archive",
                _archive,
                help=(f"Retain one {name} but exclude it from active use by setting deprecated status."),
                args=[
                    ArgumentSpec(
                        "object_id",
                        help=f"{name.title()} object id.",
                    )
                ],
                options=_workspace_options(),
            ),
        ],
    )


def build_registry() -> CLIRegistry:
    """Build the complete backend-neutral GlossWise command registry.

    Args:
        None.

    Returns:
        CLIRegistry: Configuration, workspace, Skill, term, rule, example,
            brief, and MCP commands compiled identically by every supported
            backend.
    """
    registry = CLIRegistry()
    bootstrap_option = OptionSpec.from_flags(
        "bootstrap",
        "--bootstrap",
        default="",
        help="Optional HeavenBase bootstrap YAML.",
    )
    no_activate_option = OptionSpec.from_flags(
        "no_activate",
        "--no-activate",
        type=bool,
        default=False,
        is_flag=True,
        help="Do not select this workspace after the operation.",
    )
    registry.add_group(
        CommandGroupSpec(
            "config",
            help="Manage user defaults shared by every GlossWise workspace.",
            commands=[
                CommandSpec(
                    "get",
                    _config_get,
                    help="Show the global non-secret GlossWise configuration.",
                    options=[bootstrap_option],
                ),
                CommandSpec(
                    "lang",
                    _config_languages,
                    help="Set non-empty languages inherited by new workspaces.",
                    aliases=["languages"],
                    options=[
                        _languages_option(
                            "Language to inherit; repeat for each language.",
                        ),
                        bootstrap_option,
                    ],
                ),
                CommandSpec(
                    "mode",
                    _config_mode,
                    help="Set auto, yolo, elicit, explain, or custom behavior.",
                    args=[
                        ArgumentSpec(
                            "mode",
                            help="Translation behavior mode.",
                        )
                    ],
                    options=[
                        OptionSpec.from_flags(
                            "prompt",
                            "--prompt",
                            default="",
                            help="Required behavior prompt for custom mode.",
                        ),
                        bootstrap_option,
                    ],
                ),
                CommandSpec(
                    "llm",
                    _config_llm,
                    help="Set the HeavenBase LLM preset used for translation.",
                    args=[
                        ArgumentSpec(
                            "preset",
                            help="HeavenBase LLM preset, for example chat.",
                        )
                    ],
                    options=[bootstrap_option],
                ),
                CommandSpec(
                    "ocr",
                    _config_ocr,
                    help="Set the HeavenBase LLM preset used for PDF OCR.",
                    args=[
                        ArgumentSpec(
                            "preset",
                            help="HeavenBase LLM preset, for example ocr-local.",
                        )
                    ],
                    options=[bootstrap_option],
                ),
            ],
        )
    )
    registry.add_group(
        CommandGroupSpec(
            "ws",
            help=("Browse and manage GlossWise workspaces without exposing managed storage paths."),
            commands=[
                CommandSpec(
                    "list",
                    _workspace_list,
                    help="List registered GlossWise workspaces.",
                    aliases=["ls"],
                    options=[bootstrap_option],
                ),
                CommandSpec(
                    "get",
                    _workspace_get,
                    help="Show one redacted workspace record.",
                    args=[
                        ArgumentSpec(
                            "workspace",
                            help="Workspace id; omit for active/default.",
                            required=False,
                        )
                    ],
                    options=[bootstrap_option],
                ),
                CommandSpec(
                    "lang",
                    _workspace_lang,
                    help=("Set advisory default languages; omit --lang to clear them."),
                    aliases=["languages"],
                    options=[
                        _languages_option(
                            "Advisory language; repeat for each language.",
                        ),
                        *_workspace_options(),
                    ],
                ),
                CommandSpec(
                    "files",
                    _workspace_files,
                    help="Authorize local roots for bounded text and PDF tools.",
                    options=[
                        _roots_option(
                            "Authorized directory root; repeat at least once.",
                        ),
                        _encodings_option(
                            "Strict text encoding; repeat for each encoding " "(default: utf-8).",
                        ),
                        OptionSpec.from_flags(
                            "max_bytes",
                            "--max-bytes",
                            type=int,
                            default=MAX_FILE_BYTES,
                            help="Maximum selected text bytes.",
                        ),
                        OptionSpec.from_flags(
                            "max_pdf_bytes",
                            "--max-pdf-bytes",
                            type=int,
                            default=MAX_PDF_BYTES,
                            help="Maximum PDF source bytes.",
                        ),
                        *_workspace_options(),
                    ],
                ),
                CommandSpec(
                    "create",
                    _workspace_create,
                    help=("Create or compatibly reopen a managed workspace and activate it."),
                    args=[
                        ArgumentSpec(
                            "workspace",
                            help="Workspace id (default: default).",
                            required=False,
                        )
                    ],
                    options=[
                        OptionSpec.from_flags(
                            "database",
                            "--database",
                            default="",
                            help=("Advanced SQLite path override; the default stays managed under ~/.glosswise."),
                        ),
                        no_activate_option,
                        bootstrap_option,
                    ],
                ),
                CommandSpec(
                    "activate",
                    _workspace_activate,
                    help="Select a registered GlossWise workspace.",
                    aliases=["act", "use"],
                    args=[
                        ArgumentSpec(
                            "workspace",
                            help="Workspace id.",
                        )
                    ],
                    options=[bootstrap_option],
                ),
                CommandSpec(
                    "deactivate",
                    _workspace_deactivate,
                    help=("Clear GlossWise workspace selection; this does not disable the extension."),
                    aliases=["deact"],
                    options=[bootstrap_option],
                ),
                CommandSpec(
                    "unset",
                    _workspace_remove,
                    help="Unregister a workspace while retaining its data.",
                    aliases=["remove", "rm", "del", "delete"],
                    args=[
                        ArgumentSpec(
                            "workspace",
                            help="Workspace id.",
                        )
                    ],
                    options=[bootstrap_option],
                ),
                CommandSpec(
                    "open",
                    _workspace_open,
                    help="Open a workspace and show redacted capabilities.",
                    args=[
                        ArgumentSpec(
                            "workspace",
                            help="Workspace id; omit for active/default.",
                            required=False,
                        )
                    ],
                    options=[bootstrap_option],
                ),
                CommandSpec(
                    "health",
                    _workspace_health,
                    help="Show registry and redacted runtime health.",
                    args=[
                        ArgumentSpec(
                            "workspace",
                            help="Workspace id; omit for active/default.",
                            required=False,
                        )
                    ],
                    options=[bootstrap_option],
                ),
                CommandSpec(
                    "manifest",
                    _workspace_manifest,
                    help=("Export an advanced replayable manifest, including explicit backend construction."),
                    args=[
                        ArgumentSpec(
                            "workspace",
                            help="Workspace id; omit for active/default.",
                            required=False,
                        )
                    ],
                    options=[bootstrap_option],
                ),
                CommandSpec(
                    "import",
                    _workspace_import,
                    help="Import a HeavenBase workspace manifest.",
                    args=[
                        ArgumentSpec(
                            "path",
                            help="Manifest JSON or YAML path.",
                        )
                    ],
                    options=[
                        no_activate_option,
                        bootstrap_option,
                    ],
                ),
            ],
        )
    )
    registry.add_group(
        CommandGroupSpec(
            "skill",
            help="Install the packaged GlossWise coding-agent Skill.",
            commands=[
                CommandSpec(
                    "add",
                    _skill_install,
                    help="Cleanly install the packaged Skill for local agent harnesses.",
                    aliases=["install"],
                    options=[
                        OptionSpec.from_flags(
                            "root",
                            "--root",
                            "-r",
                            default="",
                            help=("Custom common skills root; omit to install to ~/.agents/skills and ~/.claude/skills."),
                        ),
                        OptionSpec.from_flags(
                            "claude_root",
                            "--claude-root",
                            default="",
                            help="Custom Claude skills root.",
                        ),
                    ],
                )
            ],
        )
    )
    registry.add_group(
        CommandGroupSpec(
            "pdf",
            help="Render and OCR authorized PDF pages with HeavenBase.",
            commands=[
                CommandSpec(
                    "ocr",
                    _pdf_ocr,
                    help="OCR an inclusive PDF page range into a short handle.",
                    args=[
                        ArgumentSpec(
                            "path",
                            help="Authorized server-local PDF path.",
                        )
                    ],
                    options=[
                        OptionSpec.from_flags(
                            "preset",
                            "--preset",
                            default="",
                            help="HeavenBase OCR preset override.",
                        ),
                        OptionSpec.from_flags(
                            "start_page",
                            "--start-page",
                            type=int,
                            default=0,
                            help="One-based first page; omit for page 1.",
                        ),
                        OptionSpec.from_flags(
                            "end_page",
                            "--end-page",
                            type=int,
                            default=0,
                            help="Inclusive last page; omit for the final page.",
                        ),
                        OptionSpec.from_flags(
                            "dpi",
                            "--dpi",
                            type=int,
                            default=DEFAULT_OCR_DPI,
                            help="Render resolution from 72 through 600.",
                        ),
                        *_workspace_options(),
                    ],
                )
            ],
        )
    )
    registry.add_group(
        CommandGroupSpec(
            "doc",
            help="Browse and remove temporary OCR text by short handle.",
            commands=[
                CommandSpec(
                    "list",
                    _document_list,
                    help="List OCR document handles.",
                    aliases=["ls"],
                    options=_workspace_options(),
                ),
                CommandSpec(
                    "get",
                    _document_get,
                    help="Describe one OCR document.",
                    args=[
                        ArgumentSpec(
                            "handle",
                            help="Short gw-... document handle.",
                        )
                    ],
                    options=_workspace_options(),
                ),
                CommandSpec(
                    "read",
                    _document_read,
                    help="Read a bounded line range from one OCR page.",
                    args=[
                        ArgumentSpec(
                            "handle",
                            help="Short gw-... document handle.",
                        ),
                        ArgumentSpec(
                            "page",
                            type=int,
                            help="One-based source PDF page.",
                        ),
                    ],
                    options=[
                        OptionSpec.from_flags(
                            "start_line",
                            "--start-line",
                            type=int,
                            default=0,
                            help="One-based first OCR text line.",
                        ),
                        OptionSpec.from_flags(
                            "end_line",
                            "--end-line",
                            type=int,
                            default=0,
                            help="Inclusive last OCR text line.",
                        ),
                        *_workspace_options(),
                    ],
                ),
                CommandSpec(
                    "remove",
                    _document_remove,
                    help="Delete one temporary OCR document.",
                    aliases=["rm"],
                    args=[
                        ArgumentSpec(
                            "handle",
                            help="Short gw-... document handle.",
                        )
                    ],
                    options=_workspace_options(),
                ),
            ],
        )
    )
    registry.add_group(
        _record_group(
            "term",
            set_record=_term_set,
            get=_term_get,
            list_records=_term_list,
            search=_term_search,
            search_options=[
                _source_language_option(
                    default="auto",
                    help="Query/source BCP 47 language or auto.",
                ),
                _target_language_option(
                    help="Optional target-form language.",
                ),
                OptionSpec.from_flags(
                    "domain",
                    "--domain",
                    default="",
                    help="Optional exact domain.",
                ),
            ],
        )
    )
    registry.add_group(
        _record_group(
            "rule",
            set_record=_rule_set,
            get=_rule_get,
            list_records=_rule_list,
            search=_rule_search,
            search_options=[
                _source_language_option(),
                _target_language_option(),
                OptionSpec.from_flags(
                    "topic",
                    "--topic",
                    default="",
                    help="Optional exact topic.",
                ),
                OptionSpec.from_flags(
                    "style",
                    "--style",
                    default="",
                    help="Optional exact style.",
                ),
            ],
        )
    )
    registry.add_group(
        _record_group(
            "example",
            set_record=_example_set,
            get=_example_get,
            list_records=_example_list,
            search=_example_search,
            search_options=[
                _source_language_option(
                    default="",
                    help="Optional source language.",
                ),
                _target_language_option(),
                OptionSpec.from_flags(
                    "topic",
                    "--topic",
                    default="",
                    help="Optional exact topic.",
                ),
                OptionSpec.from_flags(
                    "style",
                    "--style",
                    default="",
                    help="Optional exact style.",
                ),
                OptionSpec.from_flags(
                    "tag",
                    "--tag",
                    default="",
                    help="Optional exact tag.",
                ),
            ],
        )
    )
    registry.add_root(
        CommandSpec(
            "setup",
            _setup,
            help=("Set global languages, install the agent Skill, and provision the active default workspace."),
            options=[
                _languages_option(
                    "Required default language; repeat for each language.",
                ),
                OptionSpec.from_flags(
                    "skills_root",
                    "--skills-root",
                    default="",
                    help=("Custom common skills root; omit to install to ~/.agents/skills and ~/.claude/skills."),
                ),
                OptionSpec.from_flags(
                    "claude_skills_root",
                    "--claude-skills-root",
                    default="",
                    help="Custom Claude skills root.",
                ),
                bootstrap_option,
            ],
        )
    )
    registry.add_root(
        CommandSpec(
            "scan",
            _scan,
            help=("Find term/rule occurrences in source text; this is lexical inspection, not translation."),
            args=[
                ArgumentSpec(
                    "text",
                    help="Source passage to scan, `@file`, or stdin `-`.",
                )
            ],
            options=[
                _source_language_option(
                    default="auto",
                    help="Text/source BCP 47 language or auto.",
                ),
                _target_language_option(help="Optional target-form language."),
                OptionSpec.from_flags(
                    "domain",
                    "--domain",
                    default="",
                    help="Optional exact term domain.",
                ),
                OptionSpec.from_flags(
                    "topic",
                    "--topic",
                    default="",
                    help="Optional exact rule topic.",
                ),
                OptionSpec.from_flags(
                    "style",
                    "--style",
                    default="",
                    help="Optional exact rule style.",
                ),
                OptionSpec.from_flags(
                    "start_line",
                    "--start-line",
                    type=int,
                    default=0,
                    help="One-based first line when scanning a file or text.",
                ),
                OptionSpec.from_flags(
                    "end_line",
                    "--end-line",
                    type=int,
                    default=0,
                    help="Inclusive last line when scanning a file or text.",
                ),
                OptionSpec.from_flags(
                    "limit",
                    "--limit",
                    type=int,
                    default=50,
                    help="Maximum findings from 1 through 200.",
                ),
                OptionSpec.from_flags(
                    "cursor",
                    "--cursor",
                    default="",
                    help="Opaque cursor from the same prior scan.",
                ),
                *_workspace_options(),
            ],
        )
    )
    registry.add_root(
        CommandSpec(
            "brief",
            _brief,
            help=("Prepare terms, rules, examples, and conflicts for translating a source passage; does not generate a translation."),
            args=[
                ArgumentSpec(
                    "text",
                    help=("Full source passage to analyze, not a search query; accepts `@file` or stdin `-`."),
                )
            ],
            options=[
                _target_language_option(
                    help="Concrete target BCP 47 language.",
                ),
                _source_language_option(),
                OptionSpec.from_flags(
                    "domain",
                    "--domain",
                    default="",
                    help="Optional term domain.",
                ),
                OptionSpec.from_flags(
                    "topic",
                    "--topic",
                    default="",
                    help="Optional rule/example topic.",
                ),
                OptionSpec.from_flags(
                    "style",
                    "--style",
                    default="",
                    help="Optional translation style.",
                ),
                OptionSpec.from_flags(
                    "start_line",
                    "--start-line",
                    type=int,
                    default=0,
                    help="One-based first line when briefing a file or text.",
                ),
                OptionSpec.from_flags(
                    "end_line",
                    "--end-line",
                    type=int,
                    default=0,
                    help="Inclusive last line when briefing a file or text.",
                ),
                *_workspace_options(),
            ],
        )
    )
    registry.add_root(
        CommandSpec(
            "translate",
            _translate,
            help="Translate with fresh GlossWise briefs and HeavenBase LLMSession.",
            args=[
                ArgumentSpec(
                    "text",
                    help="Source text, `@file`, or stdin `-`.",
                )
            ],
            options=[
                _target_language_option(
                    default=None,
                    multiple=True,
                    help=("Target language; repeat for multiple targets or omit " "to use workspace/global defaults."),
                ),
                _source_language_option(),
                OptionSpec.from_flags(
                    "preset",
                    "--preset",
                    default="",
                    help="HeavenBase LLM preset override.",
                ),
                OptionSpec.from_flags(
                    "domain",
                    "--domain",
                    default="",
                    help="Optional terminology domain.",
                ),
                OptionSpec.from_flags(
                    "topic",
                    "--topic",
                    default="",
                    help="Optional rule/example topic.",
                ),
                OptionSpec.from_flags(
                    "style",
                    "--style",
                    default="",
                    help="Optional translation style.",
                ),
                OptionSpec.from_flags(
                    "start_line",
                    "--start-line",
                    type=int,
                    default=0,
                    help="One-based first line when translating a file or text.",
                ),
                OptionSpec.from_flags(
                    "end_line",
                    "--end-line",
                    type=int,
                    default=0,
                    help="Inclusive last line when translating a file or text.",
                ),
                *_workspace_options(),
            ],
        )
    )
    registry.add_root(
        CommandSpec(
            "mcp",
            _mcp,
            help=("Serve the global GlossWise MCP, or print paste-ready client JSON."),
            options=[
                bootstrap_option,
                OptionSpec.from_flags(
                    "profile",
                    "--profile",
                    default="",
                    help=("Advanced restriction: full, read, or local; omit for the full generic server."),
                ),
                OptionSpec.from_flags(
                    "json",
                    "--json",
                    type=bool,
                    default=False,
                    is_flag=True,
                    help="Print generic mcpServers JSON and exit.",
                ),
                OptionSpec.from_flags(
                    "name",
                    "--name",
                    default="glosswise",
                    help="MCP server key used by --json.",
                ),
                OptionSpec.from_flags(
                    "transport",
                    "--transport",
                    "-t",
                    default="stdio",
                    help="MCP transport: stdio, http, streamable-http, or sse.",
                ),
                OptionSpec.from_flags(
                    "host",
                    "--host",
                    default=DEFAULT_MCP_HOST,
                    help="Network MCP host (default: 127.0.0.1).",
                ),
                OptionSpec.from_flags(
                    "port",
                    "--port",
                    "-p",
                    type=int,
                    default=DEFAULT_MCP_PORT,
                    help="Network MCP port (default: 61055).",
                ),
            ],
        )
    )
    return registry


def create_cli(
    mode: str = "typer",
    *,
    context: PackageCLIContext | None = None,
) -> Any:
    """Create the GlossWise CLI using one supported parser backend.

    Args:
        mode (str): Supported values:
            - `typer`: Default installed command surface.
            - `click`: Click-compatible parity surface.
            - `argparse`: Standard-library parity surface.
        context (PackageCLIContext | None): Optional test or host context.

    Returns:
        Any: Backend-specific CLI application.

    Raises:
        ValueError: If `mode` is unsupported.
    """
    selected = str(mode).strip().lower()
    if selected not in _BACKENDS:
        expected = ", ".join(sorted(_BACKENDS))
        raise ValueError(f"GlossWise CLI mode must be one of {expected}; got {mode!r}.")
    from . import __version__

    cli_context = context or PackageCLIContext(
        package="glosswise",
        version=__version__,
        out=CLIOutput(),
    )
    if cli_context.out is None:
        cli_context.out = CLIOutput()
    return _BACKENDS[selected][0](build_registry(), cli_context)


def main(argv: Sequence[str] | None = None) -> Any:
    """Run the installed Typer command surface.

    Args:
        argv (Sequence[str] | None): Arguments after the executable name.

    Returns:
        Any: Selected command result, if any.

    Raises:
        SystemExit: For normal CLI exits and rendered command failures.
    """
    app = create_cli("typer")
    return run_typer(
        app,
        None if argv is None else list(argv),
    )
