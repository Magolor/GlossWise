# GlossWise

<p align="center">
  <a href="README.en.md">English</a> ·
  <a href="README.ar.md">العربية</a> ·
  <a href="README.zh.md">中文</a> ·
  <a href="README.fr.md">Français</a> ·
  <a href="README.ru.md">Русский</a> ·
  <a href="README.es.md">Español</a> ·
  <a href="README.de.md">Deutsch</a> ·
  <strong>日本語</strong>
</p>

<p align="center">
  <img src="docs/assets/glosswise-banner.png" alt="GlossWise — AIエージェントのための用語を安全に扱う翻訳" width="100%">
</p>

<p align="center">
  <a href="https://github.com/Magolor/GlossWise/actions/workflows/ci.yml"><img src="https://github.com/Magolor/GlossWise/actions/workflows/ci.yml/badge.svg?branch=master" alt="継続的インテグレーション"></a>
  <a href="https://www.python.org/"><img src="https://img.shields.io/badge/Python-3.10–3.13-3776AB" alt="Python 3.10から3.13"></a>
  <a href="https://ahvn.top"><img src="https://img.shields.io/badge/HeavenBase-0.1.2.1-6957E5" alt="HeavenBase 0.1.2.1"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-green.svg" alt="MITライセンス"></a>
</p>

<p align="center">
  <a href="#install">インストール</a> ·
  <a href="#connect-an-agent">AIエージェントを接続</a> ·
  <a href="#try-it-teach-once-translate-consistently">デモを試す</a> ·
  <a href="#everyday-prompts">日常的なプロンプト</a> ·
  <a href="#mcp-server">MCPツール</a> ·
  <a href="#python-sdk">Python SDK</a>
</p>

GlossWiseは、承認済みの用語、翻訳ルール、用例を保存し、呼び出し元の
AIエージェントやアプリケーション向けに簡潔な翻訳ブリーフを作成します。ホストエージェントは
自身のモデルで翻訳し、直接CLIは可視のHeavenBase LLMプリセットを使用します。

GlossWiseはCLI、MCPサーバー、Python SDKとして利用できます。バージョン`0.1.0.5`は
`heavenbase>=0.1.2.1`をサポートします。

## <a id="install"></a> インストール

GlossWiseにはPython 3.10–3.13が必要です。現在のソースを
GitHubから直接インストールしてください。インストール前に[実際のAIエージェントSkill](SKILL.md)を確認できます。

```console
python -m pip install "git+https://github.com/Magolor/GlossWise.git"
glosswise setup -l en -l zh
```

ソースの確認やコントリビュートを行う場合：

```console
git clone https://github.com/Magolor/GlossWise.git
cd GlossWise
python -m pip install .
glosswise setup -l en -l zh
```

`setup`は普段翻訳する言語を必須引数としてグローバル既定値に保存し、
その言語で`default`ワークスペースを作成して有効化してから、
GlossWise AIエージェントSkillを次の場所にインストールします。

- `~/.agents/skills/glosswise`
- `~/.claude/skills/glosswise`

公開されているルートのSkillと`setup`がインストールするパッケージ版は、
バイト単位で同一に保たれます。

ワークスペースのデータは`~/.glosswise/`配下で自動的に管理されます。
データベースを選択したり公開したりする必要はありません。新しいワークスペースは
グローバル言語を継承し、`glosswise config lang -l en -l <language>`で変更できます。

インストールを確認します。

```console
glosswise ws ls
glosswise ws get
```

## <a id="connect-an-agent"></a> AIエージェントを接続

`glosswise setup`は共通版とClaude版のGlossWise Skillをインストール済みです。
対応する任意のホストから同じグローバルMCPサーバーへ接続します。

| ホスト | 1回限りの設定 |
| --- | --- |
| [Claude Code](https://code.claude.com/docs/en/mcp) | `claude mcp add --scope user glosswise -- glosswise mcp` |
| [Codex](https://developers.openai.com/codex/mcp/) | `codex mcp add glosswise -- glosswise mcp` |
| [Cursor](https://docs.cursor.com/context/model-context-protocol) | `glosswise mcp --json`を`~/.cursor/mcp.json`として保存します。 |
| [VS Code / Copilot](https://code.visualstudio.com/docs/copilot/chat/mcp-servers) | `.vscode/mcp.json`に、コマンド`glosswise`、引数`["mcp"]`のstdioエントリ`servers.glosswise`を追加します。 |
| [OpenCode](https://opencode.ai/docs/mcp-servers/) | 下記のローカルMCPエントリを`~/.config/opencode/opencode.json`に追加します。 |
| [OpenClaw](https://ahvn.top/quickstart/heavenbase-mcp#3-connect-your-agent) | `glosswise mcp --transport http`を実行し、`mcp.servers.glosswise`を`http://127.0.0.1:61055/mcp`、トランスポートを`streamable-http`に設定します。 |
| [Hermes](https://ahvn.top/quickstart/heavenbase-mcp#3-connect-your-agent) | `glosswise mcp --transport http`を実行し、`~/.hermes/config.yaml`の`mcp_servers.glosswise`にそのURLを追加します。 |
| [LM Studio](https://lmstudio.ai/docs/app/mcp) | **Program/Developer → Install → Edit mcp.json**を開き、`glosswise mcp --json`の出力を貼り付けます。 |
| [Qwen Code](https://qwenlm.github.io/qwen-code-docs/en/users/features/mcp/) | `qwen mcp add --scope user glosswise glosswise mcp` |
| [HeavenBase](https://ahvn.top/quickstart/heavenbase-mcp#3-connect-your-agent) | `glosswise mcp --transport http`を実行してから、`hb llm session --mcp http://127.0.0.1:61055/mcp`を実行します。 |

[OpenCode](https://opencode.ai/docs/mcp-servers/)では、次の内容をグローバルな
`~/.config/opencode/opencode.json`に追加します。

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

ホストのMCP一覧コマンドで接続を確認し、ドキュメントで
必要とされている場合はAIエージェントを再起動します。

新しいチャットを開始し、次のように伝えます。

```text
/glosswise ワークスペースの一覧と、現在有効なワークスペースを教えてください。
```

これでAIエージェントは、ワークスペースの作成、用語の整備と検索、
翻訳ブリーフの作成を代行できます。JSONを書いたり
データベースを管理したりする必要はありません。1つのSkillと1つのMCP接続で、
すべてのGlossWiseワークスペースを扱えます。

stdio対応の別のMCPクライアントでは、移植可能なMCPプロファイルを出力します。

```console
glosswise mcp --json
```

## <a id="try-it-teach-once-translate-consistently"></a> 試してみる：一度教えれば、一貫した翻訳に

このデモでは、まず通常のモデル翻訳を行い、自然言語でGlossWiseに2つの
用語上の決定を教えてから、新しいAIエージェントセッションで元の依頼を
繰り返します。引用文は
[メアリー・シェリーの『フランケンシュタイン』](https://www.gutenberg.org/cache/epub/42324/pg42324-images.html)からのもので、
パブリックドメインとなっている初期のSF作品です。

### 1. ワークスペースを開始

AIエージェントに次のように依頼します。

```text
/glosswise `frankenstein-lab`という名前のGlossWiseワークスペースを作成して選択してください。
デフォルト言語を英語、中国語、フランス語、ドイツ語、ロシア語、日本語に設定してください。
```

または、次の2つの短いCLIコマンドを使用します。

```console
glosswise ws create frankenstein-lab
glosswise ws lang -l en -l zh -l fr -l de -l ru -l ja
```

`ws create`は新しいワークスペースを自動的に選択します。順序付きの各言語に
`-l/--lang`を繰り返します。この集合は6言語すべての優先形式の収集を促しますが、
対応言語を強制的に制限するものではありません。

### 2. GlossWiseに教える前に翻訳

次の段落をAIエージェントに送ります。

```text
/glosswise `frankenstein-lab`ワークスペースを使用してください。次の段落を
中国語、フランス語、ドイツ語、ロシア語、日本語に翻訳してください。まずGlossWiseで
関連する指針を確認し、実際に翻訳したモデルまたはホストを明示してください。

「それは十一月の陰鬱な夜だった。私は自らの労苦の成就を目の当たりにした。
苦悶に近い不安を抱えながら、私は
生命を生み出す器具を周囲に集め、存在の火花を
足元に横たわる生命なきものへ吹き込もうとした。」
```

最初の表現はAIエージェントの翻訳モデルによって変わります。
「spark of being」→ `存在的火花`、
`étincelle de vie`、`Lebensfunken`、`искра жизни`、`命の火花`などの直訳を選ぶ場合があります。

### 3. 会話で2つの決定を教える

もう1つメッセージを送ります。

```text
/glosswise 次の語を`frankenstein-lab`ワークスペースの有効な
優先用語として保存してください。対象言語の形式は私のプロジェクトにおける用語上の決定であり、
小説の公式翻訳についての主張ではありません。

1. 「instruments of life」は実験で使用される器具を意味します。
   中国語 生命仪器、フランス語 instruments de vie、
   ドイツ語 Instrumente des Lebens、ロシア語 орудия жизни、
   日本語 生命の器具。

2. 「spark of being」は生命のない物質に与えられる生命の本質を意味します。
   中国語 生命之火、フランス語 étincelle d'existence、
   ドイツ語 Funke des Seins、ロシア語 искра бытия、
   日本語 存在の火花。

英語の原語形式も保持してください。対象言語の文法が許す場合は優先用語を厳密に使用し、
そうでない場合は、承認済みの概念を変えずに
語形を変化させてください。両方のレコードが保存されたら知らせてください。
```

構造化されたCRUD呼び出しはAIエージェントが処理します。指定されたワークスペース言語の
形式がない場合、インストール済みのSkillは、質問するか、確認用の形式を提案するか、
AIエージェントが生成した形式であることを明確に開示するよう指示します。

### 4. 新しいセッションで同じ依頼を繰り返す

現在のチャットを終了して新しいAIエージェントセッションを開始します。手順2の
まったく同じプロンプトをもう一度送ります。保存した用語についてのリマインダーは追加しないでください。

```text
/glosswise `frankenstein-lab`ワークスペースを使用してください。次の段落を
中国語、フランス語、ドイツ語、ロシア語、日本語に翻訳してください。まずGlossWiseで
関連する指針を確認し、実際に翻訳したモデルまたはホストを明示してください。

「それは十一月の陰鬱な夜だった。私は自らの労苦の成就を目の当たりにした。
苦悶に近い不安を抱えながら、私は
生命を生み出す器具を周囲に集め、存在の火花を
足元に横たわる生命なきものへ吹き込もうとした。」
```

プロンプトは同一で、変更されたのは永続化されたGlossWiseワークスペースだけです。
新しいセッションはチャットの記憶に頼らず、その状態を取得する必要があります。
重要な変化が次のように表れます。

| 言語 | ベースラインで使われる可能性のある表現 | GlossWiseの指針に沿った表現 |
| --- | --- | --- |
| 中国語 | `生命工具` · `存在的火花` | `生命仪器` · `生命之火` |
| フランス語 | `instruments de la vie` · `étincelle de vie` | `instruments de vie` · `étincelle d'existence` |
| ドイツ語 | `Werkzeuge des Lebens` · `Lebensfunken` | `Instrumente des Lebens` · `Funken des Seins`¹ |
| ロシア語 | `инструменты жизни` · `искра жизни` | `орудия жизни` · `искру бытия`¹ |
| 日本語 | `生命の道具` · `命の火花` | `生命の器具` · `存在の火花` |

¹ AIエージェントは、文に合わせて標準の優先形式を語形変化させます。

<details>
<summary>GlossWiseの指針に沿った成功例</summary>

**中国語**

> 那是十一月一个阴沉的夜晚，我目睹了自己辛劳的成果。怀着近乎痛苦的焦虑，我把生命仪器聚集在身边，想把生命之火注入躺在我脚边的无生命之物中。

**フランス語**

> Ce fut par une lugubre nuit de novembre que je contemplai l’accomplissement de mes travaux. Avec une anxiété qui confinait presque à l’agonie, je rassemblai autour de moi les instruments de vie afin d’insuffler une étincelle d'existence à la chose inanimée étendue à mes pieds.

**ドイツ語**

> Es war in einer trüben Novembernacht, als ich die Vollendung meiner Mühen erblickte. Mit einer Angst, die beinahe an Qual grenzte, versammelte ich die Instrumente des Lebens um mich, um dem leblosen Ding zu meinen Füßen einen Funken des Seins einzuhauchen.

**ロシア語**

> В мрачную ноябрьскую ночь я увидел завершение своих трудов. С тревогой, почти переходившей в агонию, я собрал вокруг себя орудия жизни, чтобы вдохнуть искру бытия в безжизненное создание, лежавшее у моих ног.

**日本語**

> 十一月の陰鬱な夜、私は自らの労苦の成就を目の当たりにした。苦悶に近い不安を抱えながら、私は生命の器具を周囲に集め、足元に横たわる生命なきものへ存在の火花を吹き込もうとした。

</details>

これらの文を生成したのはGlossWiseではなく、接続されたAIエージェントです。GlossWiseは
生成前に承認済みの用語を取得して確認できるようにしました。

### 5. 後から検索して編集

レコード識別子は必要ありません。

```text
/glosswise `frankenstein-lab`で火花に関する用語を検索してください。優先
形式を簡潔な表で表示してください。
```

続いて、自然な言葉で編集します。

```text
/glosswise 「spark of being」の日本語の優先形式だけを
`生命の火花`に変更してください。他のすべての言語は変更せず、保存されたレコードを表示してください。
```

この一連のセットアップ → 作成 → 整備 → 再起動 → ブリーフ → 検索 → 編集フローは、
インストール済みのwheelと2つの独立したstdio MCPセッションに対して
[`tests/test_quickstart.py`](https://github.com/Magolor/GlossWise/blob/master/tests/test_quickstart.py)でテストされています。

## <a id="everyday-prompts"></a> 日常的なプロンプト

接続後の日常作業はチャットだけで完結します。以下の管理用プロンプトは
意図的な変更を行います。照会と翻訳用のプロンプトは、何かを保存するよう
明示的に求めない限り、読み取り専用です。

### ワークスペースと用語を管理

- `/glosswise <name>という名前のワークスペースを作成して選択してください。`
- `/glosswise ワークスペース<name>のデフォルト言語を英語、中国語、日本語に設定してください。`
- `/glosswise ワークスペース<name>で、「rate limit」を有効な優先用語として、英語「rate limit」、中国語「速率限制」、日本語「レート制限」で保存してください。保存されたレコードを表示してください。`
- `/glosswise ワークスペース<name>で「rate limit」を検索してください。日本語の優先形式だけを「速度制限」に変更し、他のすべてのフィールドと形式は保持して、更新後のレコードを表示してください。`
- `/glosswise ワークスペース<name>の用語「rate limit」をアーカイブし、通常の有効用語検索から除外してください。変更する前に確認を求めてください。`

### 指針を検索して翻訳

- `/glosswise ワークスペース<name>で認証に関連する有効な用語を検索してください。英語、中国語、日本語の優先形式と禁止形式を表示してください。何も変更しないでください。`
- `/glosswise ワークスペース<name>でエラーメッセージをフランス語に翻訳するためのルールと用例を検索してください。優先度、スタイル、競合を表示してください。何も変更しないでください。`
- `/glosswise 「この制限を超えるリクエストは拒否されます。」をワークスペース<name>と照合してください。翻訳や保存は行わず、一致した用語とルールを一覧表示してください。`
- `/glosswise ワークスペース<name>を使用してください。「クライアントはレート制限がリセットされた後にリクエストを再試行します。」を英語から中国語と日本語に翻訳してください。各対象言語について新しいGlossWise翻訳ブリーフを作成し、有効な優先用語とルールを適用して競合を示し、実際に翻訳したモデルまたはホストを明示してください。`
- `/glosswise ワークスペース<name>を使用してください。次の英語の文章をフランス語に翻訳してください。まずGlossWise翻訳ブリーフを作成し、次に翻訳を示した後、使用した保存済みの用語、ルール、用例をすべて簡潔な表で示してください：<原文を貼り付け>。`
- `/glosswise このフランス語訳をワークスペース<name>と照合してレビューしてください。不足している優先用語、禁止形式、競合するルールを報告し、依頼しない限り書き換えも保存もしないでください：<翻訳を貼り付け>。`

チャットよりもターミナルで素早く確認したい場合は、`glosswise ws ls`、`glosswise ws use <name>`、
`glosswise ws get`を使用します。

## 組み込み翻訳、ファイル範囲、PDF OCR

直接翻訳は名前付きのHeavenBase `LLMSession`プリセットを使用します。
各結果には解決後のプリセット、ゲートウェイ、プロバイダー、モデル、
モデルIDが含まれます。プリセットと慎重さは個別に選択できます。

```console
glosswise config llm chat
glosswise config mode auto
glosswise translate "Run this query." -sl en -tl ja
glosswise translate "Run this query." -sl en -tl ja --preset chat
```

モードは`yolo`（すぐ翻訳）、`elicit`（選択肢付きの用語質問）、
`auto`（証拠に応じて調整）、`explain`（翻訳とすべての重要な
選択の説明）、および`--prompt`付きの`custom`です。
HeavenBaseは`hb.Prompt`でシステムプロンプトを描画し、指定プリセットを
解決します。`chat`で現在の高速チャット選択を使うか、プロバイダー
資格情報を重複させず専用プリセットを固定できます。

```console
hb cfg set heavenbase.llm.presets.glosswise-translate.model deepseek-v4-flash
glosswise config llm glosswise-translate
```

`scan`、`brief`、`translate`は、インラインテキスト、stdin、`@file`に対して
1始まりで両端を含む`--start-line`と`--end-line`の範囲を受け付けます。許可済みの
ローカルMCPプロファイルには同等のファイルツールがあります。

PDFではディレクトリを許可し、設定済みのHeavenBase LLMプリセットで
必要なページだけをOCRし、短い`gw-...`ハンドルを使って保持された
ページごとのテキストを閲覧します。

```console
glosswise ws files -r /absolute/path/to/documents
glosswise pdf ocr /absolute/path/to/documents/manual.pdf --start-page 4 --end-page 8
glosswise doc read gw-0123456789ab 4 --start-line 1 --end-line 80
glosswise doc rm gw-0123456789ab
```

`ws files`はワークスペース単位の読み取り許可リストを保存します。
ディレクトリごとに`-r/--root`を繰り返してください。ファイルのアップロード、
コピー、登録は行いません。追加の厳密なテキストエンコーディングが必要な
場合のみ`-e/--encoding`を繰り返します。UTF-8は既定で許可されます。

GlossWiseは1ページずつ描画してOCRし、ページ画像を直ちに削除します。
疑わしい長文の反復は黙って削除せず警告します。既定の`ocr-local`は
`hb cfg set
heavenbase.llm.presets.ocr-local.<field-or-path> <value>`で設定します。
設定項目は`desc`、`gateway`、`provider`、`model`、`default_args`で、別のプリセットは`glosswise config ocr <preset>`で選びます。

## <a id="mcp-server"></a> MCPサーバー

### ローカルstdio

ほとんどのデスクトップクライアントとコーディングAIエージェントクライアントでは、次を使用します。

```console
glosswise mcp --json
```

生成された子プロセスは、読み取り、CRUD、Skill、ワークスペース管理
ツールを備えた完全なサーバーを起動します。MCPクライアントの
`PATH`に`glosswise`実行ファイルが存在する必要があります。

### ローカルHTTP

長時間稼働するStreamable HTTPサーバーを実行するには：

```console
glosswise mcp --transport http
```

デフォルトでは`127.0.0.1:61055`にバインドし、
`http://127.0.0.1:61055/mcp`でMCPを提供します。対応するクライアントMCPプロファイルを次のコマンドで出力します。

```console
glosswise mcp --json --transport http
```

必要に応じて別のローカルエンドポイントを選択します。

```console
glosswise mcp --transport http --host 127.0.0.1 --port 61056
```

GlossWiseはネットワーク認証を追加しません。別の信頼できるレイヤーが認証と
通信のセキュリティを提供しない限り、サーバーはループバック
ホスト上に維持してください。

### MCPツール

データツールとコンテキストツールは、任意の`workspace_id`を受け取ります。省略すると、
GlossWiseは有効なワークスペース、次に管理対象のデフォルトを使用します。

| ツール | 用途 | `read` | `full` | `local` |
| --- | --- | :---: | :---: | :---: |
| `glosswise_workspace_info` | ワークスペースの機能と言語ヒントを表示します。 | ✓ | ✓ | ✓ |
| `glosswise_prepare_translation` | 原文の翻訳ブリーフを作成します。 | ✓ | ✓ | ✓ |
| `glosswise_search_terms` | 用語を検索します。 | ✓ | ✓ | ✓ |
| `glosswise_search_rules` | ルールを検索します。 | ✓ | ✓ | ✓ |
| `glosswise_search_examples` | 用例を検索します。 | ✓ | ✓ | ✓ |
| `glosswise_scan_text` | テキスト内の用語とルールの一致を走査します。 | ✓ | ✓ | ✓ |
| `glosswise_list_records` | 用語、ルール、用例を一覧表示します。 | ✓ | ✓ | ✓ |
| `glosswise_get_record` | オブジェクトIDで1件のレコードを取得します。 | ✓ | ✓ | ✓ |
| `glosswise_put_term` | 用語とその形式を作成または更新します。 | — | ✓ | ✓ |
| `glosswise_put_rule` | ルールを作成または更新します。 | — | ✓ | ✓ |
| `glosswise_put_example` | 用例を作成または更新します。 | — | ✓ | ✓ |
| `glosswise_archive` | 1件のレコードをアーカイブします。 | — | ✓ | ✓ |
| `glosswise_list_workspaces` | ワークスペースを一覧表示します。 | ✓ | ✓ | ✓ |
| `glosswise_get_workspace` | マスキング済みのワークスペースレコードを1件取得します。 | ✓ | ✓ | ✓ |
| `glosswise_create_workspace` | 管理対象ワークスペースを作成します。 | — | ✓ | ✓ |
| `glosswise_set_workspace_languages` | ワークスペースの言語ヒントを設定します。 | — | ✓ | ✓ |
| `glosswise_activate_workspace` | 有効なワークスペースを選択します。 | — | ✓ | ✓ |
| `glosswise_deactivate_workspace` | 有効な選択を解除します。 | — | ✓ | ✓ |
| `glosswise_remove_workspace` | ワークスペースの登録を解除します。 | — | ✓ | ✓ |
| `glosswise_open_workspace` | ワークスペースを開き、その機能を表示します。 | ✓ | ✓ | ✓ |
| `glosswise_health_workspace` | レジストリとランタイムの状態を検査します。 | ✓ | ✓ | ✓ |
| `glosswise_read_skill` | パッケージに含まれるAIエージェント向け指示を読み取ります。 | ✓ | ✓ | ✓ |
| `glosswise_scan_file` | 許可されたサーバーローカルのテキストファイルを走査します。 | — | — | ✓ |
| `glosswise_prepare_file` | 許可済みテキストファイル範囲からブリーフを作成します。 | — | — | ✓ |
| `glosswise_ocr_pdf` | 許可済みPDFページを短いハンドルへOCRします。 | — | — | ✓ |
| `glosswise_list_documents` | 一時OCR文書ハンドルを一覧表示します。 | — | — | ✓ |
| `glosswise_get_document` | OCR文書マニフェストを確認します。 | — | — | ✓ |
| `glosswise_read_document` | OCRページから行範囲を読み取ります。 | — | — | ✓ |
| `glosswise_remove_document` | 一時OCR文書を削除します。 | — | — | ✓ |

### MCPプロファイル

MCPプロファイルは、ワークスペースの内容やインストール済みのSkill
ファイルではなく、ツールの公開範囲を制御します。

| プロファイル | 正確な範囲 | 想定用途 |
| --- | --- | --- |
| `full` | `full`列でチェックされた22個のツール。 | デフォルト。検索、翻訳ブリーフ、CRUD、Skillの検査、ワークスペース管理をサポートします。`glosswise mcp`と`glosswise mcp --json`をそのまま実行すると、このプロファイルが選択されます。 |
| `read` | `read`列でチェックされた13個のツール。 | 読み取り専用の用語・コンテキスト利用とワークスペースの検査向けです。レコードの整備、選択の変更、ワークスペースの管理はできません。 |
| `local` | 22個すべての`full`ツールと7個の許可済み文書ツール。 | 上限付きテキスト範囲とPDF OCR用の高度なフルアクセスサーバーです。選択だけではアクセスを許可しないため、先にルートを許可します。 |

`glosswise setup`は、プロファイルに依存しないSkillを1つインストールします。Skillが
プロファイルを選択するのではなく、接続されたMCPサーバーがAIエージェントから呼び出せる
ツールを決定します。通常のセットアップでは`full`を使用します。これは、Skillが教える
すべての管理・翻訳ワークフローをサポートする唯一の非ローカルプロファイルです。

既存のインストールを変更するには、インストール済みのSkillを維持し、
AIエージェントの設定にあるMCPサーバーコマンドだけを変更してから、AIエージェントを
再起動または再接続します。

```console
glosswise mcp                 # full (default)
glosswise mcp --profile read  # read-only
glosswise mcp --profile local # full plus authorized text/PDF tools
```

`glosswise mcp --json --profile <profile>`で置き換え用のクライアント
JSONを生成します。プロファイルの切り替え時に`glosswise setup`を再実行する必要はありません。
引数なしの`glosswise mcp`に戻すと、デフォルトの`full`範囲に復元されます。

各ツールはバージョン付きJSONエンベロープを返します。AIエージェントは`items`を使用する前に、
`error`、`warnings`、`conflicts`、`truncated`を確認する必要があります。

## CLIリファレンス

| タスク | コマンド | その他の受け付ける形式 |
| --- | --- | --- |
| ワークスペースを一覧表示 | `glosswise ws ls` | `ws list` |
| ワークスペースを検査 | `glosswise ws get [<name>]` | — |
| ワークスペースを作成 | `glosswise ws create [<name>]` | — |
| ワークスペースを選択 | `glosswise ws use <name>` | `ws activate`, `ws act` |
| 選択を解除 | `glosswise ws deact` | `ws deactivate` |
| ワークスペースの登録を解除 | `glosswise ws rm <name>` | `ws unset`, `ws remove` |
| グローバル設定を表示 | `glosswise config get` | — |
| グローバル言語を設定 | `glosswise config lang -l en -l <language>` | `config languages` |
| 翻訳動作を設定 | `glosswise config mode <mode>` | — |
| 翻訳LLMプリセットを設定 | `glosswise config llm <preset>` | — |
| 言語ヒントを設定 | `glosswise ws lang -l en -l <language>` | `ws languages` |
| ローカルルートを許可 | `glosswise ws files -r <directory>` | — |
| データを作成または更新 | `glosswise term set @term.json` | `term put` |
| レコードを1件取得 | `glosswise term get <object-id>` | — |
| データを一覧表示 | `glosswise term ls` | `term list` |
| データを検索 | `glosswise term search "query"` | — |
| データをアーカイブ | `glosswise term archive <object-id>` | — |
| 文章を走査 | `glosswise scan "text"` | — |
| コンテキストを準備 | `glosswise brief "text"` | — |
| LLMSessionで翻訳 | `glosswise translate "text"` | — |
| PDFページをOCR | `glosswise pdf ocr <path>` | — |
| OCRテキストを閲覧 | `glosswise doc read <handle> <page>` | — |

同じset/get/list/search/archiveワークフローで`term`を
`rule`または`example`に置き換えられます。完全なコマンド範囲は
`glosswise --help`または`glosswise <group> --help`で確認できます。

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

`GlossWiseApp.open()`は有効なワークスペースを使用するか、グローバル言語を
設定した後に管理対象のデフォルトを作成します。
明示的に名前を付けた管理対象ワークスペースには`GlossWiseApp.create("<name>")`を、
存在しない場合にエラーとするには`GlossWiseApp.load()`を使用します。すでに
HeavenBaseワークスペースを所有するアプリケーションは、`workspace.glosswise`を直接使用できます。

## 仕組み

1. AIエージェントがMCP、CLI、Python SDKを通じて接続します。
2. GlossWiseは要求されたワークスペースを解決するか、有効なワークスペースまたはデフォルトを使用します。
3. 関連する用語、ルール、用例を取得します。
4. `brief`は、その根拠を順位付けし、警告や競合とともにパッケージ化します。
5. ホストエージェントが翻訳するか、`translate`が`hb.Prompt`管理の
   契約と可視プリセットでHeavenBase `LLMSession`を呼び出します。
6. 呼び出し元は訳文を走査するか、許可済みPDFページを
   上限付きの一時ページテキストへOCRできます。

GlossWiseは、保存処理と用語ポリシーをタスク指向の操作の背後にまとめるため、
AIエージェントに汎用データベースアクセスは必要ありません。

## 開発者向け

GlossWiseは、クリーンな独立アプリケーションでHeavenBaseを利用する方法を示す
デモプロジェクトです。次の実用的な利点を実証します。

- `workspace.glosswise`にマウントされたモジュール式の拡張機能
- 管理対象ワークスペースとアプリケーション所有のデフォルト
- Context単位のユーザー既定値と可視のHeavenBase LLMプリセット
- 型付きエンティティ、クエリ、計算による取得
- ページ単位のHeavenBase LLM OCRと上限付き文書ハンドル
- 複数のCLIバックエンドを通じて公開される1つのコマンドレジストリ
- HeavenBaseツールキットから生成されるMCPツール
- AIエージェントにアプリケーションのワークフローを教えるパッケージ版Skill

直接CLIとPython翻訳は設定済みのHeavenBaseプリセットを
`LLMSession`経由で使用し、MCPホストは自身の設定モデルを使用します。

開発時のチェック：

```console
git clone https://github.com/Magolor/GlossWise.git
cd GlossWise
bash scripts/sync-env.bash
bash scripts/flake.bash --ci
bash scripts/test.bash
bash scripts/test.bash -m full
uv build
```

コントリビューションの手順は[CONTRIBUTING.md](CONTRIBUTING.md)、
脆弱性を非公開で報告する方法は[SECURITY.md](SECURITY.md)を参照してください。

現在の制約：HeavenBase拡張機能は明示的にインストールされ、
有効な拡張機能は無効化されず、スキーマ移行は自動化されていません。またGlossWiseが
翻訳モデルを選択したり隠したりすることはありません。

## 引用

GlossWiseが研究やプロジェクトに役立った場合は、
[CITATION.cff](CITATION.cff)または次の内容で本ソフトウェアを引用してください。

```bibtex
@software{glosswise_2026,
  author  = {Magolor},
  title   = {GlossWise: Terminology-safe translation for AI agents},
  year    = {2026},
  version = {0.1.0.5},
  url     = {https://github.com/Magolor/GlossWise}
}
```

GlossWiseは[HeavenBase](https://ahvn.top)を基盤に構築されています。

## ライセンス

GlossWiseは[MITライセンス](LICENSE)の下で提供されます。
