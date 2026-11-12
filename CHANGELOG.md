# Changelog

Formato: versión semántica (`metadata.version` de SKILL.md). Una entrada por cambio relevante, con el
resultado de las evals que lo respaldan.

## [2.1.1] - 2026-11-12

Solo documentación: la skill no cambia.

### Corregido
- El enlace de `docs/instalacion.md` a la marca propia llevaba a `#tu-marca-en-un-fichero`, que no existe en el
  README. La sección es un desplegable sin encabezado, así que ahora lleva `id="marca-propia"` y el enlace apunta
  ahí. Comprobados el resto de enlaces internos de los `.md`: ninguno más roto.

## [2.1.0] - 2026-11-12

### Añadido
- **Explorador con zoom semántico** (`ensamblar.py --explorador`), para los cuatro tipos y sin `geometria`: un
  solo HTML con una lámina explotada por nivel. La rueda, el pellizco (trackpad o táctil), los botones o las
  teclas `+` y `-` sobre una pieza con «+» la abren en su lámina; hacia atrás, se vuelve al nivel de arriba. Un
  panel lleva las migas, el contexto del todo, la lista numerada como la lámina, la ficha con función y fuente
  (o «▲ supuesto») y las pruebas de comprensión.
  - Transición con View Transitions que nace en la pieza que se abre; instantánea con movimiento reducido o sin
    la API.
  - El historial acompaña: «atrás» sube un nivel, las migas reutilizan las entradas que ya existen y `#/<id>`
    abre un nivel directamente. `?sel=<id>` y `?tema=` para capturas.
  - El foco va al título del nivel nuevo o a la pieza de la que se venía; tras un gesto, una región viva lo
    anuncia. Un gesto no abre dos niveles aunque siga llegando inercia del trackpad.
  - Sin JavaScript se ve el nivel 1 con un aviso; tema claro y oscuro; móvil con la lámina arriba.
- `scripts/explorador.py`, `assets/plantilla-explorador.html` y `references/explorador.md` (gestos, enlaces,
  capturas, límites).
- **`docs/explorador.md`**: los exploradores del SSD (2 niveles) y de la historia argentina (4) con seis capturas.
- Caso de eval 8 (`explorador-auditoria`) y cuatro consultas de activación para la frontera con
  `grafico-interactivo`. Resultados en `evals/resultados-2026-11-12b.md`: calidad 16/16 con skill frente a 9/16
  sin ella, y activación 89/90.
- En `references/explorador.md`, cómo probar la rueda con eventos sintéticos: uno solo no abre un nivel, y hay
  que apuntar al rótulo de la pieza.

### Cambiado
- La descripción dice que el despiece se recorre con zoom en un explorador, y nombra «navegar con zoom por sus
  niveles» entre los disparadores. Antes, Sonnet mandaba esas peticiones a `grafico-interactivo`.
- Un gesto sobre el hueco entre las letras del rótulo de una pieza la abre. El texto SVG solo responde sobre
  los glifos, así que ahora el respaldo por caja mira también los rótulos.
- `explosionado.py` expone `figura(modelo, padre, destacar, marca, titulo, explorador=False)`: la misma
  geometría sirve a la figura estática y a las láminas del explorador, que se precalculan en Python en vez de
  portarla a JavaScript. Con `explorador=True` la lámina sale sin título, lista ni pie, con las caras marcadas
  por clase y cada llamada agrupada con el id de su pieza. **Las figuras estáticas no cambian**: los nueve
  ejemplos y un subconjunto salen idénticos byte a byte a los de la 2.0.1.

## [2.0.1] - 2026-11-12

Solo documentación: la skill no cambia.

### Cambiado
- La portada del README pasa a `docs/img/portada.png`, en el repo, en vez de la URL del CDN de Segmind, que no es
  permanente.
- Demo estática regenerada con la 2.0.0: las dos figuras de `docs/demo/figuras/` en isométrica, `docs/demo/index.html`
  y sus cuatro capturas, ahora de la página completa en claro y oscuro. `docs/demo.md` remite a la galería de los
  nueve ejemplos.

## [2.0.0] - 2026-11-12

Cambia el modelo: la skill deja de saber de hardware. Un despiece son **dos ejes y nada más**, dependencia
(`orden`) y pertenencia (`padre`); el resto es vocabulario del dominio. Los modelos de la 1.x siguen
validando: `orden_montaje` queda como alias de `orden`.

### Añadido
- **`orden`**: qué tiene que existir antes, en cualquier tipo (el montaje, el despliegue, la cronología, la
  profundidad, la cadena de una señal). Único entre hermanas; obligatorio en las raíces del tipo físico.
- **`eje`** en el modelo y en una pieza con hijas: qué ordena `orden`, en pocas palabras, para el subtítulo
  de la figura. Si las piezas no traen `orden` ni están en el `flujo`, la figura no afirma ningún orden.
- **`rol`**: el papel abstracto de una pieza (`base`, `etapa`, `capa`, `componente`, `interfaz`, `enlace`,
  `contenedor`, `limite`, `regulador`, `bloque`), que elige su silueta. `forma` le sigue ganando; las pistas
  por nombre quedan solo para lo físico.
- **Paso 8 de `SKILL.md`, abrir a demanda**: el modelo crece por la pieza que el usuario abre, sin rehacer lo
  ya abierto; `profundidad` admite hasta 4, y más allá la pieza merece un despiece propio.
- **Siete ejemplos nuevos**, válidos, sin avisos y con fuentes, uno por clase de caso: una red radial en la nube
  (`red-nube`), un pipeline de CI/CD (`cicd`), la historia política argentina (`historia-argentina`, 4 niveles),
  la familia Darwin–Wedgwood (`arbol-genealogico`), una auditoría ISO/IEC 27001 (`auditoria-iso27001`, 4
  niveles), el subsuelo de Marte (`terreno-marte`) y el sentido del tacto (`tacto`). Con el SSD y el sistema
  web, nueve. **`docs/ejemplos.md`** los muestra todos, nivel por nivel, con el comando de cada figura.
- `validar_modelo.py`: el alias, `orden` repetido entre hermanas, `orden` y `orden_montaje` distintos en una
  pieza, `rol` y `forma` conocidos, `eje` (texto corto, en el modelo y en las piezas), raíces sin rol fuera
  de lo físico (aviso), más de una `base` entre hermanas (aviso), y fuera de lo físico una pieza cuyas hijas
  llevan `orden` sin `eje` propio (aviso: su subtítulo caería en el genérico). `probar_validador.py`: 57/57.
- Evals 6 (la vista explotada de una historia, fuera de lo físico) y 7 (abrir una pieza a demanda sobre un
  modelo ya hecho): **29/32 con skill frente a 13/32 sin ella** (Sonnet y Haiku). Activación con cuatro
  consultas nuevas (historia, auditoría, línea de tiempo y organigrama): 75/78, entrenamiento 45/45; los tres
  fallos, la consulta de la página con scroll de la 1.2.0. Detalle en `evals/resultados-2026-11-12.md`.

### Cambiado
- **`explosionado.py` dibuja los cuatro tipos**, no solo el físico, y en isométrica (30°): prismas de tres
  caras, sombra bajo la base y sombra proyectada de cada pieza sobre la de abajo, eje discontinuo, pieza
  destacada con el secundario de la marca, llamadas con guía en codo y lista a la derecha sin solapes. Ocho
  siluetas: `placa`, `chip`, `conector`, `modulo`, `carcasa`, `disipador`, `cable` y `capa`.
- Sin `orden`, la pila sigue el `flujo` y, si no, el orden de escritura. El margen superior se calcula con la
  silueta real de la pieza más alta (antes quedaba una franja vacía sobre una fila de chips). La separación
  es variable: una pieza que baja en pantalla más que la de abajo se separa esa diferencia de más, y la de
  abajo queda tan a la vista como bajo una igual (una carcasa tapaba casi entero un cable o una loseta). El
  «+» de una pieza cerrada va sobre la pieza, no sobre el eje. Lo que va sobre una carcasa (bandeja abierta)
  o un disipador se sube hasta librar su borde trasero: si no, se vería dentro, y estar dentro es `padre`.
- `validar_modelo.py` avisa de una `funcion` de más de 125 caracteres (antes, 160): la figura la muestra en dos
  líneas y recorta el resto con «…».
- `references/modelo.md`: una pieza abierta sin `eje` propio toma el del tipo, no el del modelo, porque lo que
  ordena las raíces rara vez ordena a sus hijas (así lo hacía ya el código).
- Por las evals: el paso 8 entrega también tres frases y una predicción sobre el nivel abierto, y pide `eje`
  en la pieza abierta si sus hijas llevan `orden`; el paso 7 empieza por el tipo elegido y por qué;
  `modelo.md` aclara que una figura de `explosionado.py` lleva `"skill": "explosionado"` en cualquier tipo.
- `SKILL.md`: gotchas de los dos ejes, del dominio como ejemplos y de la profundidad a demanda; el paso 5
  hace de la vista explotada la figura por defecto de cada nivel y delega el flujo, la red y la secuencia.
- `references/modelo.md` (con índice), `metodo-por-tipo.md` (la vista explotada fuera de lo físico) e
  `interactivo.md`, al día. README reescrito: abre con una galería de tres casos (aparato, red, historia) y
  explica los dos ejes y los roles.
- Demos regeneradas: `docs/demo/iso/`, `docs/demo/ejemplos/` (nueva, 19 figuras) y la página interactiva de
  `docs/interactivo/` (solo cambia el JSON incrustado). `docs/demo/figuras/` y la página estática siguen siendo
  las de la 1.1.1.

## [1.2.0] - 2026-11-02

### Añadido
- **`ensamblar.py --interactivo`**: la página interactiva, desde el mismo `modelo.json`, para tipo físico con
  un bloque `geometria`. Un solo HTML sin librerías ni red: vista isométrica que se abre al cargar y con un
  deslizador, desmontaje pieza a pieza al bajar (scroll-driven animations con fallback por
  IntersectionObserver), flujo paso a paso con la flecha de cada relación y «▶ Recorrer», nivel 2 que se abre
  con el scroll o con «Ver por dentro →», predicción con opciones y popover «▲ supuesto». Funciona sin
  JavaScript, en claro y oscuro, con movimiento reducido y en el móvil. Sin `geometria`, o en otro tipo,
  escribe la estática y lo dice. Detalle en `references/interactivo.md`.
- `scripts/isometrico.py`: proyección isométrica y **alzas calculadas**, no escritas: se elige la combinación
  en la que ninguna pieza tapa más del 5 % de la cara de arriba de otra ni su número en ningún paso del
  desmontaje. Si no la hay, `ensamblar.py` sale con 1 y dice qué pieza tapa a cuál. Se ejecuta también solo.
- `scripts/interactiva.py` y `assets/plantilla-interactiva.html`: el SVG llega pintado y explotado desde
  Python; el JS solo cambia estados.
- `scripts/capturar-cdp.mjs`: captura en tiempo real por DevTools Protocol (Node 22 o superior, sin
  dependencias), porque `--screenshot` captura antes de que corran el scroll y las animaciones. Acepta `TEMA`,
  `MOVIMIENTO`, `SIN_JS` y `PUERTO`; sin `PUERTO`, el navegador elige un puerto libre y se pueden lanzar
  capturas en paralelo.
- Modelo: `figuras[].destacada`, `prediccion.opciones` y `prediccion.correcta`, `flujo_entrada` y el bloque
  `geometria`. `assets/ejemplo-fisico.json` los trae todos.
- `validar_modelo.py`: reglas para todo lo anterior (forma, rangos, una sola placa y la primera en montarse,
  volúmenes que no se solapan, `unidades` igual a `cantidad`, subconjuntos solo en raíces con hijos, huecos de
  los rótulos, `lift` escrito a mano). `evals/probar_validador.py` comprueba cada regla con una mutación del
  ejemplo: 37/37.
- `docs/interactivo.md` con la demo interactiva del SSD y sus capturas (`docs/interactivo/`), y
  `docs/research-interactivo.md` con el prototipo que sirvió para decidir (`docs/prototipo-interactivo/`).
  Sin GitHub Pages: el HTML se descarga y se abre.

### Cambiado
- `SKILL.md`: dos gotchas (la interactiva es opcional y solo física; no se revisa con `--screenshot`), el
  paso 6 con el bloque «Interactiva» y Node 22 en `compatibility`. `allowed-tools` pasa a lista e incluye
  `node` para `capturar-cdp.mjs`.
- `ensamblar.py` y `explosionado.py`: `--help` muestra la documentación entera, con los códigos de salida.
  `validar_modelo.py --help` sale por stdout con código 0, y un argumento de más, por stderr con 2.
- `explosionado.py` sigue en 2D: la vista isométrica solo existe en la página interactiva.
- README, `docs/demo.md` y `docs/instalacion.md`: pestaña «Interactiva», Node 22 como requisito opcional y
  la hoja de ruta al día.

### Evaluación
- **Caso 5 nuevo (`fisico-interactivo-ddr5`) y dos consultas de activación nuevas**, corridos el 2026-11-02
  (`evals/resultados-2026-11-02b.md`). Calidad con y sin skill en subagentes limpios: **8/8 con skill frente
  a 4/8 sin ella**, con Sonnet y con Haiku. Activación **64/66** con Sonnet, Haiku y Opus 5.5 (22 consultas
  cada uno). Los dos fallos son la misma consulta de validación: una página «que se recorra con el scroll,
  tipo 3D» se va a la guía web. Al ser de validación, no se tocó la descripción, que va por 1.001 de 1.024
  caracteres.
- Dos defectos que encontraron las evals, corregidos antes de publicar:
  - `capturar-cdp.mjs` usaba un puerto fijo, y dos capturas a la vez se colgaban. Ahora el navegador elige
    uno libre.
  - La plantilla interactiva activaba el scroll suave desde el principio, y a veces el salto inicial a un
    `#ancla` no ocurría (1 de 8 cargas). Ahora el scroll suave se activa cuando la página ya cargó: 14 de 14.

## [1.1.1] - 2026-11-02

### Corregido
- `ensamblar.py`: el pie de figura (`figcaption`) y el hueco de figura pendiente usaban el gris del tema
  (`--gris`), que en oscuro es casi blanco, sobre la lámina blanca fija de las figuras: el texto no se leía.
  Ahora llevan colores fijos para lámina blanca (`#5c6b7a` y `#dde3ea`), iguales en los dos temas. Lo
  encontró el subagente del caso 1 de las evals al revisar su página en oscuro.

### Añadido
- `docs/demo.md`: cómo se ve un despiece terminado (el SSD de `assets/ejemplo-fisico.json`), con la portada y
  la página completa capturadas en claro y oscuro, las dos vistas explotadas y el modelo del que sale todo.
  Los ficheros están en `docs/demo/`.
- `docs/instalacion.md`: paso a paso para macOS, Linux y Windows, con Git o sin él, comprobación, primer
  despiece, actualizar, desinstalar y qué hacer si algo falla.
- `docs/media/banner.svg`: cabecera del README.
- README reescrito con la identidad de Think28 (t28.io): barra de navegación hacia Demo, Instalación,
  Changelog y Licencia (GitHub no admite pestañas propias), sección «Así se ve», instalación corta que remite
  a la guía, cifras reales de las evals y hoja de ruta con la página interactiva como siguiente paso.
- `.gitignore`: `demo/` anclado a la raíz (`/demo/`) para que `docs/demo/` sí se versione.

### Evaluación
- **Evals de los casos públicos, corridas el 2026-11-02** (`evals/resultados-2026-11-02.md`). Activación
  **60/60** (Sonnet, Haiku y Fable 5.1, 20 consultas cada uno, sin iterar la descripción). Calidad, cuatro
  casos con y sin skill en subagentes limpios de Sonnet: **26/26 con skill frente a 16/26
  sin ella**; el caso físico repetido con Haiku como ejecutor: **7/7 con skill frente a 2/7 sin ella**.

## [1.1.0] - 2026-11-02

Primera versión pública, publicada como desarrollo de [t28.io](https://t28.io) en
[github.com/javierledesma28/skill-despiece](https://github.com/javierledesma28/skill-despiece).

### Cambiado
- **La marca sale de la skill.** `--marca` acepta la ruta de un JSON (`assets/marca-ejemplo.json` enseña los
  campos: `nombre`, `primario`, `secundario`, `fuente`, `pie`, `lema`) o `ninguna`, el valor por defecto. Las
  marcas de cada organización viven en sus propios repos; la skill no trae ninguna. Un fichero inexistente,
  un color que no sea `#rrggbb` o un campo desconocido devuelven salida 2 con el motivo.
- **Delegación del dibujo sin nombres fijos.** El guion visual se entrega a la skill de dibujo instalada que
  encaje (diagramas editoriales, arquitectura cloud con iconos oficiales, figuras interactivas) o, si no hay
  ninguna, a un script propio: `figuras[].skill = "propio"` y sección nueva «Sin skill de dibujo instalada»
  en `references/guion-visual.md`.
- Ejemplos, referencias, evals y este changelog sin nombres de organizaciones, clientes, rutas locales ni
  recursos concretos. Los casos de eval de calidad son nuevos (WAF genérica, Raspberry Pi 5, activación por
  PIM, idempotencia en una API de pagos) y las 20 consultas de activación se reescribieron en neutro.
- `author` en el frontmatter: t28.io (Javier Ledesma).

### Añadido
- `README.md`, `LICENSE` (MIT) y `.gitignore`.
- `validar_modelo.py`: `propio` como valor válido de `figuras[].skill`.

### Corregido
- `ensamblar.py` revisado para compilar desde Python 3.10 (sin barras invertidas dentro de expresiones de
  f-string, que exigen 3.12), como dice `compatibility`.
- Un `.pyc` que iba versionado.

### Evaluación
- Pruebas de humo de los tres scripts con los dos ejemplos: marca por fichero, sin marca, marca inexistente,
  color inválido y campo desconocido. **Las evals de calidad y de activación de los casos públicos están
  pendientes de correr**; las cifras de la 1.0 (26/26 frente a 15/26; 60/60) siguen en
  `evals/resultados-2026-11-01.md`, con los detalles privados quitados.

## [1.0.1] - 2026-11-01
### Corregido
- `ensamblar.py`: el contenedor de las figuras pasa de `--suave` (casi negro en tema oscuro) a blanco fijo,
  como lámina, en los dos temas. Lo destapó el primer uso real (el despiece de un túnel S2S entre una oficina
  y Azure): una figura con fondo transparente y tinta oscura perdía el título y las cabeceras en oscuro.
  Verificado capturando la página con `data-theme="dark"` forzado.
- `SKILL.md`, paso 6: cómo forzar cada tema al capturar, porque Edge headless sigue el del sistema y las
  dos capturas salían iguales.

## [1.0] - 2026-11-01
### Añadido
- Método de despiece por niveles para cuatro tipos de objeto (físico, proceso, sistema, idea), con
  encuadre previo (pregunta foco, lector, profundidad), modelo intermedio con fuentes, revelado del todo
  a las partes y puertas de comprensión (tres frases y predicción). Sale del research del 2026-11-01
  sobre `anatomy`, las skills de explicación visual mejor valoradas y la bibliografía de vistas
  explotadas, IDEF0, C4, MECE y multimedia learning (`references/fuentes.md`).
- `scripts/validar_modelo.py`: impone las reglas del método sobre `modelo.json` (títulos afirmativos,
  3–7 piezas por nivel, fuentes o supuestos, orden de montaje, flujo, feynman, predicción).
- `scripts/explosionado.py`: vista explotada 2D en SVG para tipo físico, numerada en orden de montaje,
  con lista de piezas, pieza destacada, subconjuntos y marca opcional.
- `scripts/ensamblar.py`: página HTML por niveles con las figuras incrustadas, malentendidos, tres
  frases, predicción plegada y fuentes; tema claro y oscuro; marca opcional.
- `references/metodo-por-tipo.md`, `references/modelo.md`, `references/guion-visual.md` (qué entregar a
  la skill de dibujo) y `references/fuentes.md`.
- Ejemplos válidos: `assets/ejemplo-fisico.json` (SSD NVMe) y `assets/ejemplo-sistema.json`
  (Application Gateway con WAF).
- Descripción en bloque `>-` con las frases del usuario y frontera con las skills vecinas (diagramas,
  gráficos de datos, presentaciones, gráficos interactivos, relevamiento); `argument-hint` para
  `/despiece [qué despiezar]`.
### Corregido durante las evals (antes del commit de la 1.0)
- `ensamblar.py`: tokens de texto `--pt`/`--st` aclarados en tema oscuro; los títulos usaban el primario
  pensado para fondo claro y con `--marca ninguna` habrían sido invisibles.
- `explosionado.py`: la función de cada pieza en la lista se envuelve en dos líneas en vez de recortarse a
  72 caracteres.
### Evaluación
- Calidad: 4 casos (sistema, físico, proceso, idea) con y sin skill en subagentes Sonnet: **26/26 con
  skill frente a 15/26 sin ella**. Sin skill fallan siempre el modelo por niveles, los supuestos pieza a
  pieza y el cierre de tres frases y predicción. Detalle en `evals/resultados-2026-11-01.md`.
- Activación: **60/60** en 3 pases (Sonnet, Haiku y Fable 5.1) por subagentes, porque `claude -p` no tenía
  sesión OAuth; 12/12 entrenamiento y 8/8 validación en cada pase, sin iterar la descripción.
