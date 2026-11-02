<div align="center">

[**← Interactiva**](interactivo.md) · [**README**](../README.md) · [**Demo**](demo.md) · [**Instalación**](instalacion.md) · [**Changelog**](../CHANGELOG.md)

</div>

# Research: la capa interactiva de `despiece`

Consolidado el 2026-11-02, antes de escribir la versión 1.2.0, y conservado como registro de por qué la página
interactiva es como es. Las decisiones ya están tomadas (sección 0) y las fases 1 a 3 están hechas
(`ensamblar.py --interactivo`). Lo que cambió al implementarlo respecto del prototipo está en la
[sección 11](#11-qué-cambió-al-implementarlo-120).

Lo acompaña el prototipo navegable del SSD que sirvió para decidir:
[prototipo-interactivo/index.html](prototipo-interactivo/index.html). Es un solo fichero de 68 KB, sin dependencias,
con sus capturas en [`prototipo-interactivo/capturas/`](prototipo-interactivo/capturas/). La versión que genera la
skill, con el mismo ejemplo, está en [interactivo/index.html](interactivo/index.html).

La pregunta era cómo pasar de una página estática con figuras a algo que se abra, se recorra y deje entrar en cada nivel,
«todo muchísimo más gráfico», sin frameworks pesados y sin perder el método: encuadre, fuentes, de 3 a 7 piezas por nivel
y las dos puertas de comprensión.

## 0. Recomendación y decisiones

**Un modo interactivo dentro de la misma skill, no una skill hermana.** Es `ensamblar.py --interactivo`, alimentado por
el mismo `modelo.json` y una geometría opcional.

**La página es un único HTML con SVG en línea, sin librerías.**
- Python calcula la proyección isométrica y deja la figura ya explotada en el SVG, así que sin JavaScript se ve igual.
- El CSS y el JS añaden cuatro gestos. En el prototipo eran unas 260 líneas de CSS y 460 de JS, contando el pintado de
  la figura, que en la skill pasó a Python:
  - abrir y cerrar con un deslizador;
  - desmontar al hacer scroll;
  - recorrer el flujo paso a paso;
  - entrar en la pieza que decide con una View Transition.
- Todo lo que no es Baseline va detrás de `@supports` y tiene una alternativa que funciona.

**Decisiones tomadas:**
1. **Flag en `ensamblar.py`**, no una skill hermana (comparación en la sección 6).
2. **La interactiva se pide con el flag.** La salida por defecto sigue siendo la estática, que sirve para PDF y
   documentos; `--interactivo` solo cambia algo si el modelo trae `geometria`.
3. **Primera entrega: fases 1 a 3, solo tipo físico.** Procesos, sistemas e ideas (fase 4) quedan para después.
4. **`explosionado.py` sigue en 2D.** La figura isométrica solo existe en la página interactiva.
5. **El prototipo y este research van a `docs/`, sin GitHub Pages.** Se ven descargando el HTML y abriéndolo.

## 1. Qué hacen los referentes

| Referente | Cómo lo hace | Qué tomamos | Qué no |
|---|---|---|---|
| **Bartosz Ciechanowski** (ciechanow.ski) | WebGL propio sin librerías (`ice.js`, 281 KB): deslizadores, arrastrar para girar, enlace de pausa, cortes con trama, complejidad progresiva | El deslizador como gesto central, la pausa y la complejidad que se revela por partes | WebGL y los modelos a mano: no escala a una skill. La licencia **no está declarada**: no se reutiliza nada suyo |
| **anatomy** (MIT) | Isométrico a 45°/30°, 3D en beta, recorrido automático en reposo, imagen estática con movimiento reducido, temas claro y oscuro | El isométrico, el recorrido automático, la imagen estática con movimiento reducido y los dos temas | Exige **≥ 40 piezas**, que chocan con nuestras 3–7, y Node ≥ 20.10. Sus ~24.000 estrellas para un repo creado el 2026-10-08 son sospechosas |
| **teardown** (MIT, creado el 2026-10-30) | HTML único y offline con three.js incrustado; necesita Node 20+, Playwright y ffmpeg | La idea de un único fichero offline | three.js (~814 KB) y la cadena Playwright/ffmpeg. Sus modos de corte **no se pudieron confirmar** |
| **Explorables** (Bret Victor, 2011; Nicky Case, en CC0; Nutshell) | El lector manipula el modelo y ve la consecuencia | Predecir antes de revelar; el detalle bajo demanda de Nutshell | — |
| **Distill** (Hohman et al., 2020) | Taxonomía de los artículos interactivos: detalle bajo demanda, varias representaciones, predecir antes de ver, scrollytelling frente a stepper | El criterio para elegir el gesto según la pregunta del lector (sección 4) | Distill está en pausa desde 2021: es referencia, no plataforma |
| **Scrollama** 3.2.0 (MIT, 2 KB) | Scrollytelling sobre IntersectionObserver | Su patrón, como fallback | La dependencia: el IntersectionObserver nativo basta |

**Librerías 3D descartadas por peso.**

| Librería | Tamaño |
|---|---|
| Zdog | 29,7 KB (7,3 KB en gzip) |
| three.js | ~814 KB |
| `<model-viewer>` | 1,07 MB |

Ninguna hace falta para lo que pide el método. Zdog queda solo para una fase opcional de giro (fase 5).

## 2. Lo que dice la evidencia: anti-patrones

- **La animación no es mejor que una figura estática solo por moverse** (Tversky, Morrison y Bétrancourt, 2002). Ayuda
  cuando el lector la controla y cuando enseña algo que cambia en el tiempo, como el orden de desmontaje o el camino del dato.
  Por eso nada se mueve sin un gesto, salvo la apertura inicial: dura menos de 2,5 s y pasa una sola vez.
- **Explotar todo a la vez confunde** (Li, Agrawala, Curless y Salesin, 2008). Hay que explotar por pasos y en el orden de
  las dependencias. Por eso las piezas salen escalonadas en orden inverso de montaje: la última que se montó sale primero.
- **Los efectos decorativos restan** (Harp y Mayer, 1998; comprobado solo en fuentes secundarias). Cada efecto de la
  página responde una pregunta (sección 4), y el paquete que viaja por la flecha solo aparece en el paso activo.
- **El scrolljacking irrita** (NN/g, 2023). El scroll nunca se secuestra: el desmontaje sigue al scroll normal y además
  tiene botones de Anterior y Siguiente.
- **WCAG 2.2.2 (pausar, detener, ocultar).** Un movimiento automático de más de 5 s necesita pausa:
  - «▶ Recorrer» solo arranca si el lector lo pide, se para en el último paso y tiene «❚❚ Pausar»;
  - el paquete hace 3 viajes de 1,3 s, menos de 5 s.
- **WCAG 2.3.3 (animación por interacción).** Con `prefers-reduced-motion: reduce`, la figura aparece ya explotada y el
  desmontaje y el flujo cambian de estado sin animar.

## 3. Soporte de navegador, a 2026-11-02

| Pieza | Estado | Uso en la página |
|---|---|---|
| Scroll-driven animations | **Limitado**: Chrome y Edge 115, Safari 26; Firefox no | Desmontaje por scroll, detrás de `@supports` y con fallback por IntersectionObserver |
| View Transitions (mismo documento) | Baseline nuevo desde 2025-10-14 | Entrar en el nivel 2 con el botón; sin ellas, el cambio es instantáneo |
| `popover` | Baseline nuevo desde 2025-01-27 | «▲ supuesto»; sin él, el clic lleva a la leyenda |
| Anchor positioning | **Limitado** | Coloca el popover junto a su botón, solo bajo `@supports (anchor-name: --x)` |
| `@property` | Baseline nuevo | `--p` animable: el progreso de la explosión |
| `light-dark()`, `<details name>` | Baseline nuevo | El tema, y la respuesta de la predicción sin elegir |
| `color-mix()` | Baseline amplio | Apagar las piezas no destacadas sin volverlas transparentes |

## 4. Arquitectura: un gesto por pregunta

Cada sección responde una pregunta distinta del lector. Si un gesto no responde ninguna, sobra.

| Sección | Pregunta del lector | Gesto y técnica | Sin soporte, sin JS o con movimiento reducido |
|---|---|---|---|
| **Nivel 0 · portada** | ¿De qué está hecho? | Se abre sola una vez, escalonada. Deslizador «Armado ↔ Explotado», con botones Explotar y Armar. Tocar una pieza la destaca y rellena la ficha. Técnica: `@property --p`; cada pieza se desplaza `--p × lift` | Sin JS, el SVG ya está explotado. Con movimiento reducido, se abre sin animar |
| **Desmontaje** | ¿En qué orden sale y por qué? | Figura fija y pasos que se desplazan; cada paso levanta y destaca una pieza. Botones ↑ Anterior y Siguiente ↓. Técnica: una `view-timeline` por paso, con `timeline-scope` en la sección | Sin scroll-driven, IntersectionObserver con 41 umbrales. Con movimiento reducido, cambio de estado sin interpolar |
| **Flujo** | ¿Por dónde pasa una escritura? | Stepper con píldoras, Anterior, Siguiente, flechas del teclado y «▶ Recorrer». La flecha activa es un arco con su etiqueta en el vértice, y un paquete viaja por ella. La entrada externa va punteada y marcada como «fuera de la frontera» | Sin la animación del paquete; el estado cambia igual |
| **Nivel 2** | ¿Qué hay dentro de la pieza que decide? | La tarjeta se abre al ocupar media pantalla, salvo que el lector la haya cerrado, o con «Ver por dentro →». Con el botón, View Transition con un único `view-transition-name`. Las capas apiladas se ven translúcidas, como en rayos X | Sin View Transitions, cambio instantáneo |
| **Puertas** | ¿Lo entendí? | Tres frases. Predicción con opciones A/B y veredicto, más «Ver la respuesta sin elegir» | `<details>` funciona sin JS |
| **Detalle bajo demanda** | ¿De dónde sale este dato? | Popover «▲ supuesto» anclado a su botón; cada pieza cita su fuente | Sin popover, el clic lleva a la leyenda |
| **Tema** | — | Auto, claro y oscuro; se recuerda en `localStorage`, dentro de `try/catch` | Sigue al sistema |

### Lo que se corrigió en el prototipo tras probarlo

Pruebas del 2026-11-02, en Edge headless y en un navegador Chromium con interfaz.

- **Las piezas apagadas pasaron de translúcidas a un lavado opaco**, mezclado con `color-mix()` hacia el color de la lámina.
  - Con opacidad, la placa asomaba a través de los chips a medio levantar, y cada chip parecía doble.
  - **Excepción: en un subconjunto apilado**, como las capas de la NAND, el lavado opaco tapa las capas de abajo. Ahí se
    queda translúcido.
  - Regla: lavado si las piezas se reparten sobre la placa, rayos X si se apilan.
  - Cuánto se apaga es un token de `:root` por tema (`--apagado`), no una media query por componente.
- **El foco solo se mueve cuando el lector pulsa un botón.** Abrir el nivel 2 al hacer scroll, o desde la URL, le robaba
  el foco y pintaba un recuadro alrededor del título. Ahora:
  - «Ver por dentro» lleva el foco al título del nivel 2;
  - «Volvé al todo» lo lleva al título del nivel 0.
- **Flujo**: la etiqueta va en el vértice del arco, y solo se ve la del paso activo.
- **Movimiento**: la apertura es escalonada, y `scroll-behavior: smooth` solo se aplica sin movimiento reducido.
- **Móvil**: la barra de navegación ocupa una sola línea.

## 5. Qué cambia en el modelo

Cuando se escribió el prototipo, sus extensiones pasaban el validador sin que este las comprobara: `validar_modelo.py`
ignoraba los campos que no conocía. En 1.2.0 tienen reglas propias (detalle en
[`references/modelo.md`](../references/modelo.md) y [`references/interactivo.md`](../references/interactivo.md)), y
`evals/probar_validador.py` comprueba cada una con una mutación del ejemplo del SSD.

| Campo | Qué es | Regla del validador |
|---|---|---|
| `figuras[].destacada` | Id de la única pieza destacada de esa figura | Debe estar en `figuras[].piezas`; si no, error |
| `prediccion.opciones[]` | De 2 a 4 respuestas cerradas | Opcional; si está, exige `correcta` |
| `prediccion.correcta` | Índice de la opción correcta | Dentro del rango de `opciones` |
| `geometria` (solo físico) | `unidad` y `placa`. Por raíz: `forma` (`placa`, `chip`, `conector`, `caja`), `x` e `y`, `alto`, y `unidades` cuando `cantidad` > 1. Por subconjunto: `huella` y, en cada capa, `z` y `patron` | Todas las raíces tienen geometría; dos piezas no ocupan el mismo volumen; `unidades` coincide con `cantidad` |
| `flujo_entrada` | De dónde llega el dato desde fuera de la frontera («el slot M.2 y el bus PCIe») | Mejor si es uno de `nivel0.fuera`, escrito igual; si no, aviso |

Dos reglas más que salieron del prototipo:
- **Cada paso del flujo necesita una relación desde un paso anterior**: es la flecha que se anima. Si falta, aviso.
- **El texto de cada paso no necesita un campo nuevo.** Sale de la relación («Llega desde *X* por «*etiqueta*»») y de la
  `funcion` de la pieza.

**`lift` no se escribe a mano.** En el prototipo se escribió a mano y, con la figura explotada del todo, el primer chip
NAND tapaba media caché DRAM justo cuando estaba destacada (captura 03 del prototipo). En 1.2.0 lo calcula Python
(sección 11) y un `lift` en el modelo se ignora con un aviso.

La geometría va como bloque opcional dentro de `modelo.json`, para tener un solo fichero, validado junto con el resto.

## 6. Qué cambia en la skill

**Flag en `ensamblar.py` frente a skill hermana:**

| | `ensamblar.py --interactivo` (elegido) | Skill hermana `despiece-interactivo` |
|---|---|---|
| Método, modelo y validador | Los mismos, sin duplicar | Los duplica, o depende de `despiece` y obliga a cargar las dos |
| Activación | Sin cambios: «despiezá esto» activa una sola skill | Frontera ambigua: ¿cuál de las dos responde a «despiezá esto»? |
| Coste en contexto | `SKILL.md` crece unas líneas; el detalle va a `references/interactivo.md` | Otra descripción cargada siempre |
| Riesgo | La skill crece en scripts | Las dos se desincronizan |

**Piezas del cambio, tal como quedaron:**

1. **`scripts/isometrico.py`**: la proyección `(x, y, z) → (cx + (x − y)·0,866·S, cy + (x + y)·0,5·S − z·S)`, las tres
   caras de cada caja y su orden de pintado, y el cálculo de las alzas sin oclusiones. Se ejecuta también solo, para ver
   el cálculo.
2. **`scripts/interactiva.py`**: dibuja cada pieza como `<g class="pieza" data-id style="--lift">`, con el SVG ya
   explotado para que sin JS se vea igual, y rellena la plantilla.
3. **`assets/plantilla-interactiva.html`**: el CSS y el JS del prototipo, sin el SSD y sin pintado. Lee el modelo de un
   bloque `<script type="application/json">`.
4. **`ensamblar.py --interactivo`**: si el modelo no trae geometría o no es físico, escribe la página estática y lo dice.
5. **`explosionado.py`**: sin cambios (decisión 4).
6. **Captura y revisión del paso 6.** Una página interactiva no se puede revisar con `--screenshot`: hay que capturar en
   tiempo real por DevTools Protocol. Lo hace `scripts/capturar-cdp.mjs`, para Node 22 o superior y sin dependencias. Se
   captura cada estado con parámetros de URL (sección 11) y una vista de móvil a 390 px.
7. **Tipos no físicos (fase 4).** El stepper y el detalle bajo demanda podrían funcionar sobre una figura delegada si cada
   nodo del SVG lleva un `data-id` igual al `id` de su pieza. Hay que pedírselo a `diagram-design` en el guion; **sin
   verificar** que lo respete.
8. **`SKILL.md`**: dos gotchas nuevos y el bloque «Interactiva» del paso 6, con el detalle en
   `references/interactivo.md`.

**Gotchas aprendidos al hacer el prototipo:**
- **Lavado o translúcido.** Lavado opaco cuando las piezas se reparten; translúcido cuando se apilan.
- **Oclusión.** Calcular `lift` para que ninguna pieza quede tapada.
- **Foco.** No moverlo nunca sin un gesto del lector.
- **`--screenshot` con `--virtual-time-budget` no sirve después de desplazar.** Ni los IntersectionObserver ni las
  animaciones ligadas al scroll se actualizan, así que la captura sale en un estado falso.
- **`--window-size` por debajo de unos 500 px no da un móvil de verdad.** Con `--headless=new`, la captura sale recortada.
- **Un panel de navegador oculto no prueba la página.** El segundo plano la estrangula: ni View Transitions ni
  IntersectionObserver.

## 7. Orden de implementación

| Fase | Contenido | Estado |
|---|---|---|
| 1 | `isometrico.py`, la geometría en el modelo con su validación, el SVG explotado sin JS, el deslizador, la pieza destacada, el popover y el tema | **Hecha en 1.2.0** |
| 2 | El desmontaje por scroll con su fallback, y el stepper del flujo con el paquete y «▶ Recorrer» | **Hecha en 1.2.0** |
| 3 | Entrar en el subconjunto, las opciones de la predicción y la captura por estados del paso 6 | **Hecha en 1.2.0** |
| 4 | Procesos, sistemas e ideas: stepper y detalle sobre figuras delegadas con `data-id` | Pendiente. Hecha cuando el ejemplo de sistema (`assets/ejemplo-sistema.json`) se recorra paso a paso |
| 5 (opcional) | Giro (con Zdog o con reproyección propia en 4 vistas), cortes con trama y vídeo | Se decide tras usar las fases 1 a 3 |

## 8. Limitaciones conocidas

- **Solo se probó en Chromium**: Edge headless y un navegador Chromium con interfaz.
  - Sin probar: Firefox (donde el desmontaje usa el fallback), Safari, dispositivos táctiles reales y lector de pantalla.
  - El foco se comprobó por DOM.
- **En móvil la figura queda pequeña.** A 390 px se reconocen las piezas, pero los números son diminutos.
- **No se puede girar.** Haría falta reproyectar las caras: es la fase 5.
- **Formas en caja.** Sirve para placas con componentes; un objeto sin base plana (un motor, una cerradura) no se dibuja
  bien y sigue usando la vista 2D de `explosionado.py`.
- **Los parámetros de URL son para capturar y probar**, no para el lector.

## 9. Sin verificar

- La licencia de Ciechanowski y los modos de corte de teardown.
- Cómo ordena Zdog por profundidad.
- El recuento de estrellas de anatomy.
- Harp y Mayer (1998), visto solo en fuentes secundarias.
- Si Firefox ya trae las scroll-driven animations. La guía de referencia dice que no; una fuente apuntaba a Firefox 159,
  sin confirmar.
- Que `diagram-design` respete los `data-id` (fase 4).

## 10. Cómo ver el prototipo

Descargar [`prototipo-interactivo/index.html`](prototipo-interactivo/index.html) y abrirlo con doble clic: no carga
nada de fuera. Qué probar:
1. Mover el deslizador.
2. Tocar una pieza.
3. Bajar por el desmontaje.
4. En el flujo, pulsar «▶ Recorrer».
5. Seguir bajando hasta que se abra la NAND.
6. Responder la predicción.
7. Cambiar el tema, arriba a la derecha.

| Captura del prototipo | Qué muestra |
|---|---|
| [`01-portada-claro.png`](prototipo-interactivo/capturas/01-portada-claro.png) · [`02-portada-oscuro.png`](prototipo-interactivo/capturas/02-portada-oscuro.png) | Nivel 0 explotado, con la controladora destacada |
| [`03-desmontaje-claro.png`](prototipo-interactivo/capturas/03-desmontaje-claro.png) | Paso 3 de 6, con las alzas escritas a mano: un chip NAND tapa media DRAM |
| [`04-flujo-claro.png`](prototipo-interactivo/capturas/04-flujo-claro.png) | Paso 3 de 4 del flujo: la «tabla de mapeo», de la controladora a la DRAM |
| [`05-nivel2-oscuro.png`](prototipo-interactivo/capturas/05-nivel2-oscuro.png) | Dentro de la NAND: la caché SLC destacada sobre las capas, en rayos X |
| [`06-prueba-claro.png`](prototipo-interactivo/capturas/06-prueba-claro.png) | Las tres frases y la predicción |
| [`07-movil-claro.png`](prototipo-interactivo/capturas/07-movil-claro.png) | La portada a 390 px |

## 11. Qué cambió al implementarlo (1.2.0)

- **La figura la pinta Python, no el JS.** El prototipo dibujaba el SSD en el navegador, con un `<noscript>` que lo
  explicaba. Ahora el SVG llega pintado y explotado en el HTML, y el JS solo cambia estados.
- **Las alzas se calculan.** La base no sube; el resto sube `arranque + escalón × rango de montaje`. Se prueban arranques
  de 0,4 a 1,2 veces el alto en pantalla de la pieza más grande y escalones de 10 a 50 px, y se elige la combinación en la que ninguna
  pieza tapa más del 5 % de la cara de arriba de otra ni su número, en la vista abierta y en cada paso del desmontaje. Si
  no hay ninguna, `ensamblar.py` sale con 1 y dice qué pieza tapa a cuál. Las capas de un subconjunto suben un 26 % del
  alto de la huella en pantalla, entre 50 y 110 px.
- **`?nand=1` pasó a ser `?abrir=<id>`**, porque cada raíz con subconjunto tiene su tarjeta. Los demás parámetros
  (`?p`, `?paso`, `?tema`) siguen igual.
- **`capturar-cdp.mjs` vive en `scripts/`, no en `docs/`**: el paso 6 lo ejecuta en cada despiece interactivo. Acepta
  `TEMA`, `MOVIMIENTO`, `SIN_JS` y `PUERTO` como variables de entorno.
- **La View Transition solo va con el botón.** Al abrir el nivel 2 con el scroll, la instantánea de la transición se
  quedaba fija mientras la página seguía desplazándose y pisaba la sección siguiente. La apertura por scroll va sin
  transición de vista; las capas se separan igual con la transición de `--p`.
- **Las capturas desplazan con `behavior: 'instant'`.** La página usa `scroll-behavior: smooth`, y un `scrollTo` normal
  dejaba la captura a mitad de camino.
- **El validador comprueba la geometría entera**: formas, rangos, una sola placa y la primera en montarse, volúmenes que
  no se solapan, `unidades` igual a `cantidad`, subconjuntos solo en raíces con hijos y huecos de los rótulos.

## Fuentes

- anatomy: github.com/wheresryan22/anatomy.
- Bartosz Ciechanowski: ciechanow.ski.
- Bret Victor, *Explorable Explanations*, 2011: worrydream.com/ExplorableExplanations.
- Hohman, Conlen, Heer y Chau, *Communicating with Interactive Articles*, Distill, 2020:
  distill.pub/2020/communicating-with-interactive-articles.
- Li, Agrawala, Curless y Salesin, *Automated Generation of Interactive 3D Exploded View Diagrams*, SIGGRAPH 2008.
- Tversky, Morrison y Bétrancourt, *Animation: can it facilitate?*, International Journal of Human-Computer Studies, 2002.
- Nielsen Norman Group, sobre scrolljacking, 2023.
- WCAG 2.2, criterios 2.2.2 y 2.3.3: w3.org/TR/WCAG22.
- Scrollama: github.com/russellsamora/scrollama.
- Guías de `modern-web-guidance` (versión 2026_10_12): `scrollytelling`, `scroll-entry-exit-effects`,
  `same-document-transitions`, `dark-mode`, `motion` y `position-aware-tooltips`.
