---
name: despiece
description: >-
  Despieza algo para que el lector lo entienda —un aparato o hardware, un proceso, un sistema o
  arquitectura, o una idea— y lo explica por niveles: encuadre (qué tiene que poder hacer el lector y
  quién es), modelo de piezas con función y fuente, revelado del todo a las partes (3–7 por nivel), la
  figura que pide cada caso (vista explotada, flujo, capas, árbol) delegada a la skill de dibujo
  instalada, y comprobación de que se entendió (tres frases y una pregunta de predicción). Usar cuando
  pidan «despiezá», «desmenuzá», «desarmá», «cómo funciona por dentro», «qué partes tiene», «anatomía de»,
  «explicámelo para entenderlo», «no veo cómo encaja», o una explicación visual de un mecanismo, aunque
  no digan «despiece». No usar cuando ya se sabe qué diagrama se quiere (ER, flujo, Gantt, red estilo
  Learn: la skill de diagramas que corresponda, p. ej. diagram-design), para gráficos de datos (dataviz),
  presentaciones, hacer interactivo un SVG existente ni para el estado de un proyecto (relevamiento).
argument-hint: "[qué despiezar]"
compatibility: Claude Code en Windows, macOS o Linux. Python 3.10 o superior sin dependencias de pip; para capturar la página en PNG, Edge o Chrome, y Node 22 o superior para capturar la interactiva.
allowed-tools:
  - Bash(python -I ${CLAUDE_SKILL_DIR}/scripts/*)
  - Bash(node ${CLAUDE_SKILL_DIR}/scripts/*)
metadata:
  version: "1.2.0"
  author: t28.io (Javier Ledesma)
  updated: "2026-11-02"
---

# Despiece explicativo

Convierte «no entiendo cómo funciona esto» en una explicación por niveles que el lector puede seguir y
comprobar: el todo y su frontera, las piezas con su función, el flujo que las une, una figura por nivel
y dos pruebas de comprensión. Es una capa de **comprensión**, no de dibujo: decide qué se muestra, en qué
orden y con qué figura, y el trazo lo pone la skill de dibujo que haya instalada (diagramas editoriales,
arquitectura cloud con iconos oficiales, figuras interactivas) o un script propio; solo la vista explotada
de hardware la dibuja esta skill.

## Gotchas

- **Encuadrar antes de dibujar.** Sin pregunta foco y sin saber quién lee, la figura sale «todo a la
  vez» y no responde nada. Tres preguntas como máximo, y ninguna si el contexto ya las responde.
- **Nada se explica de memoria.** Cada pieza lleva fuente (documento del repo de conocimiento del
  proyecto, configuración real leída en solo lectura, documentación oficial, hoja de datos) o
  `supuesto: true`, y la página lo muestra como «▲ supuesto». No se inventa arquitectura: lo que no está
  en el repo ni se leyó del recurso es un supuesto, aunque sea «lo normal».
- **Nombrar antes de explicar, y nunca empezar por una definición.** El nivel 0 es una afirmación sobre
  el todo con su frontera; las definiciones, si hacen falta, llegan al final. El validador rechaza
  títulos tipo «Qué es…» o «Arquitectura de…».
- **3–7 piezas por nivel y 6 nuevas por figura como máximo.** Si salen más, se agrupan en subconjuntos. Se
  baja un nivel solo donde cambia la respuesta a la pregunta foco; el resto queda cerrado.
- **Una metáfora solo si cabe en una frase y el lector no es del dominio.** Si no, se muestra el mecanismo
  real: las analogías forzadas (inventar una máquina para cada concepto) confunden más de lo que aclaran.
- **En lo físico, el desmontaje es el montaje al revés.** Las raíces llevan `orden_montaje`; una pieza
  con hijos se dibuja cerrada y se abre en su propia figura; una sola pieza destacada por figura; el
  objeto tiene que seguir reconociéndose.
- **La página interactiva es opcional y solo física.** `ensamblar.py --interactivo` dibuja una vista
  isométrica que se abre, se desarma al bajar y recorre el flujo, pero solo si el modelo tiene `geometria`;
  si no, avisa y escribe la estática. Las alzas no se escriben: se calculan para que nada tape a nada.
  Se usa cuando piden algo que se pueda recorrer, animado o «en 3D»; si no, la estática.
- **La interactiva no se revisa con `--screenshot`**: captura antes de que corran el scroll y las
  animaciones. Se captura con `capturar-cdp.mjs`, desplazando con `behavior: 'instant'` (la página usa
  scroll suave y, si no, la captura sale a mitad de camino).
- **Casos mixtos: manda la pregunta foco.** Un firewall es físico para «qué cable va dónde» y sistema para
  «por qué bloquea esto». Se elige un tipo y se dice.
- **El dibujo se delega con un guion, no con una idea vaga.** Quien dibuja (una skill o un script propio)
  recibe título afirmativo, piezas exactas, relaciones, pieza destacada y ruta de salida; si añade piezas
  o cambia nombres, se corrige la figura, no el modelo. SVG con `viewBox` y sin `width`/`height` fijos,
  para incrustarlo. Sin skill de dibujo instalada, script propio y `"skill": "propio"` en el modelo.
- **La marca es del proyecto, no de la skill.** `--marca` toma la ruta de un JSON con colores, fuente,
  pie y lema (`assets/marca-ejemplo.json` enseña los campos) o `ninguna`, el valor por defecto. Cada
  ámbito (una empresa, un cliente, un proyecto personal) tiene su fichero y sus fuentes, y no se mezclan;
  si la skill de dibujo pregunta por su *style guide*, se le dan los tokens de ese fichero.
- **Las puertas de comprensión no son opcionales.** Sin las tres frases y la pregunta de predicción no se
  entrega; son lo que distingue una explicación de un inventario.
- **Si piden algo corto** («en dos párrafos», «sin montar nada»), el método es el mismo pero la salida es
  texto: nivel 0, las piezas en una lista con su función, una figura si hace falta, tres frases y la
  predicción. Sin modelo en disco ni página.
- **Producción no se toca.** Las fuentes se leen (consultas, `show`, `list`, logs); nada de comandos
  dentro de las máquinas ni cambios para «ver cómo reacciona».

## Flujo de trabajo

Copiar este checklist en la respuesta y marcarlo al avanzar:

```
Despiece <objeto>:
- [ ] 1. Encuadre: pregunta foco, lector y profundidad (≤ 3 preguntas; inferir si ya están)
- [ ] 2. Tipo decidido: físico / proceso / sistema / idea
- [ ] 3. Fuentes consultadas; lo no verificado, marcado como supuesto
- [ ] 4. modelo.json escrito y validar_modelo.py sin errores
- [ ] 5. Una figura por nivel: explosionado.py (físico) o guion a quien dibuja
- [ ] 6. Página ensamblada (ensamblar.py, o --interactivo), capturada y revisada a ojo
- [ ] 7. Entrega: nivel 0, tres frases y pregunta de predicción en la respuesta, más la página
```

**1. Encuadre.** Preguntar solo lo que el contexto no responda; proponer la respuesta probable para que
el usuario solo confirme.

| Pregunta | Para qué sirve | Si no se pregunta |
|---|---|---|
| ¿Qué tiene que poder hacer el lector después? (reparar, operar, decidir, diagnosticar, explicarlo a otro) | Fija la pregunta foco y el tipo en los casos mixtos | Inferirla del verbo de la petición |
| ¿Quién lo lee y qué sabe? | Decide la profundidad y si cabe una metáfora | Técnico del dominio sin experiencia en esa pieza |
| ¿Qué profundidad? | 1, 2 o 3 niveles bajo el todo | 2 |

La salida por defecto es una página HTML con todos los niveles; si piden algo corto, texto (ver gotchas).

**2. Tipo.** Físico (eje espacial), proceso (temporal), sistema (funcional y de flujo) o idea (lógico).
Técnica, fuentes típicas y figura de cada tipo en
[references/metodo-por-tipo.md](references/metodo-por-tipo.md): leerlo al llegar aquí la primera vez
en la sesión.

**3. Fuentes.** Antes de escribir una pieza, saber de dónde sale: si el ámbito tiene un repo de
conocimiento, empezar por sus documentos (su `README` o `CLAUDE.md` y sus `docs/`) y leer la configuración
real en modo lectura, con el contexto explícito (cuenta, tenant, suscripción o entorno); en general, la
documentación oficial del producto o del estándar. Anotar la ruta o la referencia: va en `fuentes[]` del
modelo y en la página.

**4. Modelo.** Carpeta de trabajo: la que indique el usuario; si no, `despiece-<objeto>/` donde se esté
trabajando. Escribir `modelo.json` según [references/modelo.md](references/modelo.md) (leerlo la
primera vez; los ejemplos `assets/ejemplo-fisico.json` y `assets/ejemplo-sistema.json` son válidos y
completos). Si la página va a ser interactiva, añadir el bloque `geometria` según
[references/interactivo.md](references/interactivo.md) (leerlo antes del primer `--interactivo`). Validar y
corregir hasta que no haya errores; cada aviso se corrige o se justifica en la respuesta:

```bash
python -I ${CLAUDE_SKILL_DIR}/scripts/validar_modelo.py <carpeta>/modelo.json
```

Salida 0 sin errores · 1 con errores (leer `errores`, dicen qué y cómo) · 2 JSON o ruta inválidos.

**5. Figuras.** Una por nivel mostrado, en `<carpeta>/figuras/`, con el nombre que dice `fichero` en
el modelo. `<marca>` es la ruta del JSON de marca del proyecto o `ninguna`.

- **Físico** → vista explotada propia:

  ```bash
  python -I ${CLAUDE_SKILL_DIR}/scripts/explosionado.py <carpeta>/modelo.json --salida <carpeta>/figuras/n1-explosion.svg --destacar <id> --marca <marca>
  python -I ${CLAUDE_SKILL_DIR}/scripts/explosionado.py <carpeta>/modelo.json --salida <carpeta>/figuras/n2-<padre>.svg --subconjunto <padre> --marca <marca>
  ```

  Toma el título de la figura del modelo con esas mismas piezas. Salida 2 si el tipo no es físico. Si la
  página va a ser interactiva, estas figuras sobran: las dibuja desde `geometria`.
- **Proceso, sistema e idea** → guion a quien dibuja, según
  [references/guion-visual.md](references/guion-visual.md) (leerlo al dibujar la primera figura
  delegada): una skill de diagramas editoriales para flujo, calles, secuencia, estados, capas y árboles;
  una de arquitectura cloud con iconos oficiales para redes y servicios de nube; una de figuras
  interactivas solo si el nivel 2 va a explorarse en una web. Sin ninguna instalada, un script propio
  según la sección «Sin skill de dibujo instalada» de ese fichero.

Revisar cada figura con la lista del final de ese fichero antes de seguir.

**6. Página.**

```bash
python -I ${CLAUDE_SKILL_DIR}/scripts/ensamblar.py <carpeta>/modelo.json --salida <carpeta>/index.html --figuras <carpeta> --marca <marca>
```

Salida 1 = figuras pendientes (la página se escribe con el hueco marcado): dibujarlas y repetir.
Capturarla (Edge o Chrome con `--headless=new --screenshot --window-size=1240,3600`, o abrirla) y
mirar: la numeración de la lista coincide con la de la figura, los títulos afirman, nada se corta, las
fuentes se leen en tema claro y oscuro. Las figuras van sobre lámina blanca en los dos temas, así que un
SVG transparente con tinta oscura se lee igual. Edge headless sigue el tema del sistema: para capturar el
otro, poner `data-theme="light"` o `data-theme="dark"` en `<html>` de una copia.

**Interactiva** (tipo físico con `geometria`): la misma orden con `--interactivo` y sin `--figuras`.

```bash
python -I ${CLAUDE_SKILL_DIR}/scripts/ensamblar.py <carpeta>/modelo.json --salida <carpeta>/index.html --interactivo --marca <marca>
node ${CLAUDE_SKILL_DIR}/scripts/capturar-cdp.mjs <carpeta>/captura.png 1240 900 "file:///<ruta absoluta>/index.html?p=1"
```

Salida 1 = oclusiones: alguna pieza tapa a otra en algún paso (la página se escribe igual; separarlas en
`geometria` o agruparlas). Capturar al menos la portada, el desmontaje a mitad, el flujo, el nivel 2, tema
oscuro (`TEMA=dark`), móvil (390 de ancho) y sin JavaScript (`SIN_JS=1`); qué mirar en cada una, en
[references/interactivo.md](references/interactivo.md#capturar-y-revisar).

**7. Entrega.** En la respuesta: el título del nivel 0, las tres frases, la pregunta de predicción con la
respuesta al final, y la ruta de la página y las figuras. No pegar el modelo. Si el usuario quiere
profundizar, el siguiente nivel es añadir piezas hijas al modelo y repetir desde el paso 4.

## Contenido de la skill

| Ruta | Uso |
|---|---|
| `scripts/validar_modelo.py` | **Ejecutar** en el paso 4: comprueba el modelo contra las reglas del método (`--help`) |
| `scripts/explosionado.py` | **Ejecutar** en el paso 5, tipo físico: vista explotada 2D numerada con lista de piezas (`--help`) |
| `scripts/ensamblar.py` | **Ejecutar** en el paso 6: página HTML por niveles con las figuras incrustadas, o la interactiva con `--interactivo` (`--help`) |
| `scripts/capturar-cdp.mjs` | **Ejecutar** en el paso 6 con `--interactivo`: captura la página en tiempo real, con scroll y animaciones (`--help`) |
| `scripts/isometrico.py`, `scripts/interactiva.py` | Los importa `ensamblar.py --interactivo`; `isometrico.py` también se ejecuta para ver solo las alzas y las oclusiones |
| `references/metodo-por-tipo.md` | Leer **en el paso 2**: eje, técnica, fuentes y figura de cada tipo; casos mixtos |
| `references/modelo.md` | Leer **al escribir el primer modelo**: campos, reglas del validador, convenciones |
| `references/interactivo.md` | Leer **antes del primer `--interactivo`**: bloque `geometria`, alzas, parámetros de la página y cómo capturarla |
| `references/guion-visual.md` | Leer **al delegar la primera figura**: qué pedir a quien dibuja, qué hacer sin skill de dibujo y cómo revisar la figura |
| `references/fuentes.md` | Leer **si se quiere saber de dónde sale una regla**: skills estudiadas y bibliografía |
| `assets/ejemplo-fisico.json`, `assets/ejemplo-sistema.json` | Modelos completos y válidos para copiar la estructura |
| `assets/marca-ejemplo.json` | Copiar y adaptar: los campos del fichero de marca que acepta `--marca` |
| `assets/plantilla-interactiva.html` | Plantilla de la página interactiva; la rellena `interactiva.py` (no se edita en la tarea) |
| `evals/` | Casos de prueba de la skill y `probar_validador.py`, que prueba cada regla del validador (no se usan en la tarea) |
