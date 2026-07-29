# GlossWise

<p align="center">
  <a href="README.en.md">English</a> ·
  <strong>العربية</strong> ·
  <a href="README.zh.md">中文</a> ·
  <a href="README.fr.md">Français</a> ·
  <a href="README.ru.md">Русский</a> ·
  <a href="README.es.md">Español</a> ·
  <a href="README.de.md">Deutsch</a> ·
  <a href="README.ja.md">日本語</a>
</p>

<p align="center">
  <img src="docs/assets/glosswise-banner.png" alt="GlossWise — ترجمة آمنة مصطلحيًا للوكلاء الأذكياء" width="100%">
</p>

<p align="center">
  <a href="https://github.com/Magolor/GlossWise/actions/workflows/ci.yml"><img src="https://github.com/Magolor/GlossWise/actions/workflows/ci.yml/badge.svg?branch=master" alt="التكامل المستمر"></a>
  <a href="https://www.python.org/"><img src="https://img.shields.io/badge/Python-3.10–3.13-3776AB" alt="Python من 3.10 إلى 3.13"></a>
  <a href="https://ahvn.top"><img src="https://img.shields.io/badge/HeavenBase-0.1.2.1-6957E5" alt="HeavenBase 0.1.2.1"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-green.svg" alt="ترخيص MIT"></a>
</p>

<p align="center">
  <a href="#install">التثبيت</a> ·
  <a href="#connect-an-agent">ربط وكيل ذكي</a> ·
  <a href="#try-it-teach-once-translate-consistently">تجربة العرض التوضيحي</a> ·
  <a href="#everyday-prompts">مطالبات يومية</a> ·
  <a href="#mcp-server">أدوات MCP</a> ·
  <a href="#python-sdk">حزمة Python SDK</a>
</p>

يخزّن GlossWise المصطلحات المعتمدة وقواعد الترجمة والأمثلة، ثم يُعِدّ
موجز الترجمة في صيغة مضغوطة للوكيل الذكي أو التطبيق المستدعي. يترجم الوكيل المضيف
بنموذجه، بينما تستخدم CLI المباشرة إعداد HeavenBase LLM مسبقًا وظاهرًا.

يتوفر GlossWise في صورة CLI وخادم MCP وحزمة Python SDK. يدعم الإصدار `0.1.0.5`
الحزمة `heavenbase>=0.1.2.1`.

## <a id="install"></a> التثبيت

يتطلب GlossWise إصدار Python من 3.10 إلى 3.13. ثبّت المصدر الحالي مباشرة من
GitHub. قبل التثبيت، يمكنك [مراجعة Skill الوكيل الذكي نفسها](SKILL.md):

```console
python -m pip install "git+https://github.com/Magolor/GlossWise.git"
glosswise setup -l en -l zh
```

لفحص المصدر أو المساهمة فيه:

```console
git clone https://github.com/Magolor/GlossWise.git
cd GlossWise
python -m pip install .
glosswise setup -l en -l zh
```

يتطلب `setup` اللغات التي تترجم بينها عادةً ويحفظها كإعدادات
عامة، ثم ينشئ مساحة العمل `default` وينشّطها بهذه اللغات، ويثبّت
Skill وكيل GlossWise الذكي في:

- `~/.agents/skills/glosswise`
- `~/.claude/skills/glosswise`

تبقى Skill العامة في الجذر والنسخة المضمّنة التي يثبّتها `setup`
متطابقتين تمامًا على مستوى البايت.

تُدار بيانات مساحة العمل تلقائيًا ضمن `~/.glosswise/`. ولا تحتاج
إلى اختيار قاعدة بيانات أو كشفها. ترث مساحات العمل الجديدة اللغات
العامة؛ غيّرها باستخدام `glosswise config lang -l en -l <language>`.

تحقق من التثبيت:

```console
glosswise ws ls
glosswise ws get
```

## <a id="connect-an-agent"></a> ربط وكيل ذكي

يكون `glosswise setup` قد ثبّت بالفعل Skill GlossWise العامة ونسخة Claude.
صِل خادم MCP العام نفسه من أي مضيف مدعوم:

| الوكيل الذكي | إعداد لمرة واحدة |
| --- | --- |
| [Claude Code](https://code.claude.com/docs/en/mcp) | `claude mcp add --scope user glosswise -- glosswise mcp` |
| [Codex](https://developers.openai.com/codex/mcp/) | `codex mcp add glosswise -- glosswise mcp` |
| [Cursor](https://docs.cursor.com/context/model-context-protocol) | احفظ `glosswise mcp --json` باسم `~/.cursor/mcp.json`. |
| [VS Code / Copilot](https://code.visualstudio.com/docs/copilot/chat/mcp-servers) | أضف إلى `.vscode/mcp.json` إدخال stdio باسم `servers.glosswise` يستخدم الأمر `glosswise` والوسيطات `["mcp"]`. |
| [OpenCode](https://opencode.ai/docs/mcp-servers/) | أضف إدخال MCP المحلي أدناه إلى `~/.config/opencode/opencode.json`. |
| [OpenClaw](https://ahvn.top/quickstart/heavenbase-mcp#3-connect-your-agent) | شغّل `glosswise mcp --transport http`، ثم اضبط `mcp.servers.glosswise` على `http://127.0.0.1:61055/mcp` باستخدام النقل `streamable-http`. |
| [Hermes](https://ahvn.top/quickstart/heavenbase-mcp#3-connect-your-agent) | شغّل `glosswise mcp --transport http`، ثم أضف عنوان URL الخاص به تحت `mcp_servers.glosswise` في `~/.hermes/config.yaml`. |
| [LM Studio](https://lmstudio.ai/docs/app/mcp) | افتح **Program/Developer → Install → Edit mcp.json** ثم الصق ناتج `glosswise mcp --json`. |
| [Qwen Code](https://qwenlm.github.io/qwen-code-docs/en/users/features/mcp/) | `qwen mcp add --scope user glosswise glosswise mcp` |
| [HeavenBase](https://ahvn.top/quickstart/heavenbase-mcp#3-connect-your-agent) | شغّل `glosswise mcp --transport http`، ثم `hb llm session --mcp http://127.0.0.1:61055/mcp`. |

بالنسبة إلى [OpenCode](https://opencode.ai/docs/mcp-servers/)، أضف ما يلي إلى
`~/.config/opencode/opencode.json` العام:

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

تحقق من الاتصال بأمر المضيف الذي يسرد خوادم MCP، ثم أعد تشغيل الوكيل
إذا كانت وثائقه تتطلب ذلك.

ابدأ محادثة جديدة وقل:

```text
/glosswise اعرض مساحات عملي وأخبرني أيها نشطة.
```

يستطيع الوكيل الذكي الآن إنشاء مساحات عمل وتنظيم المصطلحات والبحث فيها وإعداد
موجزات الترجمة نيابةً عنك. لا تحتاج إلى كتابة JSON أو إدارة
قاعدة بيانات. تعمل Skill واحدة واتصال MCP واحد عبر جميع مساحات عمل GlossWise
كلها.

لعميل MCP آخر يدعم stdio، اطبع ملف تعريف MCP القابل للنقل:

```console
glosswise mcp --json
```

## <a id="try-it-teach-once-translate-consistently"></a> جرّبه: علّم مرة واحدة وترجم باتساق

يبدأ هذا العرض التوضيحي بترجمة عادية من النموذج، ثم يعلّم GlossWise قرارين
مصطلحيين بلغة طبيعية، وبعد ذلك يكرر الطلب الأصلي
في جلسة وكيل ذكي نظيفة. المقتطف مأخوذ من
رواية [*Frankenstein* لماري شيلي](https://www.gutenberg.org/cache/epub/42324/pg42324-images.html)،
وهي عمل مبكر من أدب الخيال العلمي يقع ضمن الملكية العامة.

### 1. ابدأ مساحة عمل

اطلب من وكيلك الذكي:

```text
/glosswise أنشئ مساحة عمل GlossWise باسم `frankenstein-lab` واخترها.
اضبط لغاتها الافتراضية على الإنجليزية والصينية والفرنسية والألمانية والروسية واليابانية.
```

أو استخدم أمري CLI القصيرين:

```console
glosswise ws create frankenstein-lab
glosswise ws lang -l en -l zh -l fr -l de -l ru -l ja
```

يختار `ws create` مساحة العمل الجديدة تلقائيًا. كرّر `-l/--lang` لكل
لغة مرتبة. وهذه المجموعة تلميح تنظيمي يذكّر الوكلاء بجمع الصيغ المفضّلة الست دون
تحويل اللغات إلى قيد صارم.

### 2. ترجم قبل تعليم GlossWise

أرسل هذه الفقرة إلى الوكيل الذكي:

```text
/glosswise استخدم مساحة العمل `frankenstein-lab`. ترجم الفقرة أدناه
إلى الصينية والفرنسية والألمانية والروسية واليابانية. تحقّق أولًا من GlossWise بحثًا عن
إرشادات ذات صلة، ثم حدّد النموذج أو المضيف الذي نفّذ الترجمة.

«في ليلة كئيبة من ليالي نوفمبر، رأيت إنجاز
أعمالي الشاقة. وبقلق كاد يبلغ حد العذاب، جمعت
أدوات الحياة حولي، كي أنفخ شرارة الوجود في
الشيء العديم الحياة الممدد عند قدميّ.»
```

تعتمد الصياغة الأولى على نموذج الترجمة لدى الوكيل الذكي. وقد يختار
عبارات حرفية مثل “spark of being” ← `存在的火花` أو
`étincelle de vie` أو `Lebensfunken` أو `искра жизни` أو `命の火花`.

### 3. علّم قرارين عبر المحادثة

أرسل رسالة أخرى:

```text
/glosswise احفظ هذه كمصطلحات مفضّلة نشطة في مساحة العمل `frankenstein-lab`.
الصيغ المستهدفة هي قرارات مصطلحية لمشروعي، وليست مزاعم
بشأن الترجمات الرسمية للرواية.

1. يعني “instruments of life” الأجهزة المستخدمة في التجربة:
   الصينية 生命仪器؛ الفرنسية instruments de vie؛
   الألمانية Instrumente des Lebens؛ الروسية орудия жизни؛
   اليابانية 生命の器具.

2. يعني “spark of being” الجوهر المحيي المنقول إلى المادة العديمة الحياة:
   الصينية 生命之火؛ الفرنسية étincelle d'existence؛
   الألمانية Funke des Seins؛ الروسية искра бытия؛
   اليابانية 存在の火花.

احتفظ أيضًا بصيغ المصدر الإنجليزية. استخدم المصطلحات المفضّلة حرفيًا عندما
تسمح قواعد اللغة المستهدفة؛ وإلا فصرّفها دون تغيير
المفهوم المعتمد. أخبرني عند تخزين السجلين.
```

يتولى الوكيل الذكي استدعاءات CRUD المنظّمة. وإذا كانت إحدى لغات مساحة العمل المطلوبة
مفقودة، تطلب منه Skill المثبّتة أن يسأل، أو يقترح صيغة
للتأكيد، أو يفصح بوضوح عن صيغة أنشأها الوكيل الذكي.

### 4. ابدأ جلسة جديدة وكرر الطلب نفسه

أنهِ المحادثة الحالية وابدأ جلسة وكيل ذكي جديدة. أرسل المطالبة نفسها تمامًا من
الخطوة 2 مجددًا—ولا تضف تذكيرًا بالمصطلحات التي خزّنتها للتو:

```text
/glosswise استخدم مساحة العمل `frankenstein-lab`. ترجم الفقرة أدناه
إلى الصينية والفرنسية والألمانية والروسية واليابانية. تحقّق أولًا من GlossWise بحثًا عن
إرشادات ذات صلة، ثم حدّد النموذج أو المضيف الذي نفّذ الترجمة.

«في ليلة كئيبة من ليالي نوفمبر، رأيت إنجاز
أعمالي الشاقة. وبقلق كاد يبلغ حد العذاب، جمعت
أدوات الحياة حولي، كي أنفخ شرارة الوجود في
الشيء العديم الحياة الممدد عند قدميّ.»
```

المطالبة متطابقة؛ وحدها مساحة عمل GlossWise الدائمة قد تغيّرت.
يجب أن تستعيد الجلسة الجديدة تلك الحالة بدل الاعتماد على ذاكرة المحادثة. ويظهر
التغيير المهم الآن بوضوح:

| اللغة | قد يستخدم خط الأساس | صياغة موجّهة من GlossWise |
| --- | --- | --- |
| الصينية | `生命工具` · `存在的火花` | `生命仪器` · `生命之火` |
| الفرنسية | `instruments de la vie` · `étincelle de vie` | `instruments de vie` · `étincelle d'existence` |
| الألمانية | `Werkzeuge des Lebens` · `Lebensfunken` | `Instrumente des Lebens` · `Funken des Seins`¹ |
| الروسية | `инструменты жизни` · `искра жизни` | `орудия жизни` · `искру бытия`¹ |
| اليابانية | `生命の道具` · `命の火花` | `生命の器具` · `存在の火花` |

¹ يصرّف الوكيل الذكي الصيغة المفضّلة الأصلية لتلائم هذه الجملة.

<details>
<summary>إحدى النتائج الناجحة الموجّهة من GlossWise</summary>

**الصينية**

> 那是十一月一个阴沉的夜晚，我目睹了自己辛劳的成果。怀着近乎痛苦的焦虑，我把生命仪器聚集在身边，想把生命之火注入躺在我脚边的无生命之物中。

**الفرنسية**

> Ce fut par une lugubre nuit de novembre que je contemplai l’accomplissement de mes travaux. Avec une anxiété qui confinait presque à l’agonie, je rassemblai autour de moi les instruments de vie afin d’insuffler une étincelle d'existence à la chose inanimée étendue à mes pieds.

**الألمانية**

> Es war in einer trüben Novembernacht, als ich die Vollendung meiner Mühen erblickte. Mit einer Angst, die beinahe an Qual grenzte, versammelte ich die Instrumente des Lebens um mich, um dem leblosen Ding zu meinen Füßen einen Funken des Seins einzuhauchen.

**الروسية**

> В мрачную ноябрьскую ночь я увидел завершение своих трудов. С тревогой, почти переходившей в агонию, я собрал вокруг себя орудия жизни, чтобы вдохнуть искру бытия в безжизненное создание, лежавшее у моих ног.

**اليابانية**

> 十一月の陰鬱な夜、私は自らの労苦の成就を目の当たりにした。苦悶に近い不安を抱えながら、私は生命の器具を周囲に集め、足元に横たわる生命なきものへ存在の火花を吹き込もうとした。

</details>

لم يُنشئ GlossWise هذه الجمل. بل أنشأها الوكيل الذكي المتصل؛ وقد جعل GlossWise
المصطلحات المعتمدة قابلة للاسترجاع والفحص قبل الإنشاء.

### 5. ابحث عنه وعدّله لاحقًا

لا حاجة إلى معرّفات السجلات:

```text
/glosswise ابحث عن المصطلح المتعلق بشرارة في `frankenstein-lab`. اعرض صيغه المفضّلة
في جدول موجز.
```

ثم عدّله بصورة طبيعية:

```text
/glosswise غيّر الصيغة اليابانية المفضّلة فقط لـ “spark of being” إلى
`生命の火花`. أبقِ كل لغة أخرى بلا تغيير وأرني السجل المحفوظ.
```

يُختبر مسار الإعداد ← الإنشاء ← التنظيم ← إعادة التشغيل ← موجز الترجمة ← البحث ← التحرير الكامل هذا
على حزمة wheel مثبّتة وجلستي MCP مستقلتين عبر stdio في
[`tests/test_quickstart.py`](https://github.com/Magolor/GlossWise/blob/master/tests/test_quickstart.py).

## <a id="everyday-prompts"></a> مطالبات يومية

بعد الاتصال، يمكن أن يبقى العمل المعتاد ضمن المحادثة. تُجري مطالبات الإدارة أدناه
تغييرات مقصودة؛ أما مطالبات الاستعلام والترجمة فهي للقراءة فقط ما لم
تطلب صراحةً حفظ شيء.

### إدارة مساحات العمل والمصطلحات

- `/glosswise أنشئ مساحة عمل باسم <name> واخترها.`
- `/glosswise في مساحة العمل <name>، اضبط اللغات الافتراضية على الإنجليزية والصينية واليابانية.`
- `/glosswise في مساحة العمل <name>، احفظ “rate limit” كمصطلح مفضّل نشط بصيغة إنجليزية “rate limit”، وصينية “速率限制”، ويابانية “レート制限”. أرني السجل المحفوظ.`
- `/glosswise ابحث عن “rate limit” في مساحة العمل <name>. غيّر صيغته اليابانية المفضّلة فقط إلى “速度制限”، وحافظ على كل حقل وصيغة أخرى، ثم أرني السجل المحدّث.`
- `/glosswise أرشف المصطلح “rate limit” في مساحة العمل <name> كي يُستبعد من البحث العادي عن المصطلحات النشطة. اطلب تأكيدي قبل إجراء التغيير.`

### البحث عن الإرشادات والترجمة

- `/glosswise في مساحة العمل <name>، ابحث عن مصطلحات نشطة مرتبطة بالمصادقة. اعرض صيغها المفضّلة والمحظورة بالإنجليزية والصينية واليابانية. لا تعدّل شيئًا.`
- `/glosswise في مساحة العمل <name>، ابحث عن قواعد وأمثلة لترجمة رسائل الأخطاء إلى الفرنسية. اعرض الأولويات والأنماط والتعارضات. لا تعدّل شيئًا.`
- `/glosswise تحقّق من “Requests over this limit are rejected.” في مساحة العمل <name>. اسرد المصطلحات والقواعد المطابقة دون ترجمة أو حفظ أي شيء.`
- `/glosswise استخدم مساحة العمل <name>. ترجم “The client retries the request after the rate limit resets.” من الإنجليزية إلى الصينية واليابانية. أعدّ موجز الترجمة الجديد من GlossWise لكل لغة مستهدفة، وطبّق المصطلحات المفضّلة النشطة والقواعد، وأشر إلى التعارضات، وحدّد النموذج أو المضيف الذي نفّذ الترجمة.`
- `/glosswise استخدم مساحة العمل <name>. ترجم المقطع الإنجليزي أدناه إلى الفرنسية. أعدّ أولًا موجز الترجمة من GlossWise، ثم اعرض الترجمة يتبعها جدول موجز بكل مصطلح أو قاعدة أو مثال مخزّن طبّقته: <paste source passage>.`
- `/glosswise راجع هذه الترجمة الفرنسية مقابل مساحة العمل <name>. أبلغ عن المصطلحات المفضّلة المفقودة والصيغ المحظورة والقواعد المتعارضة؛ لا تعِد الصياغة ولا تحفظ شيئًا ما لم أطلب ذلك: <paste translation>.`

استخدم `glosswise ws ls` و`glosswise ws use <name>` و
`glosswise ws get` عندما يكون الفحص السريع في الطرفية أنسب من المحادثة.

## الترجمة المضمنة ونطاقات الملفات وOCR لملفات PDF

تستخدم الترجمة المباشرة إعداد HeavenBase `LLMSession` مسبقًا ومسمّى.
وتورد كل نتيجة الإعداد والبوابة والمزوّد والنموذج ومعرّف النموذج بعد حلها.
اختر الإعداد وسلوك عدم اليقين كلًا على حدة:

```console
glosswise config llm chat
glosswise config mode auto
glosswise translate "Run this query." -sl en -tl ja
glosswise translate "Run this query." -sl en -tl ja --preset chat
```

الأوضاع هي `yolo` (ترجمة فورية)، و`elicit` (أسئلة مصطلحية مركزة
مع خيارات)، و`auto` (التكيف مع الأدلة المتاحة)، و`explain`
(الترجمة وشرح كل اختيار مهم)، و`custom` مع `--prompt`.
يصيّر HeavenBase مطالبة النظام عبر `hb.Prompt` ويحل الإعداد المسبق المسمّى.
استخدم `chat` لخيار الدردشة السريعة الحالي، أو ثبّت إعدادًا مخصصًا
دون تكرار بيانات اعتماد المزوّد داخل GlossWise:

```console
hb cfg set heavenbase.llm.presets.glosswise-translate.model deepseek-v4-flash
glosswise config llm glosswise-translate
```

تقبل `scan` و`brief` و`translate` نطاقات شاملة تبدأ من 1 باستخدام
`--start-line` و`--end-line` للنص المباشر وstdin ومدخل `@file`. ويضيف ملف
MCP المحلي المصرح به أدوات ملفات مكافئة.

لمعالجة PDF، صرّح بدليله ونفّذ OCR للصفحات المطلوبة فقط عبر
إعداد LLM المسبق في HeavenBase، ثم تصفح النص المحفوظ لكل صفحة
باستخدام المقبض القصير `gw-...`:

```console
glosswise ws files -r /absolute/path/to/documents
glosswise pdf ocr /absolute/path/to/documents/manual.pdf --start-page 4 --end-page 8
glosswise doc read gw-0123456789ab 4 --start-line 1 --end-line 80
glosswise doc rm gw-0123456789ab
```

يخزّن `ws files` قائمة سماح بالقراءة خاصة بمساحة العمل؛ كرّر
`-r/--root` لكل دليل. وهو لا يرفع الملفات ولا ينسخها ولا يسجلها.
كرّر `-e/--encoding` فقط عندما تتطلب الملفات ترميزات نصية صارمة إضافية؛
ويُسمح بـ UTF-8 افتراضيًا.

يصيّر GlossWise صفحة واحدة ويتعرف عليها في كل مرة ويحذف صورتها فورًا.
ويبلّغ عن التكرار الطويل المريب بدل حذفه بصمت. اضبط `ocr-local` باستخدام
`hb cfg set
heavenbase.llm.presets.ocr-local.<field-or-path> <value>`؛ وتشمل الإعدادات
`desc` و`gateway` و`provider` و`model` و`default_args`؛ واختر إعدادًا آخر عبر `glosswise config ocr <preset>`.

## <a id="mcp-server"></a> خادم MCP

### stdio محلي

ينبغي لمعظم عملاء سطح المكتب والوكلاء الأذكياء البرمجيين استخدام:

```console
glosswise mcp --json
```

تبدأ العملية الفرعية المُنشأة الخادم الكامل بأدوات القراءة وCRUD وSkill
وإدارة مساحات العمل. يجب أن يكون الملف التنفيذي `glosswise` ضمن `PATH`
لعميل MCP.

### HTTP محلي

لتشغيل خادم HTTP انسيابي طويل العمر:

```console
glosswise mcp --transport http
```

يرتبط افتراضيًا بـ `127.0.0.1:61055` ويقدّم MCP على
`http://127.0.0.1:61055/mcp`. اطبع ملف تعريف عميل MCP المطابق باستخدام:

```console
glosswise mcp --json --transport http
```

اختر نقطة نهاية محلية أخرى عند الحاجة:

```console
glosswise mcp --transport http --host 127.0.0.1 --port 61056
```

لا يضيف GlossWise مصادقة شبكية. أبقِ الخادم على مضيف loopback
ما لم توفّر طبقة موثوقة أخرى المصادقة وأمن
النقل.

### أدوات MCP

تقبل أدوات البيانات والسياق `workspace_id` اختياريًا. وعند إغفاله،
يستخدم GlossWise مساحة العمل النشطة ثم المساحة الافتراضية المُدارة.

| الأداة | الغرض | `read` | `full` | `local` |
| --- | --- | :---: | :---: | :---: |
| `glosswise_workspace_info` | عرض إمكانات مساحة العمل والتلميحات اللغوية. | ✓ | ✓ | ✓ |
| `glosswise_prepare_translation` | إنشاء موجز الترجمة للنص المصدر. | ✓ | ✓ | ✓ |
| `glosswise_search_terms` | البحث عن المصطلحات. | ✓ | ✓ | ✓ |
| `glosswise_search_rules` | البحث عن القواعد. | ✓ | ✓ | ✓ |
| `glosswise_search_examples` | البحث عن الأمثلة. | ✓ | ✓ | ✓ |
| `glosswise_scan_text` | فحص النص بحثًا عن تطابقات المصطلحات والقواعد. | ✓ | ✓ | ✓ |
| `glosswise_list_records` | سرد المصطلحات أو القواعد أو الأمثلة. | ✓ | ✓ | ✓ |
| `glosswise_get_record` | جلب سجل واحد بحسب معرّف الكائن. | ✓ | ✓ | ✓ |
| `glosswise_put_term` | إنشاء مصطلح أو تحديثه مع صيغه. | — | ✓ | ✓ |
| `glosswise_put_rule` | إنشاء قاعدة أو تحديثها. | — | ✓ | ✓ |
| `glosswise_put_example` | إنشاء مثال أو تحديثه. | — | ✓ | ✓ |
| `glosswise_archive` | أرشفة سجل واحد. | — | ✓ | ✓ |
| `glosswise_list_workspaces` | سرد مساحات العمل. | ✓ | ✓ | ✓ |
| `glosswise_get_workspace` | جلب سجل مساحة عمل واحد منقّح. | ✓ | ✓ | ✓ |
| `glosswise_create_workspace` | إنشاء مساحة عمل مُدارة. | — | ✓ | ✓ |
| `glosswise_set_workspace_languages` | ضبط التلميحات اللغوية لمساحة العمل. | — | ✓ | ✓ |
| `glosswise_activate_workspace` | اختيار مساحة العمل النشطة. | — | ✓ | ✓ |
| `glosswise_deactivate_workspace` | إلغاء الاختيار النشط. | — | ✓ | ✓ |
| `glosswise_remove_workspace` | إلغاء تسجيل مساحة عمل. | — | ✓ | ✓ |
| `glosswise_open_workspace` | فتح مساحة عمل وعرض إمكاناتها. | ✓ | ✓ | ✓ |
| `glosswise_health_workspace` | فحص سلامة السجل وبيئة التشغيل. | ✓ | ✓ | ✓ |
| `glosswise_read_skill` | قراءة تعليمات الوكيل الذكي المضمّنة. | ✓ | ✓ | ✓ |
| `glosswise_scan_file` | فحص ملف نصي محلي مصرح به للخادم. | — | — | ✓ |
| `glosswise_prepare_file` | إعداد موجز من نطاق ملف نصي مصرح به. | — | — | ✓ |
| `glosswise_ocr_pdf` | إجراء OCR لصفحات PDF مصرح بها إلى مقبض قصير. | — | — | ✓ |
| `glosswise_list_documents` | سرد مقابض مستندات OCR المؤقتة. | — | — | ✓ |
| `glosswise_get_document` | فحص بيان مستند OCR. | — | — | ✓ |
| `glosswise_read_document` | قراءة نطاق أسطر محدود من صفحة OCR. | — | — | ✓ |
| `glosswise_remove_document` | إزالة مستند OCR مؤقت. | — | — | ✓ |

### ملفات تعريف MCP

تتحكم ملفات تعريف MCP في إتاحة الأدوات، لا في محتويات مساحة العمل ولا ملف Skill
المثبّت:

| ملف تعريف MCP | النطاق الدقيق | الاستخدام المقصود |
| --- | --- | --- |
| `full` | الأدوات الـ22 المحددة في عمود `full`. | ملف تعريف MCP الافتراضي. يدعم البحث وموجزات الترجمة وCRUD وفحص Skill وإدارة مساحات العمل. يختار `glosswise mcp` المجرد و`glosswise mcp --json` ملف تعريف MCP هذا. |
| `read` | الأدوات الـ13 المحددة في عمود `read`. | استخدام المصطلحات/السياق وفحص مساحة العمل للقراءة فقط. ولا يمكنه تنظيم السجلات أو تغيير الاختيار أو إدارة مساحات العمل. |
| `local` | جميع أدوات `full` الـ22 إضافةً إلى سبع أدوات مستندات محلية مصرح بها. | وصول كامل متقدم لنطاقات النص وOCR لملفات PDF. لا يمنح الملف وحده الوصول؛ صرّح بالجذور أولًا. |

يثبّت `glosswise setup` ملف Skill واحدًا مستقلًا عن ملف تعريف MCP. ولا تختار Skill
ملف تعريف MCP: فخادم MCP المتصل هو الذي يحدد الأدوات التي يستطيع الوكيل الذكي
استدعاءها. يستخدم الإعداد المعتاد `full`، وهو ملف تعريف MCP غير المحلي الوحيد الذي
يدعم كل مسارات الإدارة والترجمة التي تعلّمها Skill.

لتغيير تثبيت موجود، احتفظ بـSkill المثبّتة وغيّر فقط
أمر خادم MCP في إعدادات الوكيل الذكي، ثم أعد تشغيله أو أعد الاتصال
بالوكيل الذكي:

```console
glosswise mcp                 # full (default)
glosswise mcp --profile read  # read-only
glosswise mcp --profile local # full plus authorized text/PDF tools
```

استخدم `glosswise mcp --json --profile <profile>` لإنشاء JSON بديل للعميل.
ولا حاجة إلى إعادة تشغيل `glosswise setup` عند تبديل ملفات تعريف MCP.
وتؤدي العودة إلى `glosswise mcp` المجرد إلى استعادة ملف تعريف MCP الافتراضي `full`.

تعيد كل أداة مغلف JSON ذا إصدار. ينبغي للوكلاء الأذكياء فحص `error`
و`warnings` و`conflicts` و`truncated` قبل استخدام `items`.

## مرجع CLI

| المهمة | الأمر | مقبول أيضًا |
| --- | --- | --- |
| سرد مساحات العمل | `glosswise ws ls` | `ws list` |
| فحص مساحة عمل | `glosswise ws get [<name>]` | — |
| إنشاء مساحة عمل | `glosswise ws create [<name>]` | — |
| اختيار مساحة عمل | `glosswise ws use <name>` | `ws activate`, `ws act` |
| إلغاء الاختيار | `glosswise ws deact` | `ws deactivate` |
| إلغاء تسجيل مساحة عمل | `glosswise ws rm <name>` | `ws unset`, `ws remove` |
| عرض الإعدادات العامة | `glosswise config get` | — |
| ضبط اللغات العامة | `glosswise config lang -l en -l <language>` | `config languages` |
| ضبط سلوك الترجمة | `glosswise config mode <mode>` | — |
| ضبط إعداد LLM المسبق للترجمة | `glosswise config llm <preset>` | — |
| ضبط التلميحات اللغوية | `glosswise ws lang -l en -l <language>` | `ws languages` |
| التصريح بالجذور المحلية | `glosswise ws files -r <directory>` | — |
| إنشاء البيانات أو تحديثها | `glosswise term set @term.json` | `term put` |
| جلب سجل واحد | `glosswise term get <object-id>` | — |
| سرد البيانات | `glosswise term ls` | `term list` |
| البحث في البيانات | `glosswise term search "query"` | — |
| أرشفة البيانات | `glosswise term archive <object-id>` | — |
| فحص مقطع | `glosswise scan "text"` | — |
| إعداد السياق | `glosswise brief "text"` | — |
| الترجمة عبر LLMSession | `glosswise translate "text"` | — |
| إجراء OCR لصفحات PDF | `glosswise pdf ocr <path>` | — |
| تصفح نص OCR | `glosswise doc read <handle> <page>` | — |

استبدل `term` بـ`rule` أو `example` لمسار
العمل set/get/list/search/archive نفسه. شغّل `glosswise --help` أو
`glosswise <group> --help` للاطلاع على سطح الأوامر الكامل.

## <a id="python-sdk"></a> حزمة Python SDK

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

تستخدم `GlossWiseApp.open()` مساحة العمل النشطة أو تنشئ الافتراضية المُدارة
بعد إعداد اللغات العامة.
استخدم `GlossWiseApp.create("<name>")` لمساحة عمل مُدارة ذات اسم صريح
و`GlossWiseApp.load()` عندما ينبغي أن يكون الغياب خطأ. ويمكن للتطبيقات التي
تمتلك بالفعل مساحة عمل HeavenBase استخدام `workspace.glosswise` مباشرة.

## آلية العمل

1. يتصل وكيل ذكي عبر MCP أو CLI أو Python SDK.
2. يحل GlossWise مساحة العمل المطلوبة أو يستخدم النشطة/الافتراضية.
3. يسترجع المصطلحات والقواعد والأمثلة ذات الصلة.
4. يصنّف `brief` تلك الأدلة ويجمعها مع التحذيرات والتعارضات.
5. يترجم الوكيل المضيف، أو يستدعي `translate` كائن HeavenBase `LLMSession`
   بعقد تديره `hb.Prompt` وإعداد مسبق ظاهر.
6. يمكن للمستدعي فحص الترجمة أو إجراء OCR لصفحات PDF المصرح بها
   إلى نص مؤقت محدود لكل صفحة.

يبقي GlossWise التخزين وسياسة المصطلحات خلف عمليات تركّز على المهام؛
ولا يحتاج الوكلاء الأذكياء إلى وصول عام إلى قاعدة البيانات.

## للمطورين

GlossWise مشروع توضيحي يبيّن كيف يمكن لتطبيق مستقل ونظيف استخدام
HeavenBase. وهو يوضح المزايا العملية لما يلي:

- امتداد معياري مثبّت عند `workspace.glosswise`؛
- مساحات عمل مُدارة وافتراضيات يملكها التطبيق؛
- إعدادات مستخدم على مستوى Context وإعدادات HeavenBase LLM مسبقة ظاهرة؛
- كيانات واستعلامات واسترجاع محسوب ذات أنواع محددة؛
- OCR لكل صفحة عبر HeavenBase LLM مع مقابض مستندات محدودة؛
- سجل أوامر واحد مكشوف عبر خلفيات CLI متعددة؛
- أدوات MCP منشأة من مجموعة أدوات HeavenBase؛ و
- Skill مضمّنة تعلّم الوكلاء الأذكياء مسار عمل التطبيق.

تستخدم ترجمة CLI المباشرة وPython إعداد HeavenBase المسبق عبر
`LLMSession`؛ ويستخدم مضيفو MCP النموذج الذي ضبطوه.

فحوص التطوير:

```console
git clone https://github.com/Magolor/GlossWise.git
cd GlossWise
bash scripts/sync-env.bash
bash scripts/flake.bash --ci
bash scripts/test.bash
bash scripts/test.bash -m full
uv build
```

راجع [CONTRIBUTING.md](CONTRIBUTING.md) لمعرفة مسار عمل المساهمة و
[SECURITY.md](SECURITY.md) للإبلاغ الخاص عن الثغرات.

الحدود الحالية: تُثبّت امتدادات HeavenBase صراحةً، ولا يمكن تعطيل
الامتدادات الممكّنة، كما أن ترحيل المخطط غير مؤتمت، ولا يختار GlossWise
نموذج ترجمة ولا يخفيه.

## الاستشهاد

إذا دعم GlossWise بحثك أو مشروعك، فاستشهد بالبرنامج باستخدام
[CITATION.cff](CITATION.cff) أو:

```bibtex
@software{glosswise_2026,
  author  = {Magolor},
  title   = {GlossWise: Terminology-safe translation for AI agents},
  year    = {2026},
  version = {0.1.0.5},
  url     = {https://github.com/Magolor/GlossWise}
}
```

بُني GlossWise على [HeavenBase](https://ahvn.top).

## الترخيص

يتوفر GlossWise بموجب [ترخيص MIT](LICENSE).
