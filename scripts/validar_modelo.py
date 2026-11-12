"""Valida un modelo de despiece (modelo.json) antes de dibujar o ensamblar.

Usage: python -I validar_modelo.py MODELO.json

Comprueba lo que el método exige y que, sin guía, se salta (E = error, A = aviso):
  E  JSON válido con objeto, tipo (fisico|proceso|sistema|idea), pregunta_foco (termina en «?»), lector
  E  nivel0.titulo y nivel0.frontera presentes; el título afirma algo (no «Qué es…», no termina en «:»)
  E  piezas con id único, nombre, funcion y fuente (o supuesto: true); padre existente y sin ciclos
  E  raíces: 2–7 (A si son 2); hijos por padre: 2–7 (una pieza con un solo hijo no se despieza)
  E  tipo fisico: orden (o su alias orden_montaje) entero en las raíces; proceso/sistema: flujo con ≥ 3 ids
  E  orden repetido entre hermanas, u orden y orden_montaje distintos en la misma pieza (A si es en otro tipo y
     solo unas raíces lo llevan); rol y forma conocidos; eje, un texto corto
  A  más de una pieza con rol «base» entre hermanas; raíces sin rol ni forma fuera del tipo fisico
  E  relaciones con de/a existentes y tipo conocido
  E  feynman con exactamente 3 frases; prediccion con pregunta (termina en «?») y respuesta
  A  figuras: > 6 piezas nuevas (E si > 9), título no afirmativo, skill desconocida, nivel > profundidad
  A  funcion > 125 caracteres (la figura muestra dos líneas y recorta el resto); nombre > 40
  A  sin malentendidos; sin figuras; piezas sin ninguna figura que las muestre
  E  figuras[].destacada fuera de las piezas de esa figura
  E  prediccion.opciones: 2–4 textos, con correcta (índice desde 0) dentro de rango
  A  flujo: un paso al que no le llega ninguna relación desde los anteriores; flujo_entrada fuera de nivel0.fuera
  Con «geometria» (página interactiva, ver references/interactivo.md):
  E  solo en tipo fisico (A si no); placa con largo y ancho > 0; cada raíz con su entrada y solo raíces;
     forma conocida; una sola «placa», y es la de menor orden_montaje; rangos [a, b] con a < b; alto > 0;
     unidades = cantidad; dos piezas que ocupan el mismo volumen; subconjuntos de raíces con hijos, con
     huella, z de cada hija y patrón conocido; rótulos con huecos {…} que no existen
  A  pieza fuera de la placa; cantidad > 1 sin unidades; «lift» escrito a mano (se calcula); raíz con hijos
     sin subconjunto o hija sin geometría (no se dibujan); paso del flujo que no es raíz; nivel 3 (no se dibuja)

Salida (stdout, JSON): {"ok", "errores": [...], "avisos": [...], "metricas": {...}}
Códigos de salida: 0 sin errores · 1 hay errores · 2 argumentos o fichero inválidos.
Ejemplo:
  python -I validar_modelo.py despiece/modelo.json
"""
from __future__ import annotations

import json
import re
import string
import sys
from pathlib import Path

TIPOS = {"fisico", "proceso", "sistema", "idea"}
TIPOS_RELACION = {"flujo", "contiene", "depende", "controla", "dato", "energia", "causa"}
SKILLS_DIBUJO = {"diagram-design", "diagrama-microsoft-learn", "grafico-interactivo", "explosionado", "propio", "ninguna"}
FORMAS = {"placa", "chip", "conector", "caja"}  # geometria.piezas[*].forma: la página interactiva
# piezas[*].forma: la silueta de la vista explotada (explosionado.py)
FORMAS_FIGURA = {"placa", "chip", "conector", "modulo", "carcasa", "disipador", "cable", "capa"}
# piezas[*].rol: el papel abstracto, que elige la silueta sin saber del dominio
ROLES = {"base", "etapa", "capa", "componente", "interfaz", "enlace", "contenedor", "limite", "regulador", "bloque"}
PATRONES = {"rejilla", "puntos"}
NO_AFIRMATIVO = re.compile(
    r"^\s*(qu[eé] es|definici[oó]n|introducci[oó]n|visi[oó]n general|resumen|overview|descripci[oó]n)\b",
    re.IGNORECASE,
)


def _utf8_stdout() -> None:
    # La consola de Windows es cp1252: sin esto, «» y acentos salen rotos en stdout y stderr.
    for flujo in (sys.stdout, sys.stderr):
        try:
            flujo.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
        except Exception:  # pragma: no cover - consolas antiguas
            pass


def orden_de(p: dict) -> int | None:
    """El orden de dependencia de una pieza: «orden», o «orden_montaje», su nombre antiguo."""
    v = p.get("orden", p.get("orden_montaje"))
    return v if isinstance(v, int) and not isinstance(v, bool) else None


def titulo_afirmativo(t: str) -> str | None:
    """Devuelve el motivo si el título no afirma nada; None si pasa."""
    if not isinstance(t, str) or not t.strip():
        return "vacío"
    if t.strip().endswith(":"):
        return "termina en «:»"
    if NO_AFIRMATIVO.search(t):
        return "empieza como una definición o un índice («Qué es…», «Introducción…»)"
    if len(t.split()) < 4:
        return "menos de 4 palabras: un rótulo, no una afirmación"
    return None


def validar(m: dict) -> tuple[list[str], list[str], dict]:
    E: list[str] = []
    A: list[str] = []

    for campo in ("objeto", "tipo", "pregunta_foco", "lector"):
        if not isinstance(m.get(campo), str) or not m[campo].strip():
            E.append(f"falta «{campo}» o está vacío")
    tipo = m.get("tipo")
    if tipo not in TIPOS:
        E.append(f"tipo «{tipo}» desconocido; usar uno de {sorted(TIPOS)}")
    pf = m.get("pregunta_foco", "")
    if isinstance(pf, str) and pf.strip() and not pf.strip().endswith("?"):
        E.append("pregunta_foco no termina en «?»: tiene que ser la pregunta que el lector quiere responder")

    profundidad = m.get("profundidad", 2)
    if not isinstance(profundidad, int) or isinstance(profundidad, bool) or not 1 <= profundidad <= 4:
        E.append("profundidad debe ser un entero entre 1 y 4 (más de 2, solo por la rama que responde a la pregunta foco)")
        profundidad = 2

    n0 = m.get("nivel0") or {}
    if not isinstance(n0, dict):
        E.append("nivel0 debe ser un objeto con titulo y frontera")
        n0 = {}
    motivo = titulo_afirmativo(n0.get("titulo", ""))
    if motivo:
        E.append(f"nivel0.titulo no afirma nada ({motivo})")
    if not isinstance(n0.get("frontera"), str) or not n0["frontera"].strip():
        E.append("nivel0.frontera vacía: hay que decir dónde empieza y termina el objeto")

    piezas = m.get("piezas")
    if not isinstance(piezas, list) or not piezas:
        E.append("piezas debe ser una lista no vacía")
        piezas = []
    ids: dict[str, dict] = {}
    for i, p in enumerate(piezas):
        if not isinstance(p, dict):
            E.append(f"piezas[{i}] no es un objeto")
            continue
        pid = p.get("id")
        if not isinstance(pid, str) or not pid.strip():
            E.append(f"piezas[{i}] sin id")
            continue
        if pid in ids:
            E.append(f"id de pieza repetido: «{pid}»")
            continue
        ids[pid] = p
        for campo in ("nombre", "funcion"):
            if not isinstance(p.get(campo), str) or not p[campo].strip():
                E.append(f"pieza «{pid}» sin «{campo}»")
        fuente = p.get("fuente")
        if not (isinstance(fuente, str) and fuente.strip()) and p.get("supuesto") is not True:
            E.append(f"pieza «{pid}» sin fuente y sin «supuesto: true»: no se explica de memoria")
        if isinstance(p.get("funcion"), str) and len(p["funcion"]) > 125:
            A.append(f"pieza «{pid}»: funcion de {len(p['funcion'])} caracteres; la figura muestra dos líneas "
                     "(unos 125) y recorta el resto con «…»")
        if isinstance(p.get("nombre"), str) and len(p["nombre"]) > 40:
            A.append(f"pieza «{pid}»: nombre de {len(p['nombre'])} caracteres; acortarlo para que quepa en la figura")
        for campo in ("orden", "orden_montaje"):
            if campo in p and orden_de({campo: p[campo]}) is None:
                E.append(f"pieza «{pid}»: {campo} debe ser un entero (1 es lo primero, abajo en la figura)")
        if "orden" in p and "orden_montaje" in p and p["orden"] != p["orden_montaje"]:
            E.append(f"pieza «{pid}»: orden = {p['orden']} y orden_montaje = {p['orden_montaje']}; son el mismo campo, dejar solo «orden»")
        if "eje" in p and (not isinstance(p["eje"], str) or not p["eje"].strip()):
            E.append(f"pieza «{pid}»: eje debe ser un texto: qué ordena a sus hijas en su figura")
        elif isinstance(p.get("eje"), str) and len(p["eje"]) > 70:
            A.append(f"pieza «{pid}»: eje de {len(p['eje'])} caracteres; va en el subtítulo de su figura")
        if "rol" in p and p["rol"] not in ROLES:
            E.append(f"pieza «{pid}»: rol «{p['rol']}» desconocido; usar uno de {sorted(ROLES)}")
        if "forma" in p and p["forma"] not in FORMAS_FIGURA:
            E.append(f"pieza «{pid}»: forma «{p['forma']}» desconocida; usar una de {sorted(FORMAS_FIGURA)} o quitarla y poner un rol")

    # Jerarquía: padres existentes, sin ciclos, conteos por nivel.
    hijos: dict[str | None, list[str]] = {}
    for pid, p in ids.items():
        padre = p.get("padre")
        if padre is not None and padre not in ids:
            E.append(f"pieza «{pid}»: padre «{padre}» no existe")
            padre = None
        hijos.setdefault(padre, []).append(pid)
    for pid in ids:
        visto = set()
        cur: str | None = pid
        while cur is not None:
            if cur in visto:
                E.append(f"ciclo en la jerarquía de piezas pasando por «{pid}»")
                break
            visto.add(cur)
            cur = ids[cur].get("padre") if cur in ids else None
    raices = hijos.get(None, [])
    if len(raices) > 7:
        E.append(f"{len(raices)} piezas en el nivel 1: más de 7 no se retienen; agrupar en subconjuntos")
    elif len(raices) < 2 and ids:
        E.append("una sola pieza en el nivel 1: eso no es un despiece")
    elif len(raices) == 2:
        A.append("solo 2 piezas en el nivel 1: comprobar que la partición no esconde una tercera")
    for padre, hs in hijos.items():
        if padre is None:
            continue
        if len(hs) == 1:
            E.append(f"«{padre}» tiene un solo hijo («{hs[0]}»): o se funden o falta alguna pieza")
        elif len(hs) > 7:
            E.append(f"«{padre}» tiene {len(hs)} hijos: más de 7 no se retienen; agrupar")

    def nivel_de(pid: str) -> int:
        n, cur = 1, ids[pid].get("padre")
        while cur in ids:
            n += 1
            cur = ids[cur].get("padre")
        return n

    niveles = {pid: nivel_de(pid) for pid in ids}
    max_nivel = max(niveles.values(), default=0)
    if max_nivel > profundidad:
        A.append(f"hay piezas en el nivel {max_nivel} y profundidad={profundidad}: o se sube la profundidad o sobran niveles")

    if tipo == "fisico":
        for pid in raices:
            if orden_de(ids[pid]) is None:
                E.append(f"tipo fisico: la pieza «{pid}» necesita orden (entero); el desmontaje es el montaje al revés")
    elif raices and 0 < sum(orden_de(ids[pid]) is not None for pid in raices) < len(raices):
        A.append("orden en unas raíces y no en otras: la figura las ordena por el flujo o por el orden de escritura")
    for padre, hs in hijos.items():
        ordenes = [orden_de(ids[h]) for h in hs if orden_de(ids[h]) is not None]
        if len(ordenes) != len(set(ordenes)):
            donde = "las raíces" if padre is None else f"las hijas de «{padre}»"
            E.append(f"orden repetido entre {donde}: cada pieza ocupa un lugar en el eje")
        bases = [h for h in hs if ids[h].get("rol") == "base"]
        if len(bases) > 1:
            A.append(f"rol «base» en {bases}: la base es una, la que sostiene al resto")
    if tipo in TIPOS - {"fisico"}:
        sin_rol = [pid for pid in raices if "rol" not in ids[pid] and "forma" not in ids[pid]]
        if sin_rol:
            A.append(f"tipo {tipo}: las raíces {sin_rol} no tienen rol; la vista explotada las dibuja como bloque "
                     "genérico (rol: base, etapa, componente, interfaz, enlace, contenedor, regulador o bloque)")
    eje = m.get("eje")
    if eje is not None and (not isinstance(eje, str) or not eje.strip()):
        E.append("eje debe ser un texto: qué ordena el eje de la figura («el orden de montaje», «la cronología»…)")
    elif isinstance(eje, str) and len(eje) > 70:
        A.append(f"eje de {len(eje)} caracteres: va en el subtítulo de la figura, decirlo en pocas palabras")

    flujo = m.get("flujo") or []
    if not isinstance(flujo, list):
        E.append("flujo debe ser una lista de ids")
        flujo = []
    for fid in flujo:
        if fid not in ids:
            E.append(f"flujo: id «{fid}» no existe en piezas")
    if tipo in {"proceso", "sistema"} and len(flujo) < 3:
        E.append(f"tipo {tipo}: flujo necesita al menos 3 pasos; sin flujo no se puede «seguir la petición»")

    for i, r in enumerate(m.get("relaciones") or []):
        if not isinstance(r, dict):
            E.append(f"relaciones[{i}] no es un objeto")
            continue
        for extremo in ("de", "a"):
            if r.get(extremo) not in ids:
                E.append(f"relaciones[{i}]: «{extremo}» = «{r.get(extremo)}» no existe")
        if r.get("tipo") not in TIPOS_RELACION:
            E.append(f"relaciones[{i}]: tipo «{r.get('tipo')}» desconocido; usar uno de {sorted(TIPOS_RELACION)}")

    rels = [r for r in m.get("relaciones") or [] if isinstance(r, dict)]
    for k, fid in enumerate(flujo[1:], 1):
        if fid in ids and not any(r.get("a") == fid and r.get("de") in flujo[:k] for r in rels):
            A.append(f"flujo: a «{fid}» (paso {k + 1}) no le llega ninguna relación desde los pasos anteriores; "
                     "añadir la relación o reordenar el flujo")
    entrada = m.get("flujo_entrada")
    if entrada is not None:
        if not isinstance(entrada, str) or not entrada.strip():
            E.append("flujo_entrada debe ser un texto: lo que entra desde fuera de la frontera")
        elif n0.get("fuera") and entrada not in n0["fuera"]:
            A.append("flujo_entrada no está en nivel0.fuera: lo que entra viene de fuera de la frontera, nombrarlo igual")

    if not m.get("malentendidos"):
        A.append("sin malentendidos: ¿qué suele creer el lector que es falso? Es lo que más ayuda a entender")

    figuras = m.get("figuras") or []
    if not isinstance(figuras, list):
        E.append("figuras debe ser una lista")
        figuras = []
    if not figuras:
        A.append("sin figuras: el despiece es visual; al menos una por nivel mostrado")
    mostradas: set[str] = set()
    for i, f in enumerate(figuras):
        if not isinstance(f, dict):
            E.append(f"figuras[{i}] no es un objeto")
            continue
        motivo = titulo_afirmativo(f.get("titulo", ""))
        if motivo:
            A.append(f"figuras[{i}]: el título no afirma nada ({motivo}); el título dice lo que la figura demuestra")
        if f.get("skill") not in SKILLS_DIBUJO:
            A.append(f"figuras[{i}]: skill «{f.get('skill')}» desconocida; usar una de {sorted(SKILLS_DIBUJO)}")
        nivel = f.get("nivel")
        if not isinstance(nivel, int) or nivel < 0:
            E.append(f"figuras[{i}]: nivel debe ser un entero ≥ 0")
        elif nivel > profundidad:
            A.append(f"figuras[{i}]: nivel {nivel} por encima de profundidad={profundidad}")
        pz = f.get("piezas") or []
        desconocidas = [p for p in pz if p not in ids]
        if desconocidas:
            E.append(f"figuras[{i}]: piezas inexistentes {desconocidas}")
        nuevas = [p for p in pz if p not in mostradas]
        if len(nuevas) > 9:
            E.append(f"figuras[{i}]: {len(nuevas)} piezas nuevas; nadie retiene más de 9 en una figura")
        elif len(nuevas) > 6:
            A.append(f"figuras[{i}]: {len(nuevas)} piezas nuevas; el tope cómodo son 6")
        if f.get("destacada") is not None and f["destacada"] not in pz:
            E.append(f"figuras[{i}]: destacada «{f['destacada']}» no está entre las piezas de esa figura")
        mostradas.update(pz)
    sin_figura = [p for p in ids if p not in mostradas]
    if figuras and sin_figura:
        A.append(f"piezas que ninguna figura muestra: {sin_figura}")

    fey = m.get("feynman")
    if not isinstance(fey, list) or len(fey) != 3 or not all(isinstance(s, str) and s.strip() for s in fey):
        E.append("feynman debe ser una lista de exactamente 3 frases no vacías")
    else:
        for s in fey:
            if len(s) > 220:
                A.append(f"feynman: frase de {len(s)} caracteres; si no cabe en una línea y media, no está entendido")

    pred = m.get("prediccion") or {}
    if not isinstance(pred, dict) or not isinstance(pred.get("pregunta"), str) or not pred["pregunta"].strip():
        E.append("prediccion.pregunta vacía: hay que hacer predecir al lector antes de darle la respuesta")
    elif not pred["pregunta"].strip().endswith("?"):
        E.append("prediccion.pregunta no termina en «?»")
    if not isinstance(pred, dict) or not isinstance(pred.get("respuesta"), str) or not pred["respuesta"].strip():
        E.append("prediccion.respuesta vacía")
    if isinstance(pred, dict) and "opciones" in pred:
        op = pred["opciones"]
        if not isinstance(op, list) or not 2 <= len(op) <= 4 or not all(isinstance(o, str) and o.strip() for o in op):
            E.append("prediccion.opciones: entre 2 y 4 textos no vacíos")
        elif not isinstance(pred.get("correcta"), int) or isinstance(pred.get("correcta"), bool) or not 0 <= pred["correcta"] < len(op):
            E.append(f"prediccion.correcta: índice de la opción buena, de 0 a {len(op) - 1}")
    elif isinstance(pred, dict) and "correcta" in pred:
        A.append("prediccion.correcta sin opciones: no se usa")

    geo = m.get("geometria")
    if geo is not None:
        validar_geometria(geo, tipo, ids, raices, hijos, niveles, flujo, E, A)

    metricas = {
        "tipo": tipo,
        "piezas": len(ids),
        "raices": len(raices),
        "niveles": max_nivel,
        "profundidad": profundidad,
        "figuras": len(figuras),
        "supuestos": sum(1 for p in ids.values() if p.get("supuesto") is True),
        "pasos_flujo": len(flujo),
        "geometria": isinstance(geo, dict),
    }
    return E, A, metricas


def _rango(v) -> tuple[float, float] | None:
    """[a, b] numérico con a < b, o None."""
    if (isinstance(v, (list, tuple)) and len(v) == 2 and all(_numero(x) for x in v) and v[0] < v[1]):
        return float(v[0]), float(v[1])
    return None


def _numero(v) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _positivo(v) -> bool:
    return _numero(v) and v > 0


def _rotulo_malo(texto, permitidos: set[str]) -> str | None:
    """Nombre del primer hueco {…} que el rótulo no admite, o None."""
    try:
        campos = [c for _, c, _, _ in string.Formatter().parse(texto) if c is not None]
    except ValueError:
        return "llaves sin cerrar"
    return next((f"{{{c}}}" for c in campos if c not in permitidos), None)


def validar_geometria(geo, tipo, ids, raices, hijos, niveles, flujo, E: list[str], A: list[str]) -> None:
    """Reglas del bloque «geometria», el que dibuja la página interactiva (ensamblar.py --interactivo)."""
    if not isinstance(geo, dict):
        E.append("geometria debe ser un objeto con placa, piezas y, si hay nivel 2, subconjuntos")
        return
    if tipo != "fisico":
        A.append(f"geometria en un modelo de tipo {tipo}: --interactivo solo la usa en tipo fisico")
        return
    placa = geo.get("placa")
    largo = ancho = None
    if not isinstance(placa, dict) or not _positivo(placa.get("largo")) or not _positivo(placa.get("ancho")):
        E.append("geometria.placa necesita largo y ancho > 0 (en la unidad de geometria.unidad)")
    else:
        largo, ancho = float(placa["largo"]), float(placa["ancho"])
        if "grosor" in placa and not _positivo(placa["grosor"]):
            E.append("geometria.placa.grosor debe ser > 0")
        malo = _rotulo_malo(placa.get("rotulo") or "", {"nombre", "ancho", "largo", "grosor", "unidad"})
        if malo:
            E.append(f"geometria.placa.rotulo: {malo} no se puede rellenar; usar {{nombre}}, {{ancho}}, {{largo}}, {{grosor}} o {{unidad}}")
        for k, ag in enumerate(placa.get("agujeros") or []):
            if not (isinstance(ag, list) and len(ag) == 3 and all(_numero(x) and x >= 0 for x in ag)):
                E.append(f"geometria.placa.agujeros[{k}]: [x, y, radio] con números ≥ 0")

    gp = geo.get("piezas")
    if not isinstance(gp, dict):
        E.append("geometria.piezas debe ser un objeto {id de raíz: {forma, x, y, alto}}")
        gp = {}
    for pid in gp:
        if pid not in ids:
            E.append(f"geometria.piezas: «{pid}» no existe en piezas")
        elif pid not in raices:
            E.append(f"geometria.piezas: «{pid}» no es raíz; sus capas van en geometria.subconjuntos.{ids[pid].get('padre')}")
    faltan = [pid for pid in raices if pid not in gp]
    if faltan:
        E.append(f"geometria.piezas: faltan las raíces {faltan}; la vista isométrica las dibuja todas")

    cajas: dict[str, list[tuple]] = {}
    placas = []
    for pid, g in gp.items():
        if pid not in raices:
            continue
        if not isinstance(g, dict):
            E.append(f"geometria.piezas.{pid} debe ser un objeto")
            continue
        if "lift" in g:
            A.append(f"geometria.piezas.{pid}: «lift» se ignora; las alzas se calculan para que nada se tape")
        forma = g.get("forma", "caja")
        if forma not in FORMAS:
            E.append(f"geometria.piezas.{pid}: forma «{forma}» desconocida; usar una de {sorted(FORMAS)}")
            continue
        if forma == "placa":
            placas.append(pid)
            continue
        y = _rango(g.get("y"))
        if not y:
            E.append(f"geometria.piezas.{pid}: y debe ser [desde, hasta] con desde < hasta")
        if not _positivo(g.get("alto")):
            E.append(f"geometria.piezas.{pid}: alto debe ser > 0")
        z0 = g.get("z", 0)
        if not _numero(z0) or z0 < 0:
            E.append(f"geometria.piezas.{pid}: z (altura a la que empieza la pieza) debe ser un número ≥ 0")
            z0 = 0
        cantidad = ids[pid].get("cantidad")
        if g.get("unidades") is not None:
            uds = g["unidades"] if isinstance(g["unidades"], list) else []
            xs = [_rango(u) for u in uds]
            if not uds or not all(xs):
                E.append(f"geometria.piezas.{pid}: unidades debe ser una lista de [desde, hasta] en x, uno por unidad")
                xs = []
            elif isinstance(cantidad, int) and cantidad != len(uds):
                E.append(f"geometria.piezas.{pid}: {len(uds)} unidades y cantidad = {cantidad}; tienen que coincidir")
        else:
            x = _rango(g.get("x"))
            xs = [x] if x else []
            if not x:
                E.append(f"geometria.piezas.{pid}: x debe ser [desde, hasta] con desde < hasta (o unidades si son varias)")
            if isinstance(cantidad, int) and cantidad > 1:
                A.append(f"geometria.piezas.{pid}: cantidad = {cantidad} sin unidades; se dibuja una sola")
        if forma == "conector" and "muesca" in g and not _rango(g.get("muesca")):
            E.append(f"geometria.piezas.{pid}: muesca debe ser [desde, hasta] en y")
        if y and xs and _positivo(g.get("alto")):
            cajas[pid] = [(x[0], y[0], x[1], y[1], float(z0), float(z0) + float(g["alto"])) for x in xs]
            if largo is not None and any(b[0] < 0 or b[1] < 0 or b[2] > largo or b[3] > ancho for b in cajas[pid]):
                A.append(f"geometria.piezas.{pid}: se sale de la placa ({largo:g} × {ancho:g}); comprobar x e y")
    if len(placas) != 1:
        E.append(f"geometria.piezas: tiene que haber exactamente una pieza con forma «placa» (hay {len(placas)}): es la base que no sube")
    elif all(orden_de(ids[r]) is not None for r in raices):
        primera = min(raices, key=lambda r: orden_de(ids[r]))
        if primera != placas[0]:
            E.append(f"geometria: la placa «{placas[0]}» tiene que ser la primera en orden (ahora lo es «{primera}»)")
    lista = sorted(cajas)
    for i, a in enumerate(lista):
        for b in lista[i + 1:]:
            if any(min(p[2], q[2]) > max(p[0], q[0]) and min(p[3], q[3]) > max(p[1], q[1])
                   and min(p[5], q[5]) > max(p[4], q[4]) for p in cajas[a] for q in cajas[b]):
                E.append(f"geometria.piezas: «{a}» y «{b}» ocupan el mismo volumen; separarlas en x/y o apilarlas con z")

    subs = geo.get("subconjuntos") or {}
    if not isinstance(subs, dict):
        E.append("geometria.subconjuntos debe ser un objeto {id de raíz con hijos: {huella, piezas}}")
        subs = {}
    for padre, sub in subs.items():
        if padre not in raices or not hijos.get(padre):
            E.append(f"geometria.subconjuntos: «{padre}» no es una raíz con hijos")
            continue
        if not isinstance(sub, dict):
            E.append(f"geometria.subconjuntos.{padre} debe ser un objeto")
            continue
        h = sub.get("huella")
        if not isinstance(h, dict) or not _rango(h.get("x")) or not _rango(h.get("y")):
            E.append(f"geometria.subconjuntos.{padre}: huella necesita x e y como [desde, hasta]")
        malo = _rotulo_malo(sub.get("rotulo") or "", {"nombre", "ancho", "largo", "unidad", "n"})
        if malo:
            E.append(f"geometria.subconjuntos.{padre}.rotulo: {malo} no se puede rellenar; usar {{nombre}}, {{ancho}}, {{largo}}, {{unidad}} o {{n}}")
        sp = sub.get("piezas") if isinstance(sub.get("piezas"), dict) else {}
        if not sp:
            E.append(f"geometria.subconjuntos.{padre}: piezas vacía; una entrada por hija con su z")
        for cid, g in sp.items():
            if cid not in hijos[padre]:
                E.append(f"geometria.subconjuntos.{padre}: «{cid}» no es hija de «{padre}»")
                continue
            if not isinstance(g, dict) or not _rango(g.get("z")):
                E.append(f"geometria.subconjuntos.{padre}.{cid}: z debe ser [desde, hasta] con desde < hasta")
                continue
            for eje in ("x", "y"):
                if eje in g and not _rango(g[eje]):
                    E.append(f"geometria.subconjuntos.{padre}.{cid}: {eje} debe ser [desde, hasta] (o quitarlo: ocupa la huella)")
            if "patron" in g and g["patron"] not in PATRONES:
                E.append(f"geometria.subconjuntos.{padre}.{cid}: patron «{g['patron']}» desconocido; usar uno de {sorted(PATRONES)}")
            if "lift" in g:
                A.append(f"geometria.subconjuntos.{padre}.{cid}: «lift» se ignora; las capas se separan solas")
        sin_geo = [c for c in hijos[padre] if c not in sp]
        if sp and sin_geo:
            A.append(f"geometria.subconjuntos.{padre}: las hijas {sin_geo} no tienen geometría y no se dibujan")
    for r in raices:
        if hijos.get(r) and r not in subs:
            A.append(f"geometria: «{r}» tiene hijos y no tiene subconjunto; la página interactiva no la abre en el nivel 2")
    no_raiz = [f for f in flujo if f in ids and f not in raices]
    if no_raiz:
        A.append(f"flujo: {no_raiz} no son raíces; en la página interactiva sus flechas no tienen dónde apoyarse")
    if any(n >= 3 for n in niveles.values()):
        A.append("hay piezas de nivel 3: la página interactiva dibuja hasta el nivel 2; el 3 queda solo en la estática")


def main(argv: list[str]) -> int:
    _utf8_stdout()
    if len(argv) != 2 or argv[1] in {"-h", "--help"}:
        print(__doc__.strip(), file=sys.stdout if len(argv) == 2 and argv[1] in {"-h", "--help"} else sys.stderr)
        return 0 if len(argv) == 2 and argv[1] in {"-h", "--help"} else 2
    ruta = Path(argv[1])
    if not ruta.is_file():
        print(f"ERROR: no existe {ruta}. Escribir primero el modelo (ver references/modelo.md).", file=sys.stderr)
        return 2
    try:
        modelo = json.loads(ruta.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"ERROR: {ruta} no es JSON válido: {e}. Revisar comas finales y comillas.", file=sys.stderr)
        return 2
    if not isinstance(modelo, dict):
        print("ERROR: el modelo debe ser un objeto JSON", file=sys.stderr)
        return 2
    E, A, metricas = validar(modelo)
    print(json.dumps({"ok": not E, "errores": E, "avisos": A, "metricas": metricas}, ensure_ascii=False, indent=2))
    return 1 if E else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
