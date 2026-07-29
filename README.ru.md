# GlossWise

<p align="center">
  <a href="README.en.md">English</a> ·
  <a href="README.ar.md">العربية</a> ·
  <a href="README.zh.md">中文</a> ·
  <a href="README.fr.md">Français</a> ·
  <strong>Русский</strong> ·
  <a href="README.es.md">Español</a> ·
  <a href="README.de.md">Deutsch</a> ·
  <a href="README.ja.md">日本語</a>
</p>

<p align="center">
  <img src="docs/assets/glosswise-banner.png" alt="GlossWise — перевод с соблюдением терминологии для ИИ-агентов" width="100%">
</p>

<p align="center">
  <a href="https://github.com/Magolor/GlossWise/actions/workflows/ci.yml"><img src="https://github.com/Magolor/GlossWise/actions/workflows/ci.yml/badge.svg?branch=master" alt="Непрерывная интеграция"></a>
  <a href="https://www.python.org/"><img src="https://img.shields.io/badge/Python-3.10–3.13-3776AB" alt="Python версий от 3.10 до 3.13"></a>
  <a href="https://ahvn.top"><img src="https://img.shields.io/badge/HeavenBase-0.1.2.1-6957E5" alt="HeavenBase 0.1.2.1"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-green.svg" alt="Лицензия MIT"></a>
</p>

<p align="center">
  <a href="#install">Установка</a> ·
  <a href="#connect-an-agent">Подключение ИИ-агента</a> ·
  <a href="#try-it-teach-once-translate-consistently">Демонстрация</a> ·
  <a href="#everyday-prompts">Повседневные промпты</a> ·
  <a href="#mcp-server">Инструменты MCP</a> ·
  <a href="#python-sdk">Python SDK</a>
</p>

GlossWise хранит утверждённые термины, правила перевода и примеры, а затем подготавливает
компактный бриф перевода для вызывающего ИИ-агента или приложения. Хост-агенты
переводят своей моделью; прямой CLI использует видимый пресет LLM HeavenBase.

GlossWise доступен как CLI, сервер MCP и Python SDK. Версия `0.1.0.5`
поддерживает `heavenbase>=0.1.2.1`.

## <a id="install"></a> Установка

Для GlossWise требуется Python 3.10–3.13. Установите текущую версию исходного кода прямо с
GitHub. Перед установкой можно [просмотреть точный Skill ИИ-агента](SKILL.md):

```console
python -m pip install "git+https://github.com/Magolor/GlossWise.git"
glosswise setup -l en -l zh
```

Чтобы изучить исходный код или внести свой вклад:

```console
git clone https://github.com/Magolor/GlossWise.git
cd GlossWise
python -m pip install .
glosswise setup -l en -l zh
```

`setup` требует обычные языки перевода и сохраняет их как глобальные
настройки, создаёт и активирует с ними пространство `default`, а затем
устанавливает Skill GlossWise для ИИ-агента в следующие каталоги:

- `~/.agents/skills/glosswise`
- `~/.claude/skills/glosswise`

Публичный Skill в корне и копия из пакета, установленная командой `setup`, остаются
полностью идентичными на уровне байтов.

Данные рабочего пространства автоматически хранятся в `~/.glosswise/`. Вам не нужно
выбирать или раскрывать базу данных. Новые пространства наследуют глобальные
языки; измените их через `glosswise config lang -l en -l <language>`.

Проверьте установку:

```console
glosswise ws ls
glosswise ws get
```

## <a id="connect-an-agent"></a> Подключение ИИ-агента

Команда `glosswise setup` уже установила общий Skill GlossWise и версию для Claude.
Подключите один глобальный сервер MCP из любого поддерживаемого хоста:

| Хост | Однократная настройка |
| --- | --- |
| [Claude Code](https://code.claude.com/docs/en/mcp) | `claude mcp add --scope user glosswise -- glosswise mcp` |
| [Codex](https://developers.openai.com/codex/mcp/) | `codex mcp add glosswise -- glosswise mcp` |
| [Cursor](https://docs.cursor.com/context/model-context-protocol) | Сохраните `glosswise mcp --json` как `~/.cursor/mcp.json`. |
| [VS Code / Copilot](https://code.visualstudio.com/docs/copilot/chat/mcp-servers) | Добавьте в `.vscode/mcp.json` stdio-запись `servers.glosswise` с командой `glosswise` и аргументами `["mcp"]`. |
| [OpenCode](https://opencode.ai/docs/mcp-servers/) | Добавьте приведённую ниже локальную запись MCP в `~/.config/opencode/opencode.json`. |
| [OpenClaw](https://ahvn.top/quickstart/heavenbase-mcp#3-connect-your-agent) | Запустите `glosswise mcp --transport http`, затем задайте `mcp.servers.glosswise` как `http://127.0.0.1:61055/mcp` с транспортом `streamable-http`. |
| [Hermes](https://ahvn.top/quickstart/heavenbase-mcp#3-connect-your-agent) | Запустите `glosswise mcp --transport http`, затем добавьте URL в `mcp_servers.glosswise` файла `~/.hermes/config.yaml`. |
| [LM Studio](https://lmstudio.ai/docs/app/mcp) | Откройте **Program/Developer → Install → Edit mcp.json** и вставьте вывод `glosswise mcp --json`. |
| [Qwen Code](https://qwenlm.github.io/qwen-code-docs/en/users/features/mcp/) | `qwen mcp add --scope user glosswise glosswise mcp` |
| [HeavenBase](https://ahvn.top/quickstart/heavenbase-mcp#3-connect-your-agent) | Запустите `glosswise mcp --transport http`, затем `hb llm session --mcp http://127.0.0.1:61055/mcp`. |

Для [OpenCode](https://opencode.ai/docs/mcp-servers/) добавьте следующий фрагмент в глобальный файл
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

Проверьте подключение командой хоста, перечисляющей серверы MCP, и
перезапустите ИИ-агента, если этого требует его документация.

Начните новый чат и напишите:

```text
/glosswise Перечисли мои рабочие пространства и сообщи, какое из них активно.
```

Теперь ИИ-агент может создавать рабочие пространства, управлять терминологией, искать в ней и подготавливать
брифы перевода от вашего имени. Вам не нужно писать JSON или администрировать
базу данных. Один Skill и одно подключение MCP работают со всеми рабочими пространствами
GlossWise.

Для другого клиента MCP с поддержкой stdio выведите переносимый профиль:

```console
glosswise mcp --json
```

## <a id="try-it-teach-once-translate-consistently"></a> Попробуйте: научите один раз, переводите единообразно

Демонстрация начинается с обычного перевода моделью, затем GlossWise получает два
терминологических решения на естественном языке, после чего исходный запрос повторяется
в новой сессии ИИ-агента. Отрывок взят из
романа [*«Франкенштейн»* Мэри Шелли](https://www.gutenberg.org/cache/epub/42324/pg42324-images.html) —
одного из ранних научно-фантастических произведений, находящегося в общественном достоянии.

### 1. Создайте рабочее пространство

Попросите своего ИИ-агента:

```text
/glosswise Создай и выбери рабочее пространство GlossWise с именем `frankenstein-lab`.
Задай английский, китайский, французский, немецкий, русский и японский языками по умолчанию.
```

Или воспользуйтесь двумя короткими командами CLI:

```console
glosswise ws create frankenstein-lab
glosswise ws lang -l en -l zh -l fr -l de -l ru -l ja
```

`ws create` автоматически выбирает новое рабочее пространство. Повторяйте `-l/--lang`
для каждого языка по порядку. Этот набор напоминает агентам собрать все шесть предпочтительных форм, не
превращая языки в жёсткое ограничение.

### 2. Переведите до обучения GlossWise

Отправьте ИИ-агенту этот абзац:

```text
/glosswise Используй рабочее пространство `frankenstein-lab`. Переведи приведённый ниже абзац
на китайский, французский, немецкий, русский и японский языки. Сначала проверь GlossWise на наличие
подходящих указаний, а затем назови модель или хост, выполнившие перевод.

“It was on a dreary night of November, that I beheld the accomplishment of my
toils. With an anxiety that almost amounted to agony, I collected the
instruments of life around me, that I might infuse a spark of being into the
lifeless thing that lay at my feet.”
```

Первая формулировка зависит от модели перевода ИИ-агента. Она может выбрать
буквальные выражения, например “spark of being” → `存在的火花`,
`étincelle de vie`, `Lebensfunken`, `искра жизни` или `命の火花`.

### 3. Объясните два решения в диалоге

Отправьте ещё одно сообщение:

```text
/glosswise Сохрани их как активные предпочтительные термины в рабочем пространстве `frankenstein-lab`.
Целевые формы — это терминологические решения моего проекта, а не утверждения
об официальных переводах романа.

1. «instruments of life» означает аппаратуру, использованную в эксперименте:
   китайский 生命仪器; французский instruments de vie;
   немецкий Instrumente des Lebens; русский орудия жизни;
   японский 生命の器具.

2. «spark of being» означает оживляющую сущность, переданную безжизненной материи:
   китайский 生命之火; французский étincelle d'existence;
   немецкий Funke des Seins; русский искра бытия;
   японский 存在の火花.

Сохрани также английские исходные формы. Используй предпочтительную терминологию точно, когда
это допускает грамматика целевого языка; в противном случае склоняй её, не меняя
утверждённого понятия. Сообщи, когда обе записи будут сохранены.
```

ИИ-агент выполняет структурированные вызовы CRUD. Если в рабочем пространстве отсутствует запрошенный язык,
установленный Skill предписывает ему запросить перевод, предложить форму для
подтверждения или явно указать, что форма создана ИИ-агентом.

### 4. Начните новую сессию и повторите тот же запрос

Завершите текущий чат и начните новую сессию ИИ-агента. Снова отправьте точный промпт из
шага 2 — не добавляйте напоминание о только что сохранённых терминах:

```text
/glosswise Используй рабочее пространство `frankenstein-lab`. Переведи приведённый ниже абзац
на китайский, французский, немецкий, русский и японский языки. Сначала проверь GlossWise на наличие
подходящих указаний, а затем назови модель или хост, выполнившие перевод.

“It was on a dreary night of November, that I beheld the accomplishment of my
toils. With an anxiety that almost amounted to agony, I collected the
instruments of life around me, that I might infuse a spark of being into the
lifeless thing that lay at my feet.”
```

Промпт идентичен; изменилось только сохранённое рабочее пространство GlossWise.
Новая сессия должна получить это состояние, а не полагаться на память чата. Теперь
хорошо заметно важное изменение:

| Язык | В исходном варианте может использоваться | Формулировка с учётом GlossWise |
| --- | --- | --- |
| Китайский | `生命工具` · `存在的火花` | `生命仪器` · `生命之火` |
| Французский | `instruments de la vie` · `étincelle de vie` | `instruments de vie` · `étincelle d'existence` |
| Немецкий | `Werkzeuge des Lebens` · `Lebensfunken` | `Instrumente des Lebens` · `Funken des Seins`¹ |
| Русский | `инструменты жизни` · `искра жизни` | `орудия жизни` · `искру бытия`¹ |
| Японский | `生命の道具` · `命の火花` | `生命の器具` · `存在の火花` |

¹ ИИ-агент склоняет каноническую предпочтительную форму, чтобы она подходила к этому предложению.

<details>
<summary>Один из успешных результатов с учётом GlossWise</summary>

**Китайский**

> 那是十一月一个阴沉的夜晚，我目睹了自己辛劳的成果。怀着近乎痛苦的焦虑，我把生命仪器聚集在身边，想把生命之火注入躺在我脚边的无生命之物中。

**Французский**

> Ce fut par une lugubre nuit de novembre que je contemplai l’accomplissement de mes travaux. Avec une anxiété qui confinait presque à l’agonie, je rassemblai autour de moi les instruments de vie afin d’insuffler une étincelle d'existence à la chose inanimée étendue à mes pieds.

**Немецкий**

> Es war in einer trüben Novembernacht, als ich die Vollendung meiner Mühen erblickte. Mit einer Angst, die beinahe an Qual grenzte, versammelte ich die Instrumente des Lebens um mich, um dem leblosen Ding zu meinen Füßen einen Funken des Seins einzuhauchen.

**Русский**

> В мрачную ноябрьскую ночь я увидел завершение своих трудов. С тревогой, почти переходившей в агонию, я собрал вокруг себя орудия жизни, чтобы вдохнуть искру бытия в безжизненное создание, лежавшее у моих ног.

**Японский**

> 十一月の陰鬱な夜、私は自らの労苦の成就を目の当たりにした。苦悶に近い不安を抱えながら、私は生命の器具を周囲に集め、足元に横たわる生命なきものへ存在の火花を吹き込もうとした。

</details>

GlossWise не создавал эти предложения. Их создал подключённый ИИ-агент; GlossWise
сделал утверждённую терминологию доступной для поиска и проверки перед генерацией.

### 5. Найдите и измените позже

Идентификаторы записей не нужны:

```text
/glosswise Найди в `frankenstein-lab` термин, связанный с искрой. Покажи его предпочтительные
формы в компактной таблице.
```

Затем измените его естественной фразой:

```text
/glosswise Измени только японскую предпочтительную форму для «spark of being» на
`生命の火花`. Не меняй другие языки и покажи мне сохранённую запись.
```

Весь этот путь: настройка → создание → ведение → перезапуск → бриф перевода → поиск → изменение —
проверяется с установленным wheel и двумя независимыми сессиями MCP stdio в
[`tests/test_quickstart.py`](https://github.com/Magolor/GlossWise/blob/master/tests/test_quickstart.py).

## <a id="everyday-prompts"></a> Повседневные промпты

После подключения обычную работу можно вести в чате. Приведённые ниже управляющие промпты
намеренно вносят изменения; промпты запросов и перевода доступны только для чтения, если в них
нет явной просьбы что-либо сохранить.

### Управление рабочими пространствами и терминологией

- `/glosswise Создай и выбери рабочее пространство с именем <name>.`
- `/glosswise В рабочем пространстве <name> задай английский, китайский и японский языками по умолчанию.`
- `/glosswise В рабочем пространстве <name> сохрани “rate limit” как активный предпочтительный термин с английской формой “rate limit”, китайской “速率限制” и японской “レート制限”. Покажи мне сохранённую запись.`
- `/glosswise Найди “rate limit” в рабочем пространстве <name>. Измени только японскую предпочтительную форму на “速度制限”, сохрани все остальные поля и формы, а затем покажи мне обновлённую запись.`
- `/glosswise Архивируй термин “rate limit” в рабочем пространстве <name>, чтобы исключить его из обычного поиска активных терминов. Спроси меня перед изменением.`

### Поиск указаний и перевод

- `/glosswise В рабочем пространстве <name> найди активные термины, связанные с аутентификацией. Покажи их предпочтительные и запрещённые формы на английском, китайском и японском языках. Ничего не изменяй.`
- `/glosswise В рабочем пространстве <name> найди правила и примеры для перевода сообщений об ошибках на французский язык. Покажи приоритеты, стили и конфликты. Ничего не изменяй.`
- `/glosswise Проверь “Requests over this limit are rejected.” по рабочему пространству <name>. Перечисли совпавшие термины и правила, ничего не переводя и не сохраняя.`
- `/glosswise Используй рабочее пространство <name>. Переведи “The client retries the request after the rate limit resets.” с английского на китайский и японский языки. Подготовь свежий бриф перевода GlossWise для каждого целевого языка, примени активные предпочтительные термины и правила, отметь конфликты и назови модель или хост, выполнившие перевод.`
- `/glosswise Используй рабочее пространство <name>. Переведи приведённый ниже английский текст на французский. Сначала подготовь бриф перевода GlossWise, затем после перевода покажи компактную таблицу всех применённых сохранённых терминов, правил или примеров: <paste source passage>.`
- `/glosswise Проверь этот французский перевод по рабочему пространству <name>. Сообщи об отсутствующих предпочтительных терминах, запрещённых формах и конфликтующих правилах; ничего не переписывай и не сохраняй без моей просьбы: <paste translation>.`

Используйте `glosswise ws ls`, `glosswise ws use <name>` и
`glosswise ws get`, когда быстрая проверка в терминале удобнее чата.

## Встроенный перевод, диапазоны файлов и OCR PDF

Прямой перевод использует именованный пресет `LLMSession` HeavenBase. Результат
сообщает разрешённые пресет, шлюз, провайдера, модель и идентификатор модели.
Пресет и режим неопределённости выбираются отдельно:

```console
glosswise config llm chat
glosswise config mode auto
glosswise translate "Run this query." -sl en -tl ja
glosswise translate "Run this query." -sl en -tl ja --preset chat
```

Режимы: `yolo` (переводить сразу), `elicit` (задавать точные вопросы о терминах
с вариантами), `auto` (учитывать имеющиеся сведения), `explain`
(переводить и объяснять каждый существенный выбор) и `custom` с `--prompt`.
HeavenBase создаёт системный промпт через `hb.Prompt` и разрешает именованный
пресет. `chat` использует текущий быстрый чат; отдельный пресет позволяет
не дублировать учётные данные провайдера внутри GlossWise:

```console
hb cfg set heavenbase.llm.presets.glosswise-translate.model deepseek-v4-flash
glosswise config llm glosswise-translate
```

`scan`, `brief` и `translate` принимают включительные диапазоны от 1 через
`--start-line` и `--end-line` для текста, stdin и `@file`. Авторизованный
локальный профиль MCP добавляет равнозначные файловые инструменты.

Для PDF авторизуйте каталог, распознайте только нужные страницы через
настроенный пресет LLM HeavenBase и просматривайте сохранённый постраничный
текст по короткому идентификатору `gw-...`:

```console
glosswise ws files -r /absolute/path/to/documents
glosswise pdf ocr /absolute/path/to/documents/manual.pdf --start-page 4 --end-page 8
glosswise doc read gw-0123456789ab 4 --start-line 1 --end-line 80
glosswise doc rm gw-0123456789ab
```

`ws files` сохраняет список разрешённых для чтения каталогов в рамках рабочей
области; повторяйте `-r/--root` для каждого каталога. Команда не загружает, не
копирует и не регистрирует файлы. Повторяйте `-e/--encoding` только для
дополнительных строгих кодировок текста; UTF-8 разрешена по умолчанию.

GlossWise обрабатывает по одной странице и сразу удаляет её изображение.
Подозрительные длинные повторы отмечаются, но не удаляются молча.
Настройте `ocr-local` командой `hb cfg set
heavenbase.llm.presets.ocr-local.<field-or-path> <value>`; доступны поля
`desc`, `gateway`, `provider`, `model` и `default_args`; другой пресет выбирается через `glosswise config ocr <preset>`.

## <a id="mcp-server"></a> Сервер MCP

### Локальный stdio

Большинству настольных клиентов и клиентов для ИИ-агентов программирования следует использовать:

```console
glosswise mcp --json
```

Созданный дочерний процесс запускает полный сервер с инструментами чтения, CRUD, Skill и
управления рабочими пространствами. Исполняемый файл `glosswise` должен находиться в `PATH`
клиента MCP.

### Локальный HTTP

Чтобы запустить долгоживущий потоковый HTTP-сервер:

```console
glosswise mcp --transport http
```

По умолчанию он привязывается к `127.0.0.1:61055` и обслуживает MCP по адресу
`http://127.0.0.1:61055/mcp`. Выведите подходящий профиль клиента командой:

```console
glosswise mcp --json --transport http
```

При необходимости выберите другую локальную конечную точку:

```console
glosswise mcp --transport http --host 127.0.0.1 --port 61056
```

GlossWise не добавляет сетевую аутентификацию. Оставьте сервер на узле
loopback, если другой доверенный уровень не обеспечивает аутентификацию и безопасность
передачи данных.

### Инструменты MCP

Инструменты данных и контекста принимают необязательный `workspace_id`. Если он не указан,
GlossWise использует активное рабочее пространство, а затем управляемое пространство по умолчанию.

| Инструмент | Назначение | `read` | `full` | `local` |
| --- | --- | :---: | :---: | :---: |
| `glosswise_workspace_info` | Показывает возможности рабочего пространства и языковые подсказки. | ✓ | ✓ | ✓ |
| `glosswise_prepare_translation` | Создаёт бриф перевода для исходного текста. | ✓ | ✓ | ✓ |
| `glosswise_search_terms` | Ищет термины. | ✓ | ✓ | ✓ |
| `glosswise_search_rules` | Ищет правила. | ✓ | ✓ | ✓ |
| `glosswise_search_examples` | Ищет примеры. | ✓ | ✓ | ✓ |
| `glosswise_scan_text` | Проверяет текст на совпадения с терминами и правилами. | ✓ | ✓ | ✓ |
| `glosswise_list_records` | Перечисляет термины, правила или примеры. | ✓ | ✓ | ✓ |
| `glosswise_get_record` | Получает запись по идентификатору объекта. | ✓ | ✓ | ✓ |
| `glosswise_put_term` | Создаёт или обновляет термин и его формы. | — | ✓ | ✓ |
| `glosswise_put_rule` | Создаёт или обновляет правило. | — | ✓ | ✓ |
| `glosswise_put_example` | Создаёт или обновляет пример. | — | ✓ | ✓ |
| `glosswise_archive` | Архивирует одну запись. | — | ✓ | ✓ |
| `glosswise_list_workspaces` | Перечисляет рабочие пространства. | ✓ | ✓ | ✓ |
| `glosswise_get_workspace` | Получает запись рабочего пространства со скрытыми данными. | ✓ | ✓ | ✓ |
| `glosswise_create_workspace` | Создаёт управляемое рабочее пространство. | — | ✓ | ✓ |
| `glosswise_set_workspace_languages` | Задаёт языковые подсказки рабочего пространства. | — | ✓ | ✓ |
| `glosswise_activate_workspace` | Выбирает активное рабочее пространство. | — | ✓ | ✓ |
| `glosswise_deactivate_workspace` | Сбрасывает активный выбор. | — | ✓ | ✓ |
| `glosswise_remove_workspace` | Отменяет регистрацию рабочего пространства. | — | ✓ | ✓ |
| `glosswise_open_workspace` | Открывает рабочее пространство и показывает его возможности. | ✓ | ✓ | ✓ |
| `glosswise_health_workspace` | Проверяет состояние реестра и среды выполнения. | ✓ | ✓ | ✓ |
| `glosswise_read_skill` | Читает упакованные инструкции для ИИ-агента. | ✓ | ✓ | ✓ |
| `glosswise_scan_file` | Проверяет авторизованный локальный текстовый файл сервера. | — | — | ✓ |
| `glosswise_prepare_file` | Создаёт бриф из диапазона авторизованного файла. | — | — | ✓ |
| `glosswise_ocr_pdf` | Распознаёт страницы PDF в короткий идентификатор. | — | — | ✓ |
| `glosswise_list_documents` | Перечисляет временные документы OCR. | — | — | ✓ |
| `glosswise_get_document` | Показывает манифест документа OCR. | — | — | ✓ |
| `glosswise_read_document` | Читает ограниченный диапазон строк страницы OCR. | — | — | ✓ |
| `glosswise_remove_document` | Удаляет временный документ OCR. | — | — | ✓ |

### Профили MCP

Профили управляют доступностью инструментов, а не содержимым рабочих пространств или установленным файлом
Skill:

| Профиль | Точный набор | Назначение |
| --- | --- | --- |
| `full` | 22 инструмента, отмеченные в столбце `full`. | По умолчанию. Поддерживает поиск, брифы перевода, CRUD, проверку Skill и управление рабочими пространствами. Команды `glosswise mcp` и `glosswise mcp --json` выбирают этот профиль. |
| `read` | 13 инструментов, отмеченных в столбце `read`. | Доступ только для чтения к терминологии и контексту, а также проверка рабочих пространств. Не позволяет вести записи, менять выбор или управлять рабочими пространствами. |
| `local` | Все 22 инструмента `full` и семь авторизованных локальных инструментов документов. | Расширенный доступ для диапазонов текста и OCR PDF. Один профиль не даёт доступ; сначала авторизуйте каталоги. |

`glosswise setup` устанавливает Skill, не зависящий от профиля. Skill не
выбирает профиль: подключённый сервер MCP решает, какие инструменты может вызывать ИИ-агент.
Обычная настройка использует `full` — единственный нелокальный профиль, который
поддерживает все описанные в Skill процессы управления и перевода.

Чтобы изменить существующую установку, сохраните установленный Skill и измените только
команду сервера MCP в конфигурации ИИ-агента, а затем перезапустите или повторно подключите
ИИ-агента:

```console
glosswise mcp                 # full (default)
glosswise mcp --profile read  # read-only
glosswise mcp --profile local # full plus authorized text/PDF tools
```

Используйте `glosswise mcp --json --profile <profile>`, чтобы создать новый клиентский
JSON. Повторно выполнять `glosswise setup` при смене профилей не нужно.
Возврат к простой команде `glosswise mcp` восстанавливает набор `full` по умолчанию.

Каждый инструмент возвращает версионированную оболочку JSON. ИИ-агенты должны проверить `error`,
`warnings`, `conflicts` и `truncated`, прежде чем использовать `items`.

## Справочник CLI

| Задача | Команда | Также принимается |
| --- | --- | --- |
| Перечислить рабочие пространства | `glosswise ws ls` | `ws list` |
| Проверить рабочее пространство | `glosswise ws get [<name>]` | — |
| Создать рабочее пространство | `glosswise ws create [<name>]` | — |
| Выбрать рабочее пространство | `glosswise ws use <name>` | `ws activate`, `ws act` |
| Сбросить выбор | `glosswise ws deact` | `ws deactivate` |
| Отменить регистрацию рабочего пространства | `glosswise ws rm <name>` | `ws unset`, `ws remove` |
| Показать глобальные настройки | `glosswise config get` | — |
| Задать глобальные языки | `glosswise config lang -l en -l <language>` | `config languages` |
| Задать режим перевода | `glosswise config mode <mode>` | — |
| Задать пресет LLM перевода | `glosswise config llm <preset>` | — |
| Задать языковые подсказки | `glosswise ws lang -l en -l <language>` | `ws languages` |
| Авторизовать локальные каталоги | `glosswise ws files -r <directory>` | — |
| Создать или обновить данные | `glosswise term set @term.json` | `term put` |
| Получить одну запись | `glosswise term get <object-id>` | — |
| Перечислить данные | `glosswise term ls` | `term list` |
| Найти данные | `glosswise term search "query"` | — |
| Архивировать данные | `glosswise term archive <object-id>` | — |
| Проверить отрывок | `glosswise scan "text"` | — |
| Подготовить контекст | `glosswise brief "text"` | — |
| Перевести через LLMSession | `glosswise translate "text"` | — |
| Распознать страницы PDF | `glosswise pdf ocr <path>` | — |
| Читать текст OCR | `glosswise doc read <handle> <page>` | — |

Замените `term` на `rule` или `example`, чтобы использовать тот же процесс
создания/получения/перечисления/поиска/архивации. Выполните `glosswise --help` или
`glosswise <group> --help`, чтобы просмотреть весь набор команд.

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

`GlossWiseApp.open()` использует активное пространство или создаёт управляемое
пространство по умолчанию после настройки глобальных языков.
Используйте `GlossWiseApp.create("<name>")` для явно именованного управляемого рабочего пространства
и `GlossWiseApp.load()`, когда отсутствие должно считаться ошибкой. Приложения, которым
уже принадлежит рабочее пространство HeavenBase, могут использовать `workspace.glosswise` напрямую.

## Как это работает

1. ИИ-агент подключается через MCP, CLI или Python SDK.
2. GlossWise находит запрошенное рабочее пространство либо использует активное/предустановленное.
3. Он получает подходящие термины, правила и примеры.
4. `brief` ранжирует и упаковывает эти сведения вместе с предупреждениями и конфликтами.
5. Хост-агент переводит, либо `translate` вызывает `LLMSession` HeavenBase
   по контракту `hb.Prompt` с видимым пресетом.
6. Вызывающая сторона может проверить перевод или распознать авторизованные PDF
   во временный ограниченный постраничный текст.

GlossWise скрывает хранилище и терминологическую политику за предметными операциями;
ИИ-агентам не нужен общий доступ к базе данных.

## Для разработчиков

GlossWise — демонстрационный проект, показывающий, как чисто спроектированное автономное приложение может использовать
HeavenBase. Он демонстрирует практические преимущества:

- модульного расширения, подключённого как `workspace.glosswise`;
- управляемых рабочих пространств и значений по умолчанию, принадлежащих приложению;
- настроек пользователя на уровне Context и видимых пресетов LLM HeavenBase;
- типизированных сущностей, запросов и вычисляемого поиска;
- постраничного OCR через HeavenBase LLM с ограниченными документами;
- единого реестра команд, доступного через несколько бэкендов CLI;
- инструментов MCP, созданных на основе toolkit HeavenBase; и
- упакованного Skill, который обучает ИИ-агентов рабочему процессу приложения.

Прямые CLI- и Python-переводы используют настроенный пресет HeavenBase через
`LLMSession`; хосты MCP используют собственную настроенную модель.

Проверки для разработчиков:

```console
git clone https://github.com/Magolor/GlossWise.git
cd GlossWise
bash scripts/sync-env.bash
bash scripts/flake.bash --ci
bash scripts/test.bash
bash scripts/test.bash -m full
uv build
```

Сведения о процессе внесения изменений см. в [CONTRIBUTING.md](CONTRIBUTING.md), а
о конфиденциальном сообщении об уязвимостях — в [SECURITY.md](SECURITY.md).

Текущие ограничения: расширения HeavenBase устанавливаются явно, включённые
расширения не отключаются, миграция схемы не автоматизирована, а GlossWise
не выбирает и не скрывает модель перевода.

## Цитирование

Если GlossWise помогает в вашем исследовании или проекте, процитируйте программу с помощью
[CITATION.cff](CITATION.cff) или:

```bibtex
@software{glosswise_2026,
  author  = {Magolor},
  title   = {GlossWise: Terminology-safe translation for AI agents},
  year    = {2026},
  version = {0.1.0.5},
  url     = {https://github.com/Magolor/GlossWise}
}
```

GlossWise создан на основе [HeavenBase](https://ahvn.top).

## Лицензия

GlossWise доступен по [лицензии MIT](LICENSE).
