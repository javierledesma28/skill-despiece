# Changelog

Formato: versión semántica (`metadata.version` de SKILL.md). Una entrada por cambio relevante, con el
resultado de las evals que lo respaldan.

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
