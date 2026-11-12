# Resultados de evaluación — despiece 2.1.0 (explorador) — 2026-11-12

Evaluación de la 2.1.0, que añade el explorador con zoom semántico (`ensamblar.py --explorador`) para cualquier
tipo. Se corrió el caso nuevo, 8 (`explorador-auditoria`), y las 30 consultas de `trigger_queries.json`, cuatro
de ellas nuevas, en dos iteraciones de la descripción. Los casos 1 a 7 no se repitieron. Los resultados
anteriores están en [resultados-2026-11-12.md](resultados-2026-11-12.md).

Modelo principal de la sesión: Claude Opus 5.5. Calidad: Sonnet y Haiku, con y sin skill. Activación: Sonnet,
Haiku y Opus, un pase cada uno por iteración. Los transcripts no se guardan; aquí va el resumen con la evidencia
que se comprobó sobre los ficheros que dejó cada subagente.

## Activación

Por subagentes, como en las versiones anteriores. Cada uno recibe las 35 skills instaladas con su descripción y
las 30 consultas barajadas con otra semilla (11, 23 y 37), y elige la skill que invocaría primero o ninguna.

Consultas nuevas, para la frontera del explorador con `grafico-interactivo` y con las skills de diagramas:

- **Entrenamiento, debe activar**: «quiero navegar con zoom por cómo funciona un router por dentro: acercarme a
  una pieza y que se abra en sus partes, y alejarme para volver».
- **Entrenamiento, no debe activar**: «tengo este SVG de la arquitectura en el blog y quiero que se pueda hacer
  zoom y arrastrar, con puntos que se abran al hacer clic». Es de `grafico-interactivo`.
- **Validación, debe activar**: «armame algo para explorar por niveles cómo está organizada la ISO 27001,
  entrando en cada dominio con zoom».
- **Validación, no debe activar**: «hacé un mapa interactivo de la red de la oficina en el que se pueda hacer
  zoom sobre cada sede, con los iconos oficiales de Azure».

**Iteración 0**, con la descripción de la 2.0.1:

| Pase | Modelo | Entrenamiento (17) | Validación (13) | Total |
|---|---|---|---|---|
| 1 | Sonnet | 16/17 | 12/13 | 28/30 |
| 2 | Haiku | 17/17 | 12/13 | 29/30 |
| 3 | Opus 5.5 | 17/17 | 12/13 | 29/30 |

**86/90.** Sonnet mandó el router y la ISO 27001 a `grafico-interactivo` («navegación con zoom explorable»): la
descripción no decía que el despiece se pudiera recorrer con zoom. Haiku y Opus fallaron la consulta de la placa
base que se recorre con el scroll, igual que en la 2.0.0.

**Iteración 1.** Con el fallo de entrenamiento de Sonnet, la descripción dice ahora que la vista explotada «se
abre a demanda o con zoom en un explorador» y nombra «navegar con zoom por sus niveles» entre los disparadores.
Para no pasar de 1.024 caracteres, «el flujo o la red delegados a la skill de dibujo instalada» quedó en «el
flujo delegado a la skill de dibujo».

| Pase | Modelo | Entrenamiento (17) | Validación (13) | Total |
|---|---|---|---|---|
| 1 | Sonnet | 17/17 | 13/13 | 30/30 |
| 2 | Haiku | 17/17 | 13/13 | 30/30 |
| 3 | Opus 5.5 | 17/17 | 12/13 | 29/30 |

**89/90, validación 38/39 frente a 36/39: se queda la iteración 1.** Las cuatro consultas nuevas acertaron en
los tres pases. El único fallo es otra vez la placa base con scroll, que Opus manda a `modern-web-guidance`:
el formato del entregable le sigue ganando al verbo, como en la 1.2.0 y la 2.0.0.

## Calidad: caso 8, el explorador de la auditoría

Encargo: «Tengo el despiece de una auditoría ISO 27001 en despiece-iso/modelo.json. Quiero recorrerlo con
zoom: acercarme a una fase y que se abra, alejarme y volver, y poder pasarle a alguien un enlace que abra
directamente dentro de una pieza. Dejalo en despiece-iso/.» Cada carpeta llevaba
`assets/ejemplo-auditoria-iso27001.json` como `despiece-iso/modelo.json` (tipo proceso, cuatro niveles que se
abren: el todo, `etapa2`, `tecnologicos` y `c8-13`), con el hash anotado.

Cuatro subagentes limpios, sin poder preguntar y sin tocar ninguna nube. Calificación con el hash del modelo,
`validar_modelo.py`, el HTML (recursos externos y una `<template data-nivel>` por nivel) y la respuesta.

| Aserción | Con skill, Sonnet | Con skill, Haiku | Sin skill, Sonnet | Sin skill, Haiku |
|---|---|---|---|---|
| 1. Parte del modelo y no cambia sus piezas | ✓ | ✓ | ✓ | ✓ |
| 2. Pasa `validar_modelo.py` antes de generar | ✓ | ✓ | ✓ (sin tocar) | ✓ (sin tocar) |
| 3. `ensamblar.py --explorador`, sin `--interactivo` ni `geometria` | ✓ | ✓ | ✗ | ✗ |
| 4. Un solo HTML sin recursos externos, una lámina por nivel | ✓ (4 de 4) | ✓ (4 de 4) | ✗ | ✗ |
| 5. Revisa la página y dice qué comprobó | ✓ | ✓ | ✓ | ✓ |
| 6. Explica cómo se navega: acercar, alejar, + y − | ✓ | ✓ | ✓ | ✗ |
| 7. Enlace `#/<id>` a una pieza con hijas | ✓ | ✓ | ✓ (espíritu) | ✓ (espíritu) |
| 8. Tres frases y predicción en la respuesta | ✓ | ✓ | ✗ | ✗ |
| **Total** | **8/8** | **8/8** | **5/8** | **4/8** |

- **Con skill, los dos.** Explorador de 115 KB con las cuatro láminas, el modelo intacto y validado sin avisos,
  y capturas con `capturar-cdp.mjs`: el todo, un nivel en oscuro y el móvil. Haiku añadió el enlace profundo y
  la página sin JavaScript. Enlaces `#/c8-13` y `#/etapa2`. **Ninguno pudo comprobar el zoom con la rueda**: un
  solo evento `wheel` sintético no abría la pieza, y lo dijeron. Lo probaron con «+» y «−».
- **Sin skill, Sonnet.** Escribió su propio generador y una página de 33 KB con tarjetas HTML por nivel, sin
  vista explotada. Implementó la rueda, el historial y el enlace directo, y los probó en un navegador. El
  enlace tiene la forma `#c8-13`. Las tres frases y la predicción están en la página, pero no en la respuesta.
- **Sin skill, Haiku.** Una página de 33 KB con un solo SVG en la vista inicial. Se navega con clic, Esc y
  botones, **sin rueda ni pellizco**: el encargo pedía zoom. El enlace es una ruta,
  `#/etapa2/tecnologicos/c8-13`. Sin tres frases en la respuesta.

**Calidad total: 16/16 con skill frente a 9/16 sin ella.**

## Qué cambió por las evals

- **`references/explorador.md`, gotcha nuevo.** Un solo `wheel` sintético no abre un nivel: el zoom se
  acumula y hacen falta unos 6 eventos de `deltaY: -40`, o uno con `ctrlKey`. Hay que apuntar al rótulo de la
  pieza (`.fv-llamada`), porque en las vistas apiladas el centro de su caja cae sobre la pieza de encima. Va
  con un bucle listo para `capturar-cdp.mjs -`. Origen: los dos subagentes con skill.
- **`assets/plantilla-explorador.html`, fallo corregido.** Al preparar ese bucle salió un fallo real. Un gesto
  sobre el hueco entre dos letras del rótulo no abría nada, porque el texto SVG solo responde sobre los glifos.
  La pista decía «Acercá sobre una pieza con «+»». Ahora el respaldo por caja mira también los rótulos.
  - Verificado en 1240×900, 1240×1600, 1024×700 y 390×844.
  - Sin regresiones: rueda en 6 pasos para entrar y 5 para salir, Ctrl + rueda en 5, pellizco en 5, y el
    historial igual que antes.
- **Descripción**: la de la iteración 1 (ver «Activación»).

## Observaciones

- **Sin re-ejecución del caso 8 tras los arreglos.** El gotcha es de texto, y el fallo de la plantilla se
  verificó con el mismo bucle que se documenta.
- **Lo que la skill añade aquí es la geometría y las puertas.** Sin skill, Sonnet hizo un explorador que
  funciona, con rueda e historial, en una sola pasada. Lo que no tiene es la vista explotada de cada nivel ni
  las tres frases en la respuesta.
- **Los subagentes siguen heredando las instrucciones globales del entorno.** Haiku con skill y los dos sin
  skill aplicaron la marca de esas instrucciones, aunque el encargo no la pedía. Sonnet con skill la dejó sin
  marca. Con skill, la marca es explícita (`--marca`), y Haiku dijo cuál usó y cómo cambiarla.
