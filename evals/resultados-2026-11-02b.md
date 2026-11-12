# Resultados de evaluación — despiece 1.2.0 (página interactiva) — 2026-11-02

Evaluación de la 1.2.0, que añade `ensamblar.py --interactivo`: el caso nuevo 5 (`fisico-interactivo-ddr5`) y
las 22 consultas de `trigger_queries.json`, dos de ellas nuevas. Los casos 1 a 4 no se repitieron: la 1.2.0
no toca el camino estático, y la demo estática sale idéntica con el modelo nuevo. Los resultados anteriores
están en [resultados-2026-11-02.md](resultados-2026-11-02.md).

Modelo principal de la sesión: Claude Opus 5.5. Calidad: Sonnet y Haiku, con y sin skill. Activación: Sonnet,
Haiku y Opus, un pase cada uno. Los transcripts no se guardan; aquí va el resumen con la evidencia que se
comprobó a mano sobre los ficheros que dejó cada subagente.

## Activación

Como en la 1.1.1, por subagentes: `claude -p` no estaba disponible para `eval_activacion.py`. Cada subagente
recibe el listado de las 21 skills instaladas con su descripción y las 22 consultas barajadas con otra
semilla, y elige la skill que invocaría primero (o ninguna).

Consultas nuevas en la 1.2.0:

- **Entrenamiento, no debe activar**: «al diagrama de la placa base que ya tengo en la web agregale zoom y que
  al tocar cada componente se abra su ficha». Es hacer interactivo un diagrama que ya existe, la frontera con
  `grafico-interactivo`.
- **Validación, debe activar**: «quiero ver cómo se desarma una placa base pieza a pieza en una página que se
  recorra con el scroll, tipo 3D». Es la petición que motiva la página interactiva.

| Pase | Modelo | Entrenamiento (13) | Validación (9) | Total |
|---|---|---|---|---|
| 1 | Sonnet | 13/13 | 8/9 | 21/22 |
| 2 | Haiku | 13/13 | 9/9 | 22/22 |
| 3 | Opus 5.5 | 13/13 | 8/9 | 21/22 |

**64/66.** Los dos fallos son la misma consulta, la nueva de validación: Sonnet y Opus la mandaron a
`modern-web-guidance` («lo que pide es una página web con scroll-driven animation», y Opus añadió que era
«el caso más dudoso, porque “se desarma pieza a pieza” también evoca despiece»). Haiku la mandó a `despiece`:
«el scroll 3D es solo el formato de la figura». El casi acierto nuevo de entrenamiento cayó en
`grafico-interactivo` en los tres pases.

**No se tocó la descripción**, por dos razones:

- El método ajusta la descripción solo con fallos del conjunto de **entrenamiento**. Este es de validación.
- La descripción va por 1.001 de 1.024 caracteres. Nombrar la página interactiva obliga a quitar algo.

Lectura del fallo: el formato del entregable («una página que se recorra con el scroll») le gana al verbo
(«se desarma pieza a pieza»). En Claude Code se pueden cargar las dos skills a la vez, y el método de
`despiece` no choca con la guía web; el clasificador de esta prueba, en cambio, obliga a elegir una sola. Es
un límite conocido de la 1.2.0: para la página interactiva, conviene pedir el despiece de forma explícita
(`/despiece …` o «despiezá…»). Si se repite en uso real, el siguiente paso es pasar una consulta de este
tipo a entrenamiento y hacerle sitio en la descripción.

## Calidad: caso 5, con y sin skill

Encargo: «Armame una página que se pueda abrir y recorrer con el scroll, tipo despiece en 3D, de un módulo de
memoria DDR5 SO-DIMM de portátil: qué piezas tiene y por dónde pasa un dato desde el conector hasta los chips.
Es para la sección de hardware de nuestra web, que lee gente que arma sus propias PC. Usá la marca de
marca.json.» Cada carpeta llevaba una copia de `assets/marca-ejemplo.json` como `marca.json`.

Cuatro subagentes limpios, Sonnet y Haiku, con y sin skill, con el mismo encargo y una carpeta propia. Los de
«con» tenían la orden de invocar `despiece` y seguirla entera; los de «sin», la prohibición de invocarla o
leer su carpeta. Ninguno podía preguntar al usuario ni tocar repositorios o nube.

Calificación con evidencia sobre los ficheros:

- `validar_modelo.py` sobre cada `modelo.json` y `grep` de `"lift"`.
- `ensamblar.py --interactivo` repetido sobre el modelo, en una carpeta aparte, para comprobar
  `"interactivo": true` y `oclusiones: []`.
- `grep` del nombre, el pie y el lema de la marca en el HTML.
- Las capturas de cada subagente, más capturas propias con `capturar-cdp.mjs` sin JavaScript (`SIN_JS=1`)
  donde el subagente no la hizo.

Como en las anteriores, una aserción se da por cumplida al subagente sin skill cuando la cumple en espíritu.

| Aserción | Con skill, Sonnet | Con skill, Haiku | Sin skill, Sonnet | Sin skill, Haiku |
|---|---|---|---|---|
| 1. Físico, pregunta foco, `geometria` válida | ✓ | ✓ | ✗ | ✗ |
| 2. `--interactivo` y la marca | ✓ | ✓ | ✓ (espíritu) | ✓ (espíritu) |
| 3. Se abre, se desarma, flujo, sin JS abierta | ✓ | ✓ | ✗ | ✗ |
| 4. Ninguna pieza tapada | ✓ | ✓ (corregida) | ✓ (espíritu) | ✓ (espíritu) |
| 5. Sin `lift` a mano | ✓ | ✓ | ✗ | ✗ |
| 6. Medidas citadas o aproximadas; supuestos | ✓ | ✓ | ✓ | ✓ |
| 7. Capturas en varios estados | ✓ | ✓ | ✓ (espíritu) | ✓ (espíritu) |
| 8. Tres frases y predicción | ✓ | ✓ | ✗ | ✗ |
| **Total** | **8/8** | **8/8** | **4/8** | **4/8** |

### Con skill, Sonnet: 8/8

- **Encuadre y modelo.** Tipo físico; pregunta foco «¿Por dónde pasa un dato que escribe el procesador, desde
  los contactos dorados hasta las celdas de un chip, y para qué sirve cada pieza que no lo toca?». Nivel 0
  «Un SO-DIMM DDR5 tiene seis piezas y el dato solo pasa por tres». 10 piezas, 6 raíces, 1 supuesto (los
  pasivos), `ok: true` sin avisos, 0 `lift`.
- **Medidas.** Tomó un módulo concreto como referencia (Kingston KVR56S46BS6-8, 69,6 × 30 mm, cuatro chips
  ×16 en una cara) para no inventar la otra cara; el chip, 7,5 × 14 mm, de la hoja de Micron. El rótulo de la
  placa dice «colocación de los componentes ilustrativa». 5 fuentes, con Wikipedia y Bus Pirate declaradas
  como secundarias.
- **Página.** `ensamblar.py --interactivo --marca marca.json`: salida 0, `oclusiones: []`. Nivel 2 dentro de
  un chip (bolas, E/S, ECC interno, bancos), con «(no es un corte real)» en el pie.
- **Revisión.** 18 capturas con `capturar-cdp.mjs`: portada abierta y armada, desmontaje, tres pasos del
  flujo, nivel 2, oscuro, móvil, sin JavaScript, la predicción respondida y el popover del supuesto.
- **Cierre.** Tres frases y una predicción con tres opciones: un contacto de órdenes sucio afecta a más
  chips que uno de datos, porque el bus de órdenes es común a los chips del subcanal.

### Con skill, Haiku: 8/8

- **Encuadre y modelo.** Tipo físico; pregunta foco «¿Qué piezas tiene un módulo SO-DIMM DDR5 y por dónde pasa
  el dato desde el conector hasta los chips?». Nivel 0 «En un SO-DIMM DDR5 el dato va del conector a los chips
  sin ningún chip intermedio». 9 piezas, 6 raíces, 2 supuestos, `ok: true` sin avisos, 0 `lift`.
- **Medidas.** «Placa de unos 30 × 67,6 mm (medida aproximada)», y la placa y las celdas, como supuesto. Cada
  fuente dice hasta dónde se leyó («solo resumen de búsqueda», «la ficha dio 404»).
- **Oclusión corregida.** La primera vez `ensamblar.py` salió con 1: el conector quedaba tapado por los chips
  del subcanal A y el PMIC en el paso 5 del desmontaje. Corrigió la geometría y la segunda salió con 0.
- **Revisión.** 14 capturas con `capturar-cdp.mjs`. La de la portada sin JavaScript la hizo el calificador:
  sale abierta.
- **Cierre.** Tres frases y una predicción con opciones: si se estropea el PMIC, los chips se quedan sin
  tensión y la DRAM pierde lo guardado.

### Sin skill, Sonnet: 4/8

- **Lo que hizo.** La página más vistosa de las cuatro: un visor 3D oscuro fijo y 16 tarjetas que pasan al
  lado. Diez pasos abren el módulo pieza a pieza, por las dos caras, y seis siguen un dato desde un contacto
  dorado hasta la bola del chip, con una barra de progreso. Lleva la marca de `marca.json` (nombre ×3, pie ×1,
  lema ×2) y la voz rioplatense. Las medidas reales salen de fichas (69,6 × 30 mm, 262 contactos, 5 V a 1,1 y
  1,8 V), y la página avisa de que «los componentes y el trazado interior son ilustrativos».
- **Revisión.** Los 16 pasos en el navegador integrado a 1440, 1024 y 390 px, en claro y oscuro. Corrigió
  rótulos que tapaban el módulo y un paso que no se veía. Avisó de que no pudo medir la fluidez real.
- **Lo que falla.** No hay modelo, ni tipo, ni pregunta foco. Sin JavaScript el visor queda vacío: el
  `<noscript>` solo avisa de que el texto se lee igual (captura del calificador). Las posiciones están
  escritas a mano. Hay una pregunta de predicción en un desplegable del último paso, pero ni la página ni la
  respuesta cierran con tres frases.

### Sin skill, Haiku: 4/8

- **Lo que hizo.** Una página propia con un modelo 3D en `<canvas>` que se separa capa a capa con el scroll y
  se gira arrastrando, siete piezas, un apartado del camino del dato con un punto que lo recorre y la marca de
  `marca.json` (nombre ×2, pie ×1, lema ×2). Dio el largo como 67,6 o 69,6 mm según la fuente, el dibujo como
  esquemático, y dijo qué no verificó.
- **Revisión.** En el navegador integrado a 800 y 375 px y con un simulador del DOM en Node.
- **Lo que falla.** No hay modelo, ni tipo, ni pregunta foco. Sin JavaScript la figura queda vacía: es un
  `<canvas>` y no hay `<noscript>` (captura del calificador). Las separaciones están escritas a mano en el
  JS. No cierra con tres frases ni predicción.

Sin skill, los dos modelos hacen una página interactiva que se recorre con el scroll y lleva la marca, y los
dos dicen qué es ilustrativo. Lo que no hacen es lo que pone la skill: el encuadre con pregunta foco, el modelo
validado, una figura que sin JavaScript sigue abierta, las alturas calculadas y comprobadas contra
oclusiones, y las puertas de comprensión. Con skill, Haiku cumple lo mismo que Sonnet.

## Qué cambió por las evals

- **`capturar-cdp.mjs`, capturas en paralelo.** El puerto de depuración era fijo (9333). Los dos subagentes
  con skill capturaron a la vez, y el segundo se quedó colgado hasta que cada uno pasó un `PUERTO` propio.
  Ahora, sin `PUERTO`, el navegador elige un puerto libre y el script lo lee de `DevToolsActivePort`, en su
  perfil temporal. Verificado con tres capturas simultáneas de estados distintos: cada una salió con su
  página.
- **Plantilla interactiva, salto inicial a un ancla.** Haiku vio una captura de `#flujo` que salía en otro
  sitio. Se reprodujo: con `scroll-behavior: smooth` activo desde el principio, el salto inicial al `#ancla`
  falló 1 de 8 veces en la demo, y 0 de 8 con movimiento reducido. Ahora el scroll suave se activa con una
  clase cuando la página ya cargó. Verificado: 14 de 14 cargas de `#flujo` en su sitio, y todas las anclas y
  parámetros (`?p`, `?paso`, `?abrir`) siguen respondiendo.
- Sin cambios en la descripción: ver «Activación».

## Observaciones

- **Una edición a mitad de una eval la contamina.** El arreglo del puerto se escribió mientras el subagente
  Haiku con skill seguía capturando: cuatro de sus capturas fallaron al cargar el script a medio escribir, y
  las repitió. Sonnet con skill releyó `references/interactivo.md` porque cambió durante su tarea (solo el
  encabezado del índice). Ninguna de las dos cosas cambia la calificación. Para la próxima: no tocar la skill
  hasta que terminen las evals.
- **La etiqueta de la relación activa puede caer sobre una pieza.** En el flujo en oscuro del subagente
  Haiku, «CA y DQ del subcanal A» queda encima de un chip y se lee peor, aunque lleva halo. Candidato a
  apartarla de las piezas en la siguiente versión.
- **Alzas altas cuando el conector va detrás.** En el modelo de Haiku, para no tapar el conector, el
  arranque elegido es de 208 px con el escalón mínimo (10 px): las piezas flotan juntas, muy por encima de la
  placa. Es válido (ninguna oclusión), pero se lee peor que el SSD. Candidato a revisar con más modelos.
- **La página sin skill de Sonnet es más cinematográfica** (visor oscuro, vuelta del módulo, 16 pasos) y le
  dedicó 40 minutos, frente a 18 del subagente con skill. La interactiva de la skill gana en rigor y en
  robustez (sin JavaScript, tema, oclusiones); la experiencia «más 3D» que pidió el autor queda para las
  fases 4 y 5 del [research](../docs/research-interactivo.md).
- **Los subagentes siguen leyendo la marca del entorno.** Los cuatro usaron `marca.json` como pedía el
  encargo, pero tres de ellos se preguntaron en la respuesta si debían aplicar la marca corporativa que el
  `CLAUDE.md` global de la máquina exige. No es defecto de la skill. Es el mismo recordatorio que en la
  1.1.1: las evals heredan las instrucciones globales del entorno donde se corren.
