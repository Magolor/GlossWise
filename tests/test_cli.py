"""Backend-neutral CLI registry and Skill installation contracts."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
import inspect
import json

import click
import pytest
from click.testing import CliRunner as ClickRunner
from typer.testing import CliRunner as TyperRunner

from heavenbase.cli.backends import run_argparse
import glosswise.cli as cli_module
from glosswise.cli import build_registry, create_cli
from glosswise.lifecycle import install_agent_skills

from conftest import restore_owner_permissions


@pytest.mark.fast
def test_cli_registry_has_complete_external_workflow() -> None:
    """One registry should declare every documented application operation."""
    registry = build_registry()
    assert {command.name for command in registry.root_commands} == {
        "brief",
        "mcp",
        "scan",
        "setup",
        "translate",
    }
    groups = {group.name: {command.name for command in group.commands} for group in registry.groups}
    assert groups == {
        "ws": {
            "activate",
            "create",
            "deactivate",
            "get",
            "health",
            "import",
            "files",
            "lang",
            "list",
            "manifest",
            "open",
            "unset",
        },
        "config": {"get", "lang", "llm", "mode", "ocr"},
        "skill": {"add"},
        "pdf": {"ocr"},
        "doc": {"get", "list", "read", "remove"},
        "term": {"set", "get", "list", "search", "archive"},
        "rule": {"set", "get", "list", "search", "archive"},
        "example": {"set", "get", "list", "search", "archive"},
    }
    aliases = {(group.name, command.name): set(command.aliases) for group in registry.groups for command in group.commands}
    assert aliases[("ws", "lang")] == {"languages"}
    assert aliases[("skill", "add")] == {"install"}
    assert aliases[("term", "set")] == {"put"}


@pytest.mark.fast
def test_cli_registry_uses_one_language_flag_vocabulary() -> None:
    """Every language-bearing command should expose the same role flags."""
    registry = build_registry()
    commands = [(command.name, command) for command in registry.root_commands]
    commands.extend((f"{group.name} {command.name}", command) for group in registry.groups for command in group.commands)
    options = [
        (path, option)
        for path, command in commands
        for option in command.options
        if option.name
        in {
            "lang",
            "src_lang",
            "tgt_lang",
        }
    ]

    assert {path for path, option in options if option.name == "lang"} == {
        "config lang",
        "setup",
        "ws lang",
    }
    assert {path for path, option in options if option.name == "src_lang"} == {
        "brief",
        "example search",
        "rule search",
        "scan",
        "term search",
        "translate",
    }
    assert {path for path, option in options if option.name == "tgt_lang"} == {
        "brief",
        "example search",
        "rule search",
        "scan",
        "term search",
        "translate",
    }
    for path, option in options:
        if option.name == "lang":
            assert option.flags == ("--lang", "-l")
            assert option.multiple is True
        elif option.name == "src_lang":
            assert option.flags == ("--src-lang", "-sl")
            assert option.multiple is False
        else:
            assert option.flags == ("--tgt-lang", "-tl")
            assert option.multiple is (path == "translate")


@pytest.mark.fast
def test_cli_registry_uses_repeatable_file_access_flags() -> None:
    """File-access lists should use repeatable scalar flags, never JSON."""
    registry = build_registry()
    workspace_group = next(group for group in registry.groups if group.name == "ws")
    files = next(command for command in workspace_group.commands if command.name == "files")
    options = {option.name: option for option in files.options}

    assert files.args == []
    assert options["root"].flags == ("--root", "-r")
    assert options["root"].multiple is True
    assert options["encoding"].flags == ("--encoding", "-e")
    assert options["encoding"].multiple is True


@pytest.mark.fast
def test_click_option_names_match_registry_keys() -> None:
    """Click should deliver every parsed option under its declared key."""
    registry = build_registry()
    commands = list(registry.root_commands)
    commands.extend(command for group in registry.groups for command in group.commands)
    for command in commands:
        for option in command.options:
            compiled = click.Option(list(option.click_flags()))
            assert compiled.name == option.name


@pytest.mark.fast
def test_cli_callback_parameters_match_registry_keys() -> None:
    """Every command should receive exactly the keys its registry declares."""
    registry = build_registry()
    commands = list(registry.root_commands)
    commands.extend(command for group in registry.groups for command in group.commands)
    for command in commands:
        expected = [
            "context",
            *[argument.name for argument in command.args],
            *[option.name for option in command.options],
        ]
        assert list(inspect.signature(command.callback).parameters) == expected


@pytest.mark.fast
@pytest.mark.parametrize("mode", ["typer", "click", "argparse"])
def test_all_cli_backends_parse_repeatable_language_flags(
    mode: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Every parser backend should preserve repeated values and role aliases."""
    captured: dict[str, object] = {}

    def capture_setup(
        context: object,
        lang: Sequence[str] | None,
        skills_root: str,
        claude_skills_root: str,
        bootstrap: str,
    ) -> None:
        captured["languages"] = list(lang or ())

    def capture_search(
        context: object,
        query: str,
        src_lang: str,
        tgt_lang: str,
        domain: str,
        limit: int,
        workspace: str,
        bootstrap: str,
    ) -> None:
        captured["search"] = (src_lang, tgt_lang, workspace)

    def capture_translate(
        context: object,
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
        captured["translate"] = (
            list(tgt_lang or ()),
            src_lang,
        )

    monkeypatch.setattr(cli_module, "_setup", capture_setup)
    monkeypatch.setattr(cli_module, "_term_search", capture_search)
    monkeypatch.setattr(cli_module, "_translate", capture_translate)
    app = create_cli(mode)

    def invoke(argv: list[str]) -> None:
        if mode == "typer":
            result = TyperRunner().invoke(app, argv)
            assert result.exit_code == 0, result.output
        elif mode == "click":
            result = ClickRunner().invoke(app, argv)
            assert result.exit_code == 0, result.output
        else:
            run_argparse(app, argv)

    invoke(["setup", "-l", "en", "--lang", "zh", "-l", "ja"])
    invoke(
        [
            "term",
            "search",
            "query",
            "-sl",
            "en",
            "-tl",
            "zh",
            "-w",
            "demo",
        ]
    )
    invoke(
        [
            "translate",
            "query",
            "-sl",
            "en",
            "-tl",
            "ja",
            "--tgt-lang",
            "fr",
        ]
    )
    assert captured == {
        "languages": ["en", "zh", "ja"],
        "search": ("en", "zh", "demo"),
        "translate": (["ja", "fr"], "en"),
    }


@pytest.mark.fast
@pytest.mark.parametrize("mode", ["typer", "click", "argparse"])
def test_all_cli_backends_parse_repeatable_file_access_flags(
    mode: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Every parser backend should preserve repeated roots and encodings."""
    captured: dict[str, object] = {}

    def capture_files(
        context: object,
        root: Sequence[str] | None,
        encoding: Sequence[str] | None,
        max_bytes: int,
        max_pdf_bytes: int,
        workspace: str,
        bootstrap: str,
    ) -> None:
        captured["files"] = (
            list(root or ()),
            list(encoding or ()),
            workspace,
        )

    monkeypatch.setattr(cli_module, "_workspace_files", capture_files)
    app = create_cli(mode)
    argv = [
        "ws",
        "files",
        "-r",
        "/work/docs",
        "--root",
        "/work/manuals",
        "-e",
        "utf-8",
        "--encoding",
        "utf-16",
        "-w",
        "demo",
    ]
    if mode == "typer":
        result = TyperRunner().invoke(app, argv)
        assert result.exit_code == 0, result.output
    elif mode == "click":
        result = ClickRunner().invoke(app, argv)
        assert result.exit_code == 0, result.output
    else:
        run_argparse(app, argv)

    assert captured == {
        "files": (
            ["/work/docs", "/work/manuals"],
            ["utf-8", "utf-16"],
            "demo",
        ),
    }


@pytest.mark.fast
def test_all_cli_backends_install_the_exact_packaged_skill(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Typer, Click, and argparse should invoke the same Skill command."""
    root = tmp_path / "skills"
    typer_result = TyperRunner().invoke(
        create_cli("typer"),
        ["skill", "add", "--root", str(root)],
    )
    assert typer_result.exit_code == 0, typer_result.output

    click_result = ClickRunner().invoke(
        create_cli("click"),
        ["skill", "install", "--root", str(root)],
    )
    assert click_result.exit_code == 0, click_result.output

    run_argparse(
        create_cli("argparse"),
        ["skill", "install", "--root", str(root)],
    )
    capsys.readouterr()
    installed = root / "glosswise" / "SKILL.md"
    packaged = Path(__file__).resolve().parents[1] / "src" / "glosswise" / "skills" / "glosswise" / "SKILL.md"
    installed.write_text("---\nname: glosswise\n---\nstale\n", encoding="utf-8")
    refreshed = TyperRunner().invoke(
        create_cli("typer"),
        [
            "skill",
            "add",
            "--root",
            str(root),
        ],
    )
    assert refreshed.exit_code == 0, refreshed.output
    assert installed.read_bytes() == packaged.read_bytes()

    installed.write_text("---\nname: another-skill\n---\n", encoding="utf-8")
    refused = TyperRunner().invoke(
        create_cli("typer"),
        ["skill", "add", "--root", str(root)],
    )
    assert refused.exit_code != 0
    assert "unverified Skill" in refused.output


@pytest.mark.fast
def test_cli_rejects_unknown_backend() -> None:
    """Programmatic callers should receive supported parser choices."""
    with pytest.raises(ValueError, match="argparse, click, typer"):
        create_cli("unknown")


@pytest.mark.fast
def test_multi_harness_skill_install_preflights_every_target(
    tmp_path: Path,
) -> None:
    """A conflicting second harness should not partially refresh the first."""
    common = tmp_path / "agents"
    claude = tmp_path / "claude"
    common_skill = common / "glosswise" / "SKILL.md"
    claude_skill = claude / "glosswise" / "SKILL.md"
    common_skill.parent.mkdir(parents=True)
    claude_skill.parent.mkdir(parents=True)
    stale = "---\nname: glosswise\n---\nstale\n"
    common_skill.write_text(stale, encoding="utf-8")
    claude_skill.write_text(
        "---\nname: another-skill\n---\n",
        encoding="utf-8",
    )

    with pytest.raises(FileExistsError, match="unverified Skill"):
        install_agent_skills([common, claude])

    assert common_skill.read_text(encoding="utf-8") == stale


@pytest.mark.fast
def test_cli_setup_hides_storage_and_emits_portable_mcp_json(
    tmp_path: Path,
) -> None:
    """First setup should require languages and hide managed storage."""
    runner = TyperRunner()
    environment = {"HOME": str(tmp_path / "home")}
    try:
        missing_languages = runner.invoke(
            create_cli("typer"),
            ["setup"],
            env=environment,
        )
        assert missing_languages.exit_code != 0
        assert "Setup requires at least one default language." in (missing_languages.output)

        setup = runner.invoke(
            create_cli("typer"),
            [
                "setup",
                "-l",
                "en",
                "--lang",
                "zh",
                "-l",
                "ru",
            ],
            env=environment,
        )
        assert setup.exit_code == 0, setup.output
        result = json.loads(setup.stdout)
        assert result["workspace"]["id"] == "default"
        assert result["workspace"]["active"] is True
        assert result["workspace"]["default_languages"] == ["en", "zh", "ru"]
        assert result["user_config"]["default_languages"] == ["en", "zh", "ru"]
        assert result["skills"] == [
            str((tmp_path / "home" / ".agents" / "skills" / "glosswise" / "SKILL.md").resolve()),
            str((tmp_path / "home" / ".claude" / "skills" / "glosswise" / "SKILL.md").resolve()),
        ]
        assert "database" not in setup.stdout.lower()

        listed = runner.invoke(
            create_cli("typer"),
            ["ws", "ls"],
            env=environment,
        )
        assert listed.exit_code == 0, listed.output
        assert json.loads(listed.stdout)["items"][0]["id"] == "default"
        assert json.loads(listed.stdout)["items"][0]["default_languages"] == [
            "en",
            "zh",
            "ru",
        ]

        languages = runner.invoke(
            create_cli("typer"),
            [
                "ws",
                "lang",
                "-l",
                "en",
                "--lang",
                "zh",
                "-l",
                "en",
                "-l",
                "ru",
            ],
            env=environment,
        )
        assert languages.exit_code == 0, languages.output
        assert json.loads(languages.stdout)["default_languages"] == [
            "en",
            "zh",
            "ru",
        ]

        file_access = runner.invoke(
            create_cli("typer"),
            ["ws", "files", "-r", str(tmp_path)],
            env=environment,
        )
        assert file_access.exit_code == 0, file_access.output
        file_policy = json.loads(file_access.stdout)
        assert file_policy["allowed_roots"] == [str(tmp_path.resolve())]
        assert file_policy["encodings"] == ["utf-8"]

        missing_root = runner.invoke(
            create_cli("typer"),
            ["ws", "files"],
            env=environment,
        )
        assert missing_root.exit_code != 0
        assert "At least one --root is required." in missing_root.output

        created = runner.invoke(
            create_cli("typer"),
            [
                "workspace",
                "create",
                "secondary",
                "--no-activate",
            ],
            env=environment,
        )
        assert created.exit_code != 0

        created = runner.invoke(
            create_cli("typer"),
            [
                "ws",
                "create",
                "secondary",
                "--no-activate",
            ],
            env=environment,
        )
        assert created.exit_code == 0, created.output
        assert json.loads(created.stdout)["active"] is False
        assert json.loads(created.stdout)["default_languages"] == [
            "en",
            "zh",
            "ru",
        ]

        mode = runner.invoke(
            create_cli("typer"),
            ["config", "mode", "explain"],
            env=environment,
        )
        assert mode.exit_code == 0, mode.output
        assert json.loads(mode.stdout) == {
            "custom_prompt": "",
            "mode": "explain",
        }
        llm = runner.invoke(
            create_cli("typer"),
            ["config", "llm", "translation"],
            env=environment,
        )
        assert llm.exit_code == 0, llm.output
        assert json.loads(llm.stdout) == {"preset": "translation"}

        activated = runner.invoke(
            create_cli("typer"),
            ["ws", "use", "secondary"],
            env=environment,
        )
        assert activated.exit_code == 0, activated.output
        assert json.loads(activated.stdout)["active"] is True

        health = runner.invoke(
            create_cli("typer"),
            ["ws", "health"],
            env=environment,
        )
        assert health.exit_code == 0, health.output
        assert "database" not in health.stdout.lower()

        deactivated = runner.invoke(
            create_cli("typer"),
            ["ws", "deact"],
            env=environment,
        )
        assert deactivated.exit_code == 0, deactivated.output
        assert json.loads(deactivated.stdout)["deactivated"] == "secondary"

        removed = runner.invoke(
            create_cli("typer"),
            ["ws", "rm", "secondary"],
            env=environment,
        )
        assert removed.exit_code == 0, removed.output
        assert json.loads(removed.stdout)["data_retained"] is True

        config = runner.invoke(
            create_cli("typer"),
            ["mcp", "--json"],
            env=environment,
        )
        assert config.exit_code == 0, config.output
        server = json.loads(config.stdout)["mcpServers"]["glosswise"]
        assert server == {
            "command": "glosswise",
            "args": ["mcp"],
        }

        http_config = runner.invoke(
            create_cli("typer"),
            ["mcp", "--json", "--transport", "http"],
            env=environment,
        )
        assert http_config.exit_code == 0, http_config.output
        assert json.loads(http_config.stdout)["mcpServers"]["glosswise"] == {
            "transport": "http",
            "url": "http://127.0.0.1:61055/mcp",
        }

        custom_http = runner.invoke(
            create_cli("typer"),
            [
                "mcp",
                "--json",
                "--transport",
                "sse",
                "--host",
                "localhost",
                "--port",
                "61056",
            ],
            env=environment,
        )
        assert custom_http.exit_code == 0, custom_http.output
        assert json.loads(custom_http.stdout)["mcpServers"]["glosswise"] == {
            "transport": "sse",
            "url": "http://localhost:61056/sse",
        }

        invalid_port = runner.invoke(
            create_cli("typer"),
            ["mcp", "--json", "--port", "70000"],
            env=environment,
        )
        assert invalid_port.exit_code != 0

        brief_help = runner.invoke(
            create_cli("typer"),
            ["brief", "--help"],
        )
        assert "does not generate a translation" in brief_help.stdout
        set_help = runner.invoke(
            create_cli("typer"),
            ["term", "set", "--help"],
        )
        assert "Create or update" in set_help.stdout
        put_alias_help = runner.invoke(
            create_cli("typer"),
            ["term", "put", "--help"],
        )
        assert put_alias_help.exit_code == 0
    finally:
        restore_owner_permissions(tmp_path)
