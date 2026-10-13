# -*- coding: utf-8 -*-
"""Lectura de los cinco SRD 5.2.1 oficiales (EN, ES, DE, FR, IT).

Vuelca cada PDF linea a linea (pagina, columna, posicion, fuente, tamano y tramos) a una cache fuera de
la carpeta sincronizada, y da las utilidades comunes para cortar entradas: capitulos, limpieza de texto y
union de lineas deshaciendo los cortes de palabra.

Las cinco ediciones comparten maqueta: las mismas fuentes y tamanos marcan lo mismo en todas.

Variables de entorno:
    SRD_DIR    carpeta con los PDF (por defecto G:\\General\\D&D\\Recursos\\SRD)
    SRD_CACHE  carpeta de la cache (por defecto %LOCALAPPDATA%\\compendio-srd\\cache)
"""
import json
import os
import re
import unicodedata

SRD_DIR = os.environ.get("SRD_DIR", r"G:\General\D&D\Recursos\SRD")
CACHE = os.environ.get("SRD_CACHE", os.path.join(os.environ.get("LOCALAPPDATA", os.path.expanduser("~")),
                                                  "compendio-srd", "cache"))
LANGS = ("es", "en", "de", "fr", "it")
PDFS = {l: f"SRD 5.2.1 {l.upper()} (oficial, CC-BY).pdf" for l in LANGS}
VERSION_VOLCADO = 1

# Primera pagina de cada capitulo, leida en el titulo de capitulo de cada PDF (GillSans-SemiBold 26).
CAP = {
    "es": dict(conjuros=114, glosario=194, herramientas=211, objetos=223, monstruos=278, monstruos_az=283,
               animales=376, fin=398),
    "en": dict(conjuros=104, glosario=176, herramientas=192, objetos=204, monstruos=254, monstruos_az=258,
               animales=344, fin=364),
    "de": dict(conjuros=118, glosario=203, herramientas=222, objetos=236, monstruos=295, monstruos_az=300,
               animales=392, fin=412),
    "fr": dict(conjuros=111, glosario=187, herramientas=203, objetos=215, monstruos=267, monstruos_az=272,
               animales=360, fin=380),
    "it": dict(conjuros=118, glosario=202, herramientas=220, objetos=232, monstruos=289, monstruos_az=294,
               animales=385, fin=405),
}
ORDEN_CAP = ["conjuros", "glosario", "herramientas", "objetos", "monstruos", "monstruos_az", "animales", "fin"]


def rango(lang, cap):
    """(primera, ultima) pagina de un capitulo."""
    c = CAP[lang]
    if cap == "animales":
        return c["animales"], c["fin"]
    sig = ORDEN_CAP[ORDEN_CAP.index(cap) + 1]
    return c[cap], c[sig] - 1


def en_paginas(lang, p0, p1):
    return [r for r in filas(lang) if p0 <= r["p"] <= p1]


def _ruta_volcado(lang):
    return os.path.join(CACHE, f"lineas_{lang}.v{VERSION_VOLCADO}.jsonl")


def volcar(lang, forzar=False):
    """Vuelca el PDF de un idioma a la cache (una fila por linea visual)."""
    import fitz  # PyMuPDF
    out = _ruta_volcado(lang)
    if os.path.exists(out) and not forzar:
        return out
    os.makedirs(CACHE, exist_ok=True)
    doc = fitz.open(os.path.join(SRD_DIR, PDFS[lang]))
    tmp = out + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        for pno in range(doc.page_count):
            page = doc[pno]
            W = page.rect.width
            d = page.get_text("dict", flags=fitz.TEXT_PRESERVE_WHITESPACE | fitz.TEXT_PRESERVE_LIGATURES)
            for b in d["blocks"]:
                if b.get("type") != 0:
                    continue
                for l in b["lines"]:
                    for s_ in l["spans"]:
                        s_["text"] = unicodedata.normalize("NFC", s_["text"])
                    spans = [s for s in l["spans"] if s["text"].strip() != ""]
                    if not spans:
                        continue
                    x0 = min(s["bbox"][0] for s in spans)
                    y0 = min(s["bbox"][1] for s in spans)
                    yb = max(s["origin"][1] for s in spans)
                    cnt = {}
                    for s in spans:
                        k = (s["font"], round(s["size"], 1), s["flags"])
                        cnt[k] = cnt.get(k, 0) + len(s["text"])
                    font, size, flags = max(cnt, key=cnt.get)
                    fila = {
                        "p": pno + 1, "x": round(x0, 1), "y": round(y0, 1), "yb": round(yb, 1),
                        "x1": round(max(s["bbox"][2] for s in spans), 1),
                        "col": 0 if x0 < W / 2 - 10 else 1,
                        "font": font, "size": size,
                        "spans": [[s["text"], s["font"], round(s["size"], 1), s["flags"], round(s["bbox"][0], 1)]
                                  for s in spans],
                        "t": "".join(s["text"] for s in l["spans"]),
                    }
                    f.write(json.dumps(fila, ensure_ascii=False) + "\n")
    os.replace(tmp, out)
    return out


_cache = {}


def filas(lang):
    """Todas las lineas en orden de lectura (pagina, columna, altura), sin la cabecera corrida y el numero
    de pagina (GillSans 11)."""
    if lang not in _cache:
        rows = []
        with open(volcar(lang), encoding="utf-8") as f:
            for line in f:
                r = json.loads(line)
                if r["size"] == 11.0 and r["font"].startswith("GillSans"):
                    continue
                rows.append(r)
        _tablas_anchas(rows)
        rows.sort(key=lambda r: (r["p"], r["col"], r["yb"], r["x"]))
        for i, r in enumerate(rows):
            r["i"] = i
        _cache[lang] = rows
    return _cache[lang]


def _es_tabla(r):
    return r["font"].startswith("GillSans") and (abs(r["size"] - 9.2) < 0.05 or abs(r["size"] - 9.5) < 0.05)


def _tablas_anchas(rows):
    """Tablas que ocupan las dos columnas (la de palancas del aparato del crustaceo): sus celdas de la derecha
    caen en la columna 1 y el orden de lectura las separaria de su fila. Si una fila de cabecera de tabla de la
    columna 1 esta a la misma altura que otra de la columna 0, las filas de tabla de la columna 1 que siguen a
    la misma altura que las de la izquierda pasan a la columna 0."""
    por_pagina = {}
    for r in rows:
        por_pagina.setdefault(r["p"], []).append(r)
    for p, rs in por_pagina.items():
        cab0 = [r for r in rs if r["col"] == 0 and r["font"] == "GillSans-SemiBold" and abs(r["size"] - 9.2) < 0.05]
        cab1 = [r for r in rs if r["col"] == 1 and r["font"] == "GillSans-SemiBold" and abs(r["size"] - 9.2) < 0.05]
        for c1 in cab1:
            c0 = next((c for c in cab0 if abs(c["yb"] - c1["yb"]) < 1.0), None)
            if c0 is None:
                continue
            # alto de la tabla en la columna 0: filas de tabla seguidas desde la cabecera
            izq = sorted((r for r in rs if r["col"] == 0 and _es_tabla(r) and r["yb"] >= c0["yb"] - 0.5),
                         key=lambda r: r["yb"])
            fin, prev = c0["yb"], c0["yb"]
            for r in izq:
                if r["yb"] - prev > 30:
                    break
                fin = prev = r["yb"]
            # una tabla ancha de verdad pasa el margen de la columna izquierda (el texto normal acaba hacia x=299);
            # dos tablas distintas, una en cada columna y a la misma altura, no
            if max((r["x1"] for r in izq if r["yb"] <= fin + 0.5), default=0) <= 302:
                continue
            alturas = {round(r["yb"]) for r in izq if r["yb"] <= fin + 0.5}
            for r in rs:
                if r["col"] == 1 and _es_tabla(r) and c1["yb"] - 0.5 <= r["yb"] <= fin + 13 and \
                        (round(r["yb"]) in alturas or any(abs(r["yb"] - a) < 14 for a in alturas)):
                    r["col"] = 0
                    r["_ancha"] = True


def limpia(t):
    """Texto de una linea sin tabuladores, guiones de corte blandos ni espacios raros."""
    t = t.replace("\u00ad", "").replace("\xa0", " ").replace("\u202f", " ").replace("\u2009", " ").replace("\t", " ")
    t = t.replace("\u2011", "-")
    return re.sub(r"\s+", " ", t).strip()


CONJUNCIONES = {"und", "oder", "bzw.", "sowie", "bis", "y", "o", "e", "u", "and", "or", "et", "ou", "ed"}


def une(lineas):
    """Une las lineas de un parrafo deshaciendo el guion de fin de linea."""
    out = ""
    pegar = False  # la linea anterior acababa en guion blando: la palabra sigue sin espacio
    for l in lineas:
        t = limpia(l)
        if not t:
            continue
        if pegar:
            out = out + t
        elif out.endswith("-") and len(out) > 1 and out[-2].isalpha() and t[:1].islower() \
                and t.split()[0] not in CONJUNCIONES:
            out = out[:-1] + t  # corte de palabra con guion duro
        elif out.endswith("-") and len(out) > 1 and out[-2].isalpha() and t[:1].islower():
            out = out + " " + t  # guion de compuesto suspendido: "Nah- oder Fernkampf"
        elif out.endswith("-") and len(out) > 1 and out[-2].isalnum() and t[:1].isupper():
            out = out + t  # compuesto con guion partido: "W20-" + "Prüfungen"
        else:
            out = (out + " " + t) if out else t
        pegar = l.rstrip(" \t").endswith("\u00ad")
    return out


def es(r, font, size, tol=0.05):
    return r["font"] == font and abs(r["size"] - size) < tol


if __name__ == "__main__":
    import sys
    forzar = "--forzar" in sys.argv
    for l in LANGS:
        ruta = volcar(l, forzar)
        print(l, ruta, sum(1 for _ in open(ruta, encoding="utf-8")), "lineas")
