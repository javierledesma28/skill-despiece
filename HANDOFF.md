# Handoff · rama `vista-isometrica`

Estado al 12-nov-2026 (sesión de voz desde el móvil). Retomar desde Claude Code en la laptop con el repo clonado.

## Qué hay hecho en esta rama

- `scripts/explosionado.py` reescrito: vista explotada **isométrica** (30°), prismas de 3 caras, sombra bajo la base, eje de montaje discontinuo, pieza destacada con el secundario de marca, llamadas numeradas con guía en codo, lista a la derecha sin solapes.
- Siluetas por tipo de pieza (campo opcional `forma` o inferida por nombre): `placa`, `chip`, `conector`, `modulo`, `carcasa`, `disipador`, `cable`, `capa`.
- Último commit del script añade detalle sin perder minimalismo: sombra proyectada de cada pieza sobre la de abajo, brillo en chips, serigrafía en la placa, contactos alternos en el conector, tornillos en la carcasa, sombra entre aletas.
- `README.md` reescrito (rioplatense, solapas, portada en CDN de Segmind).
- Demos en `docs/demo/iso/` (**desactualizadas**: generadas con la versión anterior del script).

---

## PRIORIDAD 1 · Diseño: la skill es 100 % agnóstica

> **Principio.** La skill no sabe de hardware, de redes ni de historia. Sabe de *todos* que contienen *partes*. Las partes se **ordenan por dependencia** y se **agrupan por pertenencia**. Todo lo demás es vocabulario. El resultado no es una figura: es un **navegador** de cualquier cosa, de más a menos, con profundidad que crece según el usuario la pida.

### Los dos ejes (y nada más)

| Eje | Pregunta | En el SSD | En otros dominios |
|---|---|---|---|
| **Dependencia** (hoy `orden_montaje`) | ¿Qué tiene que existir antes de qué? | orden de montaje | despliegue (Azure), cronología (historia), generaciones (árbol genealógico), fases (auditoría), profundidad (estratos de Marte), cadena de señal (tacto: receptor → nervio → médula → corteza) |
| **Pertenencia** (hoy `padre`) | ¿Qué está dentro de qué? → el «+» | NAND contiene celdas/bloques | dominio ⊃ control ⊃ evidencia; período ⊃ década ⊃ hecho; VNet ⊃ subnet ⊃ NIC |

Decisión: renombrar conceptualmente `orden_montaje` → **`orden`** (dependencia), manteniendo `orden_montaje` como alias retrocompatible. El subtítulo de la figura deja de ser «orden de montaje» y lo da el modelo (`eje: "cronología"`, `eje: "profundidad"`, …).

### Roles → formas

`explosionado.py` debe aceptar los **cuatro tipos** (`fisico | proceso | sistema | idea`), no solo `fisico`. Cada pieza tiene un **rol** abstracto; el rol elige la silueta. Las ocho formas actuales se mantienen como siluetas; lo que cambia es la tabla de entrada:

| Rol (campo `rol`) | Significa | Forma |
|---|---|---|
| `base` | Sobre lo que se apoya el resto | `placa` |
| `etapa` / `capa` | Período, fase, estrato, dominio | `capa` |
| `componente` | Unidad activa con identidad propia | `chip` |
| `interfaz` | Punto de contacto / entrada-salida | `conector` |
| `enlace` | Relación entre dos partes (peering, parentesco, causa) | `cable` |
| `contenedor` / `límite` | Lo que encierra o restringe (NSG, marco legal, membrana) | `carcasa` |
| `regulador` | Lo que disipa, controla o compensa | `disipador` |
| `bloque` | Genérico, cuando no hay nada mejor | `modulo` |

`forma` explícita sigue ganando a `rol`; `rol` gana a la inferencia por nombre. Las `PISTAS` por nombre pasan a ser el último recurso.

### Casos de prueba (todos deben salir con el mismo motor)

Crear un `assets/ejemplo-*.json` por caso y una figura de demo por cada uno:

1. **SSD NVMe** (físico, ya existe) — montaje.
2. **Conectividad Azure**: VNet, subnets, NIC, VPN Gateway site-to-site, peering, NSG — despliegue. VNet=`base`, subnet=`capa`, NIC=`componente`, gateway=`interfaz`, peering=`enlace`, NSG=`contenedor`.
3. **Historia argentina, últimos 200 años** — cronología. Períodos=`etapa`; dentro, décadas → hechos → actores.
4. **Auditoría ISO 27001** — fases *y* capas a la vez: fase 1..n como orden; dentro de cada fase, dominios ⊃ controles ⊃ evidencias. Es el caso que valida que los dos ejes conviven.
5. **Árbol genealógico** — generaciones como orden; parentesco=`enlace`.
6. **Terreno de Marte** — profundidad: regolito, estratos, permafrost, basalto; de superficie a fondo.
7. **El sentido del tacto** — cadena de señal: receptores, nervios, médula, tálamo, corteza; cada uno abre sus partes.
8. **Un proceso cualquiera** (p. ej. CI/CD) — para no perder el tipo `proceso`.

Criterio de éxito: pedir `/despiece` de cualquiera de los 8 por voz o texto, sin dar pistas de formato, y obtener un navegador de más a menos donde cada nivel se abre a demanda.

### Profundidad a demanda

El modelo del nivel n+1 **no se genera por adelantado**: se genera cuando el usuario abre esa pieza. Guardar el modelo incremental (`modelo.json` crece) para que lo ya abierto no se recalcule. Esto es lo que después alimenta el explorador interactivo.

### Qué toca

- `references/formato-modelo.md`: `orden`, `eje`, `rol`, retrocompatibilidad.
- `scripts/validar_modelo.py`: aceptar `rol` y `eje`; `orden_montaje` como alias.
- `scripts/explosionado.py`: quitar el rechazo de tipos no físicos; tabla rol→forma; subtítulo desde `eje`.
- `SKILL.md`: flujo de «abrir a demanda»; vocabulario por dominio como ejemplos, nunca como reglas.
- `README.md`: abrir con tres casos (físico, sistema, idea), no solo el SSD.

---

## Pendiente después (en orden)

0. **Portada del README**: bajarla a `docs/img/portada.png` y apuntar el `<img src>` ahí (el CDN de Segmind no es permanente):
   ```bash
   mkdir -p docs/img
   curl -L -o docs/img/portada.png "https://images.segmind.com/generations/8aa288dd-101b-44f6-93ca-a50fe89ea2b3/7a70afc9ad5052b713213588bb8f0157.png"
   ```
1. **Regenerar las demos** con el script actual:
   ```bash
   python -I scripts/explosionado.py assets/ejemplo-fisico.json --salida docs/demo/iso/n1-explosion.svg --destacar controladora
   python -I scripts/explosionado.py assets/ejemplo-fisico.json --salida docs/demo/iso/n2-nand.svg --subconjunto nand
   ```
2. **Revisar visualmente** los SVG; ajustar `dibujar_pieza()` donde haga falta.
3. **Explorador interactivo** `explorador.html` (autocontenido): zoom semántico, rueda/pellizco abre y cierra niveles, clic entra, panel lateral con pieza, función, fuente y migas. Portar la geometría de `explosionado.py` a JS. Se apoya en «profundidad a demanda».
4. **Documentar** `SKILL.md` y `CHANGELOG.md`; comprobar que la instalación del README coincide con `SKILL.md`. Versión 2.0.0 (cambia el modelo).
5. PR `vista-isometrica` → `main`.

## Notas

- Sin dependencias: Python 3.10+.
- Probar en caliente desde Claude Code abierto en esta carpeta: `/despiece` usa el código local.
- Borrar este archivo al cerrar el PR.
