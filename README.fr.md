# GlossWise

<p align="center">
  <a href="README.en.md">English</a> ·
  <a href="README.ar.md">العربية</a> ·
  <a href="README.zh.md">中文</a> ·
  <strong>Français</strong> ·
  <a href="README.ru.md">Русский</a> ·
  <a href="README.es.md">Español</a> ·
  <a href="README.de.md">Deutsch</a> ·
  <a href="README.ja.md">日本語</a>
</p>

<p align="center">
  <img src="docs/assets/glosswise-banner.png" alt="GlossWise — des traductions terminologiquement fiables pour les agents IA" width="100%">
</p>

<p align="center">
  <a href="https://github.com/Magolor/GlossWise/actions/workflows/ci.yml"><img src="https://github.com/Magolor/GlossWise/actions/workflows/ci.yml/badge.svg?branch=master" alt="Intégration continue"></a>
  <a href="https://www.python.org/"><img src="https://img.shields.io/badge/Python-3.10–3.13-3776AB" alt="Python 3.10 à 3.13"></a>
  <a href="https://ahvn.top"><img src="https://img.shields.io/badge/HeavenBase-0.1.2.1-6957E5" alt="HeavenBase 0.1.2.1"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-green.svg" alt="Licence MIT"></a>
</p>

<p align="center">
  <a href="#install">Installer</a> ·
  <a href="#connect-an-agent">Connecter un agent IA</a> ·
  <a href="#try-it-teach-once-translate-consistently">Essayer la démo</a> ·
  <a href="#everyday-prompts">Prompts courants</a> ·
  <a href="#mcp-server">Outils MCP</a> ·
  <a href="#python-sdk">SDK Python</a>
</p>

GlossWise stocke les termes approuvés, les règles de traduction et les exemples, puis prépare
un dossier de traduction compact pour l’agent IA ou l’application qui l’appelle. Les agents hôtes
traduisent avec leur propre modèle ; le CLI direct utilise un preset LLM HeavenBase visible.

GlossWise est disponible sous forme de CLI, de serveur MCP et de SDK Python. La version `0.1.0.5`
prend en charge `heavenbase>=0.1.2.1`.

## <a id="install"></a> Installation

GlossWise nécessite Python 3.10 à 3.13. Installez directement la version actuelle des sources
depuis GitHub. Avant l’installation, vous pouvez [examiner le Skill exact de l’agent IA](SKILL.md) :

```console
python -m pip install "git+https://github.com/Magolor/GlossWise.git"
glosswise setup -l en -l zh
```

Pour examiner les sources ou y contribuer :

```console
git clone https://github.com/Magolor/GlossWise.git
cd GlossWise
python -m pip install .
glosswise setup -l en -l zh
```

`setup` exige les langues entre lesquelles vous traduisez habituellement et
les enregistre globalement, crée et active `default` avec ces langues, puis
installe le Skill de l’agent IA GlossWise dans :

- `~/.agents/skills/glosswise`
- `~/.claude/skills/glosswise`

Le Skill public à la racine et sa copie intégrée installée par `setup` restent
strictement identiques octet pour octet.

Les données de l’espace de travail sont gérées automatiquement sous `~/.glosswise/`. Vous n’avez pas
à choisir ni à exposer de base de données. Les nouveaux espaces héritent des langues
globales ; modifiez-les avec `glosswise config lang -l en -l <language>`.

Vérifiez l’installation :

```console
glosswise ws ls
glosswise ws get
```

## <a id="connect-an-agent"></a> Connecter un agent IA

`glosswise setup` a déjà installé les Skills GlossWise commun et Claude.
Connectez le même serveur MCP global depuis tout hôte pris en charge :

| Hôte | Configuration unique |
| --- | --- |
| [Claude Code](https://code.claude.com/docs/en/mcp) | `claude mcp add --scope user glosswise -- glosswise mcp` |
| [Codex](https://developers.openai.com/codex/mcp/) | `codex mcp add glosswise -- glosswise mcp` |
| [Cursor](https://docs.cursor.com/context/model-context-protocol) | Enregistrez `glosswise mcp --json` sous `~/.cursor/mcp.json`. |
| [VS Code / Copilot](https://code.visualstudio.com/docs/copilot/chat/mcp-servers) | Ajoutez à `.vscode/mcp.json` une entrée stdio `servers.glosswise` avec la commande `glosswise` et les arguments `["mcp"]`. |
| [OpenCode](https://opencode.ai/docs/mcp-servers/) | Ajoutez l’entrée MCP locale ci-dessous à `~/.config/opencode/opencode.json`. |
| [OpenClaw](https://ahvn.top/quickstart/heavenbase-mcp#3-connect-your-agent) | Lancez `glosswise mcp --transport http`, puis définissez `mcp.servers.glosswise` sur `http://127.0.0.1:61055/mcp` avec le transport `streamable-http`. |
| [Hermes](https://ahvn.top/quickstart/heavenbase-mcp#3-connect-your-agent) | Lancez `glosswise mcp --transport http`, puis ajoutez son URL sous `mcp_servers.glosswise` dans `~/.hermes/config.yaml`. |
| [LM Studio](https://lmstudio.ai/docs/app/mcp) | Ouvrez **Program/Developer → Install → Edit mcp.json**, puis collez la sortie de `glosswise mcp --json`. |
| [Qwen Code](https://qwenlm.github.io/qwen-code-docs/en/users/features/mcp/) | `qwen mcp add --scope user glosswise glosswise mcp` |
| [HeavenBase](https://ahvn.top/quickstart/heavenbase-mcp#3-connect-your-agent) | Lancez `glosswise mcp --transport http`, puis `hb llm session --mcp http://127.0.0.1:61055/mcp`. |

Pour [OpenCode](https://opencode.ai/docs/mcp-servers/), ajoutez ceci au fichier global
`~/.config/opencode/opencode.json` :

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

Vérifiez la connexion avec la commande de l’hôte qui liste les serveurs MCP,
puis redémarrez l’agent lorsque sa documentation l’exige.

Ouvrez une nouvelle conversation et dites :

```text
/glosswise Liste mes espaces de travail et indique-moi lequel est actif.
```

L’agent IA peut maintenant créer des espaces de travail, gérer la terminologie, y effectuer des recherches et préparer
des dossiers de traduction pour vous. Vous n’avez pas besoin d’écrire du JSON ni de gérer une
base de données. Un Skill et une connexion MCP uniques fonctionnent pour tous les espaces de travail
GlossWise.

Pour un autre client MCP compatible avec stdio, affichez le profil MCP portable :

```console
glosswise mcp --json
```

## <a id="try-it-teach-once-translate-consistently"></a> Essayez : enseignez une fois, traduisez avec cohérence

Cette démonstration commence par une traduction ordinaire du modèle, enseigne à GlossWise deux
décisions terminologiques en langage naturel, puis répète la demande d’origine
dans une nouvelle session d’agent IA. L’extrait provient de
[*Frankenstein* de Mary Shelley](https://www.gutenberg.org/cache/epub/42324/pg42324-images.html),
une œuvre pionnière de la science-fiction appartenant au domaine public.

### 1. Créer un espace de travail

Demandez à votre agent IA :

```text
/glosswise Crée et sélectionne un espace de travail GlossWise nommé `frankenstein-lab`.
Définis ses langues par défaut sur l’anglais, le chinois, le français, l’allemand, le russe et le japonais.
```

Vous pouvez aussi utiliser ces deux courtes commandes CLI :

```console
glosswise ws create frankenstein-lab
glosswise ws lang -l en -l zh -l fr -l de -l ru -l ja
```

`ws create` sélectionne automatiquement le nouvel espace de travail. Répétez `-l/--lang`
pour chaque langue ordonnée. Cet ensemble rappelle aux agents de recueillir les six formes privilégiées, sans
pour autant imposer une restriction stricte sur les langues.

### 2. Traduire avant d’enseigner à GlossWise

Envoyez ce paragraphe à l’agent IA :

```text
/glosswise Utilise l’espace de travail `frankenstein-lab`. Traduis le paragraphe ci-dessous
en chinois, français, allemand, russe et japonais. Consulte d’abord GlossWise pour trouver
des consignes pertinentes, puis indique le modèle ou l’hôte qui a effectué la traduction.

« Ce fut par une lugubre nuit de novembre que je contemplai l’accomplissement de mes
travaux. Avec une anxiété qui confinait presque à l’agonie, je rassemblai autour de moi les
instruments de vie afin d’insuffler une étincelle d’existence à la
chose inanimée étendue à mes pieds. »
```

La première formulation dépend du modèle de traduction de l’agent IA. Celui-ci peut choisir
des expressions littérales telles que « spark of being » → `存在的火花`,
`étincelle de vie`, `Lebensfunken`, `искра жизни` ou `命の火花`.

### 3. Enseigner deux décisions par la conversation

Envoyez un autre message :

```text
/glosswise Enregistre-les comme termes privilégiés actifs dans l’espace de travail `frankenstein-lab`.
Les formes cibles correspondent aux décisions terminologiques de mon projet et ne constituent pas des affirmations
sur les traductions officielles du roman.

1. « instruments of life » désigne l’appareillage utilisé dans l’expérience :
   chinois 生命仪器 ; français instruments de vie ;
   allemand Instrumente des Lebens ; russe орудия жизни ;
   japonais 生命の器具.

2. « spark of being » désigne l’essence animatrice insufflée à la matière inerte :
   chinois 生命之火 ; français étincelle d'existence ;
   allemand Funke des Seins ; russe искра бытия ;
   japonais 存在の火花.

Conserve aussi les formes sources anglaises. Emploie exactement la terminologie privilégiée lorsque
la grammaire de la langue cible le permet ; sinon, fléchis-la sans modifier
le concept approuvé. Dis-moi quand les deux enregistrements sont stockés.
```

L’agent IA gère les appels CRUD structurés. S’il manque une langue demandée pour l’espace de travail,
le Skill installé lui demande de solliciter l’utilisateur, de proposer une forme à
confirmer, ou de signaler clairement qu’une forme a été générée par l’agent IA.

### 4. Ouvrir une nouvelle session et répéter la même demande

Terminez la conversation en cours et ouvrez une nouvelle session d’agent IA. Envoyez de nouveau le prompt exact de
l’étape 2, sans ajouter de rappel concernant les termes que vous venez de stocker :

```text
/glosswise Utilise l’espace de travail `frankenstein-lab`. Traduis le paragraphe ci-dessous
en chinois, français, allemand, russe et japonais. Consulte d’abord GlossWise pour trouver
des consignes pertinentes, puis indique le modèle ou l’hôte qui a effectué la traduction.

« Ce fut par une lugubre nuit de novembre que je contemplai l’accomplissement de mes
travaux. Avec une anxiété qui confinait presque à l’agonie, je rassemblai autour de moi les
instruments de vie afin d’insuffler une étincelle d’existence à la
chose inanimée étendue à mes pieds. »
```

Le prompt est identique ; seul l’espace de travail persistant de GlossWise a changé.
La nouvelle session doit récupérer cet état au lieu de s’appuyer sur la mémoire de la conversation. La
différence importante est désormais visible :

| Langue | Une traduction de référence peut employer | Formulation guidée par GlossWise |
| --- | --- | --- |
| Chinois | `生命工具` · `存在的火花` | `生命仪器` · `生命之火` |
| Français | `instruments de la vie` · `étincelle de vie` | `instruments de vie` · `étincelle d'existence` |
| Allemand | `Werkzeuge des Lebens` · `Lebensfunken` | `Instrumente des Lebens` · `Funken des Seins`¹ |
| Russe | `инструменты жизни` · `искра жизни` | `орудия жизни` · `искру бытия`¹ |
| Japonais | `生命の道具` · `命の火花` | `生命の器具` · `存在の火花` |

¹ L’agent IA fléchit la forme privilégiée canonique pour l’adapter à cette phrase.

<details>
<summary>Exemple de résultat obtenu avec succès grâce à GlossWise</summary>

**Chinois**

> 那是十一月一个阴沉的夜晚，我目睹了自己辛劳的成果。怀着近乎痛苦的焦虑，我把生命仪器聚集在身边，想把生命之火注入躺在我脚边的无生命之物中。

**Français**

> Ce fut par une lugubre nuit de novembre que je contemplai l’accomplissement de mes travaux. Avec une anxiété qui confinait presque à l’agonie, je rassemblai autour de moi les instruments de vie afin d’insuffler une étincelle d'existence à la chose inanimée étendue à mes pieds.

**Allemand**

> Es war in einer trüben Novembernacht, als ich die Vollendung meiner Mühen erblickte. Mit einer Angst, die beinahe an Qual grenzte, versammelte ich die Instrumente des Lebens um mich, um dem leblosen Ding zu meinen Füßen einen Funken des Seins einzuhauchen.

**Russe**

> В мрачную ноябрьскую ночь я увидел завершение своих трудов. С тревогой, почти переходившей в агонию, я собрал вокруг себя орудия жизни, чтобы вдохнуть искру бытия в безжизненное создание, лежавшее у моих ног.

**Japonais**

> 十一月の陰鬱な夜、私は自らの労苦の成就を目の当たりにした。苦悶に近い不安を抱えながら、私は生命の器具を周囲に集め、足元に横たわる生命なきものへ存在の火花を吹き込もうとした。

</details>

GlossWise n’a pas généré ces phrases. C’est l’agent IA connecté qui l’a fait ; GlossWise
a rendu la terminologie approuvée récupérable et vérifiable avant la génération.

### 5. Retrouver et modifier ultérieurement

Aucun identifiant d’enregistrement n’est nécessaire :

```text
/glosswise Trouve le terme relatif à une étincelle dans `frankenstein-lab`. Affiche ses formes privilégiées
dans un tableau compact.
```

Modifiez-le ensuite en langage naturel :

```text
/glosswise Modifie uniquement la forme japonaise privilégiée de « spark of being » en
`生命の火花`. Conserve toutes les autres langues sans modification et montre-moi l’enregistrement sauvegardé.
```

Ce parcours complet configuration → création → curation → redémarrage → dossier de traduction → recherche → modification est
testé sur un paquet wheel installé et deux sessions MCP stdio indépendantes dans
[`tests/test_quickstart.py`](https://github.com/Magolor/GlossWise/blob/master/tests/test_quickstart.py).

## <a id="everyday-prompts"></a> Prompts courants

Une fois la connexion établie, les tâches habituelles peuvent rester dans la conversation. Les prompts de gestion ci-dessous apportent
des modifications volontaires ; les prompts de requête et de traduction sont en lecture seule, sauf s’ils
demandent explicitement d’enregistrer quelque chose.

### Gérer les espaces de travail et la terminologie

- `/glosswise Crée et sélectionne un espace de travail nommé <name>.`
- `/glosswise Dans l’espace de travail <name>, définis les langues par défaut sur l’anglais, le chinois et le japonais.`
- `/glosswise Dans l’espace de travail <name>, enregistre « rate limit » comme terme privilégié actif avec l’anglais « rate limit », le chinois « 速率限制 » et le japonais « レート制限 ». Montre-moi l’enregistrement sauvegardé.`
- `/glosswise Trouve « rate limit » dans l’espace de travail <name>. Modifie uniquement sa forme japonaise privilégiée en « 速度制限 », conserve tous les autres champs et toutes les autres formes, puis montre-moi l’enregistrement mis à jour.`
- `/glosswise Archive le terme « rate limit » dans l’espace de travail <name> afin qu’il soit exclu de la recherche normale des termes actifs. Demande-moi confirmation avant d’effectuer la modification.`

### Rechercher des consignes et traduire

- `/glosswise Dans l’espace de travail <name>, trouve les termes actifs liés à l’authentification. Affiche leurs formes privilégiées et interdites en anglais, en chinois et en japonais. Ne modifie rien.`
- `/glosswise Dans l’espace de travail <name>, trouve les règles et les exemples de traduction des messages d’erreur en français. Affiche les priorités, les styles et les conflits. Ne modifie rien.`
- `/glosswise Vérifie « Requests over this limit are rejected. » dans l’espace de travail <name>. Liste les termes et règles correspondants sans rien traduire ni enregistrer.`
- `/glosswise Utilise l’espace de travail <name>. Traduis « The client retries the request after the rate limit resets. » de l’anglais vers le chinois et le japonais. Prépare un nouveau dossier de traduction GlossWise pour chaque langue cible, applique les termes privilégiés et règles actifs, signale les conflits et indique le modèle ou l’hôte qui a effectué la traduction.`
- `/glosswise Utilise l’espace de travail <name>. Traduis le passage anglais ci-dessous en français. Prépare d’abord un dossier de traduction GlossWise, puis affiche la traduction, suivie d’un tableau compact de tous les termes, règles ou exemples stockés que tu as appliqués : <paste source passage>.`
- `/glosswise Compare cette traduction française à l’espace de travail <name>. Signale les termes privilégiés manquants, les formes interdites et les règles contradictoires ; ne la réécris pas et n’enregistre rien sauf si je le demande : <paste translation>.`

Utilisez `glosswise ws ls`, `glosswise ws use <name>` et
`glosswise ws get` lorsqu’une vérification rapide dans le terminal est plus pratique que la conversation.

## Traduction intégrée, plages de fichiers et OCR PDF

La traduction directe utilise un preset HeavenBase `LLMSession` nommé. Chaque
résultat indique le preset, la passerelle, le fournisseur, le modèle et son
identifiant résolus. Réglez séparément le preset et la prudence :

```console
glosswise config llm chat
glosswise config mode auto
glosswise translate "Run this query." -sl en -tl ja
glosswise translate "Run this query." -sl en -tl ja --preset chat
```

Les modes sont `yolo` (traduction immédiate), `elicit` (questions terminologiques
ciblées avec options), `auto` (adaptation aux preuves disponibles), `explain`
(traduction et explication de chaque choix important) et `custom` avec `--prompt`.
HeavenBase rend le prompt système via `hb.Prompt` et résout le preset nommé.
Utilisez `chat` pour son choix de chat rapide actuel, ou épinglez un preset
dédié sans dupliquer les identifiants fournisseur dans GlossWise :

```console
hb cfg set heavenbase.llm.presets.glosswise-translate.model deepseek-v4-flash
glosswise config llm glosswise-translate
```

`scan`, `brief` et `translate` acceptent des plages inclusives à partir de 1 avec
`--start-line` et `--end-line` pour le texte direct, stdin et `@file`. Le profil
MCP local autorisé offre des outils de fichiers équivalents.

Pour un PDF, autorisez son répertoire, appliquez l’OCR uniquement aux pages utiles
avec le preset LLM HeavenBase configuré, puis parcourez le texte conservé page
par page grâce au handle court `gw-...` :

```console
glosswise ws files -r /absolute/path/to/documents
glosswise pdf ocr /absolute/path/to/documents/manual.pdf --start-page 4 --end-page 8
glosswise doc read gw-0123456789ab 4 --start-line 1 --end-line 80
glosswise doc rm gw-0123456789ab
```

`ws files` enregistre une liste de lecture autorisée propre à l’espace de
travail ; répétez `-r/--root` pour chaque répertoire. Aucun fichier n’est
téléversé, copié ou enregistré. Répétez `-e/--encoding` uniquement pour ajouter
des encodages de texte stricts ; UTF-8 est autorisé par défaut.

GlossWise rend et traite une page à la fois, puis supprime aussitôt son image.
Les longues répétitions suspectes sont signalées, jamais supprimées en silence.
Configurez `ocr-local` avec `hb cfg set
heavenbase.llm.presets.ocr-local.<field-or-path> <value>` ; les réglages incluent
`desc`, `gateway`, `provider`, `model` et `default_args` ; choisissez un autre preset avec `glosswise config ocr <preset>`.

## <a id="mcp-server"></a> Serveur MCP

### stdio local

La plupart des clients de bureau et des agents IA de programmation devraient utiliser :

```console
glosswise mcp --json
```

Le processus enfant généré lance le serveur complet avec les outils de lecture, de CRUD, de Skill et de
gestion des espaces de travail. L’exécutable `glosswise` doit figurer dans le `PATH`
du client MCP.

### HTTP local

Pour exécuter un serveur HTTP streamable de longue durée :

```console
glosswise mcp --transport http
```

Par défaut, il se lie à `127.0.0.1:61055` et sert MCP à l’adresse
`http://127.0.0.1:61055/mcp`. Affichez le profil MCP client correspondant avec :

```console
glosswise mcp --json --transport http
```

Choisissez un autre point de terminaison local si nécessaire :

```console
glosswise mcp --transport http --host 127.0.0.1 --port 61056
```

GlossWise n’ajoute aucune authentification réseau. Maintenez le serveur sur une adresse de bouclage,
sauf si une autre couche de confiance assure l’authentification et la sécurité
du transport.

### Outils MCP

Les outils de données et de contexte acceptent un `workspace_id` facultatif. Lorsqu’il est omis,
GlossWise utilise l’espace de travail actif, puis l’espace par défaut géré.

| Outil | Rôle | `read` | `full` | `local` |
| --- | --- | :---: | :---: | :---: |
| `glosswise_workspace_info` | Afficher les capacités de l’espace de travail et les indications de langue. | ✓ | ✓ | ✓ |
| `glosswise_prepare_translation` | Construire un dossier de traduction pour le texte source. | ✓ | ✓ | ✓ |
| `glosswise_search_terms` | Rechercher des termes. | ✓ | ✓ | ✓ |
| `glosswise_search_rules` | Rechercher des règles. | ✓ | ✓ | ✓ |
| `glosswise_search_examples` | Rechercher des exemples. | ✓ | ✓ | ✓ |
| `glosswise_scan_text` | Rechercher dans le texte les occurrences des termes et des règles. | ✓ | ✓ | ✓ |
| `glosswise_list_records` | Lister les termes, les règles ou les exemples. | ✓ | ✓ | ✓ |
| `glosswise_get_record` | Récupérer un enregistrement par son identifiant d’objet. | ✓ | ✓ | ✓ |
| `glosswise_put_term` | Créer ou mettre à jour un terme et ses formes. | — | ✓ | ✓ |
| `glosswise_put_rule` | Créer ou mettre à jour une règle. | — | ✓ | ✓ |
| `glosswise_put_example` | Créer ou mettre à jour un exemple. | — | ✓ | ✓ |
| `glosswise_archive` | Archiver un enregistrement. | — | ✓ | ✓ |
| `glosswise_list_workspaces` | Lister les espaces de travail. | ✓ | ✓ | ✓ |
| `glosswise_get_workspace` | Récupérer un enregistrement d’espace de travail expurgé. | ✓ | ✓ | ✓ |
| `glosswise_create_workspace` | Créer un espace de travail géré. | — | ✓ | ✓ |
| `glosswise_set_workspace_languages` | Définir les indications de langue de l’espace de travail. | — | ✓ | ✓ |
| `glosswise_activate_workspace` | Sélectionner l’espace de travail actif. | — | ✓ | ✓ |
| `glosswise_deactivate_workspace` | Effacer la sélection active. | — | ✓ | ✓ |
| `glosswise_remove_workspace` | Désenregistrer un espace de travail. | — | ✓ | ✓ |
| `glosswise_open_workspace` | Ouvrir un espace de travail et afficher ses capacités. | ✓ | ✓ | ✓ |
| `glosswise_health_workspace` | Vérifier l’état du registre et de l’environnement d’exécution. | ✓ | ✓ | ✓ |
| `glosswise_read_skill` | Lire les instructions intégrées pour l’agent IA. | ✓ | ✓ | ✓ |
| `glosswise_scan_file` | Analyser un fichier texte local autorisé côté serveur. | — | — | ✓ |
| `glosswise_prepare_file` | Construire un dossier depuis une plage de fichier autorisée. | — | — | ✓ |
| `glosswise_ocr_pdf` | OCRiser des pages PDF autorisées vers un handle court. | — | — | ✓ |
| `glosswise_list_documents` | Lister les handles temporaires de documents OCR. | — | — | ✓ |
| `glosswise_get_document` | Inspecter le manifeste d’un document OCR. | — | — | ✓ |
| `glosswise_read_document` | Lire une plage de lignes bornée d’une page OCR. | — | — | ✓ |
| `glosswise_remove_document` | Supprimer un document OCR temporaire. | — | — | ✓ |

### Profils MCP

Les profils MCP contrôlent l’exposition des outils, et non le contenu des espaces de travail ni le fichier Skill
installé :

| Profil MCP | Périmètre exact | Usage prévu |
| --- | --- | --- |
| `full` | Les 22 outils cochés dans la colonne `full`. | Profil MCP par défaut. Il prend en charge la recherche, les dossiers de traduction, le CRUD, l’examen du Skill et la gestion des espaces de travail. `glosswise mcp` et `glosswise mcp --json` sans autre option sélectionnent ce profil MCP. |
| `read` | Les 13 outils cochés dans la colonne `read`. | Utilisation en lecture seule de la terminologie et du contexte, et inspection des espaces de travail. Il ne permet ni de gérer les enregistrements, ni de changer la sélection, ni d’administrer les espaces de travail. |
| `local` | Les 22 outils de `full`, plus sept outils de documents locaux autorisés. | Serveur avancé pour plages de texte bornées et OCR PDF. Le profil seul n’accorde aucun accès ; autorisez d’abord les racines. |

`glosswise setup` installe un Skill indépendant du profil MCP. Le Skill ne
sélectionne aucun profil MCP : le serveur MCP connecté détermine les outils que l’agent IA peut
appeler. La configuration normale utilise `full`, le seul profil MCP non local qui
prend en charge tous les parcours de gestion et de traduction enseignés par le Skill.

Pour modifier une installation existante, conservez le Skill installé et changez uniquement
la commande du serveur MCP dans la configuration de l’agent IA, puis redémarrez ou reconnectez
l’agent IA :

```console
glosswise mcp                 # full (default)
glosswise mcp --profile read  # read-only
glosswise mcp --profile local # full plus authorized text/PDF tools
```

Utilisez `glosswise mcp --json --profile <profile>` pour générer un nouveau JSON client.
Il est inutile de réexécuter `glosswise setup` lorsque vous changez de profil MCP.
Le retour à la commande simple `glosswise mcp` restaure le profil MCP `full` par défaut.

Chaque outil renvoie une enveloppe JSON versionnée. Les agents IA doivent examiner `error`,
`warnings`, `conflicts` et `truncated` avant d’utiliser `items`.

## Référence CLI

| Tâche | Commande | Également accepté |
| --- | --- | --- |
| Lister les espaces de travail | `glosswise ws ls` | `ws list` |
| Examiner un espace de travail | `glosswise ws get [<name>]` | — |
| Créer un espace de travail | `glosswise ws create [<name>]` | — |
| Sélectionner un espace de travail | `glosswise ws use <name>` | `ws activate`, `ws act` |
| Effacer la sélection | `glosswise ws deact` | `ws deactivate` |
| Désenregistrer un espace de travail | `glosswise ws rm <name>` | `ws unset`, `ws remove` |
| Afficher la configuration globale | `glosswise config get` | — |
| Définir les langues globales | `glosswise config lang -l en -l <language>` | `config languages` |
| Définir le comportement | `glosswise config mode <mode>` | — |
| Définir le preset LLM de traduction | `glosswise config llm <preset>` | — |
| Définir les indications de langue | `glosswise ws lang -l en -l <language>` | `ws languages` |
| Autoriser des racines locales | `glosswise ws files -r <directory>` | — |
| Créer ou mettre à jour des données | `glosswise term set @term.json` | `term put` |
| Récupérer un enregistrement | `glosswise term get <object-id>` | — |
| Lister les données | `glosswise term ls` | `term list` |
| Rechercher des données | `glosswise term search "query"` | — |
| Archiver des données | `glosswise term archive <object-id>` | — |
| Analyser un passage | `glosswise scan "text"` | — |
| Préparer le contexte | `glosswise brief "text"` | — |
| Traduire via LLMSession | `glosswise translate "text"` | — |
| OCRiser des pages PDF | `glosswise pdf ocr <path>` | — |
| Parcourir le texte OCR | `glosswise doc read <handle> <page>` | — |

Remplacez `term` par `rule` ou `example` pour le même
flux de travail set/get/list/search/archive. Exécutez `glosswise --help` ou
`glosswise <group> --help` pour afficher la totalité des commandes.

## <a id="python-sdk"></a> SDK Python

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

`GlossWiseApp.open()` utilise l’espace de travail actif ou crée l’espace géré
par défaut après la configuration des langues globales.
Utilisez `GlossWiseApp.create("<name>")` pour créer un espace de travail géré explicitement nommé
et `GlossWiseApp.load()` lorsque l’absence doit constituer une erreur. Les applications qui
possèdent déjà un espace de travail HeavenBase peuvent utiliser directement `workspace.glosswise`.

## Fonctionnement

1. Un agent IA se connecte par MCP, le CLI ou le SDK Python.
2. GlossWise résout l’espace de travail demandé ou utilise celui qui est actif/par défaut.
3. Il récupère les termes, règles et exemples pertinents.
4. `brief` classe et regroupe ces éléments probants avec les avertissements et les conflits.
5. L’agent hôte traduit, ou `translate` appelle `LLMSession` de HeavenBase
   avec un contrat géré par `hb.Prompt` et un preset visible.
6. L’appelant peut analyser la traduction ou OCRiser des pages PDF autorisées
   en texte temporaire borné par page.

GlossWise maintient le stockage et la politique terminologique derrière des opérations centrées sur les tâches ;
les agents IA n’ont pas besoin d’un accès générique à la base de données.

## Pour les développeurs

GlossWise est un projet de démonstration qui montre comment une application autonome et bien conçue peut utiliser
HeavenBase. Il illustre les avantages concrets des éléments suivants :

- une extension modulaire montée sur `workspace.glosswise` ;
- des espaces de travail gérés et des valeurs par défaut appartenant à l’application ;
- des valeurs utilisateur au niveau du Context et des presets LLM HeavenBase visibles ;
- des entités typées, des requêtes et une récupération calculée ;
- l’OCR LLM HeavenBase page par page avec des handles de documents bornés ;
- un registre de commandes unique exposé par plusieurs backends CLI ;
- des outils MCP générés à partir d’une boîte à outils HeavenBase ; et
- un Skill intégré qui enseigne aux agents IA le workflow de l’application.

Le CLI direct et Python utilisent le preset HeavenBase configuré via
`LLMSession` ; les hôtes MCP utilisent leur propre modèle configuré.

Vérifications pour le développement :

```console
git clone https://github.com/Magolor/GlossWise.git
cd GlossWise
bash scripts/sync-env.bash
bash scripts/flake.bash --ci
bash scripts/test.bash
bash scripts/test.bash -m full
uv build
```

Consultez [CONTRIBUTING.md](CONTRIBUTING.md) pour le workflow de contribution et
[SECURITY.md](SECURITY.md) pour signaler confidentiellement les vulnérabilités.

Limites actuelles : les extensions HeavenBase sont explicitement installées, les
extensions activées ne peuvent pas être désactivées, la migration du schéma n’est pas automatisée et GlossWise
ne choisit ni ne dissimule de modèle de traduction.

## Citation

Si GlossWise soutient vos recherches ou votre projet, citez le logiciel en utilisant
[CITATION.cff](CITATION.cff) ou :

```bibtex
@software{glosswise_2026,
  author  = {Magolor},
  title   = {GlossWise: Terminology-safe translation for AI agents},
  year    = {2026},
  version = {0.1.0.5},
  url     = {https://github.com/Magolor/GlossWise}
}
```

GlossWise est construit sur [HeavenBase](https://ahvn.top).

## Licence

GlossWise est distribué sous [licence MIT](LICENSE).
