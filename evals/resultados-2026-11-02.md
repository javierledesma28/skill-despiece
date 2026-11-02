# Resultados de evaluación — despiece 1.1.0 → 1.1.1 — 2026-11-02

Primera ejecución de los **casos públicos** de `evals.json` y de las 20 consultas de `trigger_queries.json`,
reescritos en la 1.1.0 sin ningún detalle del entorno privado del autor. Los resultados de la 1.0, con los
casos privados, están en [resultados-2026-11-01.md](resultados-2026-11-01.md).

Modelo principal de la sesión: Claude Fable 5.1. Subagentes de calidad: Sonnet, más Haiku en el caso físico.
Activación: Sonnet, Haiku y el modelo principal, un pase cada uno. Los transcripts no se guardan; aquí va el
resumen con la evidencia que se comprobó a mano sobre los ficheros que dejó cada subagente.

## Activación

`eval_activacion.py` (del método `creando-skills`) no se pudo usar: `claude -p` seguía fallando con *OAuth
session expired*. Camino alternativo del método: 3 subagentes limpios, cada uno con el listado de las skills
instaladas y sus descripciones, clasifican las 20 consultas barajadas y eligen la skill que invocarían
primero (o ninguna).

| Pase | Modelo | Entrenamiento (12) | Validación (8) | Total |
|---|---|---|---|---|
| 1 | Sonnet | 12/12 | 8/8 | 20/20 |
| 2 | Haiku | 12/12 | 8/8 | 20/20 |
| 3 | Fable 5.1 | 12/12 | 8/8 | 20/20 |

**60/60**, sin iterar la descripción. Los casi aciertos cayeron en la skill vecina esperada en los tres
pases: diagrama ER y draw.io → diagramas editoriales (`diagram-design`); red estilo Learn → arquitectura
cloud con iconos oficiales; barras → gráficos de datos; deck → presentaciones; relevamiento → relevamiento;
SVG con zoom → gráfico interactivo; ticket → work items; «qué es un NSG en una frase» y «resumime en tres
líneas» → ninguna. Los «sí» sin la palabra despiece («qué partes tiene», «anatomía de», «explicámelo para
que lo entienda», «desmenuzame», «desarmámelo pieza por pieza») activaron en los tres.

## Calidad: 4 casos, con y sin skill

Cada caso se ejecutó en dos subagentes Sonnet limpios con el mismo encargo y una carpeta de salida propia en
el scratchpad de la sesión: uno con la orden de invocar `despiece` y seguirla entera, y otro con la
prohibición de invocarla o leerla (podía usar cualquier otra skill). Ninguno podía preguntar al usuario ni
tocar repositorios o recursos de nube. El caso físico se repitió con **Haiku** en los dos papeles.

Las aserciones se calificaron leyendo la respuesta y comprobando los ficheros: `validar_modelo.py` sobre
cada `modelo.json`; conteo de piezas destacadas en los SVG de `explosionado.py` (`fill="#e6f4f3"`, que solo
lleva la destacada); `grep` del pie y el lema de `assets/marca-ejemplo.json` en los `index.html`; figuras
incrustadas y huecos `class="pendiente"`. Como en la 1.0, una aserción se da por cumplida al subagente sin
skill cuando la cumple en espíritu (por ejemplo, separa lo verificado de lo no verificado en prosa aunque no
exista un modelo donde marcarlo).

| Caso | Con skill (Sonnet) | Sin skill (Sonnet) |
|---|---|---|
| 1 sistema (una petición que se salta la WAF de una Application Gateway) | **8/8** | 6/8 |
| 2 físico (Raspberry Pi 5, para el taller) | **7/7** | 2/7 |
| 3 proceso (activación de un rol por PIM) | **6/6** | 4/6 |
| 4 idea (idempotencia en una API de pagos, sin marca) | **5/5** | 4/5 |
| **Total** | **26/26** | **16/26** |

| Caso 2 con Haiku | Con skill | Sin skill |
|---|---|---|
| físico (Raspberry Pi 5) | **7/7** | 2/7 |

Sin skill, Sonnet explica bien, cita fuentes oficiales, separa lo verificado de lo que infiere y en tres de los
cuatro casos cierra con alguna pregunta, pero no modela por niveles, no marca supuestos pieza a pieza y no deriva
la figura de un guion con las piezas exactas: las aserciones de modelo y de niveles fallaron en los cuatro casos. Con skill, las aserciones pasaron todas en los casos
1, 2 y 4 y también en el 3, y Haiku siguió el método entero.

### Caso 1 · sistema (WAF de una Application Gateway, marca de ejemplo)

Con skill: encuadre inferido y declarado (lector: soporte de primer nivel; pregunta foco: por qué una
petición llega al portal sin pasar por la WAF); tipo sistema; modelo de 12 piezas, 5 raíces, flujo de 5,
`ok: true` sin avisos; 0 supuestos y 6 fuentes, todas páginas de Microsoft Learn; nivel 0 «La WAF solo
vigila la puerta de la gateway, y el portal puede tener otras puertas»; tres figuras con `skill:
diagram-design`, dibujadas por un script propio que aplica las reglas de esa skill con las piezas exactas
del modelo; página ensamblada con `--marca …/assets/marca-ejemplo.json` (el pie «Acme Research ·
Documentación técnica interna» aparece 1 vez y el lema «ENTENDER ANTES DE TOCAR» 2 veces en el HTML); tres
frases y predicción con respuesta; ninguna operación de nube. **8/8.**

El subagente encontró además el defecto de `ensamblar.py` que motiva la 1.1.1 (ver abajo) y lo parcheó en
su copia de la página para poder entregarla legible en oscuro.

Sin skill: explicación sólida y bien documentada: 11 páginas de Microsoft Learn, lector (soporte) y pregunta foco tomados del encargo, tabla de piezas con función y fuente, «lo que no pude confirmar» separado, dos figuras (arquitectura de las puertas y flujo de la gateway) hechas con un script propio según `diagram-design`, marca de ejemplo aplicada a mano (el pie aparece 1 vez y el lema 2 en el HTML), tres frases y predicción con la respuesta plegada, ninguna operación de nube. Pero sin `modelo.json` (aserción 2) ni niveles de 3–7 piezas (aserción 4): ordena ocho caminos en dos familias. **6/8.** Un matiz que pesa: el propio subagente declaró que tomó la estructura (encuadre, piezas con fuente, 3 a 7 por nivel, tres frases y predicción) de la **descripción** de `despiece` que ve en el listado de skills, aunque no la invocó ni leyó su carpeta. Este baseline no es «sin skill» del todo, sino «sin el cuerpo de la skill».

### Caso 2 · físico (Raspberry Pi 5)

Con skill (Sonnet): tipo físico, pregunta foco «qué compran y por qué calienta más que la 4»; 16 piezas, 6
raíces con `orden_montaje` 1–6, `ok: true` sin avisos; 0 supuestos y 7 fuentes de raspberrypi.com (hoja de
producto, datasheet del RP1, documentación de hardware, el artículo oficial sobre refrigeración); tres
vistas explotadas con `explosionado.py` (`--destacar cerebro`, `--subconjunto cerebro --destacar cpu`,
`--subconjunto ventilador --destacar cabecera`), **una destacada por figura** (1 `fill="#e6f4f3"` en cada
SVG), `--marca ninguna`, página capturada en claro y oscuro; tres frases y predicción. La premisa del
encargo («calienta más que la 4») la matizó con la fuente oficial: a igual carga la Pi 5 se calienta menos;
lo que sube es el pico (12 W frente a 8 W). **7/7.**

Con skill (Haiku): `ok: true` con 1 aviso (7 piezas nuevas en la figura 1, justificado en la respuesta);
tipo físico; 12 piezas, 7 raíces con `orden_montaje` 1–7; 1 supuesto (`reg`, los reguladores) declarado en la
respuesta; dos vistas explotadas con `explosionado.py` (`--destacar soc`; `--subconjunto soc --destacar
cpu`), una destacada por figura (comprobado en los 2 SVG); `--marca ninguna`; tres frases y predicción con
respuesta. Una desviación de proceso sin efecto en las aserciones: abrió el navegador integrado para revisar
la página en lugar de capturarla. **7/7.**

Sin skill (Sonnet): muy buena explicación, con la hoja de producto y el datasheet del RP1 extraídos con
`pdftotext`, tabla comparativa Pi 4 / Pi 5, sección «Lo que no pude comprobar» y cuenta propia marcada como
tal; diagrama de bloques funcional con dos acentos y gráfica de temperaturas, dibujados con un script propio
según `diagram-design`; cierra con una pregunta para el taller con respuesta, pero sin las tres frases. No
clasifica el objeto, no hay modelo ni `orden_montaje`, no usa `explosionado.py`. Pasan 3 (lo no verificado
va dicho) y 4 (ninguna referencia inventada). **2/7.**

Sin skill (Haiku): tabla de piezas con fuentes y un diagrama de bloques SVG hecho a mano; señala en prosa lo
que no verificó; sin modelo, sin orden de montaje, sin vista explotada, sin tres frases ni predicción. Pasan
3 y 4. **2/7.**

### Caso 3 · proceso (activación de un rol por PIM)

Con skill: tipo proceso con eje temporal; pregunta foco «¿en qué momento un rol que solo podés pedir pasa a ser un permiso que funciona, y qué cambia si exige aprobación?», lector administrador que ya usa PIM y mezcla los términos; flujo de 6 pasos en orden (elegible → solicitud → aprobación → activa → efectivo → fin); 16 piezas, 6 raíces, `ok: true` sin avisos; 0 supuestos y 7 páginas de Microsoft Learn como únicas fuentes; 4 malentendidos, dos de ellos sobre elegible frente a activo («elegible es un permiso que ya tengo, solo que en espera», «la aprobación es un tercer estado entre elegible y activo»); nivel 0 «Elegible y activo son dos estados de una asignación, y la aprobación es solo un peaje entre ambos»; cuatro figuras `skill: diagram-design` (calles con 4 carriles y 6 piezas, anidada, flujo con decisión, flujo con ramas) dibujadas por un script propio desde las piezas exactas del modelo (6, 4, 3 y 3 nuevas por figura), con un comprobador geométrico propio y `self_check.py` OK; 4 figuras incrustadas, 0 pendientes, SVG sin `width`/`height`; `--marca ninguna`; tres frases y predicción concreta (el aprobador responde a las 10:30 del día siguiente: la solicitud caducó a las 24 h y sigue siendo solo elegible). **6/6.**

Sin skill: explicación sólida con 8 páginas de Learn; dos figuras hechas con un script propio según
`diagram-design` (calles Tú / PIM / Aprobador / Recurso y una máquina de estados), tabla que deshace la
confusión elegible / activo / aprobación, línea de tiempo en texto y cuatro casos concretos de «qué pasa
si…» con su respuesta. Sin modelo: el flujo no sale de un `modelo.json` (aserción 1) y las figuras no
derivan de un guion con las piezas exactas (aserción 5). Las piezas son pasos y los actores van como calles
(2), cita Learn (3), incluye el malentendido elegible/activo (4) y los casos concretos valen como predicción
(6). **4/6.**

### Caso 4 · idea (idempotencia en una API de pagos, sin marca)

Con skill: tipo idea; el nivel 0 arranca por la historia de un cobro de 50 € cuya respuesta se pierde,
contada con y sin clave (figura `n0-historia.svg`), y la definición queda para el final; título «Una clave
de idempotencia hace seguro reintentar un cobro cuyo resultado no conocés»; 13 piezas, 5 raíces, flujo de 5,
`ok: true` sin avisos; 6 fuentes públicas (RFC 9110 §9.2.2, el borrador `draft-ietf-httpapi-idempotency-key-
header-08`, presentado como borrador, Stripe y Adyen) y 2 piezas `supuesto: true` (el criterio de cuándo
exigir la clave es síntesis propia, y la respuesta lo dice); cuatro figuras `skill: diagram-design` dibujadas
a mano según esa skill, con `self_check.py` OK; `--marca ninguna` y 0 coincidencias de «Acme», del pie o del
lema en el HTML; 0 huecos pendientes; sin metáfora (lector del dominio); tres frases y predicción con
respuesta en dos partes. **5/5.**

Sin skill: post con cuatro figuras (dos secuencias con y sin clave, el flujo del servidor y el árbol de
decisión), tabla «qué hacer ante cada respuesta», tres trampas con el «criterio propio» marcado, pregunta
de predicción con la respuesta en un `<details>`; paleta neutra, sin marca (0 coincidencias de los tokens
corporativos del entorno). Pero **empieza por la definición** («Idempotente quiere decir…»), que es justo lo
que la aserción 1 prohíbe. Pasan 2, 3, 4 (sin metáfora) y 5. **4/5.**

## Qué cambió por las evals

- **`ensamblar.py`, pie de figura ilegible en oscuro** (→ 1.1.1). Desde la 1.0.1 las figuras van sobre una
  lámina blanca fija en los dos temas, pero `figcaption` y el hueco `.pendiente` seguían usando `--gris`,
  que en oscuro vale `#9fb0c0`: gris claro sobre blanco. Ahora llevan colores fijos para lámina blanca
  (`#5c6b7a` para el texto, `#dde3ea` para el borde del hueco). Verificado capturando la demo con
  `data-theme="dark"`. Lo detectó el subagente del caso 1.
- Sin cambios en `SKILL.md` ni en la descripción: la activación fue 60/60 a la primera.

## Observaciones

- **La descripción de la skill ya cambia al baseline.** El subagente «sin skill» del caso 1 declaró que copió la
  estructura (encuadre, piezas con fuente, 3 a 7, tres frases y predicción) de la descripción de `despiece` que
  aparece en el listado de skills disponibles, sin invocarla ni leer su carpeta; en los casos 3 y 4 el cierre con
  pregunta apunta a lo mismo. La diferencia que miden estas evals es, en rigor, la del **cuerpo** de la skill
  (modelo validado, niveles, guion, scripts) frente a la descripción sola. Para medir «sin skill» de verdad habría
  que desinstalarla de la máquina de pruebas, no solo prohibir invocarla.

- **Los subagentes sin skill aplican la marca del entorno aunque el encargo no la pida.** En los casos 2 y
  3 sin skill (Sonnet y Haiku), las figuras salieron con los colores, la fuente y el pie de la organización
  del autor, porque el `CLAUDE.md` global de la máquina lo ordena para «todo artefacto presentable». Los
  subagentes con skill usaron la marca que pedía cada encargo (`marca-ejemplo.json` en el 1, `ninguna` en
  el 2 y el 4). No es defecto de la skill: es evidencia de que la regla «la marca es del proyecto, no de la
  skill» funciona, y un recordatorio de que las evals «sin skill» heredan las instrucciones globales del
  entorno donde se corren.
- **Con skill, el dibujo delegado lo hace un script propio que aplica las reglas de la skill de dibujo**, no
  la skill invocada como tal, en los tres casos no físicos. Igual que en la 1.0: cumple el guion y es un
  camino previsto (`skill: propio` desde la 1.1.0), pero los modelos declaran `skill: diagram-design` cuando
  en rigor es `propio` siguiendo a `diagram-design`. Candidato a aclarar en `references/guion-visual.md`.
- **Haiku ejecuta el método entero** (primer caso con Haiku como ejecutor): modelo válido, vistas explotadas
  correctas, puertas de comprensión. Su única desviación fue de proceso (navegador en vez de captura).
- **Lo que la página todavía no es**: las evals miden método y rigor, no la experiencia de leer la página.
  La salida sigue siendo texto por niveles con figuras estáticas incrustadas; una vista explotada que se
  abre, flujos que se recorren y niveles en los que se entra con el scroll quedan para la siguiente
  iteración (hoja de ruta del README).
