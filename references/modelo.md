# El modelo (`modelo.json`)

Leer la primera vez que se escriba un modelo. Es la única fuente de verdad del despiece: las figuras y la
página salen de él, y `validar_modelo.py` lo comprueba antes de dibujar. Ejemplos completos y válidos en
`assets/ejemplo-*.json`, uno por clase de caso (un SSD, una red, una historia, una auditoría…).

## Contenido

1. Campos, y los de cada pieza
2. Los dos ejes: dependencia y pertenencia
3. Rol → silueta
4. Reglas que impone el validador
5. Convenciones

## Campos

| Campo | Obligatorio | Qué es |
|---|---|---|
| `objeto` | sí | Nombre de lo que se despieza, como título de la página |
| `tipo` | sí | `fisico`, `proceso`, `sistema` o `idea` |
| `pregunta_foco` | sí | La pregunta que el lector quiere responder; termina en `?` |
| `lector` | sí | Quién lee y qué sabe («técnico de sistemas que opera la gateway pero no la diseñó») |
| `profundidad` | no (2) | Niveles por debajo del 0: de 1 a 4. Más de 2 solo por la rama que responde a la pregunta foco |
| `eje` | no | Qué ordena el campo `orden` de las piezas, en pocas palabras: va en el subtítulo de la vista explotada («el orden de montaje», «la cronología, de lo más antiguo a lo más reciente», «la profundidad, de lo más hondo a la superficie»). Si falta, uno según el tipo |
| `nivel0.titulo` | sí | Afirmación sobre el todo (ver abajo) |
| `nivel0.frontera` | sí | Dónde empieza y termina el objeto |
| `nivel0.fuera` | no | Lista de lo que se deja fuera a propósito |
| `fuentes[]` | no | `{id, descripcion, url?}`; las piezas las citan por `id` |
| `piezas[]` | sí | Ver tabla siguiente |
| `relaciones[]` | no | `{de, a, tipo, etiqueta?}`; tipos: `flujo`, `contiene`, `depende`, `controla`, `dato`, `energia`, `causa` |
| `flujo[]` | proceso y sistema | Ids en el orden en que la petición, el dato o el paso ocurren; ≥ 3 |
| `malentendidos[]` | no (aviso) | Lo que el lector suele creer y es falso, con la corrección |
| `figuras[]` | no (aviso) | `{nivel, titulo, tipo_visual, skill, piezas[], fichero?, destacada?}`; `destacada` es una de sus `piezas` |
| `feynman[]` | sí | Exactamente 3 frases que un no experto entendería |
| `prediccion` | sí | `{pregunta, respuesta, opciones?, correcta?}`: una situación concreta y qué pasaría; `opciones` son 2–4 respuestas cortas y `correcta`, el índice de la buena desde 0 |
| `flujo_entrada` | no | Lo que entra desde fuera de la frontera al primer paso del flujo (mejor uno de `nivel0.fuera`) |
| `geometria` | físico, para `--interactivo` | Placa, posición y alto de cada raíz, y capas de los subconjuntos: ver `references/interactivo.md` |

### Cada pieza

| Campo | Obligatorio | Qué es |
|---|---|---|
| `id` | sí | Corto, sin espacios, único (`waf-custom`) |
| `nombre` | sí | Como se ve en la figura; ≤ 40 caracteres |
| `padre` | sí (`null` en el nivel 1) | Id de la pieza que la contiene |
| `funcion` | sí | Una línea, verbo + complemento: qué hace y por qué importa (≤ 125: la figura muestra dos líneas y recorta el resto) |
| `fuente` | sí, o `supuesto` | Id de `fuentes[]` o texto libre («Microsoft Learn: WAF custom rules») |
| `supuesto` | — | `true` cuando no hay fuente: se muestra como «▲ supuesto» en la página |
| `orden` | físico, en raíces | Entero, único entre hermanas: qué tiene que existir antes. 1 queda abajo en la figura. Es el montaje en un aparato, el despliegue en un sistema, la cronología en una historia, la profundidad en un terreno. `orden_montaje` es su nombre antiguo y sigue valiendo |
| `rol` | no (aviso fuera de lo físico) | El papel de la pieza, sin vocabulario del dominio; elige su silueta en la vista explotada (tabla de abajo) |
| `eje` | no | En una pieza con hijas: qué ordena el `orden` de sus hijas, para el subtítulo de su figura. Sin él, uno genérico según el tipo («el orden de montaje», «el orden de los pasos»), no el del modelo: lo que ordena las raíces rara vez ordena a las hijas. Si las hijas no traen `orden` ni están en el `flujo`, la figura no afirma ningún orden |
| `forma` | no | La silueta exacta, si el rol no basta: `placa`, `chip`, `conector`, `modulo`, `carcasa`, `disipador`, `cable` o `capa`. Gana a `rol` |
| `cantidad` | no | Si hay varias iguales («×4») |

### Los dos ejes: dependencia y pertenencia

Todo despiece se arma con dos relaciones, y nada más:

- **Dependencia** (`orden`): qué tiene que existir antes de qué. Ordena las piezas de un mismo nivel de
  abajo arriba.
- **Pertenencia** (`padre`): qué está dentro de qué. Es lo que hace que una pieza se abra en su propia
  figura (el «+»).

El resto es vocabulario del dominio. La skill no sabe de hardware, de redes ni de historia: lo que cambia de
un caso a otro es qué significa el eje, y eso lo dice `eje`.

| Caso | `orden` es… | `padre` es… |
|---|---|---|
| Un SSD | el montaje | la NAND contiene celdas y bloques |
| Una red en la nube | el despliegue | la red contiene subredes, y las subredes, interfaces |
| La historia de un país | la cronología | un período contiene décadas, y una década, hechos |
| Una auditoría | las fases | un dominio contiene controles, y un control, evidencias |
| Un terreno | la profundidad | un estrato contiene sus capas |
| Un sentido del cuerpo | la cadena de señal | la corteza contiene sus áreas |

### Rol → silueta

`forma` gana a `rol`; `rol` gana al nombre, que solo se mira en lo físico («pcb», «conector»,
«disipador»…). Sin nada de eso, una raíz es un `modulo` y una hija, una `capa`.

| `rol` | Significa | Silueta |
|---|---|---|
| `base` | Sobre lo que se apoya el resto (una por nivel) | `placa` |
| `etapa`, `capa` | Período, fase, estrato, dominio | `capa` |
| `componente` | Unidad activa con identidad propia | `chip` |
| `interfaz` | Punto de contacto, entrada o salida | `conector` |
| `enlace` | Relación entre dos partes (peering, parentesco, causa) | `cable` |
| `contenedor`, `limite` | Lo que encierra o restringe (un grupo de seguridad, un marco legal, una membrana) | `carcasa` |
| `regulador` | Lo que disipa, controla o compensa | `disipador` |
| `bloque` | Genérico, cuando no hay nada mejor | `modulo` |

## Reglas que impone el validador

- **Títulos afirmativos**: ≥ 4 palabras, sin «:» final, sin «Qué es…», «Introducción…», «Visión general».
  Un título dice lo que la figura demuestra: «La WAF solo inspecciona lo que entra por la gateway», no
  «Arquitectura de la gateway».
- **3–7 piezas por nivel.** Más de 7 raíces o más de 7 hijos es error: agrupar en subconjuntos. Un padre
  con un solo hijo es error: o se funden o falta una pieza.
- **≤ 6 piezas nuevas por figura** (aviso; error a partir de 10). Las ya mostradas en una figura anterior
  no cuentan.
- **Ninguna pieza sin fuente ni `supuesto: true`.** Es la regla que evita explicar de memoria.
- **`orden` único entre hermanas**, obligatorio en las raíces del tipo físico. Si una pieza trae `orden` y
  `orden_montaje` distintos, es error: son el mismo campo.
- **`rol` y `forma`** de las tablas de arriba. Fuera del tipo físico, una raíz sin ninguno de los dos da
  aviso: la vista explotada la dibujaría como bloque genérico.
- **`feynman` son 3 frases**, cada una de una línea y media como mucho. Si no cabe, no está entendido.
- **Con `geometria`**: solo en tipo físico; una entrada por raíz, una sola `placa` (la primera en
  `orden`), rangos `[desde, hasta]` crecientes, `unidades` = `cantidad`, piezas que no se interpenetran.
  Detalle en `references/interactivo.md`.
- **`prediccion.pregunta`** plantea una situación concreta («dos SSD de 1 TB, uno con DRAM y otro sin…»),
  no una definición («¿qué es la DRAM?»).

## Convenciones

- Carpeta de trabajo: la que indique el usuario; si no, `despiece-<objeto>/` donde se esté trabajando.
  Dentro: `modelo.json`, `figuras/`, `index.html`.
- Los `fichero` de las figuras son rutas relativas a esa carpeta (`figuras/n1-flujo.svg`): así
  `ensamblar.py --figuras <carpeta>` los encuentra.
- Las fuentes de un ámbito corporativo citan el documento del repo de conocimiento por su ruta relativa
  (`docs/red-y-conectividad.md`) y, si se leyó la configuración real, el recurso y la fecha.
- Cada ámbito (una empresa, un cliente, un proyecto personal) tiene sus fuentes y su marca: no se mezclan.
  Fuera de un proyecto con marca propia, la página va con `--marca ninguna`.
- En `figuras[].skill` va `explosionado` cuando la figura sale de `explosionado.py`, en cualquier tipo, y
  `propio` cuando se dibuja con un script hecho para ese despiece, sin skill de dibujo instalada.
