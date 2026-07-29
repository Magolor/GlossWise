# GlossWise

<p align="center">
  <a href="README.en.md">English</a> ·
  <a href="README.ar.md">العربية</a> ·
  <a href="README.zh.md">中文</a> ·
  <a href="README.fr.md">Français</a> ·
  <a href="README.ru.md">Русский</a> ·
  <strong>Español</strong> ·
  <a href="README.de.md">Deutsch</a> ·
  <a href="README.ja.md">日本語</a>
</p>

<p align="center">
  <img src="docs/assets/glosswise-banner.png" alt="GlossWise — traducción terminológicamente segura para agentes de IA" width="100%">
</p>

<p align="center">
  <a href="https://github.com/Magolor/GlossWise/actions/workflows/ci.yml"><img src="https://github.com/Magolor/GlossWise/actions/workflows/ci.yml/badge.svg?branch=master" alt="Integración continua"></a>
  <a href="https://www.python.org/"><img src="https://img.shields.io/badge/Python-3.10–3.13-3776AB" alt="Python de la versión 3.10 a la 3.13"></a>
  <a href="https://ahvn.top"><img src="https://img.shields.io/badge/HeavenBase-0.1.2.1-6957E5" alt="HeavenBase 0.1.2.1"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-green.svg" alt="Licencia MIT"></a>
</p>

<p align="center">
  <a href="#install">Instalación</a> ·
  <a href="#connect-an-agent">Conectar un agente de IA</a> ·
  <a href="#try-it-teach-once-translate-consistently">Probar la demostración</a> ·
  <a href="#everyday-prompts">Prompts cotidianos</a> ·
  <a href="#mcp-server">Herramientas MCP</a> ·
  <a href="#python-sdk">Python SDK</a>
</p>

GlossWise almacena términos aprobados, reglas de traducción y ejemplos, y después prepara
un informe de traducción compacto para el agente de IA o la aplicación que lo invoca. Los agentes host
traducen con su propio modelo; la CLI directa usa un preset LLM visible de HeavenBase.

GlossWise está disponible como CLI, servidor MCP y Python SDK. La versión `0.1.0.5`
es compatible con `heavenbase>=0.1.2.1`.

## <a id="install"></a> Instalación

GlossWise requiere Python 3.10–3.13. Instala el código fuente actual directamente desde
GitHub. Antes de instalarlo, puedes [consultar el Skill exacto del agente de IA](SKILL.md):

```console
python -m pip install "git+https://github.com/Magolor/GlossWise.git"
glosswise setup -l en -l zh
```

Para examinar el código fuente o contribuir a él:

```console
git clone https://github.com/Magolor/GlossWise.git
cd GlossWise
python -m pip install .
glosswise setup -l en -l zh
```

`setup` exige los idiomas entre los que traduces habitualmente y los guarda
como valores globales, crea y activa `default` con esos idiomas e instala
el Skill de GlossWise para agentes de IA en:

- `~/.agents/skills/glosswise`
- `~/.claude/skills/glosswise`

El Skill público de la raíz y la copia incluida en el paquete que instala `setup` se mantienen
idénticos byte por byte.

Los datos del espacio de trabajo se administran automáticamente en `~/.glosswise/`. No necesitas
elegir ni exponer ninguna base de datos. Los espacios nuevos heredan los idiomas
globales; cámbialos con `glosswise config lang -l en -l <language>`.

Comprueba la instalación:

```console
glosswise ws ls
glosswise ws get
```

## <a id="connect-an-agent"></a> Conectar un agente de IA

`glosswise setup` ya ha instalado los Skills común y de Claude para GlossWise.
Conecta el mismo servidor MCP global desde cualquier host compatible:

| Host | Configuración única |
| --- | --- |
| [Claude Code](https://code.claude.com/docs/en/mcp) | `claude mcp add --scope user glosswise -- glosswise mcp` |
| [Codex](https://developers.openai.com/codex/mcp/) | `codex mcp add glosswise -- glosswise mcp` |
| [Cursor](https://docs.cursor.com/context/model-context-protocol) | Guarda `glosswise mcp --json` como `~/.cursor/mcp.json`. |
| [VS Code / Copilot](https://code.visualstudio.com/docs/copilot/chat/mcp-servers) | Añade a `.vscode/mcp.json` una entrada stdio `servers.glosswise` con el comando `glosswise` y los argumentos `["mcp"]`. |
| [OpenCode](https://opencode.ai/docs/mcp-servers/) | Añade la entrada MCP local de abajo a `~/.config/opencode/opencode.json`. |
| [OpenClaw](https://ahvn.top/quickstart/heavenbase-mcp#3-connect-your-agent) | Ejecuta `glosswise mcp --transport http` y configura `mcp.servers.glosswise` como `http://127.0.0.1:61055/mcp` con transporte `streamable-http`. |
| [Hermes](https://ahvn.top/quickstart/heavenbase-mcp#3-connect-your-agent) | Ejecuta `glosswise mcp --transport http` y añade su URL bajo `mcp_servers.glosswise` en `~/.hermes/config.yaml`. |
| [LM Studio](https://lmstudio.ai/docs/app/mcp) | Abre **Program/Developer → Install → Edit mcp.json** y pega la salida de `glosswise mcp --json`. |
| [Qwen Code](https://qwenlm.github.io/qwen-code-docs/en/users/features/mcp/) | `qwen mcp add --scope user glosswise glosswise mcp` |
| [HeavenBase](https://ahvn.top/quickstart/heavenbase-mcp#3-connect-your-agent) | Ejecuta `glosswise mcp --transport http` y después `hb llm session --mcp http://127.0.0.1:61055/mcp`. |

Para [OpenCode](https://opencode.ai/docs/mcp-servers/), añade lo siguiente al archivo global
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

Comprueba la conexión con el comando del host que enumera servidores MCP y
reinicia el agente cuando su documentación lo requiera.

Inicia un chat nuevo y di:

```text
/glosswise Enumera mis espacios de trabajo e indícame cuál está activo.
```

El agente de IA ya puede crear espacios de trabajo, gestionar terminología, buscar en ella y preparar
informes de traducción por ti. No necesitas escribir JSON ni administrar una
base de datos. Un Skill y una conexión MCP funcionan con todos los espacios de trabajo de
GlossWise.

Para cualquier otro cliente MCP compatible con stdio, muestra el perfil portátil:

```console
glosswise mcp --json
```

## <a id="try-it-teach-once-translate-consistently"></a> Pruébalo: enseña una vez, traduce con coherencia

Esta demostración comienza con una traducción normal de un modelo, enseña a GlossWise dos
decisiones terminológicas en lenguaje natural y, después, repite la solicitud original
en una sesión limpia del agente de IA. El fragmento procede de
[*Frankenstein*, de Mary Shelley](https://www.gutenberg.org/cache/epub/42324/pg42324-images.html),
una de las primeras obras de ciencia ficción y de dominio público.

### 1. Crear un espacio de trabajo

Pídeselo a tu agente de IA:

```text
/glosswise Crea y selecciona un espacio de trabajo de GlossWise llamado `frankenstein-lab`.
Establece inglés, chino, francés, alemán, ruso y japonés como idiomas predeterminados.
```

O utiliza estos dos breves comandos de la CLI:

```console
glosswise ws create frankenstein-lab
glosswise ws lang -l en -l zh -l fr -l de -l ru -l ja
```

`ws create` selecciona automáticamente el espacio de trabajo nuevo. Repite `-l/--lang`
para cada idioma ordenado. El conjunto recuerda a los agentes que deben recopilar las seis formas preferidas, sin
convertir los idiomas en una restricción rígida.

### 2. Traducir antes de enseñar a GlossWise

Envía este párrafo al agente de IA:

```text
/glosswise Usa el espacio de trabajo `frankenstein-lab`. Traduce el párrafo siguiente
al chino, francés, alemán, ruso y japonés. Consulta primero GlossWise para
buscar indicaciones pertinentes y después identifica el modelo o el host que realizó la traducción.

“It was on a dreary night of November, that I beheld the accomplishment of my
toils. With an anxiety that almost amounted to agony, I collected the
instruments of life around me, that I might infuse a spark of being into the
lifeless thing that lay at my feet.”
```

La primera redacción depende del modelo de traducción del agente de IA. Puede elegir
expresiones literales como “spark of being” → `存在的火花`,
`étincelle de vie`, `Lebensfunken`, `искра жизни` o `命の火花`.

### 3. Enseñar dos decisiones mediante una conversación

Envía un mensaje más:

```text
/glosswise Guarda estos como términos preferidos activos en el espacio de trabajo `frankenstein-lab`.
Las formas de destino son decisiones terminológicas de mi proyecto, no afirmaciones
sobre las traducciones oficiales de la novela.

1. «instruments of life» significa los aparatos utilizados en el experimento:
   chino 生命仪器; francés instruments de vie;
   alemán Instrumente des Lebens; ruso орудия жизни;
   japonés 生命の器具.

2. «spark of being» significa la esencia vivificante que se infunde a la materia inerte:
   chino 生命之火; francés étincelle d'existence;
   alemán Funke des Seins; ruso искра бытия;
   japonés 存在の火花.

Conserva también las formas de origen en inglés. Usa exactamente la terminología preferida cuando
lo permita la gramática del idioma de destino; en caso contrario, flexiónala sin cambiar el
concepto aprobado. Avísame cuando se hayan guardado ambos registros.
```

El agente de IA se encarga de las llamadas CRUD estructuradas. Si falta algún idioma solicitado del espacio de trabajo,
el Skill instalado le indica que pregunte, proponga una forma para
confirmarla o revele con claridad que la forma ha sido generada por un agente de IA.

### 4. Iniciar una sesión nueva y repetir la misma solicitud

Finaliza el chat actual e inicia una nueva sesión del agente de IA. Vuelve a enviar el prompt exacto del
paso 2; no añadas ningún recordatorio sobre los términos que acabas de guardar:

```text
/glosswise Usa el espacio de trabajo `frankenstein-lab`. Traduce el párrafo siguiente
al chino, francés, alemán, ruso y japonés. Consulta primero GlossWise para
buscar indicaciones pertinentes y después identifica el modelo o el host que realizó la traducción.

“It was on a dreary night of November, that I beheld the accomplishment of my
toils. With an anxiety that almost amounted to agony, I collected the
instruments of life around me, that I might infuse a spark of being into the
lifeless thing that lay at my feet.”
```

El prompt es idéntico; solo ha cambiado el espacio de trabajo persistente de GlossWise.
La sesión nueva debe recuperar ese estado, en vez de depender de la memoria del chat. El
cambio importante ya resulta visible:

| Idioma | Una traducción de referencia podría usar | Redacción guiada por GlossWise |
| --- | --- | --- |
| Chino | `生命工具` · `存在的火花` | `生命仪器` · `生命之火` |
| Francés | `instruments de la vie` · `étincelle de vie` | `instruments de vie` · `étincelle d'existence` |
| Alemán | `Werkzeuge des Lebens` · `Lebensfunken` | `Instrumente des Lebens` · `Funken des Seins`¹ |
| Ruso | `инструменты жизни` · `искра жизни` | `орудия жизни` · `искру бытия`¹ |
| Japonés | `生命の道具` · `命の火花` | `生命の器具` · `存在の火花` |

¹ El agente de IA flexiona la forma preferida canónica para adaptarla a esta oración.

<details>
<summary>Un resultado correcto guiado por GlossWise</summary>

**Chino**

> 那是十一月一个阴沉的夜晚，我目睹了自己辛劳的成果。怀着近乎痛苦的焦虑，我把生命仪器聚集在身边，想把生命之火注入躺在我脚边的无生命之物中。

**Francés**

> Ce fut par une lugubre nuit de novembre que je contemplai l’accomplissement de mes travaux. Avec une anxiété qui confinait presque à l’agonie, je rassemblai autour de moi les instruments de vie afin d’insuffler une étincelle d'existence à la chose inanimée étendue à mes pieds.

**Alemán**

> Es war in einer trüben Novembernacht, als ich die Vollendung meiner Mühen erblickte. Mit einer Angst, die beinahe an Qual grenzte, versammelte ich die Instrumente des Lebens um mich, um dem leblosen Ding zu meinen Füßen einen Funken des Seins einzuhauchen.

**Ruso**

> В мрачную ноябрьскую ночь я увидел завершение своих трудов. С тревогой, почти переходившей в агонию, я собрал вокруг себя орудия жизни, чтобы вдохнуть искру бытия в безжизненное создание, лежавшее у моих ног.

**Japonés**

> 十一月の陰鬱な夜、私は自らの労苦の成就を目の当たりにした。苦悶に近い不安を抱えながら、私は生命の器具を周囲に集め、足元に横たわる生命なきものへ存在の火花を吹き込もうとした。

</details>

GlossWise no generó estas oraciones. Lo hizo el agente de IA conectado; GlossWise
hizo que la terminología aprobada pudiera recuperarse e inspeccionarse antes de generarlas.

### 5. Buscar y editar más adelante

No necesitas identificadores de registros:

```text
/glosswise Busca el término relacionado con una chispa en `frankenstein-lab`. Muestra sus formas
preferidas en una tabla compacta.
```

Después, edítalo con naturalidad:

```text
/glosswise Cambia únicamente la forma preferida en japonés de «spark of being» por
`生命の火花`. Mantén los demás idiomas sin cambios y muéstrame el registro guardado.
```

Este recorrido completo de configurar → crear → gestionar → reiniciar → preparar informe de traducción → buscar → editar se
prueba con un wheel instalado y dos sesiones MCP stdio independientes en
[`tests/test_quickstart.py`](https://github.com/Magolor/GlossWise/blob/master/tests/test_quickstart.py).

## <a id="everyday-prompts"></a> Prompts cotidianos

Una vez establecida la conexión, el trabajo habitual puede realizarse en el chat. Los prompts de administración siguientes
realizan cambios intencionados; los prompts de consulta y traducción son de solo lectura, salvo que
pidan explícitamente guardar algo.

### Administrar espacios de trabajo y terminología

- `/glosswise Crea y selecciona un espacio de trabajo llamado <name>.`
- `/glosswise En el espacio de trabajo <name>, establece inglés, chino y japonés como idiomas predeterminados.`
- `/glosswise En el espacio de trabajo <name>, guarda “rate limit” como término preferido activo con “rate limit” en inglés, “速率限制” en chino y “レート制限” en japonés. Muéstrame el registro guardado.`
- `/glosswise Busca “rate limit” en el espacio de trabajo <name>. Cambia únicamente su forma preferida en japonés por “速度制限”, conserva todos los demás campos y formas y, después, muéstrame el registro actualizado.`
- `/glosswise Archiva el término “rate limit” en el espacio de trabajo <name> para excluirlo de las búsquedas normales de términos activos. Pregúntame antes de realizar el cambio.`

### Consultar indicaciones y traducir

- `/glosswise En el espacio de trabajo <name>, busca términos activos relacionados con la autenticación. Muestra sus formas preferidas y prohibidas en inglés, chino y japonés. No modifiques nada.`
- `/glosswise En el espacio de trabajo <name>, busca reglas y ejemplos para traducir mensajes de error al francés. Muestra prioridades, estilos y conflictos. No modifiques nada.`
- `/glosswise Comprueba “Requests over this limit are rejected.” con el espacio de trabajo <name>. Enumera los términos y reglas coincidentes sin traducir ni guardar nada.`
- `/glosswise Usa el espacio de trabajo <name>. Traduce “The client retries the request after the rate limit resets.” del inglés al chino y al japonés. Prepara un informe de traducción nuevo de GlossWise para cada idioma de destino, aplica términos preferidos y reglas activos, señala los conflictos e identifica el modelo o el host que realizó la traducción.`
- `/glosswise Usa el espacio de trabajo <name>. Traduce al francés el pasaje en inglés que aparece a continuación. Prepara primero un informe de traducción de GlossWise y, después de la traducción, muestra una tabla compacta con todos los términos, reglas o ejemplos almacenados que hayas aplicado: <paste source passage>.`
- `/glosswise Revisa esta traducción al francés con el espacio de trabajo <name>. Informa de términos preferidos ausentes, formas prohibidas y reglas contradictorias; no la reescribas ni guardes nada, salvo que te lo pida: <paste translation>.`

Usa `glosswise ws ls`, `glosswise ws use <name>` y
`glosswise ws get` cuando una comprobación rápida en la terminal resulte más práctica que el chat.

## Traducción integrada, rangos de archivo y OCR de PDF

La traducción directa usa un preset con nombre de `LLMSession` de HeavenBase.
Cada resultado informa del preset, gateway, proveedor, modelo e identificador
resueltos. Elige por separado el preset y el grado de cautela:

```console
glosswise config llm chat
glosswise config mode auto
glosswise translate "Run this query." -sl en -tl ja
glosswise translate "Run this query." -sl en -tl ja --preset chat
```

Los modos son `yolo` (traducir de inmediato), `elicit` (preguntas terminológicas
con opciones), `auto` (adaptarse a las pruebas disponibles), `explain`
(traducir y explicar cada elección importante) y `custom` con `--prompt`.
HeavenBase renderiza el prompt del sistema mediante `hb.Prompt` y resuelve el
preset indicado. Usa `chat` para su opción de chat rápido actual o fija un
preset dedicado sin duplicar credenciales de proveedor en GlossWise:

```console
hb cfg set heavenbase.llm.presets.glosswise-translate.model deepseek-v4-flash
glosswise config llm glosswise-translate
```

`scan`, `brief` y `translate` aceptan rangos inclusivos desde 1 con
`--start-line` y `--end-line` para texto directo, stdin y `@file`. El perfil
MCP local autorizado añade herramientas equivalentes para archivos.

Para un PDF, autoriza su directorio, aplica OCR solo a las páginas necesarias
con el preset LLM de HeavenBase configurado y examina el texto conservado por
página mediante el handle corto `gw-...`:

```console
glosswise ws files -r /absolute/path/to/documents
glosswise pdf ocr /absolute/path/to/documents/manual.pdf --start-page 4 --end-page 8
glosswise doc read gw-0123456789ab 4 --start-line 1 --end-line 80
glosswise doc rm gw-0123456789ab
```

`ws files` guarda una lista de lectura permitida para el espacio de trabajo;
repite `-r/--root` por cada directorio. No sube, copia ni registra archivos.
Repite `-e/--encoding` solo si los archivos requieren codificaciones de texto
estrictas adicionales; UTF-8 está permitido de forma predeterminada.

GlossWise renderiza y reconoce una página cada vez y borra su imagen de inmediato.
Las repeticiones largas sospechosas se señalan y nunca se borran en silencio.
Configura `ocr-local` con `hb cfg set
heavenbase.llm.presets.ocr-local.<field-or-path> <value>`; los ajustes incluyen
`desc`, `gateway`, `provider`, `model` y `default_args`; elige otro preset con `glosswise config ocr <preset>`.

## <a id="mcp-server"></a> Servidor MCP

### stdio local

La mayoría de los clientes de escritorio y para agentes de IA de programación deberían usar:

```console
glosswise mcp --json
```

El proceso hijo generado inicia el servidor completo con herramientas de lectura, CRUD, Skill y
administración de espacios de trabajo. El ejecutable `glosswise` debe estar en el `PATH`
del cliente MCP.

### HTTP local

Para ejecutar un servidor HTTP transmisible de larga duración:

```console
glosswise mcp --transport http
```

De forma predeterminada, se vincula a `127.0.0.1:61055` y sirve MCP en
`http://127.0.0.1:61055/mcp`. Muestra el perfil de cliente correspondiente con:

```console
glosswise mcp --json --transport http
```

Elige otro punto de conexión local cuando sea necesario:

```console
glosswise mcp --transport http --host 127.0.0.1 --port 61056
```

GlossWise no incorpora autenticación de red. Mantén el servidor en un host de
bucle local, salvo que otra capa de confianza proporcione autenticación y seguridad
del transporte.

### Herramientas MCP

Las herramientas de datos y contexto aceptan un `workspace_id` opcional. Cuando se omite,
GlossWise usa el espacio de trabajo activo y después el predeterminado administrado.

| Herramienta | Finalidad | `read` | `full` | `local` |
| --- | --- | :---: | :---: | :---: |
| `glosswise_workspace_info` | Muestra las capacidades y las indicaciones de idioma del espacio de trabajo. | ✓ | ✓ | ✓ |
| `glosswise_prepare_translation` | Crea un informe de traducción para el texto de origen. | ✓ | ✓ | ✓ |
| `glosswise_search_terms` | Busca términos. | ✓ | ✓ | ✓ |
| `glosswise_search_rules` | Busca reglas. | ✓ | ✓ | ✓ |
| `glosswise_search_examples` | Busca ejemplos. | ✓ | ✓ | ✓ |
| `glosswise_scan_text` | Examina el texto para buscar coincidencias con términos y reglas. | ✓ | ✓ | ✓ |
| `glosswise_list_records` | Enumera términos, reglas o ejemplos. | ✓ | ✓ | ✓ |
| `glosswise_get_record` | Obtiene un registro mediante el identificador de objeto. | ✓ | ✓ | ✓ |
| `glosswise_put_term` | Crea o actualiza un término y sus formas. | — | ✓ | ✓ |
| `glosswise_put_rule` | Crea o actualiza una regla. | — | ✓ | ✓ |
| `glosswise_put_example` | Crea o actualiza un ejemplo. | — | ✓ | ✓ |
| `glosswise_archive` | Archiva un registro. | — | ✓ | ✓ |
| `glosswise_list_workspaces` | Enumera los espacios de trabajo. | ✓ | ✓ | ✓ |
| `glosswise_get_workspace` | Obtiene un registro del espacio de trabajo con los datos sensibles ocultos. | ✓ | ✓ | ✓ |
| `glosswise_create_workspace` | Crea un espacio de trabajo administrado. | — | ✓ | ✓ |
| `glosswise_set_workspace_languages` | Establece las indicaciones de idioma del espacio de trabajo. | — | ✓ | ✓ |
| `glosswise_activate_workspace` | Selecciona el espacio de trabajo activo. | — | ✓ | ✓ |
| `glosswise_deactivate_workspace` | Borra la selección activa. | — | ✓ | ✓ |
| `glosswise_remove_workspace` | Anula el registro de un espacio de trabajo. | — | ✓ | ✓ |
| `glosswise_open_workspace` | Abre un espacio de trabajo y muestra sus capacidades. | ✓ | ✓ | ✓ |
| `glosswise_health_workspace` | Examina el estado del registro y del entorno de ejecución. | ✓ | ✓ | ✓ |
| `glosswise_read_skill` | Lee las instrucciones empaquetadas para el agente de IA. | ✓ | ✓ | ✓ |
| `glosswise_scan_file` | Examina un archivo de texto local del servidor autorizado. | — | — | ✓ |
| `glosswise_prepare_file` | Crea un informe desde un rango de archivo autorizado. | — | — | ✓ |
| `glosswise_ocr_pdf` | Aplica OCR a páginas PDF autorizadas en un handle corto. | — | — | ✓ |
| `glosswise_list_documents` | Enumera handles temporales de documentos OCR. | — | — | ✓ |
| `glosswise_get_document` | Examina el manifiesto de un documento OCR. | — | — | ✓ |
| `glosswise_read_document` | Lee un rango de líneas limitado de una página OCR. | — | — | ✓ |
| `glosswise_remove_document` | Elimina un documento OCR temporal. | — | — | ✓ |

### Perfiles MCP

Los perfiles controlan qué herramientas se exponen, no el contenido de los espacios de trabajo ni el archivo
del Skill instalado:

| Perfil | Superficie exacta | Uso previsto |
| --- | --- | --- |
| `full` | Las 22 herramientas marcadas en la columna `full`. | Predeterminado. Admite búsquedas, informes de traducción, CRUD, inspección del Skill y administración de espacios de trabajo. Tanto `glosswise mcp` como `glosswise mcp --json` seleccionan este perfil. |
| `read` | Las 13 herramientas marcadas en la columna `read`. | Uso de terminología y contexto de solo lectura e inspección de espacios de trabajo. No permite gestionar registros, cambiar la selección ni administrar espacios de trabajo. |
| `local` | Las 22 herramientas de `full`, más siete herramientas autorizadas de documentos locales. | Acceso completo avanzado para rangos limitados y OCR de PDF. El perfil no concede acceso por sí solo; autoriza primero las raíces. |

`glosswise setup` instala un Skill independiente del perfil. El Skill no
selecciona ningún perfil: el servidor MCP conectado decide qué herramientas puede invocar el agente de IA.
La configuración normal usa `full`, que es el único perfil no local que
admite todos los flujos de administración y traducción que enseña el Skill.

Para cambiar una instalación existente, conserva el Skill instalado y modifica únicamente
el comando del servidor MCP en la configuración del agente de IA; después, reinicia o vuelve a conectar
el agente de IA:

```console
glosswise mcp                 # full (default)
glosswise mcp --profile read  # read-only
glosswise mcp --profile local # full plus authorized text/PDF tools
```

Usa `glosswise mcp --json --profile <profile>` para generar un JSON de cliente
de sustitución. No hace falta volver a ejecutar `glosswise setup` para cambiar de perfil.
Volver a usar `glosswise mcp` sin más restaura la superficie `full` predeterminada.

Cada herramienta devuelve un sobre JSON con versión. Los agentes de IA deben inspeccionar `error`,
`warnings`, `conflicts` y `truncated` antes de usar `items`.

## Referencia de la CLI

| Tarea | Comando | También se acepta |
| --- | --- | --- |
| Enumerar espacios de trabajo | `glosswise ws ls` | `ws list` |
| Examinar un espacio de trabajo | `glosswise ws get [<name>]` | — |
| Crear un espacio de trabajo | `glosswise ws create [<name>]` | — |
| Seleccionar un espacio de trabajo | `glosswise ws use <name>` | `ws activate`, `ws act` |
| Borrar la selección | `glosswise ws deact` | `ws deactivate` |
| Anular el registro de un espacio de trabajo | `glosswise ws rm <name>` | `ws unset`, `ws remove` |
| Mostrar configuración global | `glosswise config get` | — |
| Definir idiomas globales | `glosswise config lang -l en -l <language>` | `config languages` |
| Definir comportamiento | `glosswise config mode <mode>` | — |
| Definir el preset LLM de traducción | `glosswise config llm <preset>` | — |
| Establecer indicaciones de idioma | `glosswise ws lang -l en -l <language>` | `ws languages` |
| Autorizar raíces locales | `glosswise ws files -r <directory>` | — |
| Crear o actualizar datos | `glosswise term set @term.json` | `term put` |
| Obtener un registro | `glosswise term get <object-id>` | — |
| Enumerar datos | `glosswise term ls` | `term list` |
| Buscar datos | `glosswise term search "query"` | — |
| Archivar datos | `glosswise term archive <object-id>` | — |
| Examinar un pasaje | `glosswise scan "text"` | — |
| Preparar contexto | `glosswise brief "text"` | — |
| Traducir mediante LLMSession | `glosswise translate "text"` | — |
| Aplicar OCR a PDF | `glosswise pdf ocr <path>` | — |
| Examinar texto OCR | `glosswise doc read <handle> <page>` | — |

Sustituye `term` por `rule` o `example` para seguir el mismo flujo de
crear/obtener/enumerar/buscar/archivar. Ejecuta `glosswise --help` o
`glosswise <group> --help` para consultar toda la superficie de comandos.

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

`GlossWiseApp.open()` usa el espacio de trabajo activo o crea el predeterminado
administrado después de configurar los idiomas globales.
Usa `GlossWiseApp.create("<name>")` para indicar explícitamente el nombre de un espacio de trabajo administrado
y `GlossWiseApp.load()` cuando su ausencia deba producir un error. Las aplicaciones que
ya poseen un espacio de trabajo de HeavenBase pueden usar `workspace.glosswise` directamente.

## Cómo funciona

1. Un agente de IA se conecta mediante MCP, la CLI o el Python SDK.
2. GlossWise resuelve el espacio de trabajo solicitado o usa el activo/predeterminado.
3. Recupera términos, reglas y ejemplos pertinentes.
4. `brief` clasifica y empaqueta esas pruebas con advertencias y conflictos.
5. El agente host traduce, o `translate` invoca `LLMSession` de HeavenBase
   mediante un contrato administrado por `hb.Prompt` y un preset visible.
6. El invocador puede examinar la traducción o aplicar OCR a páginas PDF autorizadas
   en texto temporal limitado por página.

GlossWise mantiene el almacenamiento y la política terminológica tras operaciones centradas en las tareas;
los agentes de IA no necesitan acceso genérico a bases de datos.

## Para desarrolladores

GlossWise es un proyecto de demostración que muestra cómo una aplicación independiente y bien estructurada puede usar
HeavenBase. Demuestra las ventajas prácticas de:

- una extensión modular montada en `workspace.glosswise`;
- espacios de trabajo administrados y valores predeterminados propiedad de la aplicación;
- valores de usuario del Context y presets LLM visibles de HeavenBase;
- entidades y consultas tipadas, y recuperación calculada;
- OCR LLM de HeavenBase por página con handles de documentos limitados;
- un registro de comandos expuesto mediante varios backends de CLI;
- herramientas MCP generadas a partir de un toolkit de HeavenBase; y
- un Skill empaquetado que enseña a los agentes de IA el flujo de trabajo de la aplicación.

La CLI directa y Python usan el preset configurado de HeavenBase mediante
`LLMSession`; los hosts MCP usan su propio modelo configurado.

Comprobaciones de desarrollo:

```console
git clone https://github.com/Magolor/GlossWise.git
cd GlossWise
bash scripts/sync-env.bash
bash scripts/flake.bash --ci
bash scripts/test.bash
bash scripts/test.bash -m full
uv build
```

Consulta [CONTRIBUTING.md](CONTRIBUTING.md) para conocer el flujo de contribuciones y
[SECURITY.md](SECURITY.md) para informar de vulnerabilidades de forma privada.

Límites actuales: las extensiones de HeavenBase se instalan de forma explícita, las
extensiones habilitadas no se deshabilitan, la migración del esquema no está automatizada y GlossWise
no elige ni oculta ningún modelo de traducción.

## Cita

Si GlossWise ayuda en tu investigación o proyecto, cita el software mediante
[CITATION.cff](CITATION.cff) o:

```bibtex
@software{glosswise_2026,
  author  = {Magolor},
  title   = {GlossWise: Terminology-safe translation for AI agents},
  year    = {2026},
  version = {0.1.0.5},
  url     = {https://github.com/Magolor/GlossWise}
}
```

GlossWise se basa en [HeavenBase](https://ahvn.top).

## Licencia

GlossWise está disponible bajo la [licencia MIT](LICENSE).
