"""Geometría de la página interactiva: proyección isométrica, alzas sin solapes y láminas SVG.

Usage: python -I isometrico.py MODELO.json

Lo importa ensamblar.py --interactivo. Como programa, solo calcula: lee el bloque «geometria» de un
modelo de tipo físico, elige las alzas de la vista explotada (cuánto sube cada pieza) y comprueba que,
abierta del todo y en cada paso del desmontaje, ninguna pieza tape la cara de arriba ni el número de
otra. No escribe ficheros.

Las alzas no se escriben a mano: se calculan. Piezas repartidas sobre la base: la base no sube, y el
resto sube más cuanto más tarde se montó (el desmontaje es el montaje al revés), con el mayor escalón
entre piezas que no provoque solapes. Capas apiladas de un subconjunto: cada una sube lo suficiente para
que asome una franja de la de abajo; la página las pinta en rayos X (translúcidas).

Salida en stdout: JSON {"escala", "base", "escalon", "alzas", "oclusiones", "subconjuntos"}.
Códigos de salida: 0 sin oclusiones · 1 con oclusiones (la página se genera igual; mover piezas o
agrupar) · 2 fichero, JSON o geometría inválidos.
Ejemplo:
  python -I isometrico.py despiece/modelo.json
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

C30 = math.cos(math.radians(30))  # 0,8660254: ancho de un mm en x o en y
ANCHO_BASE = 640                   # px que ocupa la base en la lámina del nivel 1
ANCHO_CAPAS = 470                  # px que ocupa la huella de un subconjunto en su lámina
BADGE_PALO, BADGE_R = 14, 12       # número de cada pieza: palito y círculo
MARGEN = 18
TOLERANCIA_PX2 = 4.0               # solapes menores se ignoran (antialias, aristas compartidas)
MAX_TAPADO = 0.05                  # fracción de la cara de arriba que otra pieza puede tapar
FORMAS = {"placa", "chip", "conector", "caja"}
PATRONES = {"rejilla", "puntos"}


# ---------- proyección y polígonos ----------

def proyector(S: float, cx: float, cy: float):
    """(x, y, z) en mm → (u, v) en px. x baja a la derecha, y baja a la izquierda, z sube."""
    return lambda x, y, z: (cx + (x - y) * C30 * S, cy + (x + y) * 0.5 * S - z * S)


def caras(P, b) -> dict[str, list]:
    """Las tres caras visibles de una caja b = (x0, y0, x1, y1, z0, z1): izquierda (y = y1), derecha
    (x = x1) y arriba (z = z1). Se pintan en ese orden para que la de arriba tape las aristas."""
    x0, y0, x1, y1, z0, z1 = b
    return {
        "l": [P(x0, y1, z1), P(x1, y1, z1), P(x1, y1, z0), P(x0, y1, z0)],
        "r": [P(x1, y0, z1), P(x1, y1, z1), P(x1, y1, z0), P(x1, y0, z0)],
        "t": [P(x0, y0, z1), P(x1, y0, z1), P(x1, y1, z1), P(x0, y1, z1)],
    }


def envolvente(puntos: list) -> list:
    """Envolvente convexa (cadena monótona), en sentido antihorario."""
    pts = sorted(set((round(u, 3), round(v, 3)) for u, v in puntos))
    if len(pts) <= 2:
        return pts
    cruz = lambda o, a, b: (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])  # noqa: E731
    bajo, alto = [], []
    for p in pts:
        while len(bajo) >= 2 and cruz(bajo[-2], bajo[-1], p) <= 0:
            bajo.pop()
        bajo.append(p)
    for p in reversed(pts):
        while len(alto) >= 2 and cruz(alto[-2], alto[-1], p) <= 0:
            alto.pop()
        alto.append(p)
    return bajo[:-1] + alto[:-1]


def silueta(P, b) -> list:
    x0, y0, x1, y1, z0, z1 = b
    return envolvente([P(x, y, z) for x in (x0, x1) for y in (y0, y1) for z in (z0, z1)])


def area(poly: list) -> float:
    n = len(poly)
    return abs(sum(poly[i][0] * poly[(i + 1) % n][1] - poly[(i + 1) % n][0] * poly[i][1] for i in range(n))) / 2 if n > 2 else 0.0


def interseccion(sujeto: list, recorte: list) -> float:
    """Área de sujeto ∩ recorte; recorte convexo (Sutherland–Hodgman)."""
    if len(sujeto) < 3 or len(recorte) < 3:
        return 0.0
    signo = 1 if sum(recorte[i][0] * recorte[(i + 1) % len(recorte)][1] - recorte[(i + 1) % len(recorte)][0] * recorte[i][1]
                     for i in range(len(recorte))) > 0 else -1
    dentro = lambda p, a, b: signo * ((b[0] - a[0]) * (p[1] - a[1]) - (b[1] - a[1]) * (p[0] - a[0])) >= 0  # noqa: E731

    def corte(p, q, a, b):
        dx1, dy1, dx2, dy2 = q[0] - p[0], q[1] - p[1], b[0] - a[0], b[1] - a[1]
        den = dx1 * dy2 - dy1 * dx2
        if abs(den) < 1e-12:
            return q
        t = ((a[0] - p[0]) * dy2 - (a[1] - p[1]) * dx2) / den
        return (p[0] + t * dx1, p[1] + t * dy1)

    salida = list(sujeto)
    for i in range(len(recorte)):
        a, b = recorte[i], recorte[(i + 1) % len(recorte)]
        entrada, salida = salida, []
        if not entrada:
            break
        s = entrada[-1]
        for e in entrada:
            if dentro(e, a, b):
                if not dentro(s, a, b):
                    salida.append(corte(s, e, a, b))
                salida.append(e)
            elif dentro(s, a, b):
                salida.append(corte(s, e, a, b))
            s = e
    return area(salida)


def subir(poly: list, dv: float) -> list:
    return [(u, v - dv) for u, v in poly]


def circulo(u: float, v: float, r: float, lados: int = 12) -> list:
    return [(u + r * math.cos(2 * math.pi * k / lados), v + r * math.sin(2 * math.pi * k / lados)) for k in range(lados)]


# ---------- lectura de la geometría ----------

def _rango(v) -> tuple[float, float]:
    return float(v[0]), float(v[1])


def unidades_de(g: dict, placa: dict | None = None) -> list[tuple]:
    """Cajas (x0, y0, x1, y1, z0, z1) de una pieza: una, o una por unidad si son varias iguales."""
    if g.get("forma") == "placa":
        return [(0.0, 0.0, float(placa["largo"]), float(placa["ancho"]), -float(placa.get("grosor", 1)), 0.0)]
    z0 = float(g.get("z", 0))
    z1 = z0 + float(g["alto"])
    y0, y1 = _rango(g["y"])
    if g.get("unidades"):
        return [(float(u[0]), y0, float(u[1]), y1, z0, z1) for u in g["unidades"]]
    x0, x1 = _rango(g["x"])
    return [(x0, y0, x1, y1, z0, z1)]


def conjunto(modelo: dict) -> dict:
    """Base y resto de raíces con su geometría, en orden de pintado (de lejos a cerca)."""
    geo = modelo["geometria"]
    placa = geo["placa"]
    raices = sorted((p for p in modelo["piezas"] if p.get("padre") is None), key=lambda p: p.get("orden_montaje", 0))
    piezas = []
    for p in raices:
        g = geo["piezas"][p["id"]]
        uds = unidades_de(g, placa)
        x0, x1 = min(u[0] for u in uds), max(u[2] for u in uds)
        y0, y1 = min(u[1] for u in uds), max(u[3] for u in uds)
        piezas.append({"id": p["id"], "pieza": p, "forma": g.get("forma", "caja"), "geo": g, "unidades": uds,
                       "orden": p.get("orden_montaje", 0), "centro": ((x0 + x1) / 2, (y0 + y1) / 2),
                       "arriba": max(u[5] for u in uds)})
    base = next(q for q in piezas if q["forma"] == "placa")
    resto = sorted((q for q in piezas if q is not base), key=lambda q: min(u[0] + u[1] for u in q["unidades"]))
    # El número de la base va cerca de la esquina más próxima al lector, en un hueco sin piezas
    L, W = float(placa["largo"]), float(placa["ancho"])
    huecos = [(L - f * L, W - g * W) for f in (0.05, 0.12, 0.2, 0.3) for g in (0.07, 0.04)]
    libre = lambda x, y: not any(u[0] <= x <= u[2] and u[1] <= y <= u[3] for q in resto for u in q["unidades"])  # noqa: E731
    base["centro_numero"] = next((h for h in huecos if libre(*h)), huecos[0])
    for q in resto:
        q["centro_numero"] = q["centro"]
    return {"base": base, "resto": resto, "placa": placa, "unidad": geo.get("unidad", "mm")}


# ---------- alzas ----------

def _numero(P, q, alza: float) -> list:
    u, v = P(q["centro_numero"][0], q["centro_numero"][1], q["arriba"])
    return circulo(u, v - alza - BADGE_PALO - BADGE_R, BADGE_R + 1)


def oclusiones(P, orden_pintado: list, alzas: dict, levantadas: set) -> list[dict]:
    """Qué pieza tapa a cuál con estas alzas, cuando solo las de «levantadas» están subidas."""
    dz = lambda q: alzas.get(q["id"], 0) if q["id"] in levantadas else 0  # noqa: E731
    hallazgos = []
    for i, a in enumerate(orden_pintado):
        tops = [subir(caras(P, u)["t"], dz(a)) for u in a["unidades"]]
        total = sum(area(t) for t in tops) or 1.0
        num = _numero(P, a, dz(a))
        tapado = num_tapado = 0.0
        culpables = set()
        for b in orden_pintado[i + 1:]:
            sils = [subir(silueta(P, u), dz(b)) for u in b["unidades"]]
            t = sum(interseccion(top, s) for top in tops for s in sils)
            n = sum(interseccion(num, s) for s in sils)
            if t > TOLERANCIA_PX2 or n > TOLERANCIA_PX2:
                culpables.add(b["id"])
            tapado += t
            num_tapado += n
        if a.get("forma") == "placa":
            tapado = 0.0  # la base queda debajo de todo: solo importa que su número se vea
        if tapado / total > MAX_TAPADO or num_tapado > TOLERANCIA_PX2:
            hallazgos.append({"tapada": a["id"], "por": sorted(culpables), "cara_tapada": round(tapado / total, 2),
                              "numero_tapado": num_tapado > TOLERANCIA_PX2})
    return hallazgos


def estados_desmontaje(resto: list) -> list[set]:
    """Piezas subidas en cada paso del desmontaje: primero la última en montarse; el último estado es
    la vista explotada entera."""
    por_orden = sorted(resto, key=lambda q: q["orden"], reverse=True)
    return [{q["id"] for q in por_orden[:j]} for j in range(1, len(por_orden) + 1)]


def calcular_alzas(cj: dict, S: float) -> dict:
    """La base no sube; el resto sube arranque + escalón × rango de montaje. Se prueban arranques de 0,4 a
    1,2 veces el alto en pantalla de la pieza más grande y escalones de 10 a 50 px, y vale cualquier
    combinación en la que ninguna pieza tapa más del 5 % de la cara de arriba de otra ni ningún número, en
    la vista abierta y en cada paso del desmontaje; entre ellas, la de escalón más claro sin pasar en más de
    20 px la alza máxima de la más compacta. Si ninguna lo logra, la de menos tapado, con las oclusiones
    informadas."""
    P = proyector(S, 0, 0)
    base, resto = cj["base"], cj["resto"]
    pintado = [base] + resto
    rango = {q["id"]: k for k, q in enumerate(sorted(resto, key=lambda q: q["orden"]))}
    estados = estados_desmontaje(resto)
    alto_max = max(max(u[2] - u[0] + u[3] - u[1] for u in q["unidades"]) * 0.5 * S + q["arriba"] * S for q in resto)
    mejor, aceptables = None, []
    for f in range(4, 13):
        arranque = round(alto_max * f / 10)
        for escalon in range(10, 51, 5):
            alzas = {base["id"]: 0, **{q["id"]: arranque + escalon * rango[q["id"]] for q in resto}}
            hallados = [h | {"estado": len(lev)} for lev in estados for h in oclusiones(P, pintado, alzas, lev)]
            peor = max([1.0 if h["numero_tapado"] else h["cara_tapada"] for h in hallados] or [0.0])
            techo = max(alzas.values())
            if mejor is None or peor < mejor[0]:
                mejor = (peor, arranque, escalon, alzas, hallados)
            if not hallados:
                aceptables.append((techo, arranque, escalon, alzas))
    if aceptables:
        # Entre las que no se tapan y caben en 20 px más que la más compacta, el escalón más claro
        minimo = min(a[0] for a in aceptables)
        _, arranque, escalon, alzas = min((a for a in aceptables if a[0] <= minimo + 20), key=lambda a: (-a[2], a[0]))
        return {"base": arranque, "escalon": escalon, "alzas": alzas, "oclusiones": []}
    _, arranque, escalon, alzas, hallados = mejor
    return {"base": arranque, "escalon": escalon, "alzas": alzas, "oclusiones": hallados}


# ---------- láminas: escala, encuadre y SVG ----------

def num(v: float) -> str:
    """8.5 → «8,5»; 22.0 → «22»."""
    return ("%g" % float(v)).replace(".", ",")


def _ancho_texto(t: str, tam: float) -> float:
    return len(t) * tam * 0.56


def _pts(poly: list) -> str:
    return " ".join(f"{u:.1f},{v:.1f}" for u, v in poly)


def _esc(t: object) -> str:
    return str(t).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def _caja_svg(P, b) -> str:
    c = caras(P, b)
    return '<g class="caja">' + "".join(f'<polygon class="cara {k}" points="{_pts(c[k])}"/>' for k in ("l", "r", "t")) + "</g>"


def _badge(P, x, y, z, numero, mult=None) -> tuple[str, list]:
    """Número de la pieza: palito desde el centro de su cara de arriba y círculo encima."""
    u, v = P(x, y, z)
    top = v - BADGE_PALO - BADGE_R
    partes = [f'<line x1="{u:.1f}" y1="{v:.1f}" x2="{u:.1f}" y2="{top + BADGE_R:.1f}"/>',
              f'<circle cx="{u:.1f}" cy="{top:.1f}" r="{BADGE_R}"/>', f'<text x="{u:.1f}" y="{top:.1f}">{numero}</text>']
    puntos = circulo(u, top, BADGE_R + 2, 8) + [(u, v)]
    if mult:
        t = f"×{mult}"
        partes.append(f'<text class="mult" x="{u + 15:.1f}" y="{top:.1f}">{t}</text>')
        puntos.append((u + 15 + _ancho_texto(t, 10.5), top))
    return '<g class="badge">' + "".join(partes) + "</g>", puntos


def _ras(P, b, lift: float) -> str:
    """Rastro de una pieza: su huella punteada donde estaba y la guía hasta donde subió."""
    x0, y0, x1, y1, z0, _ = b
    huella = [P(x0, y0, z0 + .02), P(x1, y0, z0 + .02), P(x1, y1, z0 + .02), P(x0, y1, z0 + .02)]
    gu, gv = P((x0 + x1) / 2, (y0 + y1) / 2, z0)
    return (f'<polygon class="huella" points="{_pts(huella)}"/>'
            f'<line class="guia" x1="{gu:.1f}" y1="{gv:.1f}" x2="{gu:.1f}" y2="{gv - lift:.1f}" '
            f'style="transform-origin:{gu:.1f}px {gv:.1f}px"/>')


def _encuadrar(lam: dict, dibujar) -> None:
    """Dibuja una vez en el origen para medir y fija el desplazamiento y el viewBox con margen."""
    lam["desplazamiento"] = (0.0, 0.0)
    puntos: list = []
    dibujar(puntos)
    umin, vmin = min(p[0] for p in puntos), min(p[1] for p in puntos)
    umax, vmax = max(p[0] for p in puntos), max(p[1] for p in puntos)
    lam["desplazamiento"] = (MARGEN - umin, MARGEN - vmin)
    lam["viewbox"] = (0, 0, round(umax - umin + 2 * MARGEN), round(vmax - vmin + 2 * MARGEN))


def lamina_conjunto(modelo: dict) -> dict:
    """Escala, alzas y encuadre de la lámina del nivel 1: la misma para la portada, el desmontaje y el
    flujo, para que el objeto no cambie de tamaño al bajar por la página."""
    cj = conjunto(modelo)
    placa = cj["placa"]
    S = ANCHO_BASE / ((float(placa["largo"]) + float(placa["ancho"])) * C30)
    calc = calcular_alzas(cj, S)
    lam = {"cj": cj, "S": S, "alzas": calc["alzas"], "base": calc["base"], "escalon": calc["escalon"],
           "oclusiones": calc["oclusiones"], "p_flujo": 0.3}
    _encuadrar(lam, lambda pts: svg_conjunto(lam, modelo, svg_id="", etiqueta="", con_mas=True, flujo=True, recoger=pts))
    return lam


def _centro(lam: dict, P, q: dict, p: float) -> tuple[float, float]:
    """Punto de anclaje de las flechas: el centro de la cara de arriba, con la pieza subida p."""
    if q["forma"] == "placa":
        placa = lam["cj"]["placa"]
        return P(float(placa["largo"]) / 2, float(placa["ancho"]) / 2, 0)
    u, v = P(q["centro"][0], q["centro"][1], q["arriba"])
    return u, v - lam["alzas"][q["id"]] * p


def _detalle_conector(P, g: dict, b: tuple, L: float, W: float) -> str:
    """Contactos dorados a lo largo del lado largo y, si hay «muesca» [desde, hasta], la llave, abierta
    hacia el borde de la base más cercano."""
    x0, y0, x1, y1, _, z1 = b
    z = z1 + .01
    largo_x = (x1 - x0) >= (y1 - y0)
    n, partes = 7, []
    for i in range(1, n + 1):
        if largo_x:
            y = y0 + i * (y1 - y0) / (n + 1)
            a, c = P(x0 + .05 * (x1 - x0), y, z), P(x1 - .05 * (x1 - x0), y, z)
        else:
            x = x0 + i * (x1 - x0) / (n + 1)
            a, c = P(x, y0 + .05 * (y1 - y0), z), P(x, y1 - .05 * (y1 - y0), z)
        partes.append(f'<line class="detalle" x1="{a[0]:.1f}" y1="{a[1]:.1f}" x2="{c[0]:.1f}" y2="{c[1]:.1f}"/>')
    m = g.get("muesca")
    if m:
        m0, m1, z = float(m[0]), float(m[1]), z + .01
        if largo_x:
            c0, c1 = (y0, y0 + .4 * (y1 - y0)) if y0 <= W - y1 else (y1 - .4 * (y1 - y0), y1)
            poly = [P(m0, c0, z), P(m1, c0, z), P(m1, c1, z), P(m0, c1, z)]
        else:
            c0, c1 = (x0, x0 + .4 * (x1 - x0)) if x0 <= L - x1 else (x1 - .4 * (x1 - x0), x1)
            poly = [P(c0, m0, z), P(c1, m0, z), P(c1, m1, z), P(c0, m1, z)]
        partes.append(f'<polygon class="hueco" points="{_pts(poly)}"/>')
    return "".join(partes)


MARCADORES = ('<defs>'
              '<marker id="punta" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path class="punta" d="M0 0L10 5L0 10z"/></marker>'
              '<marker id="punta-activa" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path class="punta activa" d="M0 0L10 5L0 10z"/></marker>'
              '</defs>')


def svg_conjunto(lam: dict, modelo: dict, *, svg_id: str, etiqueta: str, con_mas: bool = False, flujo: bool = False,
                 recoger: list | None = None) -> str:
    """SVG de la lámina del nivel 1. con_mas marca con «+» las piezas que se abren en el nivel 2; flujo
    añade las flechas de las relaciones entre raíces y la de entrada desde fuera de la frontera.
    recoger, si se pasa, acumula los puntos dibujados (sirve para encuadrar)."""
    cj, S = lam["cj"], lam["S"]
    P = proyector(S, *lam["desplazamiento"])
    placa = cj["placa"]
    L, W, G = float(placa["largo"]), float(placa["ancho"]), float(placa.get("grosor", 1))
    max_orden = max((q["orden"] for q in cj["resto"]), default=1)
    hijos = {p.get("padre") for p in modelo["piezas"] if p.get("padre")}
    pts = recoger if recoger is not None else []
    base, bp = cj["base"], cj["base"]["pieza"]

    # La base: no sube; su número va en un hueco cerca de la esquina más próxima
    b = base["unidades"][0]
    pts += silueta(P, b)
    cuerpo = [f'<title>{_esc(bp["nombre"])}</title>', _caja_svg(P, b)]
    for ag in placa.get("agujeros") or []:
        u, v = P(float(ag[0]), float(ag[1]), .01)
        r = float(ag[2]) * S
        cuerpo.append(f'<ellipse class="hueco" cx="{u:.1f}" cy="{v:.1f}" rx="{r * math.sqrt(1.5):.1f}" ry="{r * math.sqrt(.5):.1f}"/>')
    badge, pb = _badge(P, *base["centro_numero"], 0, base["orden"])
    pts += pb
    cuerpo.append(badge)
    g_base = (f'<g class="pieza k-pcb" data-id="{_esc(base["id"])}" role="button" tabindex="0" '
              f'aria-label="{_esc(str(base["orden"]) + ". " + bp["nombre"])}" style="--lift:0">' + "".join(cuerpo) + "</g>")
    rotulo = (placa.get("rotulo") or "{nombre} · {ancho} × {largo} {unidad}").format(
        nombre=bp["nombre"], ancho=num(W), largo=num(L), grosor=num(G), unidad=cj["unidad"])
    cu, cv = P(L, W, -G)
    cota = f'<text class="cota" x="{cu - 12:.1f}" y="{cv + 22:.1f}" text-anchor="end">{_esc(rotulo)}</text>'
    pts += [(cu - 12 - _ancho_texto(rotulo, 12), cv + 27), (cu, cv + 27)]

    rastros, piezas = [], []
    for q in cj["resto"]:
        p, lift = q["pieza"], lam["alzas"][q["id"]]
        mult = p.get("cantidad") if p.get("cantidad") not in (None, 1) else None
        aria = f'{q["orden"]}. {p["nombre"]}' + (f" ×{mult}" if mult else "")
        cuerpo, ras = [f'<title>{_esc(p["nombre"])}</title>'], []
        for u_ in q["unidades"]:
            ras.append(_ras(P, u_, lift))
            cuerpo.append(_caja_svg(P, u_))
            if q["forma"] == "conector":
                cuerpo.append(_detalle_conector(P, q["geo"], u_, L, W))
            for dz in (0, lift):
                pts += subir(silueta(P, u_), dz)
        cx, cy = q["centro"]
        badge, pb = _badge(P, cx, cy, q["arriba"], q["orden"], mult)
        cuerpo.append(badge)
        for dz in (0, lift):
            pts += subir(pb, dz)
        if con_mas and q["id"] in hijos:
            mu = max(x for x, _ in pb) + 16  # el borde del círculo, a 8 px del «×n»
            mv = P(cx, cy, q["arriba"])[1] - BADGE_PALO - BADGE_R
            cuerpo.append(f'<g class="marca-mas"><circle cx="{mu:.1f}" cy="{mv:.1f}" r="8"/>'
                          f'<path d="M{mu - 4:.1f} {mv:.1f}h8M{mu:.1f} {mv - 4:.1f}v8"/></g>')
            pts += [(mu + 9, mv - lift - 9), (mu + 9, mv + 9)]
        estilo = f"--lift:{lift};--retraso:{max_orden - q['orden']}"
        clase = "k-oro" if q["forma"] == "conector" else "k-chip"
        rastros.append(f'<g class="rastro" data-id="{_esc(q["id"])}" style="{estilo}">' + "".join(ras) + "</g>")
        piezas.append(f'<g class="pieza {clase}" data-id="{_esc(q["id"])}" role="button" tabindex="0" '
                      f'aria-label="{_esc(aria)}" style="{estilo}">' + "".join(cuerpo) + "</g>")

    flechas = ""
    if flujo:
        pf = lam["p_flujo"]
        por_id = {q["id"]: q for q in [base] + cj["resto"]}
        capa = []
        for r in modelo.get("relaciones") or []:
            if r.get("de") not in por_id or r.get("a") not in por_id:
                continue
            a, c_ = _centro(lam, P, por_id[r["de"]], pf), _centro(lam, P, por_id[r["a"]], pf)
            ctrl = ((a[0] + c_[0]) / 2, min(a[1], c_[1]) - (60 + .25 * abs(c_[0] - a[0])))
            mid = ((a[0] + 2 * ctrl[0] + c_[0]) / 4, (a[1] + 2 * ctrl[1] + c_[1]) / 4 - 10)
            et = r.get("etiqueta") or ""
            datos = f'data-de="{_esc(r["de"])}" data-a="{_esc(r["a"])}"'
            capa.append(f'<path class="flecha" {datos} d="M{a[0]:.1f} {a[1]:.1f} Q{ctrl[0]:.1f} {ctrl[1]:.1f} {c_[0]:.1f} {c_[1]:.1f}" marker-end="url(#punta)"/>'
                        f'<text class="etiqueta" {datos} x="{mid[0]:.1f}" y="{mid[1]:.1f}">{_esc(et)}</text>')
            ancho = _ancho_texto(et, 14) / 2
            pts += [a, c_, (mid[0] - ancho, mid[1] - 14), (mid[0] + ancho, mid[1] + 4)]
        primero = (modelo.get("flujo") or [None])[0]
        if primero in por_id:
            c_ = _centro(lam, P, por_id[primero], pf)
            a = (c_[0] - 44, c_[1] - 150)
            entrada = modelo.get("flujo_entrada")
            txt = f"desde {entrada} · fuera de la frontera" if entrada else "desde fuera de la frontera"
            tx, ty = a[0] - 28, a[1] - 12
            capa.append(f'<path class="flecha externa" data-de="" data-a="{_esc(primero)}" '
                        f'd="M{a[0]:.1f} {a[1]:.1f} Q{a[0] - 6:.1f} {c_[1] - 30:.1f} {c_[0]:.1f} {c_[1]:.1f}" marker-end="url(#punta)"/>'
                        f'<text class="etiqueta fija" data-de="" data-a="{_esc(primero)}" x="{tx:.1f}" y="{ty:.1f}">{_esc(txt)}</text>')
            pts += [a, (tx, ty - 14), (tx + _ancho_texto(txt, 14), ty + 4)]
        flechas = '<g class="flechas">' + "".join(capa) + "</g>" + MARCADORES

    vb = lam.get("viewbox", (0, 0, 100, 100))
    estilo_svg = f' style="--p:{lam["p_flujo"]}"' if flujo else ""
    return (f'<svg id="{_esc(svg_id)}" viewBox="{vb[0]} {vb[1]} {vb[2]} {vb[3]}" role="group" aria-label="{_esc(etiqueta)}"{estilo_svg}>'
            + cota + g_base + '<g class="rastros">' + "".join(rastros) + '</g><g class="piezas">' + "".join(piezas) + "</g>"
            + flechas + "</svg>")


# ---------- subconjuntos: capas apiladas ----------

def lamina_subconjunto(modelo: dict, padre: str) -> dict:
    """Capas de un subconjunto, de abajo arriba. La de abajo no sube; cada una sube sobre la anterior un
    cuarto largo del alto de la huella en pantalla (26 %, entre 50 y 110 px): asoma la franja de la de
    abajo y, como la página las pinta translúcidas, el resto se ve a través."""
    geo = modelo["geometria"]
    sub = geo["subconjuntos"][padre]
    hx0, hx1 = _rango(sub["huella"]["x"])
    hy0, hy1 = _rango(sub["huella"]["y"])
    S = ANCHO_CAPAS / ((hx1 - hx0 + hy1 - hy0) * C30)
    nombres = {p["id"]: p for p in modelo["piezas"]}
    capas = []
    for cid, g in sub["piezas"].items():
        x0, x1 = _rango(g.get("x", (hx0, hx1)))
        y0, y1 = _rango(g.get("y", (hy0, hy1)))
        z0, z1 = _rango(g["z"])
        capas.append({"id": cid, "pieza": nombres[cid], "geo": g, "caja": (x0, y0, x1, y1, z0, z1)})
    capas.sort(key=lambda c: c["caja"][4])
    hueco = round(min(110, max(50, 0.26 * (hx1 - hx0 + hy1 - hy0) * 0.5 * S)))
    for k, c in enumerate(capas):
        c["numero"], c["lift"] = k + 1, k * hueco
    lam = {"padre": padre, "pieza": nombres[padre], "S": S, "capas": capas, "hueco": hueco,
           "huella": (hx0, hy0, hx1, hy1), "unidad": geo.get("unidad", "mm"), "rotulo": sub.get("rotulo")}
    _encuadrar(lam, lambda pts: svg_subconjunto(lam, svg_id="", etiqueta="", recoger=pts))
    return lam


def _patron(P, patron: str, b: tuple) -> str:
    x0, y0, x1, y1, _, z1 = b
    z, partes = z1 + .01, []
    if patron == "rejilla":
        for i in range(1, 5):
            x = x0 + i * (x1 - x0) / 5
            a, c = P(x, y0, z), P(x, y1, z)
            partes.append(f'<line class="rejilla" x1="{a[0]:.1f}" y1="{a[1]:.1f}" x2="{c[0]:.1f}" y2="{c[1]:.1f}"/>')
        for i in range(1, 8):
            y = y0 + i * (y1 - y0) / 8
            a, c = P(x0, y, z), P(x1, y, z)
            partes.append(f'<line class="rejilla" x1="{a[0]:.1f}" y1="{a[1]:.1f}" x2="{c[0]:.1f}" y2="{c[1]:.1f}"/>')
    elif patron == "puntos":
        paso = min(x1 - x0, y1 - y0) / 7
        m = paso / 4
        x = x0 + paso * .75
        while x < x1 - paso * .3:
            y = y0 + paso * .75
            while y < y1 - paso * .3:
                partes.append(f'<polygon class="rejilla" points="{_pts([P(x - m, y - m, z), P(x + m, y - m, z), P(x + m, y + m, z), P(x - m, y + m, z)])}"/>')
                y += paso
            x += paso
    return "".join(partes)


def svg_subconjunto(lam: dict, *, svg_id: str, etiqueta: str, recoger: list | None = None) -> str:
    """SVG de un subconjunto abierto en capas. La clase «capas» le dice a la página que las apagadas van
    translúcidas (rayos X) en vez de lavadas."""
    P = proyector(lam["S"], *lam["desplazamiento"])
    pts = recoger if recoger is not None else []
    rastros, piezas = [], []
    for c in lam["capas"]:
        b, lift, p = c["caja"], c["lift"], c["pieza"]
        cuerpo = [f'<title>{_esc(p["nombre"])}</title>', _caja_svg(P, b), _patron(P, c["geo"].get("patron", ""), b)]
        cx, cy = (b[0] + b[2]) / 2, (b[1] + b[3]) / 2
        badge, pb = _badge(P, cx, cy, b[5], c["numero"])
        cuerpo.append(badge)
        for dz in (0, lift):
            pts += subir(silueta(P, b), dz) + subir(pb, dz)
        if lift:
            rastros.append(f'<g class="rastro" data-id="{_esc(c["id"])}" style="--lift:{lift}">' + _ras(P, b, lift) + "</g>")
        piezas.append(f'<g class="pieza k-chip" data-id="{_esc(c["id"])}" role="button" tabindex="0" '
                      f'aria-label="{_esc(str(c["numero"]) + ". " + p["nombre"])}" style="--lift:{lift}">' + "".join(cuerpo) + "</g>")
    hx0, hy0, hx1, hy1 = lam["huella"]
    rotulo = (lam["rotulo"] or "{nombre} · {ancho} × {largo} {unidad}, abierto en {n} capas").format(
        nombre=lam["pieza"]["nombre"], ancho=num(hx1 - hx0), largo=num(hy1 - hy0), unidad=lam["unidad"], n=len(lam["capas"]))
    cu, cv = P(hx1, hy1, lam["capas"][0]["caja"][4])
    cota = f'<text class="cota" x="{cu:.1f}" y="{cv + 26:.1f}" text-anchor="middle">{_esc(rotulo)}</text>'
    ancho = _ancho_texto(rotulo, 12) / 2
    pts += [(cu - ancho, cv + 30), (cu + ancho, cv + 14)]
    vb = lam.get("viewbox", (0, 0, 100, 100))
    return (f'<svg id="{_esc(svg_id)}" class="capas" viewBox="{vb[0]} {vb[1]} {vb[2]} {vb[3]}" role="group" aria-label="{_esc(etiqueta)}">'
            + '<g class="rastros">' + "".join(rastros) + '</g><g class="piezas">' + "".join(piezas) + "</g>" + cota + "</svg>")


# ---------- informe por línea de comandos ----------

def informe(modelo: dict) -> dict:
    lam = lamina_conjunto(modelo)
    subs = {}
    for padre in (modelo["geometria"].get("subconjuntos") or {}):
        ls = lamina_subconjunto(modelo, padre)
        subs[padre] = {"escala": round(ls["S"], 2), "hueco": ls["hueco"], "alzas": {c["id"]: c["lift"] for c in ls["capas"]},
                       "viewbox": ls["viewbox"]}
    return {"escala": round(lam["S"], 3), "base": lam["base"], "escalon": lam["escalon"], "alzas": lam["alzas"],
            "viewbox": lam["viewbox"], "oclusiones": lam["oclusiones"], "subconjuntos": subs}


def _utf8_stdout() -> None:
    # La consola de Windows es cp1252: sin esto, «» y acentos salen rotos en stdout y stderr.
    for flujo in (sys.stdout, sys.stderr):
        try:
            flujo.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
        except Exception:  # pragma: no cover
            pass


def main(argv: list[str]) -> int:
    _utf8_stdout()
    if len(argv) != 2 or argv[1] in {"-h", "--help"}:
        print(__doc__.strip(), file=sys.stdout if len(argv) == 2 else sys.stderr)
        return 0 if len(argv) == 2 else 2
    ruta = Path(argv[1])
    try:
        modelo = json.loads(ruta.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as ex:
        print(f"ERROR: no se pudo leer {ruta}: {ex}", file=sys.stderr)
        return 2
    if modelo.get("tipo") != "fisico" or not isinstance(modelo.get("geometria"), dict):
        print("ERROR: hace falta un modelo de tipo «fisico» con bloque «geometria» (references/interactivo.md). "
              "Pasar antes por validar_modelo.py.", file=sys.stderr)
        return 2
    try:
        r = informe(modelo)
    except (KeyError, StopIteration, TypeError, ValueError, IndexError) as ex:
        print(f"ERROR: geometría incompleta ({type(ex).__name__}: {ex}). validar_modelo.py dice qué falta.", file=sys.stderr)
        return 2
    print(json.dumps(r, ensure_ascii=False, indent=2))
    for o in r["oclusiones"]:
        print(f"AVISO: «{o['tapada']}» queda tapada por {o['por']} en el paso {o['estado']} del desmontaje", file=sys.stderr)
    return 1 if r["oclusiones"] else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
