# El explorador (`ensamblar.py --explorador`)

Leer antes de usar `--explorador` por primera vez en la sesión. Explica qué genera, cómo se navega, los
enlaces que acepta, cómo capturarlo para revisarlo y qué no hace.

## Contenido

[Qué genera](#qué-genera) · [Cómo se navega](#cómo-se-navega) · [Enlaces y parámetros](#enlaces-y-parámetros) ·
[Capturar y revisar](#capturar-y-revisar) · [Límites](#límites) · [Por qué se precalcula](#por-qué-se-precalcula)

## Qué genera

Un solo `explorador.html` autocontenido, sin dependencias ni red, para **cualquier tipo** y sin bloque
`geometria`. Lleva una lámina explotada por cada nivel que se puede abrir (el todo y cada pieza con hijas),
dibujada por `explosionado.py` con el mismo código que las figuras de la página estática:

| Zona | Qué hace |
|---|---|
| Lámina | La vista explotada del nivel. Las piezas con «+» se abren acercándose a ellas |
| Migas y «Volver» | La ruta desde el todo; cada miga lleva a ese nivel |
| Título y eje | El título de la figura del nivel y lo que ordena sus piezas (`eje`) |
| Contexto | Solo en el todo: el nivel 0, la pregunta foco, la frontera, lo que queda fuera y el lector |
| Lista | Las piezas del nivel con el número de la lámina; «+ N dentro» en las que se abren |
| Ficha | Función y fuente de la pieza elegida, o «▲ supuesto»; «Abrir…» si tiene hijas |
| Comprensión | Las tres frases y la predicción, con la respuesta plegada |

No usa `--figuras`: las figuras de flujo, red o secuencia que se delegan a otra skill no entran (ver
[Límites](#límites)).

## Cómo se navega

| Gesto | Efecto |
|---|---|
| Rueda, pellizco del trackpad o pellizco táctil **sobre una pieza con «+»** | La abre en su lámina |
| Lo mismo hacia atrás, en cualquier punto | Sube al nivel de arriba |
| Botones «+» y «−», teclas `+` y `-` | Abre la pieza elegida; sube un nivel |
| Clic en una pieza (lámina o lista) | La elige y muestra su ficha; doble clic la abre |
| «Atrás» y «adelante» del navegador | Suben y bajan un nivel |

Si la página tiene scroll (pantallas bajas, móvil), la rueda desplaza y el zoom pide Ctrl o el pellizco. Un
gesto no abre dos niveles seguidos aunque siga llegando inercia del trackpad.

Al cambiar de nivel, el foco va al título del nivel nuevo, o a la pieza de la que se venía al subir; tras un
gesto, el cambio se anuncia en una región viva. La transición usa View Transitions y nace en la pieza que se
abre; con `prefers-reduced-motion: reduce` o en navegadores sin la API, el cambio es instantáneo.

## Enlaces y parámetros

| Parámetro | Efecto |
|---|---|
| `#/<id>` | Abre el nivel de esa pieza (una con hijas). Un id que no existe cae en el todo y se quita de la barra |
| `?sel=<id>` | Pieza elegida al cargar, si está en el nivel que se abre |
| `?tema=light\|dark` | Tema forzado (el botón «Tema» lo recuerda en el navegador) |

Un enlace profundo funciona como cualquier otro nivel: «Volver» sube al padre y «atrás» vuelve al enlace.

## Capturar y revisar

`scripts/capturar-cdp.mjs` lo captura en tiempo real (Node 22 o más; `--help` para todo). Funciona con
`file://` y por HTTP:

```bash
node scripts/capturar-cdp.mjs todo.png 1240 900 "file:///<ruta>/explorador.html"
TEMA=dark node scripts/capturar-cdp.mjs nivel-oscuro.png 1240 900 "file:///<ruta>/explorador.html?sel=<hija>#/<pieza>"
node scripts/capturar-cdp.mjs movil.png 390 844 "file:///<ruta>/explorador.html"
SIN_JS=1 node scripts/capturar-cdp.mjs sin-js.png 1240 900 "file:///<ruta>/explorador.html"
MOVIMIENTO=reduce node scripts/capturar-cdp.mjs - 1240 900 "file:///<ruta>/explorador.html" "<js que navega y devuelve el estado>"
```

Con `-` como salida no captura: imprime lo que devuelve el JavaScript, que puede lanzar eventos `wheel`,
`PointerEvent` o `keydown` y devolver `location.hash`, `history.state` y el elemento con foco. Salida 1 = la
página lanzó errores de JavaScript (van a stderr).

**Un solo evento `wheel` sintético no abre nada.** El zoom se acumula, así que hacen falta unos 6 eventos de
`deltaY: -40`, o uno con `ctrlKey`. Hay que apuntar al **rótulo** de la pieza (`.fv-llamada`), no al centro de
su caja: en las vistas apiladas ese centro cae sobre la pieza de encima. Si la página tiene scroll, la rueda
sin Ctrl desplaza. Este bucle abre `<pieza>` y devuelve dónde quedó:

```js
(async () => {
  const id = '<pieza>', esc = document.getElementById('escenario');
  const dormir = ms => new Promise(f => setTimeout(f, ms));
  const rotulo = document.querySelector(`#lamina .fv-llamada[data-id="${id}"]`);
  rotulo.scrollIntoView({ block: 'center' }); await dormir(100);
  const r = rotulo.getBoundingClientRect(), x = r.left + r.width / 2, y = r.top + r.height / 2;
  const ctrl = document.scrollingElement.scrollHeight > innerHeight + 2;
  for (let i = 0; i < 12 && location.hash !== `#/${id}`; i++) {
    esc.dispatchEvent(new WheelEvent('wheel', { deltaY: -40, ctrlKey: ctrl, clientX: x, clientY: y, bubbles: true, cancelable: true }));
    await dormir(16);
  }
  await dormir(800);
  return { hash: location.hash, nivel: history.state?.nivel };
})()
```

Una pestaña oculta pausa las View Transitions: revisar con `capturar-cdp.mjs` y no en un panel de
navegador que no se ve, donde la transición se queda a medias y parece un fallo de la página.

Mirar: cada lámina se ve entera y los números coinciden con la lista; la rueda sobre una pieza con «+» la
abre y hacia atrás vuelve; «atrás» del navegador sube un nivel; los textos se leen en oscuro; nada se corta
en móvil; sin JavaScript se ve el nivel 1 con su aviso.

## Límites

- Solo la vista explotada. Si la pregunta foco se responde con un flujo, una red o una secuencia, esas
  figuras van en la página estática: el explorador la acompaña, no la sustituye.
- Sin JavaScript solo se ve el nivel 1.
- El modelo se lee al generar, no en el navegador: si cambia, se vuelve a ensamblar.
- Pesa unos 100 KB con 2 niveles y 130 KB con 4 (los ejemplos de la skill); cada nivel añade su lámina.

## Por qué se precalcula

La lámina de cada nivel se dibuja en Python al ensamblar, en vez de portar la geometría de
`explosionado.py` a JavaScript. Así hay una sola implementación del dibujo, el explorador enseña
exactamente las mismas figuras que la página estática y una corrección en `explosionado.py` llega a las
dos. El navegador solo cambia de lámina y anima la transición.
