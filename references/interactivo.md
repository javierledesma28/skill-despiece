# La página interactiva (`ensamblar.py --interactivo`)

Leer antes de usar `--interactivo` por primera vez en la sesión. Explica el bloque `geometria` del
modelo, cómo se calculan las alzas, qué hace la página y cómo capturarla para revisarla.

## Contenido

[Qué genera](#qué-genera) · [El bloque geometria](#el-bloque-geometria) ·
[Otros campos que usa](#otros-campos-que-usa) · [Alzas y oclusiones](#alzas-y-oclusiones) ·
[Parámetros de la página](#parámetros-de-la-página) · [Capturar y revisar](#capturar-y-revisar) ·
[Límites](#límites)

## Qué genera

Un solo `index.html` autocontenido, sin dependencias ni red, con las figuras dibujadas desde la geometría
(no usa `figuras/`, ni las de `explosionado.py`):

| Sección | Qué hace |
|---|---|
| Nivel 0 | Vista isométrica que se abre sola al cargar (o con el deslizador y «Explotar» / «Armar»). Cada pieza se selecciona en la figura o en la lista, y su ficha dice función y fuente |
| Desmontaje | Al bajar por la página, las piezas se separan una a una en el orden inverso al montaje |
| Flujo | Solo si hay `flujo`: paso a paso, con la flecha de la relación que alimenta cada pieza y un paquete que la recorre |
| Nivel 2 | Una tarjeta por raíz con subconjunto: se abre al llegar con el scroll o con «Ver por dentro →», y muestra las capas en rayos X |
| Malentendidos, tres frases, prueba | La predicción con opciones si hay `opciones`; si no, la respuesta plegada |

Funciona sin JavaScript (figuras abiertas, fichas visibles), en tema claro y oscuro, con
`prefers-reduced-motion` (sin animaciones, todo por pasos) y en móvil.

## El bloque `geometria`

Ejes: **x** a lo largo de la placa, **y** a lo ancho, **z** hacia arriba desde la cara de la placa.
Origen en una esquina; todas las medidas en `unidad` (por defecto `mm`). Ejemplo completo y válido en
`assets/ejemplo-fisico.json`.

| Campo | Qué es |
|---|---|
| `unidad` | Texto para los rótulos (`mm`) |
| `placa.largo`, `placa.ancho` | Tamaño de la base, > 0 |
| `placa.grosor` | Grosor de la base (por defecto 1) |
| `placa.agujeros` | `[[x, y, radio], …]` |
| `placa.rotulo` | Pie de la lámina; huecos: `{nombre}`, `{ancho}`, `{largo}`, `{grosor}`, `{unidad}` |
| `piezas.<id>` | Una entrada por **raíz**, ni más ni menos |
| `subconjuntos.<id>` | Una por raíz con hijos que se quiera abrir en el nivel 2 |

**Cada raíz** (`piezas.<id>`):

| Campo | Qué es |
|---|---|
| `forma` | `placa` (exactamente una: la base, con el `orden` más bajo), `chip`, `conector` o `caja` (por defecto). `chip` y `caja` se ven igual; `conector` va en dorado con pines |
| `x`, `y` | `[desde, hasta]`, con desde < hasta |
| `alto` | > 0 |
| `z` | Altura a la que empieza (por defecto 0, sobre la placa); para apilar una pieza sobre otra |
| `unidades` | En lugar de `x`, cuando hay varias iguales en fila: `[[x0, x1], …]`, tantas como `cantidad` |
| `muesca` | Solo `conector`: `[desde, hasta]` en y, el hueco de la llave |

**Cada subconjunto** (`subconjuntos.<id>`): `huella` (`{x: [..], y: [..]}`, el contorno de la pieza
abierta), `rotulo` (huecos `{nombre}`, `{ancho}`, `{largo}`, `{unidad}`, `{n}`) y `piezas`, una entrada
por hija con `z` (`[desde, hasta]`, de abajo arriba), y opcionales `x`, `y` (si no, ocupa toda la huella) y
`patron` (`rejilla` o `puntos`) para distinguir capas que, si no, serían iguales.

**Medidas.** Salen de la hoja de datos o de la norma (en el SSD, la M.2 fija 22 × 80 mm). Si son
aproximadas, el rótulo no las presenta como exactas: «Placa de unos 10 × 15 cm», no «10 × 15 cm».

`validar_modelo.py` comprueba todo esto (y que dos piezas no ocupen el mismo volumen): pasarlo antes de
ensamblar.

## Otros campos que usa

| Campo | Para qué |
|---|---|
| `figuras[].destacada` | Id de la pieza que la portada (figura de nivel 1) o la tarjeta del nivel 2 muestran seleccionada al abrir. Tiene que estar en `piezas` de esa figura |
| `prediccion.opciones` | 2–4 respuestas cortas; la página pide elegir antes de enseñar la respuesta |
| `prediccion.correcta` | Índice de la buena, desde 0 |
| `flujo_entrada` | Lo que entra desde fuera de la frontera al primer paso del flujo; mejor si es uno de `nivel0.fuera`, escrito igual |

El flujo se dibuja con las `relaciones`: a cada paso le llega la relación desde el paso anterior más
cercano. Si no hay ninguna, la ficha lo dice y el validador avisa.

## Alzas y oclusiones

Las alzas (cuánto sube cada pieza al abrir) **no se escriben**: un `lift` en el modelo se ignora. La base no
sube; el resto sube `arranque + escalón × rango de montaje`, y se elige la combinación más clara en la que
ninguna pieza tapa más del 5 % de la cara de arriba de otra ni su número, en la vista abierta y en cada
paso del desmontaje. Las capas de un subconjunto suben cada una un 26 % del alto de la huella en pantalla
(entre 50 y 110 px), para que asome la franja de la de abajo.

Si no hay combinación sin solapes, `ensamblar.py` escribe la página igual, sale con 1 y pone en
`oclusiones` qué pieza tapa a cuál (`tapada`, `por`, `cara_tapada`, `numero_tapado`, `estado` = paso del
desmontaje). Arreglo: separar las piezas en x/y, o agrupar las pequeñas. Para ver solo el cálculo:
`python -I scripts/isometrico.py modelo.json`.

## Parámetros de la página

| Parámetro | Efecto |
|---|---|
| `?p=0..1` | Apertura de la portada (0 armada, 1 abierta) |
| `?paso=N` | Paso del flujo, desde 0 |
| `?abrir=<id>` | Tarjeta del nivel 2 abierta |
| `?tema=light\|dark` | Tema forzado (el botón «Tema» lo recuerda en el navegador) |
| `#nivel0`, `#recorrido`, `#flujo`, `#nivel2`, `#prueba` | Ir a una sección |

## Capturar y revisar

`--screenshot` de Edge o Chrome no sirve aquí: captura antes de que corran el scroll y las animaciones.
`scripts/capturar-cdp.mjs` abre el navegador headless por DevTools Protocol y captura en tiempo real
(Node 22 o más; `--help` para todo):

```bash
node scripts/capturar-cdp.mjs portada.png 1240 900 "file:///<ruta>/index.html?p=1"
TEMA=dark node scripts/capturar-cdp.mjs flujo-oscuro.png 1240 900 "file:///<ruta>/index.html?paso=2#flujo"
node scripts/capturar-cdp.mjs desmontaje.png 1240 900 "file:///<ruta>/index.html" "scrollTo({top: document.getElementById('recorrido').offsetTop + 1400, behavior: 'instant'})" 1200
node scripts/capturar-cdp.mjs movil.png 390 844 "file:///<ruta>/index.html"
SIN_JS=1 node scripts/capturar-cdp.mjs sin-js.png 1240 900 "file:///<ruta>/index.html#nivel2"
```

El JavaScript de la captura tiene que desplazar con `behavior: 'instant'`: la página usa scroll suave y,
si no, la captura sale a mitad de camino. Salida 1 = la página lanzó errores de JavaScript (van a stderr).

Mirar: la pieza destacada se ve y no la tapa nada; los números de la figura coinciden con la lista; el
desmontaje separa en orden inverso al montaje; en el flujo, la flecha iluminada es la de la ficha; nada se
corta en móvil; los textos se leen en oscuro; sin JavaScript se ve todo abierto.

## Límites

- Solo tipo `fisico`. En el resto, o sin `geometria`, `--interactivo` avisa y escribe la página estática.
- Dibuja hasta el nivel 2; las piezas de nivel 3 quedan solo en la estática.
- Las flechas del flujo se apoyan en raíces: un paso del flujo que no es raíz no tiene dónde dibujarse.
- Formas en caja: sirve para placas con componentes (tarjetas, discos, routers, placas base). Un objeto
  sin una base plana (un motor, una cerradura) no se dibuja bien: usar la vista 2D de `explosionado.py`.
