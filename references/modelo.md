# El modelo (`modelo.json`)

Leer la primera vez que se escriba un modelo. Es la única fuente de verdad del despiece: las figuras y la
página salen de él, y `validar_modelo.py` lo comprueba antes de dibujar. Ejemplos completos y válidos en
`assets/ejemplo-fisico.json` (SSD NVMe) y `assets/ejemplo-sistema.json` (Application Gateway con WAF).

## Campos

| Campo | Obligatorio | Qué es |
|---|---|---|
| `objeto` | sí | Nombre de lo que se despieza, como título de la página |
| `tipo` | sí | `fisico`, `proceso`, `sistema` o `idea` |
| `pregunta_foco` | sí | La pregunta que el lector quiere responder; termina en `?` |
| `lector` | sí | Quién lee y qué sabe («técnico de sistemas que opera la gateway pero no la diseñó») |
| `profundidad` | no (2) | Niveles por debajo del 0: 1, 2 o 3 |
| `nivel0.titulo` | sí | Afirmación sobre el todo (ver abajo) |
| `nivel0.frontera` | sí | Dónde empieza y termina el objeto |
| `nivel0.fuera` | no | Lista de lo que se deja fuera a propósito |
| `fuentes[]` | no | `{id, descripcion, url?}`; las piezas las citan por `id` |
| `piezas[]` | sí | Ver tabla siguiente |
| `relaciones[]` | no | `{de, a, tipo, etiqueta?}`; tipos: `flujo`, `contiene`, `depende`, `controla`, `dato`, `energia`, `causa` |
| `flujo[]` | proceso y sistema | Ids en el orden en que la petición, el dato o el paso ocurren; ≥ 3 |
| `malentendidos[]` | no (aviso) | Lo que el lector suele creer y es falso, con la corrección |
| `figuras[]` | no (aviso) | `{nivel, titulo, tipo_visual, skill, piezas[], fichero?}` |
| `feynman[]` | sí | Exactamente 3 frases que un no experto entendería |
| `prediccion` | sí | `{pregunta, respuesta}`: una situación concreta y qué pasaría |

### Cada pieza

| Campo | Obligatorio | Qué es |
|---|---|---|
| `id` | sí | Corto, sin espacios, único (`waf-custom`) |
| `nombre` | sí | Como se ve en la figura; ≤ 40 caracteres |
| `padre` | sí (`null` en el nivel 1) | Id de la pieza que la contiene |
| `funcion` | sí | Una línea, verbo + complemento: qué hace y por qué importa (≤ 160) |
| `fuente` | sí, o `supuesto` | Id de `fuentes[]` o texto libre («Microsoft Learn: WAF custom rules») |
| `supuesto` | — | `true` cuando no hay fuente: se muestra como «▲ supuesto» en la página |
| `orden_montaje` | físico, en raíces | Entero; 1 es lo primero que se monta (queda abajo en la figura) |
| `cantidad` | no | Si hay varias iguales («×4») |

## Reglas que impone el validador

- **Títulos afirmativos**: ≥ 4 palabras, sin «:» final, sin «Qué es…», «Introducción…», «Visión general».
  Un título dice lo que la figura demuestra: «La WAF solo inspecciona lo que entra por la gateway», no
  «Arquitectura de la gateway».
- **3–7 piezas por nivel.** Más de 7 raíces o más de 7 hijos es error: agrupar en subconjuntos. Un padre
  con un solo hijo es error: o se funden o falta una pieza.
- **≤ 6 piezas nuevas por figura** (aviso; error a partir de 10). Las ya mostradas en una figura anterior
  no cuentan.
- **Ninguna pieza sin fuente ni `supuesto: true`.** Es la regla que evita explicar de memoria.
- **`feynman` son 3 frases**, cada una de una línea y media como mucho. Si no cabe, no está entendido.
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
- En `figuras[].skill` vale `propio` cuando la figura se dibuja con un script del propio despiece, sin skill
  de dibujo instalada.
