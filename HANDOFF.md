# Handoff · rama `vista-isometrica`

Estado al 12-nov-2026 (sesión de voz desde el móvil). Retomar desde Claude Code en la laptop con el repo clonado.

## Qué hay hecho en esta rama

- `scripts/explosionado.py` reescrito: vista explotada **isométrica** (30°), prismas de 3 caras, sombra bajo la base, eje de montaje discontinuo, pieza destacada con el secundario de marca, llamadas numeradas con guía en codo, lista a la derecha sin solapes.
- Siluetas por tipo de pieza (campo opcional `forma` en cada pieza o inferida por nombre): `placa`, `chip`, `conector`, `modulo`, `carcasa`, `disipador`, `cable`, `capa`.
- Último commit del script añade un nivel más de detalle sin perder minimalismo: sombra proyectada de cada pieza sobre la de abajo, brillo en chips, serigrafía y pasivos en la placa, contactos alternos y pestañas en el conector, tornillos en la carcasa, sombra entre aletas del disipador.
- `README.md` reescrito (rioplatense, solapas, portada). La portada apunta a una URL del CDN de Segmind.
- Demos en `docs/demo/iso/` (**desactualizadas**: generadas con la versión anterior del script).

## Pendiente (en orden)

0. **Portada del README**: descargar la imagen a `docs/img/portada.png` y cambiar el `<img src>` del README por la ruta local (el CDN de Segmind no es permanente):
   ```bash
   mkdir -p docs/img
   curl -L -o docs/img/portada.png "https://images.segmind.com/generations/8aa288dd-101b-44f6-93ca-a50fe89ea2b3/7a70afc9ad5052b713213588bb8f0157.png"
   ```
1. **Regenerar las demos** con el script actual:
   ```bash
   python -I scripts/explosionado.py assets/ejemplo-fisico.json --salida docs/demo/iso/n1-explosion.svg --destacar controladora
   python -I scripts/explosionado.py assets/ejemplo-fisico.json --salida docs/demo/iso/n2-nand.svg --subconjunto nand
   ```
   Opcional: crear `assets/test-formas.json` (el SSD de ejemplo + un disipador + una carcasa, con `forma` explícita) y generar `docs/demo/iso/test-formas.svg` para ver todas las siluetas juntas.
2. **Revisar visualmente** los SVG. Si alguna pieza sigue pareciendo "la misma caja", ajustar su rama en `dibujar_pieza()`.
3. **Explorador interactivo** `explorador.html` (autocontenido, sin dependencias) con zoom semántico: rueda/pellizco acerca; al superar un umbral sobre una pieza con hijos, se abre y los hijos explotan con transición; alejar los cierra; clic/toque entra; panel lateral con pieza activa, función, fuente y migas. Portar la geometría de `explosionado.py` a JS.
4. **Documentar**: `SKILL.md` y `CHANGELOG.md` → campo `forma`, formas disponibles, salida JSON con `formas`, demos. Comprobar que los comandos de instalación del README coinciden con lo que dice `SKILL.md`. Subir versión (1.2.0).
5. Abrir PR `vista-isometrica` → `main`.
6. Más adelante: figuras propias para `proceso`, `sistema` e `idea`.

## Notas

- El script no tiene dependencias: Python 3.10+ y nada más.
- Probar la skill en caliente desde Claude Code abierto en esta carpeta: `/despiece` usa el código local.
- Borrar este archivo al cerrar el PR.
