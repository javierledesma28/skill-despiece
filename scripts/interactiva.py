"""Página interactiva del despiece: la escribe ensamblar.py --interactivo, no se ejecuta sola.

Rellena assets/plantilla-interactiva.html con el contenido del modelo ya escrito en HTML (títulos,
fichas, pasos, flujo, nivel 2, prueba y fuentes) y con las láminas isométricas de isometrico.py. El
JavaScript de la plantilla solo cambia de estado: sin él, la página se lee entera, con las figuras
explotadas y la tarjeta del nivel 2 abierta.
"""
from __future__ import annotations

import html
import json
import re
from pathlib import Path

import isometrico as iso

PLANTILLA = Path(__file__).resolve().parent.parent / "assets" / "plantilla-interactiva.html"
NEUTRO_PRIMARIO = "#1f2933"
FONDO_C, FONDO_O, TINTA_O = "#ffffff", "#0f141a", "#e6ebf0"
EN_LETRA = {1: "Una idea", 2: "Dos ideas", 3: "Tres ideas", 4: "Cuatro ideas", 5: "Cinco ideas"}


def e(t: object) -> str:
    return html.escape(str(t if t is not None else ""), quote=True)


def en_frase(t: str) -> str:
    """Primera letra en minúscula para meter un nombre a mitad de frase, salvo siglas («DRAM …»)."""
    return t if len(t) > 1 and t[1].isupper() else t[:1].lower() + t[1:]


def con_punto(t: str) -> str:
    t = (t or "").strip()
    return t if not t or t[-1] in ".!?…»)" else t + "."


# ---------- color: la marca, ajustada para que se lea en los dos temas ----------

def _rgb(h: str) -> tuple[int, int, int]:
    h = h.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def mezclar(a: str, b: str, t: float) -> str:
    """a con un t de b (0 = a, 1 = b)."""
    ra, rb = _rgb(a), _rgb(b)
    return "#%02x%02x%02x" % tuple(round(x + (y - x) * t) for x, y in zip(ra, rb))


def luminancia(h: str) -> float:
    def canal(c: int) -> float:
        c = c / 255
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (canal(c) for c in _rgb(h))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contraste(a: str, b: str) -> float:
    la, lb = sorted((luminancia(a), luminancia(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def ajustar(color: str, hacia: str, fondo: str, minimo: float = 4.5) -> str:
    """Acerca el color a «hacia» lo justo para que contraste al menos «minimo» con «fondo» (WCAG AA)."""
    for paso in range(51):
        c = mezclar(color, hacia, paso / 50)
        if contraste(c, fondo) >= minimo:
            return c
    return hacia


def tokens_marca(mk: dict) -> dict:
    """Acento = secundario de la marca y títulos = primario, ajustados: el acento lleva texto blanco
    encima en tema claro y es texto sobre fondo oscuro en tema oscuro."""
    s, p = mk["secundario"], mk["primario"]
    acento_c = ajustar(s, "#000000", FONDO_C)
    acento_o = ajustar(s, "#ffffff", "#171e27")
    neutra = p.lower() == NEUTRO_PRIMARIO
    return {
        "ACENTO_C": acento_c, "ACENTO_O": acento_o,
        "SUAVE_C": mezclar(s, "#ffffff", .88), "SUAVE_O": mezclar(s, FONDO_O, .76),
        "TITULO_C": ajustar(p, "#000000", "#f4f6f8"),
        "TITULO_O": TINTA_O if neutra else ajustar(p, "#ffffff", FONDO_O, 7.0),
        "SEL_T_C": mezclar(s, "#ffffff", .5), "SEL_L_C": s, "SEL_R_C": mezclar(s, "#000000", .24),
        "SEL_T_O": mezclar(s, "#ffffff", .58), "SEL_L_O": mezclar(s, "#ffffff", .12), "SEL_R_O": mezclar(s, "#000000", .07),
        "FUENTE": re.sub(r"[<>{};]", "", mk["fuente"]) or "system-ui, sans-serif",
    }


# ---------- piezas de HTML ----------

def json_en_html(dato: object) -> str:
    """JSON dentro de <script>: «<», «>» y «&» escapados para que el texto no pueda cerrar la etiqueta."""
    return (json.dumps(dato, ensure_ascii=False, indent=1)
            .replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026"))


def marcar_sel(svg: str, sel: str | None) -> str:
    """Deja escrita la pieza destacada (y las demás apagadas), para que se vea así también sin JavaScript."""
    if not sel:
        return svg

    def cambio(mt: re.Match) -> str:
        extra = " sel" if mt.group(2) == sel else " dim"
        return f'<g class="pieza {mt.group(1)}{extra}" data-id="{mt.group(2)}"'
    return re.sub(r'<g class="pieza ([^"]*)" data-id="([^"]*)"', cambio, svg)


class Contenido:
    def __init__(self, m: dict):
        self.m = m
        self.piezas = [p for p in m.get("piezas", []) if isinstance(p, dict) and "id" in p]
        self.por_id = {p["id"]: p for p in self.piezas}
        self.fuentes = {f["id"]: f for f in m.get("fuentes", []) if isinstance(f, dict) and "id" in f}
        self.hijos = {}
        for p in self.piezas:
            if p.get("padre"):
                self.hijos.setdefault(p["padre"], []).append(p)

    def nombre(self, p: dict, sep: str = " × ") -> str:
        c = p.get("cantidad")
        return p.get("nombre", p["id"]) + (f"{sep}{c}" if c not in (None, 1) else "")

    def fuente(self, p: dict, clase: str = "fuente") -> str:
        f = self.fuentes.get(p.get("fuente") or "")
        if p.get("supuesto") is True or not f:
            return (f'<p class="{clase}"><button class="sup" type="button" popovertarget="pop-supuesto">▲ supuesto</button>'
                    " · sin fuente verificada</p>")
        texto = e(f.get("descripcion", f["id"]))
        if f.get("url"):
            texto = f'<a href="{e(f["url"])}" target="_blank" rel="noopener">{texto}</a>'
        return f'<p class="{clase}">Fuente: {texto}</p>'

    def entrar(self, p: dict, subs: set) -> str:
        if p["id"] not in subs:
            return ""
        return f'<a class="boton" href="#sub-{e(p["id"])}" data-entrar="{e(p["id"])}">Ver por dentro →</a>'

    def ficha(self, items: list[tuple[dict, int]], destacada: str | None, subs: set) -> str:
        """Ficha lateral: una tarjeta por pieza (solo se ve la seleccionada) y la lista numerada."""
        vacia = ('<div class="ficha-vacia"' + (" hidden" if destacada else "") + '><p class="kicker">Piezas, en orden de montaje</p>'
                 '<p class="nota solo-js">Tocá una para verla en color, con su función y su fuente.</p></div>')
        fichas, lista = [], []
        for p, n in items:
            hijos = self.hijos.get(p["id"], [])
            h = ""
            if hijos:
                h = (f'<p class="hijos">Contiene {len(hijos)} piezas: {e(", ".join(x.get("nombre", x["id"]) for x in hijos))}. '
                     + self.entrar(p, subs) + "</p>")
            fichas.append(f'<div class="ficha-pieza" data-id="{e(p["id"])}"' + ("" if p["id"] == destacada else " hidden") + ">"
                          f'<span class="num">{n}</span><h3>{e(self.nombre(p))}</h3><p class="fn">{e(con_punto(p.get("funcion", "")))}</p>'
                          + self.fuente(p) + h + "</div>")
            sup = '<span class="sup" aria-label="supuesto">▲</span>' if p.get("supuesto") is True else ""
            lista.append(f'<li><button type="button" data-id="{e(p["id"])}" aria-pressed="{str(p["id"] == destacada).lower()}">'
                         f'<span class="n">{n}</span><span>{e(self.nombre(p, " ×"))}</span>{sup}</button></li>')
        return vacia + "".join(fichas) + '<ol class="lista-piezas">' + "".join(lista) + "</ol>"


def destacada_de(figuras: list, ids: set) -> str | None:
    for f in figuras:
        d = f.get("destacada")
        if d in ids and ids & set(f.get("piezas") or []):
            return d
    return None


def pagina(m: dict, mk: dict) -> tuple[str, dict]:
    """HTML completo y un resumen {secciones, oclusiones, alzas}. Lanza KeyError, ValueError… si la
    geometría está incompleta: ensamblar.py lo convierte en un error accionable."""
    c = Contenido(m)
    figuras = [f for f in m.get("figuras", []) if isinstance(f, dict)]
    lam = iso.lamina_conjunto(m)
    cj = lam["cj"]
    base = cj["base"]
    raices = [base] + sorted(cj["resto"], key=lambda q: q["orden"])
    items_raiz = [(q["pieza"], q["orden"]) for q in raices]
    geo_subs = (m["geometria"].get("subconjuntos") or {})
    subs = {pid for pid in geo_subs if pid in c.hijos}
    objeto = m.get("objeto", "Despiece")
    fig1 = [f for f in figuras if f.get("nivel") == 1]
    dest_hero = destacada_de(fig1, {q["id"] for q in raices})

    # Láminas del nivel 1: la misma para la portada, el desmontaje y el flujo
    svg_hero = marcar_sel(iso.svg_conjunto(lam, m, svg_id="hero-svg", con_mas=True,
                                           etiqueta=f"Vista explotada de {en_frase(objeto)}; cada pieza se puede seleccionar"), dest_hero)
    svg_rec = iso.svg_conjunto(lam, m, svg_id="rec-svg", etiqueta="Vista explotada que se desarma al bajar por la página")
    flujo = [i for i in m.get("flujo") or [] if i in c.por_id]
    svg_flujo = iso.svg_conjunto(lam, m, svg_id="flujo-svg", flujo=True, etiqueta="El flujo sobre la vista medio abierta") if flujo else ""

    # Desmontaje: el montaje al revés, empezando por el objeto armado y terminando en la base
    n_resto = len(cj["resto"])
    pasos = [f'<section class="paso" data-id="{e(base["id"])}" data-intro="1"><p class="orden">Armado</p>'
             f'<h3>{e(objeto)}, montado</h3><p>Las {len(raices)} piezas, en su sitio. Bajá para separarlas en el orden inverso al que se montaron.</p></section>']
    for i, q in enumerate(sorted(cj["resto"], key=lambda q: -q["orden"]), 1):
        p = q["pieza"]
        boton = c.entrar(p, subs)
        pasos.append(f'<section class="paso" data-id="{e(p["id"])}"><p class="orden">Se separa {i} de {n_resto} · pieza {q["orden"]}</p>'
                     f'<h3>{e(c.nombre(p))}</h3><p>{e(con_punto(p.get("funcion", "")))}</p>' + c.fuente(p)
                     + (f"<p>{boton}</p>" if boton else "") + "</section>")
    bp = base["pieza"]
    pasos.append(f'<section class="paso" data-id="{e(bp["id"])}" data-final="1"><p class="orden">Queda {e(en_frase(bp.get("nombre", bp["id"])))} · pieza {base["orden"]}</p>'
                 f'<h3>{e(c.nombre(bp))}</h3><p>{e(con_punto(bp.get("funcion", "")))}</p>' + c.fuente(bp) + "</section>")

    # Flujo: cada paso sabe por qué relación le llega lo que viene del anterior
    pills, fichas_flujo = [], []
    rels = [r for r in m.get("relaciones") or [] if isinstance(r, dict)]
    entrada = m.get("flujo_entrada")
    for i, pid in enumerate(flujo):
        p = c.por_id[pid]
        if i == 0:
            de, rel = "", ("Entra desde fuera de la frontera: " + e(entrada) + "." if entrada else "Entra desde fuera de la frontera.")
        else:
            previos = flujo[:i]
            cand = [r for r in rels if r.get("a") == pid and r.get("de") in previos]
            cand.sort(key=lambda r: -previos.index(r["de"]))
            if cand:
                r = cand[0]
                de = r["de"]
                rel = f'Llega desde {e(en_frase(c.por_id[de].get("nombre", de)))} por «{e(r.get("etiqueta", ""))}».'
            else:
                de, rel = None, "Ninguna relación del modelo le llega desde los pasos anteriores."
        datos = f' data-de="{e(de)}"' if de is not None else ""
        pills.append(f'<li><button class="pill" type="button"><span class="n">{i + 1}</span>{e(p.get("nombre", pid))}</button></li>')
        fichas_flujo.append(f'<div class="paso-flujo-item{" activo" if i == 0 else ""}" data-id="{e(pid)}"{datos}>'
                            f'<p class="kicker">Paso {i + 1} de {len(flujo)}</p><h3>{e(p.get("nombre", pid))}</h3>'
                            f'<p class="rel">{rel}</p><p>{e(con_punto(p.get("funcion", "")))}</p>' + c.fuente(p, "nota") + "</div>")

    # Nivel 2: una tarjeta por pieza con hijos, que se abre en su propia lámina
    bloques, destacadas, alzas_sub = [], {}, {}
    for q in raices:
        pid = q["id"]
        if pid not in subs:
            continue
        p = q["pieza"]
        ls = iso.lamina_subconjunto(m, pid)
        ids_capas = {x["id"] for x in ls["capas"]}
        figs2 = [f for f in figuras if f.get("nivel") == 2 and ids_capas & set(f.get("piezas") or [])]
        dest = destacada_de(figs2, ids_capas)
        destacadas[pid] = dest
        alzas_sub[pid] = {x["id"]: x["lift"] for x in ls["capas"]}
        titulo = figs2[0].get("titulo") if figs2 else f"Dentro de {en_frase(p.get('nombre', pid))}"
        svg = marcar_sel(iso.svg_subconjunto(ls, svg_id=f"sub-svg-{pid}",
                                             etiqueta=f"{p.get('nombre', pid)}: {len(ls['capas'])} capas, de abajo arriba"), dest)
        vt = "nivel-" + re.sub(r"[^A-Za-z0-9_-]", "-", pid)
        bloques.append(
            f'<div class="sub" id="sub-{e(pid)}"><p class="kicker">Nivel 2 · dentro de {e(en_frase(p.get("nombre", pid)))}</p>'
            f'<h2 id="titulo-n2-{e(pid)}" tabindex="-1">{e(titulo)}</h2>'
            '<p class="nota solo-js">En el nivel 1 esta pieza se dibujó cerrada. Acá se abre: entrá con el botón o seguí bajando.</p>'
            f'<div class="tarjeta" data-padre="{e(pid)}" data-titulo="titulo-n2-{e(pid)}" style="view-transition-name:{vt}">'
            f'<div class="lamina modo-nivel">{svg}</div><div>'
            f'<div class="cerrada-solo"><p><b>{e(c.nombre(p))}</b> · contiene {len(ls["capas"])} piezas</p>'
            f'<p class="nota">{e(con_punto(p.get("funcion", "")))}</p>'
            '<button class="boton primario" type="button" data-abrir>Ver por dentro →</button></div>'
            '<div class="abierta-solo"><aside class="ficha" aria-live="polite">'
            + c.ficha([(x["pieza"], x["numero"]) for x in ls["capas"]], dest, set())
            + '</aside><p style="margin-top:1rem"><button class="boton solo-js" type="button" data-volver>← Volvé al todo</button></p></div>'
            "</div></div></div>")

    pred = m.get("prediccion") or {}
    opciones = pred.get("opciones") if isinstance(pred.get("opciones"), list) else []
    pred_html = f'<p id="pregunta">{e(pred.get("pregunta"))}</p>'
    if opciones:
        pred_html += (f'<div class="opciones solo-js" id="opciones" data-correcta="{int(pred.get("correcta", 0))}">'
                      + "".join(f'<button class="opcion" type="button" aria-pressed="false"><span class="letra">{chr(65 + i)}</span><span>{e(t)}</span></button>'
                                for i, t in enumerate(opciones))
                      + f'</div><div class="respuesta" id="respuesta" hidden><p class="veredicto" id="veredicto"></p><p>{e(pred.get("respuesta"))}</p></div>')
    pred_html += (f'<details class="plegada" id="plegada"><summary>Ver la respuesta{" sin elegir" if opciones else ""}</summary>'
                  f'<p>{e(pred.get("respuesta"))}</p></details>')

    malentendidos = [x for x in m.get("malentendidos") or [] if isinstance(x, str)]
    hay_fuentes = bool(c.fuentes) or any(p.get("supuesto") is True for p in c.piezas)
    n0 = m.get("nivel0") or {}
    fuera = n0.get("fuera") or []
    nav = [("nivel0", "Nivel 0"), ("recorrido", "Desmontaje")] + ([("flujo", "Flujo")] if flujo else []) \
        + ([("nivel2", "Nivel 2")] if bloques else []) + [("prueba", "Prueba")] + ([("fuentes", "Fuentes")] if hay_fuentes else [])
    nombre_marca = (mk.get("nombre") or "").strip()
    pie_izq = e(mk["pie"]) if mk.get("pie") else f"Despiece de {e(en_frase(objeto))} · generado desde <code>modelo.json</code>"

    valores = {
        "TITULO_PAGINA": e(f"{objeto} · despiece"),
        **tokens_marca(mk),
        "MARCA_BARRA": (f"{e(nombre_marca)} <span>· despiece</span>" if nombre_marca else f"despiece <span>· {e(en_frase(objeto))}</span>"),
        "NAV": "".join(f'<a href="#{k}">{t}</a>' for k, t in nav),
        "OBJETO": e(objeto), "TITULO0": e(n0.get("titulo")), "FRONTERA": e(n0.get("frontera")),
        "FOCO": e(m.get("pregunta_foco")),
        "FUERA": ('<ul class="chips">' + "".join(f"<li>{e(x)}</li>" for x in fuera) + "</ul>") if fuera else "",
        "LECTOR": e(f"Para {m.get('lector', '')}. Profundidad: {m.get('profundidad', 2)} niveles bajo el todo."),
        "SVG_HERO": svg_hero, "FICHA_HERO": c.ficha(items_raiz, dest_hero, subs),
        "TITULO_N1": e(fig1[0].get("titulo") if fig1 else f"Las {len(raices)} piezas de {en_frase(objeto)}"),
        "SVG_REC": svg_rec, "PASOS": "".join(pasos),
        "TITULO_FLUJO": e(" → ".join(c.por_id[i].get("nombre", i) for i in flujo)),
        "SVG_FLUJO": svg_flujo, "PILLS": "".join(pills), "FICHAS_FLUJO": "".join(fichas_flujo),
        "SUBCONJUNTOS": "".join(bloques),
        "TITULO_MALENTENDIDOS": EN_LETRA.get(len(malentendidos), f"{len(malentendidos)} ideas") + " que el despiece desmonta",
        "MALENTENDIDOS": "".join(f'<li class="revelar"><span class="ico" aria-hidden="true">✗</span>{e(x)}</li>' for x in malentendidos),
        "FEYNMAN": "".join(f'<li class="revelar"><span class="n">{i}</span><p>{e(x)}</p></li>'
                           for i, x in enumerate(m.get("feynman") or [], 1)),
        "PREDICCION": pred_html,
        "FUENTES": "".join(f'<li id="fuente-{e(f["id"])}"><b>{e(f["id"])}</b> · '
                           + (f'<a href="{e(f["url"])}" target="_blank" rel="noopener">{e(f.get("descripcion", f["id"]))}</a>'
                              if f.get("url") else e(f.get("descripcion", f["id"]))) + "</li>" for f in c.fuentes.values()),
        "PIE": f"<span>{pie_izq}</span>" + (f'<span class="lema">{e(mk["lema"])}</span>' if mk.get("lema") else ""),
        "MODELO_JSON": json_en_html(m),
        "VISTA_JSON": json_en_html({"destacada": dest_hero, "destacadas": destacadas}),
    }

    plantilla = PLANTILLA.read_text(encoding="utf-8")
    bloques_si = {"flujo": bool(flujo), "nivel2": bool(bloques), "malentendidos": bool(malentendidos), "fuentes": hay_fuentes}
    for nombre, mantener in bloques_si.items():
        patron = re.compile(rf"<!--si:{nombre}-->\n?(.*?)<!--/si:{nombre}-->\n?", re.S)
        plantilla = patron.sub(lambda mt: mt.group(1) if mantener else "", plantilla)
    pagina_html = re.sub(r"\{\{([A-Z0-9_]+)\}\}", lambda mt: valores[mt.group(1)], plantilla)

    secciones = ["nivel0", "recorrido"] + (["flujo"] if flujo else []) + [f"nivel2:{x}" for x in destacadas] \
        + (["malentendidos"] if malentendidos else []) + ["prueba"] + (["fuentes"] if hay_fuentes else [])
    info = {"secciones": secciones, "oclusiones": lam["oclusiones"], "alzas": lam["alzas"], "alzas_subconjuntos": alzas_sub}
    return pagina_html, info
