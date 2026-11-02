<div align="center">

# despiece

**Despiezá cualquier cosa hasta entenderla de verdad.**

Una skill de [Claude Code](https://claude.com/claude-code) que convierte «no entiendo cómo funciona esto»
en una explicación por niveles, con figuras, fuentes y dos pruebas de que lo entendiste.

[![Versión](https://img.shields.io/badge/versi%C3%B3n-1.1.0-0b3d91)](CHANGELOG.md)
[![Licencia MIT](https://img.shields.io/badge/licencia-MIT-1b998b)](LICENSE)
[![Claude Code skill](https://img.shields.io/badge/Claude%20Code-skill-7c3aed)](https://claude.com/claude-code)
[![Python 3.10+ sin pip](https://img.shields.io/badge/python-3.10%2B%20sin%20pip-3776ab)](scripts/)
[![Un desarrollo de t28.io](https://img.shields.io/badge/un%20desarrollo%20de-t28.io-111111)](https://t28.io)

</div>

---

## El problema

Pedile a una IA que te explique cómo funciona algo y te devuelve un muro de texto: definiciones primero,
todo a la vez, sin decir de dónde sacó cada cosa y sin forma de saber si lo entendiste o solo lo leíste.

Los buenos explicadores no hacen eso. Un ilustrador técnico explota una máquina pieza por pieza. Un
profesor nombra las partes antes de explicar el mecanismo. Un divulgador te hace predecir antes de
revelar. **`despiece` mete esa disciplina dentro de Claude Code.**

## Qué hace

Con unas palabras («despiezame la Application Gateway», «cómo funciona por dentro un SSD», «no veo cómo
encaja PIM»), la skill:

1. **Encuadra antes de dibujar.** Qué tiene que poder hacer el lector después, quién es y hasta dónde
   bajar. Tres preguntas como máximo; ninguna si el contexto ya las responde.
2. **Clasifica el objeto.** Físico, proceso, sistema o idea. Cada tipo tiene su eje y su técnica.
3. **Busca fuentes.** Documentación oficial, hojas de datos, el repo del proyecto, la configuración real
   en solo lectura. Lo que no tiene fuente se marca como supuesto, pieza a pieza. **Nada se explica de
   memoria.**
4. **Modela.** Un `modelo.json` con el todo y su frontera, de 3 a 7 piezas por nivel con su función y su
   fuente, y el flujo que las une. Un validador lo revisa contra las reglas del método.
5. **Dibuja una figura por nivel.** Vista explotada propia para hardware; flujo, calles, capas o árbol
   delegados a la skill de dibujo que tengas instalada, o a un script propio.
6. **Ensambla una página** HTML con tema claro y oscuro, las figuras incrustadas y tu marca si querés.
7. **Comprueba que se entendió.** Tres frases que un no experto seguiría y una pregunta de predicción con
   la respuesta plegada al final.

## Lo que obtenés

| Fichero | Qué es |
|---|---|
| `modelo.json` | La única fuente de verdad: piezas, funciones, fuentes, relaciones, flujo, malentendidos |
| `figuras/*.svg` | Una por nivel. Vectoriales, sin tamaño fijo, listas para incrustar donde quieras |
| `index.html` | La explicación completa, autocontenida, claro y oscuro, con la predicción plegada |

Y en la conversación, lo esencial: el título del nivel 0, las tres frases y la pregunta de predicción.

## Un ejemplo en treinta segundos

Objeto: **un SSD NVMe**. Pregunta foco: *¿por qué dos SSD del mismo tamaño y precio rinden tan distinto
en escrituras largas?*

> **Nivel 0 · Un SSD es una placa con cinco piezas, y solo dos deciden su velocidad.**
>
> **En tres frases.** Un SSD es una placa con una controladora que reparte los datos entre varios chips de
> memoria. Va rápido mientras escribe en paralelo en muchos chips y tiene a mano la tabla de dónde está
> cada cosa. Cuando la caché rápida se llena o no hay DRAM, el disco baja a la velocidad real de sus celdas.
>
> **Ponete a prueba.** Dos SSD de 1 TB: uno con 4 chips NAND y DRAM, otro con 2 chips y sin DRAM. Copiás
> 200 GB seguidos. ¿Cuál se frena antes y por qué?

El modelo completo está en [`assets/ejemplo-fisico.json`](assets/ejemplo-fisico.json). La vista explotada
que sale de él, numerada en orden de montaje y con la controladora destacada, se genera con un comando
(más abajo).

## Cuatro tipos de cosa, cuatro formas de abrirla

| Tipo | Ejemplos | Eje | Figura |
|---|---|---|---|
| **Físico** | un SSD, un firewall, una Raspberry Pi | espacial | vista explotada numerada (la dibuja la skill) |
| **Proceso** | una activación por PIM, un despliegue, un alta | temporal | flujo o calles |
| **Sistema** | una arquitectura, una red, el camino de una petición | funcional y de flujo | flujo, capas, C4 |
| **Idea** | un concepto, un patrón, una decisión de diseño | lógico | árbol MECE, mapa conceptual |

Los casos mixtos los decide la pregunta foco: un firewall es físico para «qué cable va dónde» y sistema
para «por qué bloquea esto».

## Instalación

Cloná el repo en la carpeta de skills personales de Claude Code:

```bash
git clone https://github.com/javierledesma28/skill-despiece.git ~/.claude/skills/despiece
```

En Windows, con PowerShell:

```powershell
git clone https://github.com/javierledesma28/skill-despiece.git "$env:USERPROFILE\.claude\skills\despiece"
```

Requisitos: Claude Code y Python 3.10 o superior. **Sin dependencias de pip.** Para capturar la página en
PNG, Edge o Chrome.

## Uso

Dentro de Claude Code, con el comando o con tus palabras:

```
/despiece el túnel VPN entre la oficina y la nube
```

```
no entiendo cómo funciona por dentro un SSD NVMe, desmenuzámelo
```

```
qué partes tiene una Raspberry Pi 5 y qué hace cada una, para la ficha del taller
```

Se activa con «despiezá», «desmenuzá», «desarmá», «cómo funciona por dentro», «qué partes tiene»,
«anatomía de», «explicámelo para entenderlo», «no veo cómo encaja»… aunque no digas «despiece». Si pedís
algo corto («en dos párrafos»), aplica el mismo método pero responde en texto, sin montar la página.

## Probalo en dos minutos, sin Claude

Los scripts funcionan solos. Con el ejemplo del SSD:

```bash
cd ~/.claude/skills/despiece
python -I scripts/validar_modelo.py assets/ejemplo-fisico.json
mkdir -p demo/figuras
python -I scripts/explosionado.py assets/ejemplo-fisico.json --salida demo/figuras/n1-explosion.svg --destacar controladora --marca assets/marca-ejemplo.json
python -I scripts/explosionado.py assets/ejemplo-fisico.json --salida demo/figuras/n2-nand.svg --subconjunto nand --marca assets/marca-ejemplo.json
python -I scripts/ensamblar.py assets/ejemplo-fisico.json --salida demo/index.html --figuras demo --marca assets/marca-ejemplo.json
```

Abrí `demo/index.html`. Cambiá el tema del sistema a oscuro: la página cambia y las figuras siguen sobre
lámina blanca.

## Tu marca, en un fichero

La skill no trae la marca de nadie. Si querés la tuya, un JSON:

```json
{
  "nombre": "Acme Research",
  "primario": "#0b3d91",
  "secundario": "#1b998b",
  "fuente": "'Segoe UI', system-ui, sans-serif",
  "pie": "Acme Research · Documentación técnica interna",
  "lema": "ENTENDER ANTES DE TOCAR"
}
```

y `--marca ruta/a/marca.json` en `explosionado.py` y `ensamblar.py`. Sin el flag, o con `--marca ninguna`,
la página sale neutra. Los colores se aclaran solos en tema oscuro para seguir leyéndose.

## Skills de dibujo: opcionales

`despiece` es una capa de **comprensión**, no de dibujo: decide qué se muestra, en qué orden y con qué
figura. Para hardware dibuja ella misma la vista explotada. Para el resto entrega un **guion** (título
afirmativo, piezas exactas, relaciones, pieza destacada, ruta de salida) a la skill de dibujo que tengas
instalada, por ejemplo una de diagramas editoriales para flujos, calles, capas y árboles. Si no tenés
ninguna, dibuja con un script propio siguiendo el guion. Las reglas están en
[`references/guion-visual.md`](references/guion-visual.md).

## El método, y de dónde sale

Vistas explotadas de Agrawala y Li (SIGGRAPH 2003 y 2008) y Stephen Biesty para lo físico; IDEF0 e
instrucciones paso a paso para procesos; C4, FAST y la tradición *what happens when* para sistemas; MECE,
mapas conceptuales de Novak y la técnica de Feynman para ideas. Encima, la ciencia de aprender con figuras:
Mayer (nombrar antes de explicar, señalizar, segmentar), Sweller (de 3 a 7 por nivel), Distill (predecir
antes de revelar) y los anti-patrones de Julia Evans y Nicky Case. Y lo que se tomó y lo que se descartó de
ocho skills de explicación visual. Todo trazado regla por regla en
[`references/fuentes.md`](references/fuentes.md).

## Qué tan bien funciona

Medido, no prometido. En las evals de la versión 1.0 (cuatro casos reales, uno por tipo, ejecutados con y
sin la skill en subagentes limpios):

| | Con skill | Sin skill |
|---|---|---|
| Aserciones cumplidas | **26 / 26** | 15 / 26 |
| Activación correcta (20 consultas × 3 modelos) | **60 / 60** | — |

Sin la skill, el modelo explica bien y cita fuentes, pero no modela por niveles, no marca supuestos pieza
a pieza y nunca cierra con las pruebas de comprensión. Detalle y limitaciones en
[`evals/resultados-2026-11-01.md`](evals/resultados-2026-11-01.md). Los casos de la 1.1.0, ya públicos,
están pendientes de correr.

## Hoja de ruta

- [ ] Correr las evals públicas de la 1.1.0 (calidad y activación) y publicar los resultados.
- [ ] Capturas y vídeo de un despiece de punta a punta.
- [ ] Cortes y vistas isométricas en la vista explotada.
- [ ] Un caso con Haiku como ejecutor.

¿Lo usaste para algo? Abrí un issue con tu `modelo.json`: los buenos despieces se convierten en ejemplos.

## Licencia

[MIT](LICENSE). Usalo, modificalo, compartilo.

---

<div align="center">

**Un desarrollo de [t28.io](https://t28.io)** · hecho con Claude Code

</div>
