# Resultados de evaluación — despiece 1.0 — 2026-11-01

> **Nota de la versión 1.1.0 (2026-11-02).** Estas evals se corrieron sobre la 1.0, con casos y fuentes del
> entorno privado del autor: un repo de conocimiento corporativo, su infraestructura leída en solo lectura y
> su marca. Al publicar la skill, los casos de `evals.json` y las consultas de `trigger_queries.json` se
> reescribieron con objetos públicos (una WAF genérica, una Raspberry Pi 5, la activación por PIM, la
> idempotencia en una API de pagos) y **están pendientes de correr**. Lo de abajo son los resultados de la
> 1.0 con los detalles privados quitados; las cifras no cambian.

Modelo principal de la sesión: Claude Fable 5.1. Subagentes de calidad: Sonnet. Activación: Sonnet, Haiku
y el modelo principal (un pase cada uno). Los transcripts no se guardan; aquí va el resumen con la evidencia
que se comprobó a mano.

## Activación

`eval_activacion.py` (del método `creando-skills`) no se pudo usar: `claude -p` fallaba con *OAuth session
expired*. Camino alternativo del método: 3 subagentes limpios, cada uno con el listado de las 13 skills
instaladas relevantes y sus descripciones, clasifican las 20 consultas de `trigger_queries.json` barajadas y
eligen la skill que invocarían primero.

| Pase | Modelo | Entrenamiento (12) | Validación (8) | Total |
|---|---|---|---|---|
| 1 | Sonnet | 12/12 | 8/8 | 20/20 |
| 2 | Haiku | 12/12 | 8/8 | 20/20 |
| 3 | Fable 5.1 | 12/12 | 8/8 | 20/20 |

**60/60.** Los casi aciertos se resolvieron hacia la skill vecina en los tres pases: ER → diagramas
editoriales, red estilo Learn → arquitectura cloud con iconos oficiales, barras → gráficos de datos, deck →
presentaciones, relevamiento → relevamiento, SVG interactivo → gráfico interactivo, draw.io → diagramas
editoriales, ticket → work items; «qué es un NSG en una frase» y «resumime en tres líneas» → ninguna. Y los
«sí» sin la palabra despiece («qué partes tiene», «anatomía de», «explicámelo para que lo entienda»,
«desmenuzame») activaron en los tres. Sin iteraciones sobre la descripción (no hubo fallos de
entrenamiento).

## Calidad: 4 casos, con y sin skill

Cada caso se ejecutó en dos subagentes Sonnet limpios con el mismo encargo y la misma carpeta de salida: uno
con la orden de invocar `despiece` y seguirla entera, y otro con la prohibición de invocarla o leerla (podía
usar cualquier otra skill). Ninguno podía preguntar al usuario. Las aserciones se calificaron leyendo la
respuesta y comprobando los ficheros: `validar_modelo.py` sobre cada `modelo.json`, conteo de piezas
destacadas en los SVG, figuras incrustadas y marca en el `index.html`, `grep` del nombre de la organización.

| Caso | Con skill | Sin skill |
|---|---|---|
| 1 sistema (WAF de una Application Gateway) | **8/8** | 4/8 |
| 2 físico (un firewall de sobremesa) | **7/7** | 3/7 |
| 3 proceso (activación por PIM) | **6/6** | 5/6 |
| 4 idea (proyecto personal, sin marca) | **5/5** | 3/5 |
| **Total** | **26/26** | **15/26** |

Sin skill, Sonnet explica bien y cita fuentes, pero no modela por niveles, no marca supuestos pieza a pieza
y nunca cierra con las puertas de comprensión (tres frases y predicción): esas aserciones fallaron en los
cuatro casos. Con skill, las 26 pasaron, con dos desviaciones declaradas por los propios subagentes que no
rompen aserción alguna (ver casos 1 y 4).

### Caso 1 · sistema (WAF de una Application Gateway, con el repo de conocimiento del equipo)

Con skill: encuadre inferido y declarado (lector soporte, pregunta foco, tipo sistema, frontera y fuera);
modelo de 12 piezas, 5 raíces, flujo de 5, `ok: true` sin avisos; las 6 fuentes son documentos del repo
(hallazgo, evidencias del incidente, operativa) más una lectura propia de solo lectura con el contexto
explícito; nivel 0 «Una petición se salta la WAF por una puerta sin gateway o por un pase dentro de la
WAF»; tres figuras de flujo con las piezas exactas; página con la marca del proyecto y 0 figuras pendientes;
tres frases y predicción con respuesta; `git status` intacto y ninguna escritura en la nube. Declaró además
dos simplificaciones de la figura de la WAF y que en el nivel 2 tres carriles comparten el acento
(desviación consciente de «una destacada»).

Sin skill: explicación correcta y bien documentada (lecturas en vivo, tres figuras con marca, nota de
confidencialidad), pero sin modelo, sin piezas con fuente individual, sin niveles ni cierre de comprensión.
Fallan las aserciones 2, 3, 4 y 7.

### Caso 2 · físico (un firewall de sobremesa, modelo concreto del fabricante)

Con skill: tipo físico, pregunta foco ligada a la renovación; 6 raíces con `orden_montaje` 1–6 y 15 hijas;
2 piezas `supuesto` (disco y RAM: la guía documenta capacidad, no función) y dichas en la respuesta; 19 con
fuente (guía de hardware y fichas públicas del fabricante); cinco vistas explotadas con `explosionado.py`,
**una destacada por figura** (comprobado en los 5 SVG), incrustadas; tres frases y predicción. Sin inventar
referencias: lo que no verificó (ventiladores, núcleos, si el M.2 es SSD) lo declaró como no confirmado.

Sin skill: muy buena separación «dato / explicación mía» y fuentes oficiales, pero sin modelo ni orden de
montaje, figura propia con dos focales (procesador y fuente) y sin tres frases ni predicción. Fallan 1, 2,
5, 6 y 7.

Ambos subagentes leyeron, en solo lectura, la consola del fabricante y vieron que el modelo en producción
no era el del encargo: el encargo era hipotético, pero muestra que la regla «nada se explica de memoria»
lleva a contrastar con la realidad.

### Caso 3 · proceso (activación por PIM)

Con skill: tipo proceso, flujo de 6 pasos (elegible → política → solicitud → aprobación → activa →
efectivo); piezas que son pasos o estados y actores como calles; 5 páginas de Learn y el repo como fuentes;
6 malentendidos, dos de ellos sobre elegible/activo; tres figuras (calles, plazo de 24 h, cachés) con las
piezas exactas, revisadas en claro y oscuro; predicción concreta (aprobador que responde a las 40 h).
Dibujó las figuras con un script propio siguiendo las reglas de la skill de diagramas editoriales, no
copiando su ejemplo de calles (que usa diagonales contra su propia regla).

Sin skill: diagrama de calles, Learn y repo citados, tabla de cuatro conceptos que deshace la confusión.
Falta la pregunta de predicción (aserción 6).

### Caso 4 · idea (proyecto personal del autor, sin marca)

Sin skill: fuentes solo del proyecto, cero coincidencias del nombre de la organización (comprobado con
`grep`), tokens del propio proyecto, página con línea de tiempo del storyboard real. Falla la metáfora («son
el reloj de donde cuelgan») porque no anota qué parte no vale, y falta el cierre de tres frases y predicción
(aserciones 4 y 5).

Con skill: tipo idea, pregunta foco que reúne «cómo encaja» y «cuándo conviene»; nivel 0 afirmativo («Las
palabras de la voz son la regla de la que cuelgan los overlays») con el ejemplo real del clip de 10 s y sus
instantes en la frontera; 12 piezas, 6 raíces, 0 supuestos, con las 6 fuentes en documentos del propio
proyecto; `--marca ninguna` y `grep` del nombre de la organización sin coincidencias en json, html, svg, py
ni png; tres figuras (línea de tiempo, zoom del ancla, árbol del criterio) con el perfil por defecto de la
skill de dibujo; tres frases y predicción con tres subcasos. La metáfora («una regla con una marca por
palabra») cabe en una frase y su límite está como pieza propia («Límites: la precisión de la regla», 100–400
ms), no como anotación explícita de «qué parte no vale»: se da por cumplida la aserción 4 con esa salvedad.

## Qué cambió por las evals

Dos defectos de los scripts salieron en la revisión visual de las páginas de los casos 2 y 3, y se
corrigieron antes del commit de la 1.0:

- **Contraste en tema oscuro** (`ensamblar.py`): los títulos usaban el primario de la marca también sobre
  fondo oscuro, y con `--marca ninguna` (primario `#1f2933`) habrían sido invisibles. Ahora hay tokens de
  texto `--pt`/`--st` que en oscuro se aclaran mezclando con blanco (`aclarar()`); los fondos y bordes
  siguen con `--p`/`--s`. Comprobado en las páginas de los casos 2 y 3 con `data-theme="dark"`.
- **Funciones cortadas en la lista de la vista explotada** (`explosionado.py`): se recortaban a 72
  caracteres con «…». Ahora se envuelven en dos líneas de 72 (`envolver()`), con recorte solo si sobra.

Sin cambios en `SKILL.md` ni en la descripción.

## Observaciones para futuras versiones

- Los subagentes con skill tienden a dibujar las figuras delegadas con un script propio que aplica las
  reglas de la skill de diagramas en vez de invocarla: el resultado cumplió el guion, y desde la 1.1.0 es un
  camino previsto (`skill: propio`), pero conviene vigilarlo si alguna vez una figura se desvía del modelo.
- ~~La vista explotada tiene fondo blanco fijo: en la página oscura se ve como una lámina clara.~~ Desde la
  1.0.1 **todas** las figuras van sobre lámina blanca en los dos temas (ver abajo): es la regla, no la
  excepción.
- Un caso con Haiku como ejecutor (no solo como clasificador) queda por correr.

## Addendum 1.0.1 · primer uso real (2026-11-01, un túnel S2S entre una oficina y Azure)

Despiece tipo sistema, 14 piezas (5 raíces, 1 supuesto), 3 figuras delegadas a subagentes (una de
arquitectura cloud con iconos oficiales, dos de diagramas editoriales), página con la marca del proyecto.

Qué funcionó: el validador pasó a la primera (3 avisos de longitud, corregidos); los tres dibujantes
respetaron el guion (piezas exactas, una destacada, título afirmativo dentro, `viewBox` sin
`width`/`height`); la lectura en vivo de la configuración, en solo lectura, destapó dos hechos que el repo
de conocimiento no tenía (uno de los dos túneles caído y el tráfico real del otro) y una afirmación del repo
probablemente falsa sobre qué clientes llegaban por ese túnel, que acabó como pregunta de predicción.

Defecto encontrado y corregido: el contenedor `<figure>` usaba `--suave`, casi negro en oscuro; una figura
`layer stack` transparente y con tinta oscura perdía título y cabeceras. Arreglo en `ensamblar.py` (fondo
blanco fijo), verificado con la página capturada con `data-theme="dark"`. De paso: Edge headless sigue el
tema del sistema, así que las capturas «clara» y «oscura» salían iguales; anotado en el paso 6 de
`SKILL.md`.
