# -*- coding: utf-8 -*-
"""Lector de los capitulos de reglas del SRD 5.2.1: todo lo que no es una ficha, un conjuro o un objeto magico
(como jugar, creacion de personajes, clases, origenes, dotes, equipo, la introduccion de los conjuros, de los objetos
y de los monstruos, el glosario de reglas y las herramientas del juego).

Convierte las lineas del PDF en una lista de bloques en orden de lectura:
    {"t": "h", "n": 0-3, "txt": ...}       titulo (0 = capitulo de 26 pt, 1 = 18 pt, 2 = 14 pt, 3 = 12 pt)
    {"t": "p", "txt": ...}                 parrafo, con <i>, <b> y <strong> dentro ("lead": rotulo inicial)
    {"t": "li", "txt": ...}                punto de una lista
    {"t": "tabla", "titulo": ..., "filas": [[...], ...]}   la primera fila es la cabecera (si la hay)
    {"t": "campos", "filas": [[rotulo, valor], ...]}        lineas "Rotulo: valor" (herramientas, trasfondos...)
    {"t": "recuadro", "titulo": ..., "bloques": [...]}      recuadro gris al margen
    {"t": "formula", "txt": ...}           linea destacada ("CA base = 10 + ...")
    {"t": "columnas", "items": [...]}      lista corta maquetada en columnas (acciones del glosario)
    {"t": "nota", "txt": ...}              nota al pie de una tabla

Las tablas, recuadros y notas flotan en la maqueta: si caen en mitad de un parrafo, el parrafo sigue y ellas van
detras.
"""
import re

from conjuros import marcar
from marcas import a_html, sin_marcas, unir_html
from srd import en_paginas, limpia, rango, une

NIVEL_TITULO = {26.0: 0, 23.0: 0, 18.0: 1, 14.0: 2, 12.0: 3}
FIN_ROTULO = (".", ":", ".”", ":”", ".»", ":»", "?”")  # el rotulo acaba en punto o dos puntos ("“You.”")
BASE_X = {0: 63.0, 1: 313.5}


def tam(r, size, tol=0.06):
    return abs(r["size"] - size) < tol


def es_titulo(r):
    return r["font"] == "GillSans-SemiBold" and round(r["size"], 1) in NIVEL_TITULO


def es_titulo_tabla(r):
    return r["font"] == "GillSans-SemiBold" and tam(r, 10.5)


def es_texto(r):
    """Texto corrido: Cambria de 10 (9,5 en el frances)."""
    return r["font"].startswith("Cambria") and (tam(r, 10.0) or tam(r, 9.5))


def es_recuadro(r):
    """Recuadro: titulo en versalitas (GillSans-Bold-SC700 7,7) y texto en GillSans de 9 (el de "Running a
    Monster" del ingles va en ScalaSansOffc de 10)."""
    return (r["font"].startswith("GillSans") and tam(r, 9.0)) or r["font"].startswith("ScalaSans") or \
        (r["font"].startswith("GillSans") and "SC700" in r["font"] and r["size"] < 9)


def es_titulo_recuadro(r):
    return "SC700" in r["font"] and r["size"] < 9


def es_campo(r):
    """Linea "Rotulo: valor" en GillSans (9,5 en las herramientas, 10 en trasfondos y especies)."""
    if not r["font"].startswith("GillSans") or not (tam(r, 9.5) or tam(r, 10.0)) or not r["spans"]:
        return False
    sp = r["spans"][0]
    # al margen de la columna, o el segundo campo de la linea ("Peso: 4 kg" a la derecha de "Caracteristica:");
    # un rotulo con dos puntos dentro de una celda de tabla ("Gesinnung:" en la tabla aleman de objetos conscientes)
    # no es un campo
    d = dx(r)
    return ("SemiBold" in sp[1] or "Bold" in sp[1]) and limpia(sp[0]).endswith(":") and len(limpia(sp[0])) > 2 \
        and (d < 4 or d > 60)


def sigue_campo(prev, r):
    """Linea que sigue el valor de un campo: GillSans sin rotulo, con la sangria francesa del campo (8 pt), justo
    debajo de la anterior o arriba del todo de la columna siguiente ("cimer (25 GP, 10 lb.)...")."""
    if not r["font"].startswith("GillSans") or "SemiBold" in r["font"] or not 5 <= dx(r) <= 12:
        return False
    if (prev["p"], prev["col"]) == (r["p"], r["col"]):
        return 0 < r["yb"] - prev["yb"] < 14
    return r["yb"] < 75


def es_tabla(r):
    return r["font"].startswith("GillSans") and (tam(r, 9.2) or tam(r, 9.5)) and not es_campo(r)


def es_destacado(r):
    """GillSans de 10 sin rotulo: formulas y listas en columnas."""
    return r["font"].startswith("GillSans") and tam(r, 10.0) and not es_campo(r)


def es_nota(r):
    return r["font"].startswith("GillSans") and tam(r, 8.0)


def dx(r, base=None):
    return r["x"] - (base if base is not None else BASE_X[r["col"]])


class Parrafos:
    """Junta lineas de texto en parrafos y puntos de lista (la logica del lector de conjuros, con la sangria medida
    desde el margen que se le de)."""

    def __init__(self, es_rotulo):
        self.es_rotulo = es_rotulo
        self.par, self.tipo = None, "p"
        self.sigue_rotulo = False
        self.colgante = False
        self.salida = []

    def abierto(self):
        return self.par is not None

    def cerrar(self):
        if self.par:
            self.salida.append({"t": self.tipo, "txt": unir_html(self.par)})
        self.par = None

    def es_nuevo(self, r, base=None):
        """(nuevo, tipo) para la linea r sin tocar el estado."""
        t = r["t"]
        d = dx(r, base)
        vineta = t.lstrip().startswith("•")
        lead = self.es_rotulo(r["spans"]) and not self.sigue_rotulo
        if vineta:
            return True, "li"
        if lead or self.par is None:
            return True, "p"
        if 5 < d < 10:
            return (not self.colgante), "p"
        if d >= 10:
            return False, self.tipo
        if self.tipo == "li" and self.par and not re.search(r"[.:;!?]\W*$", re.sub(r"<[^>]+>", "", self.par[-1]).strip()):
            # punto de lista que sigue en la linea de abajo sin sangria (los ejemplos de encuentros del ingles:
            # "and 9 Stirges (25 XP" + "each), for 1,125 XP total"): la frase no ha acabado
            return False, "li"
        return (self.tipo == "li" or self.colgante), "p"

    def linea(self, r, base=None, marcas=None):
        nuevo, tipo = self.es_nuevo(r, base)
        d = dx(r, base)
        lead = self.es_rotulo(r["spans"]) and not self.sigue_rotulo
        if nuevo:
            self.colgante = lead and d < 5
        spans = [list(x) for x in r["spans"]]
        if r["t"].lstrip().startswith("•"):
            spans[0][0] = spans[0][0].lstrip().lstrip("•").lstrip("\t ")
            if not spans[0][0]:
                spans = spans[1:]
        if spans and spans[0][0].startswith("\t"):
            spans[0][0] = spans[0][0].lstrip("\t ")
        txt = a_html((marcas or marcar)(spans, lead or self.sigue_rotulo))
        if nuevo:
            self.cerrar()
            self.par, self.tipo = [txt], tipo
        else:
            self.par.append(txt)
        self.sigue_rotulo = (lead or self.sigue_rotulo) and rotulo_abierto(spans)
        return nuevo


def _negrita(font):
    return "Bold" in font


def rotulo_abierto(spans):
    """La linea es toda rotulo (negrita) y el rotulo no ha acabado: sigue en la linea de abajo
    ("2: Los jugadores describen lo que hacen sus" + "personajes.")."""
    llenos = [s for s in spans if s[0].strip()]
    if not llenos or not all(_negrita(s[1]) for s in llenos):
        return False
    return not llenos[-1][0].strip().endswith(FIN_ROTULO)


def rotulo_texto(spans):
    """Rotulo al principio de una linea de texto: negrita cursiva, o negrita que acaba en punto o dos puntos
    ("1:", "Etiquetas entre corchetes."), o una linea entera en negrita (el rotulo sigue en la de abajo)."""
    if not spans:
        return False
    txt, font = spans[0][0].strip(), spans[0][1]
    if "Cambria-BoldItalic" in font:
        return True
    if "Cambria-Bold" in font:
        if txt.endswith(FIN_ROTULO) or re.match(r"\d+[:.]", txt):
            return True
        k = 1
        while k < len(spans) and "Cambria-Bold" in spans[k][1] and "Italic" not in spans[k][1]:
            if spans[k][0].strip().endswith(FIN_ROTULO):
                return True
            k += 1
        return rotulo_abierto(spans)
    return False


def rotulo_recuadro(spans):
    return bool(spans) and ("GillSans-BoldItalic" in spans[0][1] or
                            ("ScalaSans" in spans[0][1] and "Bold" in spans[0][1]))


def marcar_recuadro(spans, en_rotulo=False):
    out = []
    for k, (txt, font, *_) in enumerate(spans):
        if "BoldItalic" in font or ("Bold" in font and k == 0):
            out.append(("b", txt))
        elif "Bold" in font:
            out.append(("strong", txt))
        elif "Italic" in font:
            out.append(("i", txt))
        else:
            out.append(("", txt))
    return out


def marcar_texto(spans, en_rotulo=False):
    """Como el de los conjuros, pero el rotulo en negrita puede ir en varios tramos y seguir en la linea de abajo:
    en una linea de rotulo, la negrita del principio es rotulo (<b>) y no una criatura citada (<strong>)."""
    out = marcar(spans)
    if en_rotulo:
        k = 0
        while k < len(spans) and ("Cambria-Bold" in spans[k][1] or not spans[k][0].strip()):
            out[k] = ("b", spans[k][0])
            if spans[k][0].strip().endswith(FIN_ROTULO) and not re.fullmatch(r"\d+[:.]", spans[k][0].strip()):
                break
            k += 1
    return out


def marcar_gill(spans, en_rotulo=False):
    out = []
    for txt, font, *_ in spans:
        if "Bold" in font:
            out.append(("b", txt))
        elif "Italic" in font:
            out.append(("i", txt))
        else:
            out.append(("", txt))
    return out


def _x(r, x):
    """x medida desde el margen de la columna en que esta la linea (una tabla seguida en la otra columna, o
    una tabla ancha cuyas celdas de la derecha se han pasado a la columna izquierda, conservan su x)."""
    return x - (BASE_X[0] if r.get("_ancha") else BASE_X[r["col"]])


def piezas(r):
    """Trozos de una linea separados por un hueco de mas de 6 pt: cada uno es una celda ("—  —  —" de los
    espacios de conjuro va en una sola linea del PDF; "Weapon Proficiencies" y su valor tambien)."""
    out = []
    for sp in r["spans"]:
        x0 = sp[4] if len(sp) > 4 else r["x"]
        x1 = sp[5] if len(sp) > 5 else r["x1"]
        if not sp[0].strip():
            continue
        if out and x0 - out[-1]["x1"] <= 4:
            out[-1]["tramos"].append(sp)
            out[-1]["x1"] = max(out[-1]["x1"], x1)
        else:
            out.append({"x0": x0, "x1": x1, "tramos": [sp]})
    for o in out:
        o["a"], o["b"] = _x(r, o["x0"]), _x(r, o["x1"])
        o["r"] = r
        o["p"], o["col"], o["yb"] = r["p"], 0 if r.get("_ancha") else r["col"], r["yb"]
        o["rot"] = all("SemiBold" in sp[1] and abs(sp[2] - 9.2) < 0.06 for sp in o["tramos"])
        o["html"] = a_html([("i" if "Italic" in sp[1] else ("b" if "SemiBold" in sp[1] and not o["rot"] else ""),
                             sp[0]) for sp in o["tramos"]])
    return out


def piezas_tabla(lineas):
    """Las piezas de una tira de lineas de tabla; de entrada son de cabecera ("cab") las de SemiBold 9,2."""
    pz = [t for r in lineas for t in piezas(r)]
    for t in pz:
        t["cab"] = t["rot"]
    return pz


def cabecera_entera(pz):
    """En una tabla normal (no de rotulos a la izquierda), la cabecera es todo lo que queda a la altura de su
    linea de SemiBold 9,2 mas baja o por encima de ella: el ingles pone "Weight" y "Cost" en SemiBold 9,5, y la
    tabla de terreno de viaje trae media cabecera en letra normal y en dos lineas ("CD para" / "forrajear")."""
    for clave in {(t["p"], t["col"]) for t in pz if t["rot"]}:
        rot = sorted(t["yb"] for t in pz if t["rot"] and (t["p"], t["col"]) == clave)
        arriba = abajo = rot[0]
        for y in rot[1:]:
            # el bloque de cabecera: lineas de SemiBold 9,2 seguidas desde la primera; una linea con letra normal
            # es ya una fila del cuerpo
            normal = any((t["p"], t["col"]) == clave and abs(t["yb"] - y) < 1.5 and
                         any("SemiBold" not in sp[1] for sp in t["tramos"]) for t in pz)
            if y - abajo > 16 or normal:
                break
            abajo = y
        for t in pz:
            if (t["p"], t["col"]) == clave:
                # lo que queda por debajo del bloque de cabecera es cuerpo aunque vaya en SemiBold 9,2 (el "1" de
                # la primera fila de la tabla de proposito especial del SRD espanol)
                t["cab"] = arriba - 26 < t["yb"] < abajo + 1.5
    return pz


def es_vertical(pz):
    """Tabla de rotulos a la izquierda (los atributos basicos de cada clase): los rotulos (SemiBold 9,2) bajan
    por la columna izquierda, todos a la misma x, y los valores van a su derecha."""
    rot = [t for t in pz if t["cab"]]
    val = [t for t in pz if not t["cab"]]
    if not val or len({(t["p"], t["col"], round(t["yb"])) for t in rot}) < 3:
        return False
    xs = [t["a"] for t in rot]
    alturas = sorted(t["yb"] for t in rot)
    return max(xs) - min(xs) < 3 and min(t["a"] for t in val) > max(t["b"] for t in rot) - 2 and \
        alturas[-1] - alturas[0] > 40


def tabla_vertical(pz):
    """Cada rotulo abre una fila y los valores desde su altura hasta el rotulo siguiente son su valor. Un rotulo de
    dos lineas sigue siendo uno si a la altura de su segunda linea no empieza otro valor."""
    rot = sorted((t for t in pz if t["cab"]), key=lambda t: (t["p"], t["col"], t["yb"]))
    val = sorted((t for t in pz if not t["cab"]), key=lambda t: (t["p"], t["col"], t["yb"], t["a"]))

    def empieza_valor(y, p, c):
        en = [v for v in val if (v["p"], v["col"]) == (p, c) and abs(v["yb"] - y) < 1.5]
        antes = [v for v in val if (v["p"], v["col"]) == (p, c) and 1.5 <= y - v["yb"] < 13.5]
        return bool(en) and not antes

    grupos = []
    for t in rot:
        g = grupos[-1] if grupos else None
        if g and (g[-1]["p"], g[-1]["col"]) == (t["p"], t["col"]) and t["yb"] - g[-1]["yb"] < 13.5 and \
                not empieza_valor(t["yb"], t["p"], t["col"]):
            g.append(t)
        else:
            grupos.append([t])
    filas_t = []
    for k, g in enumerate(grupos):
        y0 = g[0]["yb"] - 3
        sig = grupos[k + 1][0] if k + 1 < len(grupos) else None
        dentro = [v for v in val if (v["p"], v["col"]) == (g[0]["p"], g[0]["col"]) and v["yb"] >= y0 and
                  (sig is None or (sig["p"], sig["col"]) != (v["p"], v["col"]) or v["yb"] < sig["yb"] - 3)]
        filas_t.append([une([x["html"] for x in g]), unir_html([v["html"] for v in dentro])])
    return filas_t


def partir_tablas(lineas):
    """Una tira de lineas de tabla seguidas puede traer varias tablas (la misma seguida en la otra columna, con la
    cabecera repetida): una cabecera que llega despues de filas empieza otra. Devuelve listas de piezas."""
    pz = piezas_tabla(lineas)
    if es_vertical(pz):
        return [pz]
    partes, cur = [], []
    for r in lineas:
        mias = [t for t in pz if t["r"] is r]
        # filas de cuerpo de antes que no son media cabecera en letra normal justo encima de esta linea
        cuerpo_antes = any(not q["cab"] and ((q["p"], q["col"]) != (r["p"], 0 if r.get("_ancha") else r["col"])
                                             or r["yb"] - q["yb"] > 26) for q in cur)
        if mias and all(t["cab"] for t in mias) and cuerpo_antes:
            partes.append(cur)
            cur = []
        cur.extend(mias)
    if cur:
        partes.append(cur)
    return [cabecera_entera(p) for p in partes]


def construir_tablas(titulo, lineas):
    out = []
    for k, pz in enumerate(partir_tablas(lineas)):
        tit = titulo if k == 0 else None
        if not pz:
            continue
        p = min(t["p"] for t in pz)
        if es_vertical(pz):
            out.append({"t": "tabla", "titulo": tit, "vertical": True, "filas": tabla_vertical(pz), "p": p})
        else:
            out.append(dict({"t": "tabla", "titulo": tit}, **rejilla(pz), p=p))
    return out


def _columnas(trozos):
    """Columnas de una tabla: los intervalos [a, b] de las celdas que se solapan son la misma columna (las
    alineadas a la izquierda, a la derecha o al centro se solapan siempre con las de su columna)."""
    iv = sorted([t["a"], t["b"]] for t in trozos)
    cols = []
    for a, b in iv:
        if cols and a <= cols[-1][1] - 0.5:
            cols[-1][1] = max(cols[-1][1], b)
        else:
            cols.append([a, b])
    return cols


def _col_de(cols, a, b):
    """Columnas que cubre un intervalo: las que pisa en al menos la mitad de lo que mide la mas estrecha de las
    dos (un "Kosten" que roza el final de la columna de al lado no la cubre). Si no cubre ninguna, la que mas pisa,
    y si no pisa ninguna, la mas cercana."""
    solape = [max(0.0, min(b, x1) - max(a, x0)) for x0, x1 in cols]
    hits = [k for k, (x0, x1) in enumerate(cols) if solape[k] >= 0.5 * max(0.5, min(x1 - x0, b - a))]
    if hits:
        return hits
    if max(solape) > 0:
        return [max(range(len(cols)), key=lambda k: solape[k])]
    c = (a + b) / 2
    return [min(range(len(cols)), key=lambda k: min(abs(cols[k][0] - c), abs(cols[k][1] - c)))]


def rejilla(pz):
    """Tabla a partir de sus piezas: {"filas": [...], "sin_cabecera"?: True, "grupos"?: [[texto, desde, hasta]]}.

    Las columnas salen de las celdas de las filas con dos o mas celdas. La cabecera puede tener varias lineas: cada
    trozo va a la columna que pisa; uno que pisa varias es el titulo de un grupo de columnas ("Espacios de conjuro
    por cada nivel de conjuro"). En el cuerpo, una fila visual con algo en la primera columna y a mas de 13,5 pt de
    la anterior abre fila; si no, sigue la de arriba."""
    cab = [t for t in pz if t["cab"]]
    visuales, orden = {}, []
    for t in pz:
        if t["cab"]:
            continue
        key = (t["p"], t["col"], round(t["yb"]))
        if key not in visuales:
            visuales[key] = []
            orden.append(key)
        visuales[key].append(t)
    multi = [t for k in orden if len(visuales[k]) >= 2 for t in visuales[k]]
    cols = _columnas(multi or [t for k in orden for t in visuales[k]])
    if not cols:
        cols = _columnas(cab) or [[0, 1]]
    n = len(cols)
    if not cab and n == 4 and _mitades(cols, visuales, orden):
        # dos tablas sin cabecera una al lado de la otra (las abreviaturas del glosario): una detras de otra
        corte = (cols[1][1] + cols[2][0]) / 2
        izq = rejilla([t for t in pz if t["a"] < corte])
        der = rejilla([t for t in pz if t["a"] >= corte])
        return {"filas": izq["filas"] + der["filas"], "sin_cabecera": True}
    # cabecera
    cabecera, grupos = [[] for _ in range(n)], []
    for t in sorted(cab, key=lambda t: (t["yb"], t["a"])):
        ks = _col_de(cols, t["a"], t["b"])
        if len(ks) == 1 or not multi:
            # sin limpiar: une() necesita ver el guion blando del final ("Übungs­" + "bonus")
            cabecera[ks[0]].append(sin_marcas(t["html"]))
        else:
            grupos.append([limpia(sin_marcas(t["html"])), ks[0], ks[-1], t["yb"]])
    # un grupo partido en dos lineas ("Espacios de conjuro por cada nivel" + "de conjuro") es uno solo
    juntos = []
    for g in grupos:
        if juntos and juntos[-1][1] <= g[2] and g[1] <= juntos[-1][2] and 0 < g[3] - juntos[-1][3] < 14:
            juntos[-1] = [une([juntos[-1][0], g[0]]), min(juntos[-1][1], g[1]), max(juntos[-1][2], g[2]), g[3]]
        else:
            juntos.append(g)
    for g in juntos:  # sin las rayas de adorno ("——— Encounter Difficulty ———", "—Espacios de conjuro...—")
        g[0] = re.sub(r"^[—–\-\s]+|[—–\-\s]+$", "", g[0])
    # cuerpo
    filas_t, prev = [], None
    for key in orden:
        vs = sorted(visuales[key], key=lambda t: t["a"])
        asign = [(_col_de(cols, t["a"], t["b"]), t) for t in vs]
        en_primera = any(ks[0] == 0 for ks, _ in asign)
        nueva = en_primera and (not filas_t or prev is None or key[:2] != prev[:2] or key[2] - prev[2] > 13.5)
        if nueva or not filas_t:
            filas_t.append([[] for _ in range(n)])
        for ks, t in asign:
            filas_t[-1][ks[0]].append(t["html"])
        prev = key
    filas_txt = [[unir_html(c) if c else "" for c in f] for f in filas_t]
    # fila repetida en la maqueta (estoque y tridente en la tabla de armas del SRD italiano): fuera
    vistas, sin_rep = set(), []
    for f in filas_txt:
        clave = tuple(f)
        if sum(1 for c in f if c.strip()) >= 3 and clave in vistas:
            continue
        vistas.add(clave)
        sin_rep.append(f)
    filas_txt = sin_rep
    out = {}
    if cab:
        cab_txt = [une(c) for c in cabecera]
        cab_txt = [re.sub(r"^[—–\-\s]+|[—–\-\s]+$", "", c) if re.search(r"\w", c) else c for c in cab_txt]
        out["filas"] = [cab_txt] + filas_txt
    else:
        out["filas"] = filas_txt
        out["sin_cabecera"] = True
    if juntos:
        out["grupos"] = [g[:3] for g in juntos]
    # tablas maquetadas en dos mitades iguales (dragon | tipo de dano | dragon | tipo de dano): una sola
    if cab and n % 2 == 0 and n >= 4 and out["filas"][0][:n // 2] == out["filas"][0][n // 2:]:
        m = n // 2
        izq = [f[:m] for f in filas_txt]
        der = [f[m:] for f in filas_txt if any(x.strip() for x in f[m:])]
        out["filas"] = [out["filas"][0][:m]] + izq + der
    return out


def _mitades(cols, visuales, orden):
    """Cuatro columnas sin cabecera con la primera y la tercera en negrita: dos mitades de una misma lista."""
    neg = {0: [], 2: []}
    for key in orden:
        for t in visuales[key]:
            ks = _col_de(cols, t["a"], t["b"])
            if ks[0] in neg:
                neg[ks[0]].append(all("Bold" in sp[1] for sp in t["tramos"]))
    return all(neg[0]) and all(neg[2]) and neg[0] and neg[2]


def recolocar_tablas_anchas(rows):
    """Tablas que ocupan el ancho de la pagina (las de rasgos de cada clase): sus celdas de la derecha caen en la
    columna derecha y el orden de lectura las separaria de su fila. Una cabecera de tabla en la columna derecha a la
    misma altura que otra de la izquierda, distinta de ella y sin titulo propio encima, es la mitad derecha de la
    misma tabla: sus filas pasan a la columna izquierda (con su x, marcadas "_ancha")."""
    out = [dict(r) for r in rows]
    por_pagina = {}
    for r in out:
        por_pagina.setdefault(r["p"], []).append(r)
    movidas = []
    for p, rs in por_pagina.items():
        c0 = [r for r in rs if r["col"] == 0 and r["font"] == "GillSans-SemiBold" and tam(r, 9.2)]
        for h0 in c0:
            col1 = sorted((r for r in rs if r["col"] == 1), key=lambda r: r["yb"])
            en1 = [r for r in col1 if es_fila_tabla(r) and abs(r["yb"] - h0["yb"]) < 1.2]
            if not en1:
                continue
            # la cabecera de la derecha puede tener lineas por encima ("CD para" sobre "forrajear")
            arriba = min(r["yb"] for r in en1)
            for r in reversed([r for r in col1 if r["yb"] < arriba - 0.5]):
                if es_fila_tabla(r) and arriba - r["yb"] < 14:
                    arriba = r["yb"]
                else:
                    break
            encima = [r for r in col1 if r["yb"] < arriba - 0.5]
            previa = encima[-1] if encima else None
            if previa is not None and es_titulo_tabla(previa) and arriba - previa["yb"] < 26:
                continue  # la de la derecha tiene su propio titulo: es otra tabla
            if previa is not None and es_fila_tabla(previa) and arriba - previa["yb"] < 22:
                continue  # la de la derecha viene de antes: es otra tabla que sigue
            # una tabla ancha empieza con su titulo encima de la mitad izquierda; dos tablas que siguen de la pagina
            # anterior una en cada columna (multiclase y bagatelas en el SRD frances) no tienen titulo aqui
            arriba0 = min(r["yb"] for r in c0 if -1.2 < h0["yb"] - r["yb"] < 30)
            if not any(es_titulo_tabla(r) and r["col"] == 0 and 0 < arriba0 - r["yb"] < 30 for r in rs):
                continue
            t1 = sorted(limpia(r["t"]) for r in col1 if es_fila_tabla(r) and arriba - 0.5 <= r["yb"] <= h0["yb"] + 1.2)
            t0 = sorted(limpia(r["t"]) for r in c0 if -1.2 < h0["yb"] - r["yb"] < 30)
            if t1 == t0:
                continue  # la misma tabla seguida en la otra columna, o dos tablas iguales una al lado de otra
            fin = _fin_tabla([r for r in rs if r["col"] == 0], h0)
            for r in col1:
                if r["yb"] < arriba - 0.5:
                    continue
                if r["yb"] > fin + 13 or not es_fila_tabla(r):
                    break
                r["col"] = 0
                r["_ancha"] = True
            movidas.append((p, limpia(h0["t"]), limpia(en1[0]["t"])))
        # lineas de cabecera de la mitad derecha que quedan por encima de lo ya pasado a la izquierda (aqui o en
        # srd.py): "Espacios de conjuro por cada nivel" sobre "1 2 3...", "Movimento" sobre "senza armatura"
        anchas = [r for r in rs if r.get("_ancha") and r["font"] == "GillSans-SemiBold" and tam(r, 9.2)]
        if anchas:
            arriba = min(r["yb"] for r in anchas)
            for r in sorted((r for r in rs if r["col"] == 1 and r["yb"] < arriba), key=lambda r: -r["yb"]):
                if es_fila_tabla(r) and arriba - r["yb"] < 16:
                    r["col"] = 0
                    r["_ancha"] = True
                    arriba = r["yb"]
                else:
                    break
    out.sort(key=lambda r: (r["p"], r["col"], r["yb"], r["x"]))
    return out, movidas


def es_fila_tabla(r):
    return r["font"].startswith("GillSans") and (tam(r, 9.2) or tam(r, 9.5)) and not es_campo(r)


def _fin_tabla(rs, h0):
    """Ultima linea de la tabla de la columna izquierda que empieza en la cabecera h0."""
    fin = prev = h0["yb"]
    for r in sorted((r for r in rs if r["yb"] >= h0["yb"] - 0.5), key=lambda r: r["yb"]):
        if not (r["font"].startswith("GillSans") and (tam(r, 9.2) or tam(r, 9.5))):
            if r["yb"] > prev + 1:
                break
            continue
        if r["yb"] - prev > 30:
            break
        fin = prev = r["yb"]
    return fin


def campos(lineas):
    """Lineas "Rotulo: valor" a pares; las lineas sin rotulo siguen el valor de arriba."""
    filas_t = []
    for r in lineas:
        sp = r["spans"]
        if es_campo(r):
            rot = limpia(sp[0][0]).rstrip(":").strip()
            filas_t.append([rot, [a_html(marcar_gill(sp[1:]))]])
        elif filas_t:
            filas_t[-1][1].append(a_html(marcar_gill(sp)))
    return {"t": "campos", "filas": [[r, unir_html(v)] for r, v in filas_t]}


def destacado(lineas):
    """Lineas en GillSans de 10 sin rotulo de campo. Pueden ser:
    - formulas ("CA base = 10 + ..."), a veces con el rotulo en una columna y la formula en otra, o dos formulas
      una al lado de la otra, o centradas y partidas en dos lineas;
    - listas con vinetas;
    - la lista de abreviaturas del glosario ingles (abreviatura en negrita y su significado);
    - listas cortas de terminos, en una o varias columnas.
    Cada trozo que no empieza un elemento sigue al elemento de su misma fila que tiene a la izquierda o, si no,
    al de encima con el que se solapa."""
    pz = sorted((t for r in lineas for t in piezas(r)), key=lambda t: (t["p"], t["col"], t["yb"], t["a"]))
    if not pz:
        return []
    for t in pz:
        t["html"] = a_html(marcar_gill(t["tramos"]))
        t["txt"] = limpia("".join(sp[0] for sp in t["tramos"]))
    negrita0 = lambda t: "Bold" in t["tramos"][0][1]
    todo = " ".join(t["txt"] for t in pz)
    if "=" in todo:
        modo = "formula"
        empieza = lambda t: negrita0(t) and not any(o is not t and o["yb"] == t["yb"] and o["b"] < t["a"] and
                                                     o["txt"].endswith("=") for o in pz)
    elif any(t["txt"].startswith("•") for t in pz):
        modo = "li"
        empieza = lambda t: t["txt"].startswith("•")
    elif sum(1 for t in pz if negrita0(t) and any(not negrita0(o) and abs(o["yb"] - t["yb"]) < 1.5 and
                                                  o["a"] > t["a"] for o in pz)) >= 6:
        return [abreviaturas(pz)]
    else:
        modo = "columnas"
        empieza = lambda t: not t["txt"][:1].islower()
    elementos = []
    for t in pz:
        if empieza(t) or not elementos:
            elementos.append({"pz": [t], "a": t["a"], "b": t["b"], "yb": t["yb"], "p": t["p"], "col": t["col"]})
            continue
        misma = [e for e in elementos if (e["p"], e["col"]) == (t["p"], t["col"]) and
                 abs(e["pz"][-1]["yb"] - t["yb"]) < 1.5 and e["pz"][-1]["b"] <= t["a"] + 1]
        encima = [e for e in elementos if (e["p"], e["col"]) == (t["p"], t["col"]) and
                  0 < t["yb"] - e["pz"][-1]["yb"] < 16 and t["a"] < e["b"] and t["b"] > e["a"]]
        # en una formula lo que sigue a la derecha en la misma fila es suyo ("Passive Wahrnehmung =" | "10 + ...");
        # en una lista, lo de debajo ("Preparar una" / "accion")
        destino = ((misma or encima) if modo == "formula" else (encima or misma) or elementos)[-1]
        destino["pz"].append(t)
        destino["a"], destino["b"] = min(destino["a"], t["a"]), max(destino["b"], t["b"])
    textos = [unir_html([t["html"] for t in e["pz"]]) for e in elementos]
    if modo == "formula":
        return [{"t": "formula", "txt": x} for x in textos]
    if modo == "li":
        return [{"t": "li", "txt": re.sub(r"^•\s*", "", x)} for x in textos]
    # lista de terminos: por columnas (de izquierda a derecha) y de arriba abajo
    orden = sorted(range(len(elementos)), key=lambda k: (elementos[k]["p"], elementos[k]["col"],
                                                         round(elementos[k]["a"] / 6), elementos[k]["yb"]))
    return [{"t": "columnas", "items": [textos[k] for k in orden]}]


def abreviaturas(pz):
    """La lista de abreviaturas del glosario ingles (en los otros idiomas es una tabla sin cabecera): cada
    abreviatura en negrita abre una fila y lo que sigue en letra normal es su significado."""
    neg = lambda t: "Bold" in t["tramos"][0][1]
    abrevs = [t for t in pz if neg(t)]
    # columnas de abreviaturas (la lista va en varias columnas): por la x de arranque
    xs = []
    for t in sorted(abrevs, key=lambda t: t["a"]):
        if xs and t["a"] - xs[-1][-1] < 8:
            xs[-1].append(t["a"])
        else:
            xs.append([t["a"]])
    limites = [g[0] - 1 for g in xs] + [9999]
    filas_t = []
    for k in range(len(xs)):
        a0, a1 = limites[k], limites[k + 1]
        propias = sorted((t for t in abrevs if a0 <= t["a"] < a1), key=lambda t: (t["p"], t["col"], t["yb"]))
        resto = [t for t in pz if not neg(t) and a0 <= t["a"] < a1]
        for j, ab in enumerate(propias):
            sig = propias[j + 1]["yb"] if j + 1 < len(propias) else 9999
            nb = [sp for sp in ab["tramos"] if "Bold" in sp[1]]
            pegado = [sp for sp in ab["tramos"] if "Bold" not in sp[1]]  # "Con." y "Constitution" en un trozo
            significado = ([a_html(marcar_gill(pegado))] if pegado else []) + \
                [t["html"] for t in sorted(resto, key=lambda t: (t["yb"], t["a"]))
                 if (t["p"], t["col"]) == (ab["p"], ab["col"]) and ab["yb"] - 1.5 <= t["yb"] < sig - 1.5]
            filas_t.append([f"<b>{limpia(''.join(sp[0] for sp in nb))}</b>", unir_html(significado)])
    return {"t": "tabla", "titulo": None, "sin_cabecera": True, "filas": filas_t}


def bloques(lang, rows):
    """Bloques de una tira de lineas en orden de lectura."""
    out = []
    pars = Parrafos(rotulo_texto)
    pendientes = []  # tablas, recuadros y notas que esperan a que acabe el parrafo en que cayeron
    grupo, grupo_tipo, grupo_titulo = [], None, None
    recuadro = None  # {"titulo": [...], "filas": [...]}

    def emitir(b):
        if pars.abierto():
            pendientes.append(b)
        else:
            out.append(b)

    def cerrar_grupo():
        nonlocal grupo, grupo_tipo, grupo_titulo
        if grupo_tipo == "tabla":
            for b in construir_tablas(grupo_titulo, grupo):
                emitir(b)
        elif grupo_tipo == "campos":
            # los campos y las formulas no flotan: van donde estan y cortan el parrafo
            cerrar_par()
            out.append(campos(grupo))
        elif grupo_tipo == "destacado":
            cerrar_par()
            out.extend(destacado(grupo))
        elif grupo_tipo == "nota":
            emitir({"t": "nota", "txt": une([r["t"] for r in grupo])})
        elif grupo_titulo is not None:
            # titulo de tabla sin tabla debajo (la tabla sigue en la otra columna o la pagina siguiente)
            emitir({"t": "tabla", "titulo": grupo_titulo, "filas": []})
        grupo, grupo_tipo, grupo_titulo = [], None, None

    def cerrar_recuadro():
        nonlocal recuadro
        if recuadro:
            emitir(construir_recuadro(recuadro))
        recuadro = None

    def cerrar_par():
        pars.cerrar()
        out.extend(pars.salida)
        pars.salida.clear()
        out.extend(pendientes)
        pendientes.clear()

    def cerrar_todo():
        cerrar_grupo()
        cerrar_recuadro()
        cerrar_par()

    subtitulo = False
    k = 0
    while k < len(rows):
        r = rows[k]
        if subtitulo and not es_texto(r):
            cerrar_par()
            if out and out[-1]["t"] == "p":
                out[-1]["sub"] = True
            subtitulo = False
        if es_titulo(r):
            cerrar_todo()
            nivel = NIVEL_TITULO[round(r["size"], 1)]
            lineas = [r["t"]]
            while k + 1 < len(rows) and es_titulo(rows[k + 1]) and tam(rows[k + 1], r["size"]) and \
                    (rows[k + 1]["p"], rows[k + 1]["col"]) == (r["p"], r["col"]) and \
                    0 < rows[k + 1]["yb"] - rows[k]["yb"] < r["size"] * 1.45:
                k += 1
                lineas.append(rows[k]["t"])
            out.append({"t": "h", "n": nivel, "txt": une(lineas), "p": r["p"]})
            k += 1
            continue
        if es_recuadro(r):
            cerrar_grupo()
            if es_titulo_recuadro(r) and (recuadro is None or recuadro["filas"]):
                cerrar_recuadro()
                recuadro = {"titulo": [r["t"]], "filas": []}
            elif es_titulo_recuadro(r):
                recuadro["titulo"].append(r["t"])
            else:
                if recuadro is None:
                    recuadro = {"titulo": [], "filas": []}
                recuadro["filas"].append(r)
            k += 1
            continue
        cerrar_recuadro()
        if es_titulo_tabla(r):
            cerrar_grupo()
            lineas = [r["t"]]
            while k + 1 < len(rows) and es_titulo_tabla(rows[k + 1]) and \
                    (rows[k + 1]["p"], rows[k + 1]["col"]) == (r["p"], r["col"]) and \
                    0 < rows[k + 1]["yb"] - rows[k]["yb"] < 14 and abs(rows[k + 1]["x"] - r["x"]) < 2:
                k += 1
                lineas.append(rows[k]["t"])
            grupo_titulo = une(lineas)
            k += 1
            continue
        for tipo, prueba in (("tabla", es_tabla), ("campos", es_campo), ("destacado", es_destacado),
                             ("nota", es_nota)):
            if prueba(r):
                break
        else:
            tipo = None
        if tipo == "campos" and grupo_tipo == "campos":
            grupo.append(r)
        elif tipo == "campos":
            cerrar_grupo()
            grupo, grupo_tipo = [r], "campos"
        elif grupo_tipo == "campos" and tipo == "tabla" and sigue_campo(grupo[-1], r):
            grupo.append(r)  # segunda linea del valor de un campo
        elif grupo_tipo == "campos" and tipo == "destacado" and \
                (grupo[-1]["p"], grupo[-1]["col"]) == (r["p"], r["col"]) and 0 < r["yb"] - grupo[-1]["yb"] < 15:
            grupo.append(r)
        elif tipo == "tabla":
            # las lineas de tabla seguidas van juntas; construir_tablas separa luego las tablas que haya
            if grupo_tipo not in ("tabla", None):
                cerrar_grupo()
            if grupo_tipo is None:
                grupo_tipo = "tabla"
            grupo.append(r)
        elif tipo in ("destacado", "nota"):
            if grupo_tipo != tipo:
                cerrar_grupo()
                grupo_tipo = tipo
            grupo.append(r)
        elif es_texto(r):
            cerrar_grupo()
            nuevo, _ = pars.es_nuevo(r)
            cursiva = all("Italic" in s[1] for s in r["spans"] if s[0].strip())
            if subtitulo and not cursiva:
                # la linea en cursiva bajo el titulo ("Veneno de contacto", "Trampa mortal (niveles 1-4)")
                # es un bloque aparte
                cerrar_par()
                out[-1]["sub"] = True
                subtitulo = False
                nuevo = True
            if nuevo and pendientes:
                cerrar_par()
            elif not nuevo and pendientes and pars.par and _fin_frase(pars.par[-1]) and limpia(r["t"])[:1].isupper():
                # detras de una tabla que flotaba: si la frase de antes acabo, esto es otro parrafo
                cerrar_par()
            if pars.par is None and out and out[-1]["t"] == "h" and not pendientes and cursiva:
                subtitulo = True
            pars.linea(r, marcas=marcar_texto)
        else:
            cerrar_grupo()
            out.append({"t": "otro", "txt": limpia(r["t"]), "font": r["font"], "size": r["size"], "p": r["p"]})
        k += 1
    cerrar_todo()
    return juntar_tablas(out)


def _fin_frase(html):
    t = re.sub(r"<[^>]+>", "", html).rstrip()
    return t.endswith((".", ":", "!", "?", ".”", ".)", "»"))


def construir_recuadro(rc):
    filas_r = rc["filas"]
    base = {}
    for r in filas_r:
        key = (r["p"], r["col"])
        base[key] = min(base.get(key, 999), r["x"])
    pars = Parrafos(rotulo_recuadro)
    otros = []
    for r in filas_r:
        if (r["font"].startswith("GillSans") and tam(r, 9.0)) or r["font"].startswith("ScalaSans"):
            pars.linea(r, base=base[(r["p"], r["col"])], marcas=marcar_recuadro)
        else:
            otros.append(limpia(r["t"]))
    pars.cerrar()
    b = {"t": "recuadro", "titulo": une(rc["titulo"]), "bloques": pars.salida}
    if otros:
        b["otros"] = otros
    return b


def juntar_tablas(bl):
    """Una tabla que sigue en la otra columna repite la cabecera y no lleva titulo: se junta con la de antes."""
    out = []
    for b in bl:
        prev = next((x for x in reversed(out) if x["t"] not in ("recuadro", "nota")), None)
        if b["t"] == "tabla" and not b.get("titulo") and prev is not None and prev["t"] == "tabla" and \
                prev["filas"] and b["filas"] and prev["filas"][0] == b["filas"][0] and not b.get("vertical"):
            prev["filas"].extend(b["filas"][1:])
        elif b["t"] == "tabla" and not b.get("titulo") and prev is not None and prev["t"] == "tabla" and \
                not prev["filas"] and b["filas"]:
            prev["filas"] = b["filas"]  # el titulo quedo solo al pie de la columna y la tabla sigue en la otra
            if b.get("vertical"):
                prev["vertical"] = True
        else:
            out.append(b)
    return out


def capitulo(lang, cap, p0=None, p1=None):
    a, b = rango(lang, cap)
    rows, _ = recolocar_tablas_anchas(en_paginas(lang, p0 or a, p1 or b))
    return bloques(lang, rows)
