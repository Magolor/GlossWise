# GlossWise

<p align="center">
  <a href="README.en.md">English</a> ·
  <a href="README.ar.md">العربية</a> ·
  <strong>中文</strong> ·
  <a href="README.fr.md">Français</a> ·
  <a href="README.ru.md">Русский</a> ·
  <a href="README.es.md">Español</a> ·
  <a href="README.de.md">Deutsch</a> ·
  <a href="README.ja.md">日本語</a>
</p>

<p align="center">
  <img src="docs/assets/glosswise-banner.png" alt="GlossWise — 面向 AI 智能体的术语安全翻译" width="100%">
</p>

<p align="center">
  <a href="https://github.com/Magolor/GlossWise/actions/workflows/ci.yml"><img src="https://github.com/Magolor/GlossWise/actions/workflows/ci.yml/badge.svg?branch=master" alt="持续集成"></a>
  <a href="https://www.python.org/"><img src="https://img.shields.io/badge/Python-3.10–3.13-3776AB" alt="Python 3.10 至 3.13"></a>
  <a href="https://ahvn.top"><img src="https://img.shields.io/badge/HeavenBase-0.1.2.1-6957E5" alt="HeavenBase 0.1.2.1"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-green.svg" alt="MIT 许可证"></a>
</p>

<p align="center">
  <a href="#install">安装</a> ·
  <a href="#connect-an-agent">连接智能体</a> ·
  <a href="#try-it-teach-once-translate-consistently">试用演示</a> ·
  <a href="#everyday-prompts">日常提示</a> ·
  <a href="#mcp-server">MCP 工具</a> ·
  <a href="#python-sdk">Python SDK</a>
</p>

GlossWise 存储已批准的术语、翻译规则和示例，随后为调用它的智能体或应用程序
准备一份精简的翻译简报。宿主智能体使用自己的模型翻译；
直接 CLI 则使用明确可见的 HeavenBase LLM 预设。

GlossWise 提供 CLI、MCP 服务器和 Python SDK。版本 `0.1.0.5`
支持 `heavenbase>=0.1.2.1`。

## <a id="install"></a> 安装

GlossWise 需要 Python 3.10–3.13。请直接从 GitHub 安装当前源码。
安装前，你可以[查看确切的智能体 Skill](SKILL.md)：

```console
python -m pip install "git+https://github.com/Magolor/GlossWise.git"
glosswise setup -l en -l zh
```

如需查看源码或参与贡献：

```console
git clone https://github.com/Magolor/GlossWise.git
cd GlossWise
python -m pip install .
glosswise setup -l en -l zh
```

`setup` 必须接收你常用的翻译语言并保存为全局默认值，
再以这些语言创建并激活 `default` 工作区，然后将
GlossWise 智能体 Skill 安装到：

- `~/.agents/skills/glosswise`
- `~/.claude/skills/glosswise`

公开的根目录 Skill 与 `setup` 安装的软件包副本会保持
逐字节完全一致。

工作区数据会自动托管在 `~/.glosswise/` 下。你无需
选择或公开数据库。新工作区会继承全局语言默认值；
可用 `glosswise config lang -l en -l <language>` 修改。

检查安装：

```console
glosswise ws ls
glosswise ws get
```

## <a id="connect-an-agent"></a> 连接智能体

`glosswise setup` 已安装通用版和 Claude 版 GlossWise Skill。
可从任何受支持的宿主连接同一个全局 MCP 服务器：

| 宿主 | 一次性设置 |
| --- | --- |
| [Claude Code](https://code.claude.com/docs/en/mcp) | `claude mcp add --scope user glosswise -- glosswise mcp` |
| [Codex](https://developers.openai.com/codex/mcp/) | `codex mcp add glosswise -- glosswise mcp` |
| [Cursor](https://docs.cursor.com/context/model-context-protocol) | 将 `glosswise mcp --json` 保存为 `~/.cursor/mcp.json`。 |
| [VS Code / Copilot](https://code.visualstudio.com/docs/copilot/chat/mcp-servers) | 在 `.vscode/mcp.json` 中添加 `servers.glosswise` stdio 项，命令为 `glosswise`，参数为 `["mcp"]`。 |
| [OpenCode](https://opencode.ai/docs/mcp-servers/) | 将下方本地 MCP 项添加到 `~/.config/opencode/opencode.json`。 |
| [OpenClaw](https://ahvn.top/quickstart/heavenbase-mcp#3-connect-your-agent) | 运行 `glosswise mcp --transport http`，再将 `mcp.servers.glosswise` 设为 `http://127.0.0.1:61055/mcp`，传输方式设为 `streamable-http`。 |
| [Hermes](https://ahvn.top/quickstart/heavenbase-mcp#3-connect-your-agent) | 运行 `glosswise mcp --transport http`，再将其 URL 添加到 `~/.hermes/config.yaml` 的 `mcp_servers.glosswise` 下。 |
| [LM Studio](https://lmstudio.ai/docs/app/mcp) | 打开 **Program/Developer → Install → Edit mcp.json**，粘贴 `glosswise mcp --json` 的输出。 |
| [Qwen Code](https://qwenlm.github.io/qwen-code-docs/en/users/features/mcp/) | `qwen mcp add --scope user glosswise glosswise mcp` |
| [HeavenBase](https://ahvn.top/quickstart/heavenbase-mcp#3-connect-your-agent) | 运行 `glosswise mcp --transport http`，再运行 `hb llm session --mcp http://127.0.0.1:61055/mcp`。 |

对于 [OpenCode](https://opencode.ai/docs/mcp-servers/)，请将以下内容添加到全局
`~/.config/opencode/opencode.json`：

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

使用宿主的 MCP 列表命令验证连接；若其文档要求，
请再重启智能体。

开始新对话并说：

```text
/glosswise 列出我的工作区，并告诉我当前激活的是哪一个。
```

现在，智能体可以代你创建工作区、管理术语、搜索术语并准备
翻译简报。你无需编写 JSON 或管理
数据库。一套 Skill 和一个 MCP 连接即可用于所有 GlossWise
工作区。

对于其他支持 stdio 的 MCP 客户端，可打印便携式 MCP 配置档：

```console
glosswise mcp --json
```

## <a id="try-it-teach-once-translate-consistently"></a> 试用：教一次，始终一致地翻译

本演示先由普通模型完成翻译，再用自然语言向 GlossWise 传授两项
术语决策，最后在全新的智能体会话中重复原始请求。
节选内容出自
[玛丽·雪莱的《弗兰肯斯坦》](https://www.gutenberg.org/cache/epub/42324/pg42324-images.html)，
这是一部已进入公版的早期科幻作品。

### 1. 创建工作区

请你的智能体执行：

```text
/glosswise 创建并选择一个名为 `frankenstein-lab` 的 GlossWise 工作区。
将其默认语言设置为英语、中文、法语、德语、俄语和日语。
```

也可以使用以下两条简短的 CLI 命令：

```console
glosswise ws create frankenstein-lab
glosswise ws lang -l en -l zh -l fr -l de -l ru -l ja
```

`ws create` 会自动选择新工作区。请为每个有序语言重复
`-l/--lang`。该集合会提醒智能体收集全部六种语言的首选形式，但不会
将这些语言变成硬性限制。

### 2. 在教 GlossWise 之前翻译

将这段文字发送给智能体：

```text
/glosswise 使用 `frankenstein-lab` 工作区。将下面这段文字翻译成
中文、法语、德语、俄语和日语。先在 GlossWise 中查找
相关指导，然后说明实际执行翻译的模型或宿主。

「那是在十一月一个阴沉的夜晚，我目睹了自己辛劳的成果。
怀着近乎痛苦的焦虑，我把赋予生命的器具聚集在身边，
以便将一簇存在之火注入
躺在我脚边的无生命之物。」
```

初次措辞取决于智能体使用的翻译模型。它可能选择
诸如「spark of being」→ `存在的火花`、
`étincelle de vie`、`Lebensfunken`、`искра жизни` 或 `命の火花` 这样的直译。

### 3. 通过对话传授两项决策

再发送一条消息：

```text
/glosswise 将以下内容保存为 `frankenstein-lab` 工作区中的有效
首选术语。这些目标形式是我的项目术语决策，并非对
小说官方译文的断言。

1. 「instruments of life」是指实验中使用的器具：
   中文 生命仪器；法语 instruments de vie；
   德语 Instrumente des Lebens；俄语 орудия жизни；
   日语 生命の器具。

2. 「spark of being」是指注入无生命物质、使其苏醒的本质：
   中文 生命之火；法语 étincelle d'existence；
   德语 Funke des Seins；俄语 искра бытия；
   日语 存在の火花。

同时保留英语源语言形式。在目标语言语法允许时精确使用首选术语；
否则，在不改变已批准概念的前提下进行词形变化。
两个记录都保存后告诉我。
```

智能体会处理结构化 CRUD 调用。如果所请求的工作区语言
缺少形式，已安装的 Skill 会指示它询问、提出一种形式供
确认，或者明确披露该形式由智能体生成。

### 4. 开始新会话并重复相同请求

结束当前对话并开始新的智能体会话。再次发送第 2 步中的
完全相同的提示——不要添加关于刚才所存术语的提醒：

```text
/glosswise 使用 `frankenstein-lab` 工作区。将下面这段文字翻译成
中文、法语、德语、俄语和日语。先在 GlossWise 中查找
相关指导，然后说明实际执行翻译的模型或宿主。

「那是在十一月一个阴沉的夜晚，我目睹了自己辛劳的成果。
怀着近乎痛苦的焦虑，我把赋予生命的器具聚集在身边，
以便将一簇存在之火注入
躺在我脚边的无生命之物。」
```

提示完全相同；只有持久化的 GlossWise 工作区发生了变化。
新会话必须重新获取该状态，而不能依赖对话记忆。现在可以看到
这项重要变化：

| 语言 | 基准翻译可能使用 | GlossWise 指导下的措辞 |
| --- | --- | --- |
| 中文 | `生命工具` · `存在的火花` | `生命仪器` · `生命之火` |
| 法语 | `instruments de la vie` · `étincelle de vie` | `instruments de vie` · `étincelle d'existence` |
| 德语 | `Werkzeuge des Lebens` · `Lebensfunken` | `Instrumente des Lebens` · `Funken des Seins`¹ |
| 俄语 | `инструменты жизни` · `искра жизни` | `орудия жизни` · `искру бытия`¹ |
| 日语 | `生命の道具` · `命の火花` | `生命の器具` · `存在の火花` |

¹ 智能体会改变标准首选形式的词形，使其适合这个句子。

<details>
<summary>一例成功的 GlossWise 指导结果</summary>

**中文**

> 那是十一月一个阴沉的夜晚，我目睹了自己辛劳的成果。怀着近乎痛苦的焦虑，我把生命仪器聚集在身边，想把生命之火注入躺在我脚边的无生命之物中。

**法语**

> Ce fut par une lugubre nuit de novembre que je contemplai l’accomplissement de mes travaux. Avec une anxiété qui confinait presque à l’agonie, je rassemblai autour de moi les instruments de vie afin d’insuffler une étincelle d'existence à la chose inanimée étendue à mes pieds.

**德语**

> Es war in einer trüben Novembernacht, als ich die Vollendung meiner Mühen erblickte. Mit einer Angst, die beinahe an Qual grenzte, versammelte ich die Instrumente des Lebens um mich, um dem leblosen Ding zu meinen Füßen einen Funken des Seins einzuhauchen.

**俄语**

> В мрачную ноябрьскую ночь я увидел завершение своих трудов. С тревогой, почти переходившей в агонию, я собрал вокруг себя орудия жизни, чтобы вдохнуть искру бытия в безжизненное создание, лежавшее у моих ног.

**日语**

> 十一月の陰鬱な夜、私は自らの労苦の成就を目の当たりにした。苦悶に近い不安を抱えながら、私は生命の器具を周囲に集め、足元に横たわる生命なきものへ存在の火花を吹き込もうとした。

</details>

这些句子并非由 GlossWise 生成，而是由所连接的智能体生成；GlossWise
让已批准的术语在生成之前可供检索和检查。

### 5. 日后查找和编辑

无需记录标识符：

```text
/glosswise 在 `frankenstein-lab` 中查找与火花有关的术语。用紧凑的
表格显示其首选形式。
```

然后使用自然语言编辑：

```text
/glosswise 仅将「spark of being」的日语首选形式更改为
`生命の火花`。其他所有语言保持不变，并显示保存后的记录。
```

这条完整的设置 → 创建 → 管理 → 重启 → 简报 → 搜索 → 编辑路径
已在安装好的 wheel 和两个独立的 stdio MCP 会话中通过
[`tests/test_quickstart.py`](https://github.com/Magolor/GlossWise/blob/master/tests/test_quickstart.py) 进行了测试。

## <a id="everyday-prompts"></a> 日常提示

连接后，日常工作可以始终在对话中完成。以下管理提示会进行
有意的更改；查询和翻译提示均为只读，除非其中
明确要求保存内容。

### 管理工作区和术语

- `/glosswise 创建并选择一个名为 <name> 的工作区。`
- `/glosswise 在工作区 <name> 中，将默认语言设置为英语、中文和日语。`
- `/glosswise 在工作区 <name> 中，将「rate limit」保存为有效首选术语，英语形式为「rate limit」、中文形式为「速率限制」、日语形式为「レート制限」。显示保存后的记录。`
- `/glosswise 在工作区 <name> 中查找「rate limit」。仅将其日语首选形式改为「速度制限」，保留其他所有字段和形式，然后显示更新后的记录。`
- `/glosswise 归档工作区 <name> 中的术语「rate limit」，使其不再出现在常规的有效术语检索中。更改前先征求我的同意。`

### 查找指导并翻译

- `/glosswise 在工作区 <name> 中查找与身份验证有关的有效术语。显示它们的英语、中文和日语首选与禁用形式。不要修改任何内容。`
- `/glosswise 在工作区 <name> 中查找将错误消息翻译成法语时使用的规则和示例。显示优先级、风格和冲突。不要修改任何内容。`
- `/glosswise 对照工作区 <name> 检查「超过此限制的请求会被拒绝。」列出匹配的术语和规则，不要翻译或保存任何内容。`
- `/glosswise 使用工作区 <name>。将「客户端会在速率限制重置后重试请求。」从英语翻译成中文和日语。为每种目标语言准备一份新的 GlossWise 翻译简报，应用有效的首选术语和规则，标记冲突，并说明实际执行翻译的模型或宿主。`
- `/glosswise 使用工作区 <name>。将下面的英语段落翻译成法语。先准备 GlossWise 翻译简报，然后显示译文，并附上一张紧凑表格，列出所使用的每个已存术语、规则或示例：<粘贴源文本>。`
- `/glosswise 对照工作区 <name> 审查这段法语译文。报告缺失的首选术语、禁用形式和冲突规则；除非我提出要求，否则不要重写或保存任何内容：<粘贴译文>。`

需要在终端中快速检查时，可使用 `glosswise ws ls`、`glosswise ws use <name>` 和
`glosswise ws get`，通常比对话更方便。

## 内置翻译、文件范围与 PDF OCR

直接翻译使用具名的 HeavenBase `LLMSession` 预设。每个结果都会
报告解析后的预设、网关、提供商、模型和模型 ID。预设选择与
不确定性处理行为可分别配置：

```console
glosswise config llm chat
glosswise config mode auto
glosswise translate "Run this query." -sl en -tl ja
glosswise translate "Run this query." -sl en -tl ja --preset chat
```

模式包括 `yolo`（直接翻译）、`elicit`（提出聚焦的术语
问题并提供选项）、`auto`（根据已有证据调整）、`explain`
（翻译并解释所有重要选择），以及带 `--prompt` 的 `custom`。
HeavenBase 通过 `hb.Prompt` 渲染系统提示，并解析具名预设。
使用 `chat` 可采用 HeavenBase 当前的快速聊天选择；也可固定
专用预设，而无需在 GlossWise 中重复提供商凭据：

```console
hb cfg set heavenbase.llm.presets.glosswise-translate.model deepseek-v4-flash
glosswise config llm glosswise-translate
```

`scan`、`brief` 和 `translate` 接受从 1 开始且包含端点的 `--start-line`
与 `--end-line` 范围，适用于内联文本、stdin 和 `@file` 输入。授权后的
本地 MCP 配置档提供等价的文件工具。

对于 PDF，请先授权其目录，再通过已配置的 HeavenBase LLM 预设
只识别所需页面，并使用简短的 `gw-...` 句柄浏览保留的
逐页文本：

```console
glosswise ws files -r /absolute/path/to/documents
glosswise pdf ocr /absolute/path/to/documents/manual.pdf --start-page 4 --end-page 8
glosswise doc read gw-0123456789ab 4 --start-line 1 --end-line 80
glosswise doc rm gw-0123456789ab
```

`ws files` 会保存工作区级的读取许可列表；每个目录重复使用一次
`-r/--root`。它不会上传、复制或注册文件。仅当文件需要其他严格文本
编码时，才重复使用 `-e/--encoding`；
默认允许 UTF-8。

GlossWise 每次只渲染并识别一页，随后立即删除页面图像。
可疑的长段重复会被标记，而不会静默删除。
请用 `hb cfg set heavenbase.llm.presets.ocr-local.<field-or-path> <value>`
配置默认的 `ocr-local`；支持 `desc`、`gateway`、`provider`、
`model` 和 `default_args`，也可用 `glosswise config ocr <preset>` 选择其他预设。

## <a id="mcp-server"></a> MCP 服务器

### 本地 stdio

大多数桌面客户端和编码智能体客户端应使用：

```console
glosswise mcp --json
```

生成的子进程会启动完整服务器，并提供读取、CRUD、Skill 和
工作区管理工具。MCP 客户端的 `PATH` 中必须包含
`glosswise` 可执行文件。

### 本地 HTTP

如需运行长期驻留的流式 HTTP 服务器：

```console
glosswise mcp --transport http
```

默认绑定 `127.0.0.1:61055`，并在
`http://127.0.0.1:61055/mcp` 提供 MCP 服务。使用以下命令打印匹配的客户端 MCP 配置档：

```console
glosswise mcp --json --transport http
```

需要时可选择其他本地端点：

```console
glosswise mcp --transport http --host 127.0.0.1 --port 61056
```

GlossWise 不会添加网络身份验证。请将服务器保留在环回
主机上，除非有其他可信层提供身份验证和传输
安全保障。

### MCP 工具

数据和上下文工具接受可选的 `workspace_id`。省略时，
GlossWise 会依次使用激活的工作区和托管的默认工作区。

| 工具 | 用途 | `read` | `full` | `local` |
| --- | --- | :---: | :---: | :---: |
| `glosswise_workspace_info` | 显示工作区功能和语言提示。 | ✓ | ✓ | ✓ |
| `glosswise_prepare_translation` | 为源文本构建翻译简报。 | ✓ | ✓ | ✓ |
| `glosswise_search_terms` | 搜索术语。 | ✓ | ✓ | ✓ |
| `glosswise_search_rules` | 搜索规则。 | ✓ | ✓ | ✓ |
| `glosswise_search_examples` | 搜索示例。 | ✓ | ✓ | ✓ |
| `glosswise_scan_text` | 扫描文本中的术语和规则匹配项。 | ✓ | ✓ | ✓ |
| `glosswise_list_records` | 列出术语、规则或示例。 | ✓ | ✓ | ✓ |
| `glosswise_get_record` | 按对象标识符获取一条记录。 | ✓ | ✓ | ✓ |
| `glosswise_put_term` | 创建或更新术语及其形式。 | — | ✓ | ✓ |
| `glosswise_put_rule` | 创建或更新规则。 | — | ✓ | ✓ |
| `glosswise_put_example` | 创建或更新示例。 | — | ✓ | ✓ |
| `glosswise_archive` | 归档一条记录。 | — | ✓ | ✓ |
| `glosswise_list_workspaces` | 列出工作区。 | ✓ | ✓ | ✓ |
| `glosswise_get_workspace` | 获取一条已脱敏的工作区记录。 | ✓ | ✓ | ✓ |
| `glosswise_create_workspace` | 创建托管工作区。 | — | ✓ | ✓ |
| `glosswise_set_workspace_languages` | 设置工作区语言提示。 | — | ✓ | ✓ |
| `glosswise_activate_workspace` | 选择激活的工作区。 | — | ✓ | ✓ |
| `glosswise_deactivate_workspace` | 清除激活选择。 | — | ✓ | ✓ |
| `glosswise_remove_workspace` | 注销工作区。 | — | ✓ | ✓ |
| `glosswise_open_workspace` | 打开工作区并显示其功能。 | ✓ | ✓ | ✓ |
| `glosswise_health_workspace` | 检查注册表和运行时健康状况。 | ✓ | ✓ | ✓ |
| `glosswise_read_skill` | 读取软件包中的智能体指令。 | ✓ | ✓ | ✓ |
| `glosswise_scan_file` | 扫描已获授权的服务器本地文本文件。 | — | — | ✓ |
| `glosswise_prepare_file` | 从获授权文本文件范围构建翻译简报。 | — | — | ✓ |
| `glosswise_ocr_pdf` | 将获授权 PDF 页面识别为短句柄。 | — | — | ✓ |
| `glosswise_list_documents` | 列出临时 OCR 文档句柄。 | — | — | ✓ |
| `glosswise_get_document` | 查看一份 OCR 文档清单。 | — | — | ✓ |
| `glosswise_read_document` | 读取一页 OCR 文本的有界行范围。 | — | — | ✓ |
| `glosswise_remove_document` | 删除一份临时 OCR 文档。 | — | — | ✓ |

### MCP 配置档

MCP 配置档控制工具的公开范围，而不控制工作区内容或已安装的
Skill 文件：

| 配置档 | 确切范围 | 预期用途 |
| --- | --- | --- |
| `full` | `full` 列中勾选的 22 个工具。 | 默认配置档。支持查找、翻译简报、CRUD、Skill 检查和工作区管理。直接使用 `glosswise mcp` 和 `glosswise mcp --json` 会选择此配置档。 |
| `read` | `read` 列中勾选的 13 个工具。 | 用于只读术语/上下文操作和工作区检查。无法管理记录、更改选择或管理工作区。 |
| `local` | 全部 22 个 `full` 工具，外加七个授权的本地文档工具。 | 用于有界文本范围和 PDF OCR 的高级完全访问服务器。仅选择此配置档不会授予文件访问权限；请先授权根目录。 |

`glosswise setup` 会安装一个与配置档无关的 Skill。Skill 本身不会
选择配置档：由所连接的 MCP 服务器决定智能体可以调用哪些工具。
常规设置使用 `full`，这是唯一一个支持 Skill 所教授的
全部管理和翻译工作流的非本地配置档。

如需更改现有安装，请保留已安装的 Skill，只更改
智能体配置中的 MCP 服务器命令，然后重启或重新连接
智能体：

```console
glosswise mcp                 # full (default)
glosswise mcp --profile read  # read-only
glosswise mcp --profile local # full plus authorized text/PDF tools
```

使用 `glosswise mcp --json --profile <profile>` 生成替换用的客户端
JSON。切换配置档时无需重新运行 `glosswise setup`。
改回直接使用 `glosswise mcp` 即可恢复默认的 `full` 范围。

每个工具都会返回带版本号的 JSON 信封。智能体应先检查 `error`、
`warnings`、`conflicts` 和 `truncated`，再使用 `items`。

## CLI 参考

| 任务 | 命令 | 其他可接受形式 |
| --- | --- | --- |
| 列出工作区 | `glosswise ws ls` | `ws list` |
| 检查工作区 | `glosswise ws get [<name>]` | — |
| 创建工作区 | `glosswise ws create [<name>]` | — |
| 选择工作区 | `glosswise ws use <name>` | `ws activate`, `ws act` |
| 清除选择 | `glosswise ws deact` | `ws deactivate` |
| 注销工作区 | `glosswise ws rm <name>` | `ws unset`, `ws remove` |
| 显示全局配置 | `glosswise config get` | — |
| 设置全局语言默认值 | `glosswise config lang -l en -l <language>` | `config languages` |
| 设置翻译行为 | `glosswise config mode <mode>` | — |
| 设置翻译 LLM 预设 | `glosswise config llm <preset>` | — |
| 设置语言提示 | `glosswise ws lang -l en -l <language>` | `ws languages` |
| 授权本地根目录 | `glosswise ws files -r <directory>` | — |
| 创建或更新数据 | `glosswise term set @term.json` | `term put` |
| 获取一条记录 | `glosswise term get <object-id>` | — |
| 列出数据 | `glosswise term ls` | `term list` |
| 搜索数据 | `glosswise term search "query"` | — |
| 归档数据 | `glosswise term archive <object-id>` | — |
| 扫描段落 | `glosswise scan "text"` | — |
| 准备上下文 | `glosswise brief "text"` | — |
| 通过 LLMSession 翻译 | `glosswise translate "text"` | — |
| 识别 PDF 页面 | `glosswise pdf ocr <path>` | — |
| 浏览 OCR 文本 | `glosswise doc read <handle> <page>` | — |

要使用相同的 set/get/list/search/archive 工作流，请将 `term` 替换为
`rule` 或 `example`。运行 `glosswise --help` 或
`glosswise <group> --help` 可查看完整的命令范围。

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

`GlossWiseApp.open()` 使用激活的工作区，或在配置全局语言后
创建托管的默认工作区。
使用 `GlossWiseApp.create("<name>")` 创建明确命名的托管工作区；
需要在工作区不存在时引发错误，请使用 `GlossWiseApp.load()`。已拥有
HeavenBase 工作区的应用程序可以直接使用 `workspace.glosswise`。

## 工作原理

1. 智能体通过 MCP、CLI 或 Python SDK 连接。
2. GlossWise 解析所请求的工作区，或使用激活/默认工作区。
3. 它检索相关的术语、规则和示例。
4. `brief` 对这些证据进行排序，并将其连同警告和冲突一起打包。
5. 宿主智能体执行翻译，或由 `translate` 使用 `hb.Prompt` 管理的
   契约和明确可见的预设调用 HeavenBase `LLMSession`。
6. 调用方可以扫描建议译文，或将获授权的 PDF 页面识别为
   有界的临时逐页文本。

GlossWise 将存储和术语策略封装在面向任务的操作之后；
智能体无需通用数据库访问权限。

## 面向开发者

GlossWise 是一个演示项目，展示简洁的独立应用程序如何使用
HeavenBase。它展示了以下实际优势：

- 挂载在 `workspace.glosswise` 上的模块化扩展；
- 托管工作区和应用程序自有的默认值；
- Context 级用户默认值与明确可见的 HeavenBase LLM 预设；
- 类型化实体、查询和计算式检索；
- 通过 HeavenBase LLM 逐页 OCR，并提供有界文档句柄；
- 通过多个 CLI 后端公开的一套命令注册表；
- 从 HeavenBase 工具包生成的 MCP 工具；以及
- 用于教会智能体应用程序工作流的软件包化 Skill。

直接 CLI 和 Python 翻译通过 `LLMSession` 使用已配置的
HeavenBase 预设；MCP 宿主使用其自身配置的模型。

开发检查：

```console
git clone https://github.com/Magolor/GlossWise.git
cd GlossWise
bash scripts/sync-env.bash
bash scripts/flake.bash --ci
bash scripts/test.bash
bash scripts/test.bash -m full
uv build
```

有关贡献工作流，请参阅 [CONTRIBUTING.md](CONTRIBUTING.md)；
有关私下报告安全漏洞的信息，请参阅 [SECURITY.md](SECURITY.md)。

当前边界：HeavenBase 扩展需明确安装，已启用的
扩展不会被禁用，模式迁移不会自动完成，并且 GlossWise
不选择也不隐藏翻译模型。

## 引用

如果 GlossWise 为你的研究或项目提供了帮助，请使用
[CITATION.cff](CITATION.cff) 或以下内容引用本软件：

```bibtex
@software{glosswise_2026,
  author  = {Magolor},
  title   = {GlossWise: Terminology-safe translation for AI agents},
  year    = {2026},
  version = {0.1.0.5},
  url     = {https://github.com/Magolor/GlossWise}
}
```

GlossWise 构建于 [HeavenBase](https://ahvn.top) 之上。

## 许可证

GlossWise 根据 [MIT 许可证](LICENSE) 提供。
