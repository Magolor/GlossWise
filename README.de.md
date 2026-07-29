# GlossWise

<p align="center">
  <a href="README.en.md">English</a> ·
  <a href="README.ar.md">العربية</a> ·
  <a href="README.zh.md">中文</a> ·
  <a href="README.fr.md">Français</a> ·
  <a href="README.ru.md">Русский</a> ·
  <a href="README.es.md">Español</a> ·
  <strong>Deutsch</strong> ·
  <a href="README.ja.md">日本語</a>
</p>

<p align="center">
  <img src="docs/assets/glosswise-banner.png" alt="GlossWise — terminologiesichere Übersetzung für KI-Agenten" width="100%">
</p>

<p align="center">
  <a href="https://github.com/Magolor/GlossWise/actions/workflows/ci.yml"><img src="https://github.com/Magolor/GlossWise/actions/workflows/ci.yml/badge.svg?branch=master" alt="Kontinuierliche Integration"></a>
  <a href="https://www.python.org/"><img src="https://img.shields.io/badge/Python-3.10–3.13-3776AB" alt="Python 3.10 bis 3.13"></a>
  <a href="https://ahvn.top"><img src="https://img.shields.io/badge/HeavenBase-0.1.2.1-6957E5" alt="HeavenBase 0.1.2.1"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-green.svg" alt="MIT-Lizenz"></a>
</p>

<p align="center">
  <a href="#install">Installieren</a> ·
  <a href="#connect-an-agent">KI-Agent verbinden</a> ·
  <a href="#try-it-teach-once-translate-consistently">Demo ausprobieren</a> ·
  <a href="#everyday-prompts">Prompts für den Alltag</a> ·
  <a href="#mcp-server">MCP-Werkzeuge</a> ·
  <a href="#python-sdk">Python SDK</a>
</p>

GlossWise speichert freigegebene Begriffe, Übersetzungsregeln und Beispiele und erstellt anschließend
ein kompaktes Übersetzungsbriefing für den aufrufenden KI-Agenten oder die Anwendung. Host-Agenten
übersetzen mit ihrem eigenen Modell; die direkte CLI nutzt ein sichtbares HeavenBase-LLM-Preset.

GlossWise ist als CLI, MCP-Server und Python SDK verfügbar. Version `0.1.0.5`
unterstützt `heavenbase>=0.1.2.1`.

## <a id="install"></a> Installation

GlossWise erfordert Python 3.10–3.13. Installiere den aktuellen Quellstand direkt von
GitHub. Vor der Installation kannst du den [genauen KI-Agenten-Skill](SKILL.md) einsehen:

```console
python -m pip install "git+https://github.com/Magolor/GlossWise.git"
glosswise setup -l en -l zh
```

Um den Quellcode einzusehen oder dazu beizutragen:

```console
git clone https://github.com/Magolor/GlossWise.git
cd GlossWise
python -m pip install .
glosswise setup -l en -l zh
```

`setup` verlangt die üblichen Übersetzungssprachen und speichert sie als
globale Vorgaben, erstellt und aktiviert damit den Arbeitsbereich `default`
und installiert anschließend den GlossWise-KI-Agenten-Skill unter:

- `~/.agents/skills/glosswise`
- `~/.claude/skills/glosswise`

Der öffentliche Skill im Stammverzeichnis und die durch `setup` installierte Paketkopie bleiben
Byte für Byte identisch.

Die Daten des Arbeitsbereichs werden automatisch unter `~/.glosswise/` verwaltet. Du musst
weder eine Datenbank auswählen noch eine offenlegen. Neue Arbeitsbereiche erben die globalen
Sprachen; ändere sie mit `glosswise config lang -l en -l <language>`.

Überprüfe die Installation:

```console
glosswise ws ls
glosswise ws get
```

## <a id="connect-an-agent"></a> KI-Agenten verbinden

`glosswise setup` hat den allgemeinen und den Claude-GlossWise-Skill bereits installiert.
Verbinde denselben globalen MCP-Server aus jedem unterstützten Host:

| Host | Einmalige Einrichtung |
| --- | --- |
| [Claude Code](https://code.claude.com/docs/en/mcp) | `claude mcp add --scope user glosswise -- glosswise mcp` |
| [Codex](https://developers.openai.com/codex/mcp/) | `codex mcp add glosswise -- glosswise mcp` |
| [Cursor](https://docs.cursor.com/context/model-context-protocol) | Speichere `glosswise mcp --json` als `~/.cursor/mcp.json`. |
| [VS Code / Copilot](https://code.visualstudio.com/docs/copilot/chat/mcp-servers) | Ergänze `.vscode/mcp.json` um einen stdio-Eintrag `servers.glosswise` mit Befehl `glosswise` und Argumenten `["mcp"]`. |
| [OpenCode](https://opencode.ai/docs/mcp-servers/) | Ergänze `~/.config/opencode/opencode.json` um den lokalen MCP-Eintrag unten. |
| [OpenClaw](https://ahvn.top/quickstart/heavenbase-mcp#3-connect-your-agent) | Starte `glosswise mcp --transport http` und setze `mcp.servers.glosswise` auf `http://127.0.0.1:61055/mcp` mit Transport `streamable-http`. |
| [Hermes](https://ahvn.top/quickstart/heavenbase-mcp#3-connect-your-agent) | Starte `glosswise mcp --transport http` und trage die URL unter `mcp_servers.glosswise` in `~/.hermes/config.yaml` ein. |
| [LM Studio](https://lmstudio.ai/docs/app/mcp) | Öffne **Program/Developer → Install → Edit mcp.json** und füge die Ausgabe von `glosswise mcp --json` ein. |
| [Qwen Code](https://qwenlm.github.io/qwen-code-docs/en/users/features/mcp/) | `qwen mcp add --scope user glosswise glosswise mcp` |
| [HeavenBase](https://ahvn.top/quickstart/heavenbase-mcp#3-connect-your-agent) | Starte `glosswise mcp --transport http`, dann `hb llm session --mcp http://127.0.0.1:61055/mcp`. |

Füge für [OpenCode](https://opencode.ai/docs/mcp-servers/) Folgendes zur globalen Datei
`~/.config/opencode/opencode.json` hinzu:

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

Prüfe die Verbindung mit dem MCP-Listenbefehl des Hosts und starte den Agenten
neu, wenn dessen Dokumentation dies verlangt.

Beginne einen neuen Chat und sage:

```text
/glosswise Liste meine Arbeitsbereiche auf und sage mir, welcher davon aktiv ist.
```

Der KI-Agent kann nun Arbeitsbereiche erstellen, Terminologie pflegen, darin suchen und
in deinem Auftrag Übersetzungsbriefings vorbereiten. Du musst weder JSON schreiben noch eine
Datenbank verwalten. Ein Skill und eine MCP-Verbindung funktionieren für alle GlossWise-
Arbeitsbereiche.

Gib für einen anderen stdio-fähigen MCP-Client das portable Profil aus:

```console
glosswise mcp --json
```

## <a id="try-it-teach-once-translate-consistently"></a> Ausprobieren: einmal beibringen, konsistent übersetzen

Diese Demo beginnt mit einer gewöhnlichen Modellübersetzung, bringt GlossWise zwei
Terminologieentscheidungen in natürlicher Sprache bei und wiederholt dann die ursprüngliche Anfrage
in einer neuen KI-Agentensitzung. Der Auszug stammt aus
[Mary Shelleys *Frankenstein*](https://www.gutenberg.org/cache/epub/42324/pg42324-images.html),
einem frühen gemeinfreien Werk der Science-Fiction-Literatur.

### 1. Einen Arbeitsbereich anlegen

Bitte deinen KI-Agenten:

```text
/glosswise Erstelle und wähle einen GlossWise-Arbeitsbereich namens `frankenstein-lab`.
Lege Englisch, Chinesisch, Französisch, Deutsch, Russisch und Japanisch als Standardsprachen fest.
```

Oder verwende die beiden kurzen CLI-Befehle:

```console
glosswise ws create frankenstein-lab
glosswise ws lang -l en -l zh -l fr -l de -l ru -l ja
```

`ws create` wählt den neuen Arbeitsbereich automatisch aus. Wiederhole `-l/--lang`
für jede geordnete Sprache. Diese Menge erinnert Agenten daran, alle sechs bevorzugten Formen zu erfassen, ohne
die Sprachen zu einer festen Einschränkung zu machen.

### 2. Vor dem Anlernen von GlossWise übersetzen

Sende dem KI-Agenten diesen Absatz:

```text
/glosswise Verwende den Arbeitsbereich `frankenstein-lab`. Übersetze den folgenden Absatz
ins Chinesische, Französische, Deutsche, Russische und Japanische. Prüfe GlossWise zunächst auf
relevante Hinweise und nenne anschließend das Modell oder den Host, das bzw. der die Übersetzung ausgeführt hat.

“It was on a dreary night of November, that I beheld the accomplishment of my
toils. With an anxiety that almost amounted to agony, I collected the
instruments of life around me, that I might infuse a spark of being into the
lifeless thing that lay at my feet.”
```

Die erste Formulierung hängt vom Übersetzungsmodell des KI-Agenten ab. Es könnte sich für
wörtliche Wendungen wie „spark of being“ → `存在的火花`,
`étincelle de vie`, `Lebensfunken`, `искра жизни` oder `命の火花` entscheiden.

### 3. Zwei Entscheidungen im Gespräch beibringen

Sende noch eine Nachricht:

```text
/glosswise Speichere diese als aktive bevorzugte Begriffe im Arbeitsbereich `frankenstein-lab`.
Die Zielformen sind Terminologieentscheidungen meines Projekts und keine Aussagen
über die offiziellen Übersetzungen des Romans.

1. „instruments of life“ bezeichnet die bei dem Experiment verwendeten Geräte:
   Chinesisch 生命仪器; Französisch instruments de vie;
   Deutsch Instrumente des Lebens; Russisch орудия жизни;
   Japanisch 生命の器具.

2. „spark of being“ bezeichnet die belebende Essenz, die lebloser Materie verliehen wird:
   Chinesisch 生命之火; Französisch étincelle d'existence;
   Deutsch Funke des Seins; Russisch искра бытия;
   Japanisch 存在の火花.

Behalte auch die englischen Ausgangsformen bei. Verwende die bevorzugte Terminologie exakt, wenn
die Grammatik der Zielsprache dies zulässt; flektiere sie andernfalls, ohne das
freigegebene Konzept zu verändern. Teile mir mit, sobald beide Datensätze gespeichert sind.
```

Der KI-Agent übernimmt die strukturierten CRUD-Aufrufe. Wenn eine angeforderte Sprache des Arbeitsbereichs
fehlt, weist der installierte Skill ihn an, nachzufragen, eine Form zur
Bestätigung vorzuschlagen oder eine vom KI-Agenten erzeugte Form eindeutig als solche zu kennzeichnen.

### 4. Eine neue Sitzung starten und dieselbe Anfrage wiederholen

Beende den aktuellen Chat und beginne eine neue KI-Agentensitzung. Sende den exakten Prompt aus
Schritt 2 erneut – füge keine Erinnerung an die gerade gespeicherten Begriffe hinzu:

```text
/glosswise Verwende den Arbeitsbereich `frankenstein-lab`. Übersetze den folgenden Absatz
ins Chinesische, Französische, Deutsche, Russische und Japanische. Prüfe GlossWise zunächst auf
relevante Hinweise und nenne anschließend das Modell oder den Host, das bzw. der die Übersetzung ausgeführt hat.

“It was on a dreary night of November, that I beheld the accomplishment of my
toils. With an anxiety that almost amounted to agony, I collected the
instruments of life around me, that I might infuse a spark of being into the
lifeless thing that lay at my feet.”
```

Der Prompt ist identisch; nur der persistierte GlossWise-Arbeitsbereich hat sich geändert.
Die neue Sitzung muss diesen Zustand abrufen, statt sich auf den Chatverlauf zu verlassen. Die
wichtige Änderung ist nun sichtbar:

| Sprache | Eine Ausgangsübersetzung könnte verwenden | Von GlossWise geleitete Formulierung |
| --- | --- | --- |
| Chinesisch | `生命工具` · `存在的火花` | `生命仪器` · `生命之火` |
| Französisch | `instruments de la vie` · `étincelle de vie` | `instruments de vie` · `étincelle d'existence` |
| Deutsch | `Werkzeuge des Lebens` · `Lebensfunken` | `Instrumente des Lebens` · `Funken des Seins`¹ |
| Russisch | `инструменты жизни` · `искра жизни` | `орудия жизни` · `искру бытия`¹ |
| Japanisch | `生命の道具` · `命の火花` | `生命の器具` · `存在の火花` |

¹ Der KI-Agent flektiert die kanonische bevorzugte Form passend zu diesem Satz.

<details>
<summary>Ein erfolgreiches, von GlossWise geleitetes Ergebnis</summary>

**Chinesisch**

> 那是十一月一个阴沉的夜晚，我目睹了自己辛劳的成果。怀着近乎痛苦的焦虑，我把生命仪器聚集在身边，想把生命之火注入躺在我脚边的无生命之物中。

**Französisch**

> Ce fut par une lugubre nuit de novembre que je contemplai l’accomplissement de mes travaux. Avec une anxiété qui confinait presque à l’agonie, je rassemblai autour de moi les instruments de vie afin d’insuffler une étincelle d'existence à la chose inanimée étendue à mes pieds.

**Deutsch**

> Es war in einer trüben Novembernacht, als ich die Vollendung meiner Mühen erblickte. Mit einer Angst, die beinahe an Qual grenzte, versammelte ich die Instrumente des Lebens um mich, um dem leblosen Ding zu meinen Füßen einen Funken des Seins einzuhauchen.

**Russisch**

> В мрачную ноябрьскую ночь я увидел завершение своих трудов. С тревогой, почти переходившей в агонию, я собрал вокруг себя орудия жизни, чтобы вдохнуть искру бытия в безжизненное создание, лежавшее у моих ног.

**Japanisch**

> 十一月の陰鬱な夜、私は自らの労苦の成就を目の当たりにした。苦悶に近い不安を抱えながら、私は生命の器具を周囲に集め、足元に横たわる生命なきものへ存在の火花を吹き込もうとした。

</details>

GlossWise hat diese Sätze nicht erzeugt. Der verbundene KI-Agent hat dies getan; GlossWise
hat die freigegebene Terminologie vor der Erzeugung abrufbar und überprüfbar gemacht.

### 5. Später suchen und bearbeiten

Datensatzkennungen sind nicht erforderlich:

```text
/glosswise Finde den Begriff zu einem Funken in `frankenstein-lab`. Zeige seine bevorzugten
Formen in einer kompakten Tabelle.
```

Bearbeite ihn anschließend in natürlicher Sprache:

```text
/glosswise Ändere nur die japanische bevorzugte Form für „spark of being“ in
`生命の火花`. Lasse jede andere Sprache unverändert und zeige mir den gespeicherten Datensatz.
```

Dieser vollständige Ablauf aus Einrichtung → Erstellen → Pflegen → Neustart → Übersetzungsbriefing → Suche → Bearbeiten wird
mit einem installierten Wheel und zwei unabhängigen stdio-MCP-Sitzungen in
[`tests/test_quickstart.py`](https://github.com/Magolor/GlossWise/blob/master/tests/test_quickstart.py) getestet.

## <a id="everyday-prompts"></a> Prompts für den Alltag

Nach der Verbindung kann die normale Arbeit im Chat stattfinden. Die folgenden Verwaltungs-Prompts nehmen
bewusste Änderungen vor; Abfrage- und Übersetzungs-Prompts sind schreibgeschützt, sofern sie nicht
ausdrücklich darum bitten, etwas zu speichern.

### Arbeitsbereiche und Terminologie verwalten

- `/glosswise Erstelle und wähle einen Arbeitsbereich namens <name>.`
- `/glosswise Lege im Arbeitsbereich <name> Englisch, Chinesisch und Japanisch als Standardsprachen fest.`
- `/glosswise Speichere im Arbeitsbereich <name> „rate limit“ als aktiven bevorzugten Begriff mit Englisch „rate limit“, Chinesisch „速率限制“ und Japanisch „レート制限“. Zeige mir den gespeicherten Datensatz.`
- `/glosswise Finde „rate limit“ im Arbeitsbereich <name>. Ändere nur seine japanische bevorzugte Form in „速度制限“, behalte alle anderen Felder und Formen bei und zeige mir anschließend den aktualisierten Datensatz.`
- `/glosswise Archiviere den Begriff „rate limit“ im Arbeitsbereich <name>, sodass er von der normalen Suche nach aktiven Begriffen ausgeschlossen wird. Frage mich, bevor du die Änderung vornimmst.`

### Hinweise nachschlagen und übersetzen

- `/glosswise Finde im Arbeitsbereich <name> aktive Begriffe zur Authentifizierung. Zeige ihre bevorzugten und unzulässigen Formen auf Englisch, Chinesisch und Japanisch. Ändere nichts.`
- `/glosswise Finde im Arbeitsbereich <name> Regeln und Beispiele für die Übersetzung von Fehlermeldungen ins Französische. Zeige Prioritäten, Stile und Konflikte. Ändere nichts.`
- `/glosswise Prüfe „Requests over this limit are rejected.“ anhand des Arbeitsbereichs <name>. Liste übereinstimmende Begriffe und Regeln auf, ohne etwas zu übersetzen oder zu speichern.`
- `/glosswise Verwende den Arbeitsbereich <name>. Übersetze „The client retries the request after the rate limit resets.“ aus dem Englischen ins Chinesische und Japanische. Erstelle für jede Zielsprache ein neues GlossWise-Übersetzungsbriefing, wende aktive bevorzugte Begriffe und Regeln an, kennzeichne Konflikte und nenne das Modell oder den Host, das bzw. der die Übersetzung ausgeführt hat.`
- `/glosswise Verwende den Arbeitsbereich <name>. Übersetze die folgende englische Passage ins Französische. Erstelle zunächst ein GlossWise-Übersetzungsbriefing und zeige dann nach der Übersetzung eine kompakte Tabelle mit allen gespeicherten Begriffen, Regeln oder Beispielen, die du angewendet hast: <paste source passage>.`
- `/glosswise Prüfe diese französische Übersetzung anhand des Arbeitsbereichs <name>. Melde fehlende bevorzugte Begriffe, unzulässige Formen und widersprüchliche Regeln; formuliere nichts um und speichere nichts, sofern ich nicht darum bitte: <paste translation>.`

Verwende `glosswise ws ls`, `glosswise ws use <name>` und
`glosswise ws get`, wenn eine schnelle Prüfung im Terminal bequemer ist als im Chat.

## Integrierte Übersetzung, Dateibereiche und PDF-OCR

Die direkte Übersetzung nutzt ein benanntes HeavenBase-`LLMSession`-Preset.
Jedes Ergebnis nennt Preset, Gateway, Provider, Modell und Modell-ID. Preset
und Unsicherheitsverhalten werden unabhängig gewählt:

```console
glosswise config llm chat
glosswise config mode auto
glosswise translate "Run this query." -sl en -tl ja
glosswise translate "Run this query." -sl en -tl ja --preset chat
```

Die Modi sind `yolo` (sofort übersetzen), `elicit` (gezielte Terminologiefragen
mit Optionen), `auto` (an vorhandene Belege anpassen), `explain`
(übersetzen und jede wesentliche Wahl erklären) sowie `custom` mit `--prompt`.
HeavenBase rendert den System-Prompt mit `hb.Prompt` und löst das benannte
Preset auf. `chat` übernimmt die aktuelle schnelle Chat-Auswahl; ein eigenes
Preset vermeidet doppelte Provider-Zugangsdaten in GlossWise:

```console
hb cfg set heavenbase.llm.presets.glosswise-translate.model deepseek-v4-flash
glosswise config llm glosswise-translate
```

`scan`, `brief` und `translate` akzeptieren inklusive, bei 1 beginnende Bereiche
mit `--start-line` und `--end-line` für direkten Text, stdin und `@file`. Das
autorisierte lokale MCP-Profil stellt entsprechende Datewerkzeuge bereit.

Für PDFs autorisierst du das Verzeichnis, lässt nur benötigte Seiten mit dem
konfigurierten HeavenBase-LLM-Preset erkennen und liest den seitenweisen Text
über den kurzen Handle `gw-...`:

```console
glosswise ws files -r /absolute/path/to/documents
glosswise pdf ocr /absolute/path/to/documents/manual.pdf --start-page 4 --end-page 8
glosswise doc read gw-0123456789ab 4 --start-line 1 --end-line 80
glosswise doc rm gw-0123456789ab
```

`ws files` speichert eine arbeitsbereichsbezogene Lesefreigabe; wiederhole
`-r/--root` für jedes Verzeichnis. Dateien werden weder hochgeladen noch kopiert
oder registriert. Wiederhole `-e/--encoding` nur für zusätzliche strikt zu
dekodierende Textkodierungen; UTF-8 ist standardmäßig erlaubt.

GlossWise rendert und erkennt jeweils eine Seite und löscht das Bild sofort.
Verdächtige lange Wiederholungen werden gemeldet und nie still entfernt.
Konfiguriere `ocr-local` mit `hb cfg set
heavenbase.llm.presets.ocr-local.<field-or-path> <value>`; dazu gehören
`desc`, `gateway`, `provider`, `model` und `default_args`; ein anderes Preset wählst du mit `glosswise config ocr <preset>`.

## <a id="mcp-server"></a> MCP-Server

### Lokales stdio

Die meisten Desktop-Clients und Clients für Coding-KI-Agenten sollten Folgendes verwenden:

```console
glosswise mcp --json
```

Der erzeugte Kindprozess startet den vollständigen Server mit Lese-, CRUD-, Skill- und
Arbeitsbereichsverwaltungswerkzeugen. Die ausführbare Datei `glosswise` muss im `PATH` des MCP-
Clients verfügbar sein.

### Lokales HTTP

So führst du einen langlebigen streamfähigen HTTP-Server aus:

```console
glosswise mcp --transport http
```

Er bindet standardmäßig an `127.0.0.1:61055` und stellt MCP unter
`http://127.0.0.1:61055/mcp` bereit. Gib das passende Clientprofil aus mit:

```console
glosswise mcp --json --transport http
```

Wähle bei Bedarf einen anderen lokalen Endpunkt:

```console
glosswise mcp --transport http --host 127.0.0.1 --port 61056
```

GlossWise fügt keine Netzwerkauthentifizierung hinzu. Belasse den Server auf einem Loopback-
Host, sofern nicht eine andere vertrauenswürdige Schicht Authentifizierung und Transport-
sicherheit bereitstellt.

### MCP-Werkzeuge

Daten- und Kontextwerkzeuge akzeptieren eine optionale `workspace_id`. Wird sie weggelassen,
verwendet GlossWise den aktiven Arbeitsbereich und anschließend den verwalteten Standardarbeitsbereich.

| Werkzeug | Zweck | `read` | `full` | `local` |
| --- | --- | :---: | :---: | :---: |
| `glosswise_workspace_info` | Zeigt Funktionen und Sprachhinweise des Arbeitsbereichs an. | ✓ | ✓ | ✓ |
| `glosswise_prepare_translation` | Erstellt ein Übersetzungsbriefing für den Ausgangstext. | ✓ | ✓ | ✓ |
| `glosswise_search_terms` | Sucht Begriffe. | ✓ | ✓ | ✓ |
| `glosswise_search_rules` | Sucht Regeln. | ✓ | ✓ | ✓ |
| `glosswise_search_examples` | Sucht Beispiele. | ✓ | ✓ | ✓ |
| `glosswise_scan_text` | Durchsucht Text nach übereinstimmenden Begriffen und Regeln. | ✓ | ✓ | ✓ |
| `glosswise_list_records` | Listet Begriffe, Regeln oder Beispiele auf. | ✓ | ✓ | ✓ |
| `glosswise_get_record` | Ruft einen Datensatz anhand seiner Objekt-ID ab. | ✓ | ✓ | ✓ |
| `glosswise_put_term` | Erstellt oder aktualisiert einen Begriff und seine Formen. | — | ✓ | ✓ |
| `glosswise_put_rule` | Erstellt oder aktualisiert eine Regel. | — | ✓ | ✓ |
| `glosswise_put_example` | Erstellt oder aktualisiert ein Beispiel. | — | ✓ | ✓ |
| `glosswise_archive` | Archiviert einen Datensatz. | — | ✓ | ✓ |
| `glosswise_list_workspaces` | Listet Arbeitsbereiche auf. | ✓ | ✓ | ✓ |
| `glosswise_get_workspace` | Ruft einen bereinigten Arbeitsbereichsdatensatz ab. | ✓ | ✓ | ✓ |
| `glosswise_create_workspace` | Erstellt einen verwalteten Arbeitsbereich. | — | ✓ | ✓ |
| `glosswise_set_workspace_languages` | Legt die Sprachhinweise des Arbeitsbereichs fest. | — | ✓ | ✓ |
| `glosswise_activate_workspace` | Wählt den aktiven Arbeitsbereich aus. | — | ✓ | ✓ |
| `glosswise_deactivate_workspace` | Hebt die aktive Auswahl auf. | — | ✓ | ✓ |
| `glosswise_remove_workspace` | Hebt die Registrierung eines Arbeitsbereichs auf. | — | ✓ | ✓ |
| `glosswise_open_workspace` | Öffnet einen Arbeitsbereich und zeigt seine Funktionen an. | ✓ | ✓ | ✓ |
| `glosswise_health_workspace` | Prüft die Integrität von Registry und Laufzeit. | ✓ | ✓ | ✓ |
| `glosswise_read_skill` | Liest die gepackten KI-Agentenanweisungen. | ✓ | ✓ | ✓ |
| `glosswise_scan_file` | Durchsucht eine autorisierte serverlokale Textdatei. | — | — | ✓ |
| `glosswise_prepare_file` | Erstellt ein Briefing aus einem autorisierten Dateibereich. | — | — | ✓ |
| `glosswise_ocr_pdf` | Erkennt autorisierte PDF-Seiten in einen kurzen Handle. | — | — | ✓ |
| `glosswise_list_documents` | Listet temporäre OCR-Dokument-Handles auf. | — | — | ✓ |
| `glosswise_get_document` | Prüft das Manifest eines OCR-Dokuments. | — | — | ✓ |
| `glosswise_read_document` | Liest einen begrenzten Zeilenbereich einer OCR-Seite. | — | — | ✓ |
| `glosswise_remove_document` | Entfernt ein temporäres OCR-Dokument. | — | — | ✓ |

### MCP-Profile

Profile steuern die Werkzeugfreigabe, nicht den Inhalt der Arbeitsbereiche oder die installierte Skill-
Datei:

| Profil | Exakte Oberfläche | Verwendungszweck |
| --- | --- | --- |
| `full` | Die 22 in der Spalte `full` markierten Werkzeuge. | Standard. Unterstützt Suche, Übersetzungsbriefings, CRUD, Skill-Prüfung und Verwaltung von Arbeitsbereichen. Sowohl `glosswise mcp` als auch `glosswise mcp --json` wählen dieses Profil aus. |
| `read` | Die 13 in der Spalte `read` markierten Werkzeuge. | Schreibgeschützte Nutzung von Terminologie/Kontext und Prüfung von Arbeitsbereichen. Es kann weder Datensätze pflegen noch die Auswahl ändern oder Arbeitsbereiche verwalten. |
| `local` | Alle 22 `full`-Werkzeuge sowie sieben autorisierte lokale Dokumentwerkzeuge. | Erweiterter Vollzugriff für begrenzte Textbereiche und PDF-OCR. Das Profil allein gewährt keinen Zugriff; autorisiere zuerst Stammverzeichnisse. |

`glosswise setup` installiert einen profilunabhängigen Skill. Der Skill
wählt kein Profil aus: Der verbundene MCP-Server entscheidet, welche Werkzeuge der KI-Agent
aufrufen kann. Die normale Einrichtung verwendet `full`; dies ist das einzige nicht lokale Profil, das
alle vom Skill vermittelten Verwaltungs- und Übersetzungsabläufe unterstützt.

Um eine vorhandene Installation zu ändern, behalte den installierten Skill bei und ändere nur
den MCP-Serverbefehl in der Konfiguration des KI-Agenten; starte den KI-Agenten danach neu oder verbinde
ihn erneut:

```console
glosswise mcp                 # full (default)
glosswise mcp --profile read  # read-only
glosswise mcp --profile local # full plus authorized text/PDF tools
```

Verwende `glosswise mcp --json --profile <profile>`, um Ersatz-Client-
JSON zu erzeugen. Eine erneute Ausführung von `glosswise setup` ist beim Profilwechsel nicht erforderlich.
Die Rückkehr zum einfachen Befehl `glosswise mcp` stellt die standardmäßige `full`-Oberfläche wieder her.

Jedes Werkzeug gibt einen versionierten JSON-Umschlag zurück. KI-Agenten sollten `error`,
`warnings`, `conflicts` und `truncated` prüfen, bevor sie `items` verwenden.

## CLI-Referenz

| Aufgabe | Befehl | Ebenfalls akzeptiert |
| --- | --- | --- |
| Arbeitsbereiche auflisten | `glosswise ws ls` | `ws list` |
| Einen Arbeitsbereich prüfen | `glosswise ws get [<name>]` | — |
| Einen Arbeitsbereich erstellen | `glosswise ws create [<name>]` | — |
| Einen Arbeitsbereich auswählen | `glosswise ws use <name>` | `ws activate`, `ws act` |
| Auswahl aufheben | `glosswise ws deact` | `ws deactivate` |
| Registrierung eines Arbeitsbereichs aufheben | `glosswise ws rm <name>` | `ws unset`, `ws remove` |
| Globale Konfiguration anzeigen | `glosswise config get` | — |
| Globale Sprachen setzen | `glosswise config lang -l en -l <language>` | `config languages` |
| Übersetzungsverhalten setzen | `glosswise config mode <mode>` | — |
| Übersetzungs-LLM-Preset setzen | `glosswise config llm <preset>` | — |
| Sprachhinweise festlegen | `glosswise ws lang -l en -l <language>` | `ws languages` |
| Lokale Wurzeln autorisieren | `glosswise ws files -r <directory>` | — |
| Daten erstellen oder aktualisieren | `glosswise term set @term.json` | `term put` |
| Einen Datensatz abrufen | `glosswise term get <object-id>` | — |
| Daten auflisten | `glosswise term ls` | `term list` |
| Daten durchsuchen | `glosswise term search "query"` | — |
| Daten archivieren | `glosswise term archive <object-id>` | — |
| Eine Passage durchsuchen | `glosswise scan "text"` | — |
| Kontext vorbereiten | `glosswise brief "text"` | — |
| Mit LLMSession übersetzen | `glosswise translate "text"` | — |
| PDF-Seiten erkennen | `glosswise pdf ocr <path>` | — |
| OCR-Text durchsuchen | `glosswise doc read <handle> <page>` | — |

Ersetze `term` für denselben Ablauf aus
Festlegen/Abrufen/Auflisten/Suchen/Archivieren durch `rule` oder `example`. Führe für die vollständige Befehlsoberfläche
`glosswise --help` oder `glosswise <group> --help` aus.

## <a id="python-sdk"></a> Python SDK

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

`GlossWiseApp.open()` verwendet den aktiven Arbeitsbereich oder erstellt den
verwalteten Standard erst nach Konfiguration der globalen Sprachen.
Verwende `GlossWiseApp.create("<name>")` für einen explizit benannten verwalteten Arbeitsbereich
und `GlossWiseApp.load()`, wenn das Fehlen einen Fehler auslösen soll. Anwendungen, die
bereits einen HeavenBase-Arbeitsbereich besitzen, können `workspace.glosswise` direkt verwenden.

## Funktionsweise

1. Ein KI-Agent stellt über MCP, die CLI oder das Python SDK eine Verbindung her.
2. GlossWise löst den angeforderten Arbeitsbereich auf oder verwendet den aktiven/standardmäßigen.
3. Es ruft relevante Begriffe, Regeln und Beispiele ab.
4. `brief` gewichtet und bündelt diese Belege mit Warnungen und Konflikten.
5. Der Host-Agent übersetzt, oder `translate` ruft HeavenBase `LLMSession`
   über einen von `hb.Prompt` verwalteten Vertrag und ein sichtbares Preset auf.
6. Der Aufrufer kann die Übersetzung prüfen oder autorisierte PDF-Seiten
   in begrenzten temporären Text je Seite erkennen.

GlossWise verbirgt Speicher- und Terminologierichtlinien hinter aufgabenorientierten Operationen;
KI-Agenten benötigen keinen generischen Datenbankzugriff.

## Für Entwickler

GlossWise ist ein Demoprojekt, das zeigt, wie eine sauber strukturierte, eigenständige Anwendung
HeavenBase nutzen kann. Es veranschaulicht die praktischen Vorteile von:

- einer modularen Erweiterung, die unter `workspace.glosswise` eingebunden ist;
- verwalteten Arbeitsbereichen und anwendungseigenen Standards;
- benutzerweiten Context-Vorgaben und sichtbaren HeavenBase-LLM-Presets;
- typisierten Entitäten, Abfragen und berechneter Suche;
- seitenweisem HeavenBase-LLM-OCR mit begrenzten Dokument-Handles;
- einer Befehls-Registry, die über mehrere CLI-Backends bereitgestellt wird;
- aus einem HeavenBase-Toolkit erzeugten MCP-Werkzeugen; und
- einem gepackten Skill, der KI-Agenten den Anwendungsablauf vermittelt.

Direkte CLI- und Python-Übersetzungen verwenden das konfigurierte HeavenBase-Preset
über `LLMSession`; MCP-Hosts verwenden ihr eigenes konfiguriertes Modell.

Prüfungen für die Entwicklung:

```console
git clone https://github.com/Magolor/GlossWise.git
cd GlossWise
bash scripts/sync-env.bash
bash scripts/flake.bash --ci
bash scripts/test.bash
bash scripts/test.bash -m full
uv build
```

Siehe [CONTRIBUTING.md](CONTRIBUTING.md) für den Beitragsablauf und
[SECURITY.md](SECURITY.md) für die vertrauliche Meldung von Sicherheitslücken.

Aktuelle Grenzen: HeavenBase-Erweiterungen werden ausdrücklich installiert, aktivierte
Erweiterungen werden nicht deaktiviert, Schemamigrationen sind nicht automatisiert, und GlossWise
wählt weder ein Übersetzungsmodell aus noch verbirgt es eines.

## Zitieren

Wenn GlossWise deine Forschung oder dein Projekt unterstützt, zitiere die Software mit
[CITATION.cff](CITATION.cff) oder:

```bibtex
@software{glosswise_2026,
  author  = {Magolor},
  title   = {GlossWise: Terminology-safe translation for AI agents},
  year    = {2026},
  version = {0.1.0.5},
  url     = {https://github.com/Magolor/GlossWise}
}
```

GlossWise basiert auf [HeavenBase](https://ahvn.top).

## Lizenz

GlossWise ist unter der [MIT-Lizenz](LICENSE) verfügbar.
