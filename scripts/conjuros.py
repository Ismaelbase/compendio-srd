# -*- coding: utf-8 -*-
"""Saca los conjuros de los cinco SRD 5.2.1 con su estructura.

Parte del lector de las cartas de hechizos (T-0108, generador\\paso1_srd.py, probado en ES, EN y DE) ampliado
al frances y al italiano. Cada conjuro sale con: nombre, pagina, cabecera (nivel, escuela, clases), tiempo,
alcance, componentes, duracion y el cuerpo en bloques:
    {"t": "p", "txt": "..."}      parrafo (con <i>, <b> y <strong> dentro)
    {"t": "li", "txt": "..."}     punto de una lista
    {"t": "tabla", "titulo": "...", "filas": [[celda, ...], ...]}   la primera fila es la cabecera
    {"t": "ficha", ...}           ficha de criatura dentro del conjuro
El parrafo de niveles superiores lleva "sup": "nivel" y el de mejora de truco "sup": "truco".

Uso: py -3.14 conjuros.py   (deja datos\\_conjuros_crudo.json; lo empareja emparejar_conjuros.py)
"""
import json
import os
import re
import sys

from marcas import a_html, unir_html
from srd import LANGS, en_paginas, limpia, rango, une

AQUI = os.path.dirname(os.path.abspath(__file__))
DATOS = os.path.join(os.path.dirname(AQUI), "datos")

ETIQ = {
    "en": dict(tiempo=["Casting Time"], alcance=["Range"], comp=["Components", "Component"], dur=["Duration"]),
    "es": dict(tiempo=["Tiempo de lanzamiento"], alcance=["Alcance"], comp=["Componentes", "Componente"],
               dur=["Duración"]),
    "de": dict(tiempo=["Zeitaufwand"], alcance=["Reichweite"], comp=["Komponenten", "Komponente"],
               dur=["Wirkungsdauer"]),
    "fr": dict(tiempo=["Temps d’incantation", "Temps d'incantation"], alcance=["Portée"],
               comp=["Composantes", "Composante"], dur=["Durée"]),
    "it": dict(tiempo=["Tempo di lancio"], alcance=["Gittata"], comp=["Componenti", "Componente"], dur=["Durata"]),
}
SUP = {  # rotulo del parrafo de niveles superiores y de mejora de truco
    "en": ("Using a Higher-Level Spell Slot", "Cantrip Upgrade"),
    "es": ("Con un espacio de conjuro de nivel superior", "Mejora de truco"),
    "de": ("Verwenden von Zauberplätzen höheren Grades", "Zaubertrick-Aufwertung"),
    "fr": ("Emplacement de niveau supérieur", "Amélioration de sort mineur"),
    "it": ("Utilizzo di uno slot incantesimo di livello superiore", "Trucchetto potenziato"),
}
BASE_X = {0: 63.0, 1: 313.5}


def es_cuerpo(r):
    """Texto del conjuro: Cambria de 10 (9,5 en el frances)."""
    return r["font"].startswith("Cambria") and (abs(r["size"] - 10.0) < 0.05 or abs(r["size"] - 9.5) < 0.05)


def es_nombre(r):
    return (r["font"] == "GillSans-SemiBold" and abs(r["size"] - 12.0) < 0.05) or \
           (r["font"] == "GillSans-SemiBold-SC700" and r["size"] > 8)


def cortar(lang):
    """Entradas de conjuro: nombre en GillSans-SemiBold 12 seguido de la linea en Cambria-Italic."""
    p0, p1 = rango(lang, "conjuros")
    rows = en_paginas(lang, p0, p1)
    out, cur, i = [], None, 0
    while i < len(rows):
        r = rows[i]
        if es_nombre(r):
            j = i + 1
            nombre = [r["t"]]
            while j < len(rows) and rows[j]["font"] == "GillSans-SemiBold" and abs(rows[j]["size"] - 12.0) < 0.05 \
                    and rows[j]["p"] == r["p"] and 0 < rows[j]["y"] - rows[j - 1]["y"] < 16:
                nombre.append(rows[j]["t"]); j += 1
            if j < len(rows) and rows[j]["font"] == "Cambria-Italic":
                if cur:
                    out.append(cur)
                cur = {"nombre": une(nombre), "p": r["p"], "filas": []}
                i = j
                continue
            if cur:
                out.append(cur); cur = None
        elif r["font"].startswith("GillSans-SemiBold") and r["size"] >= 14.0 and abs(r["size"] - 14.8) > 0.05:
            if cur:
                out.append(cur); cur = None
        elif cur is not None:
            cur["filas"].append(r)
        i += 1
    if cur:
        out.append(cur)
    return out


def es_rotulo(spans):
    """La linea empieza por un rotulo: negrita cursiva ("Using a Higher-Level Spell Slot.") o negrita que acaba en
    punto o dos puntos ("Drop.", "Anhalten:"), no una criatura citada."""
    if not spans:
        return False
    txt, font = spans[0][0].strip(), spans[0][1]
    if "Cambria-BoldItalic" in font:
        return True
    return "Cambria-Bold" in font and txt.endswith((".", ":")) and len(spans) > 1


def marcar(spans):
    """Texto de una linea con <b> (rotulo), <strong> (criatura citada) e <i> (conjuro citado)."""
    out = []
    rot = es_rotulo(spans)
    for k, (txt, font, size, flags, *_) in enumerate(spans):
        if "Cambria" in font and "Bold" in font and ("Italic" in font or (k == 0 and rot)):
            out.append(("b", txt))
        elif "Bold" in font and "Cambria" in font:
            out.append(("strong", txt))
        elif "Italic" in font and "Cambria" in font:
            out.append(("i", txt))
        else:
            out.append(("", txt))
    return out


def dx(r):
    return r["x"] - BASE_X[r["col"]]


def celdas_tabla(lineas):
    """Tabla a partir de sus lineas del PDF (ver la explicacion en el lector de T-0108).

    Columnas: las x de arranque de las lineas del cuerpo, agrupadas (mas de 12 pt de separacion = otra columna).
    Cabecera (SemiBold 9.2): cada tramo a la columna mas cercana. Cuerpo: una fila visual con texto en la
    primera columna y a mas de 13,5 pt de la anterior abre fila; si no, sigue la celda de arriba. Las tablas
    maquetadas en dos mitades iguales se despliegan en una."""
    cab = [r for r in lineas if abs(r["size"] - 9.2) < 0.05]
    cuerpo_t = [r for r in lineas if abs(r["size"] - 9.2) >= 0.05]
    xs = sorted({round(dx(r), 1) for r in cuerpo_t})
    grupos = []
    for x in xs:
        if grupos and x - grupos[-1][-1] < 12:
            grupos[-1].append(x)
        else:
            grupos.append([x])
    anclas = [g[0] for g in grupos] or [0]

    def col(x):
        for k, g in enumerate(grupos):
            if g[0] - 0.5 <= x <= g[-1] + 0.5:
                return k
        return min(range(len(anclas)), key=lambda k: abs(anclas[k] - x))

    ncol = len(anclas)
    piezas = []
    for r in cab:
        for sp in r["spans"]:
            if limpia(sp[0]):
                x = (sp[4] if len(sp) > 4 else r["x"]) - BASE_X[r["col"]]
                piezas.append((col(x) if cuerpo_t else 0, r["yb"], x, sp[0]))
    cabecera = []
    if piezas:
        porcol = {}
        for k, y, x, t in sorted(piezas, key=lambda p: (p[1], p[2])):
            porcol.setdefault(k, []).append(t)
        cabecera = [une(porcol.get(k, [])) for k in range(ncol)]
    filas_t, prev = [], None
    visuales, orden = {}, []
    for r in cuerpo_t:
        key = (r["p"], r["col"], round(r["yb"]))
        if key not in visuales:
            visuales[key] = []; orden.append(key)
        visuales[key].append(r)
    for key in orden:
        vs = visuales[key]
        cols = [col(dx(r)) for r in vs]
        nueva = 0 in cols and (not filas_t or prev is None or key[:2] != prev[:2] or key[2] - prev[2] > 13.5)
        if nueva or not filas_t:
            filas_t.append([[] for _ in range(ncol)])
        for r, k in zip(vs, cols):
            filas_t[-1][k].append(a_html([("i" if "Italic" in sp[1] else "", sp[0]) for sp in r["spans"]]))
        prev = key
    filas_txt = [[unir_html(c) if c else "" for c in f] for f in filas_t]
    out = ([cabecera] if cabecera else []) + filas_txt
    if cabecera and len(cabecera) % 2 == 0 and len(cabecera) >= 4:
        m = len(cabecera) // 2
        if cabecera[:m] == cabecera[m:]:
            izq = [f[:m] for f in filas_txt]
            der = [f[m:] for f in filas_txt if any(x.strip() for x in f[m:])]
            out = [cabecera[:m]] + izq + der
    return out


CAMPOS_FICHA = {
    "en": {"AC": "ca", "HP": "pg", "Speed": "vel"},
    "es": {"CA": "ca", "PG": "pg", "Velocidad": "vel"},
    "de": {"RK": "ca", "TP": "pg", "Bewegungsrate": "vel"},
    "fr": {"CA": "ca", "Pv": "pg", "PV": "pg", "Vitesse": "vel"},
    "it": {"CA": "ca", "PF": "pg", "Velocità": "vel"},
}


def marcar_ficha(spans):
    out = []
    for txt, font, size, flags, *_ in spans:
        if "Optima" in font and "Bold" in font:
            out.append(("b", txt))
        elif "Optima" in font and "Italic" in font:
            out.append(("i", txt))
        else:
            out.append(("", txt))
    return out


def estructurar_ficha(lang, nombre, filas_f):
    """Ficha de criatura dentro de un conjuro: nombre, tipo, ca, pg, vel, car [[abrev, puntuacion, mod, salv]],
    rasgos [[rotulo, valor]], secciones [{titulo, items [[nombre, texto]]}]."""
    tipo, cab, car_tokens, secciones = [], [], [], []
    for r in filas_f:
        f, sz = r["font"], r["size"]
        if f.startswith("Optima-Italic") and abs(sz - 9.0) < 0.05 and not cab and not secciones:
            tipo.append(r["t"]); continue
        if f.startswith("GillSans") and abs(sz - 6.0) < 0.05:
            continue
        if f.startswith("GillSans") and abs(sz - 9.8) < 0.1 or f.startswith("GillSans-SemiBold-SC700") \
                or f.startswith("GillSans-Bold-SC700"):
            etiqueta = "".join(s[0] for s in r["spans"] if "SemiBold" in s[1] or "Bold-SC" in s[1]).strip()
            nums = [limpia(s[0]) for s in r["spans"] if not ("SemiBold" in s[1] or "Bold-SC" in s[1])]
            if etiqueta:
                car_tokens.append(etiqueta)
            for n in nums:
                car_tokens.extend(n.split())
            continue
        if f == "GillSans" and abs(sz - 12.0) < 0.05:
            secciones.append({"titulo": limpia(r["t"]), "items": []}); continue
        if f.startswith("Optima") and abs(sz - 9.0) < 0.05 and not secciones:
            sp0 = r["spans"][0]
            if "Bold" in sp0[1]:
                cab.append([limpia(sp0[0]).rstrip(":").strip(), [a_html(marcar_ficha(r["spans"][1:]))]])
            elif cab:
                cab[-1][1].append(a_html(marcar_ficha(r["spans"])))
            continue
        if f.startswith("Optima") and secciones:
            sp0 = r["spans"][0]
            items = secciones[-1]["items"]
            if "BoldItalic" in sp0[1] and items and items[-1][2]:
                items[-1][0] = une([items[-1][0], sp0[0]])
                items[-1][1].append(a_html(marcar_ficha(r["spans"][1:])))
            elif "BoldItalic" in sp0[1]:
                items.append([sp0[0], [a_html(marcar_ficha(r["spans"][1:]))], False])
            elif items:
                items[-1][1].append(a_html(marcar_ficha(r["spans"])))
            if items:
                items[-1][2] = len(r["spans"]) == 1 and "BoldItalic" in r["spans"][-1][1]
            continue
    car, k = [], 0
    while k < len(car_tokens):
        t = car_tokens[k]
        if re.fullmatch(r"[A-Za-zÄÖÜäöüßÀ-ÿ]{2,4}", t):
            vals = []
            k += 1
            while k < len(car_tokens) and not re.fullmatch(r"[A-Za-zÄÖÜäöüßÀ-ÿ]{2,4}", car_tokens[k]) and len(vals) < 3:
                vals.append(car_tokens[k]); k += 1
            car.append([t, *vals])
        else:
            k += 1
    car = [[c[0], int(c[1]), c[2].replace("-", "−"), (c[3] if len(c) > 3 else c[2]).replace("-", "−")]
           for c in car if len(c) >= 3 and c[1].isdigit()]
    campos, rasgos = {}, []
    for rot, trozos in cab:
        v = unir_html(trozos)
        clave = CAMPOS_FICHA[lang].get(rot)
        if clave:
            campos[clave] = v
        else:
            rasgos.append([rot, v])
    return {"t": "ficha", "nombre": nombre, "tipo": une(tipo), **campos, "car": car, "rasgos": rasgos,
            "secciones": [{"titulo": s["titulo"], "items": [[limpia(une([n])).rstrip(".:").strip(), unir_html(tx)]
                                                           for n, tx, _ in s["items"]]} for s in secciones]}


def cuerpo(lang, fs):
    """Divide las filas del cuerpo en bloques."""
    bloques = []
    par, par_tipo = None, "p"
    sigue_rotulo = False
    colgante = False
    tabla, tabla_titulo = None, None
    ficha = None

    def cerrar_par():
        nonlocal par
        if par:
            bloques.append({"t": par_tipo, "txt": unir_html(par)})
        par = None

    def cerrar_tabla():
        nonlocal tabla, tabla_titulo
        if tabla:
            bloques.append({"t": "tabla", "titulo": tabla_titulo, "filas": celdas_tabla(tabla)})
        tabla, tabla_titulo = None, None

    def cerrar_ficha():
        nonlocal ficha
        if ficha:
            bloques.append(estructurar_ficha(lang, ficha["nombre"], ficha["filas"]))
        ficha = None

    for r in fs:
        f, sz, t = r["font"], r["size"], r["t"]
        if f == "GillSans-SemiBold" and abs(sz - 14.8) < 0.05:
            cerrar_par(); cerrar_tabla(); cerrar_ficha()
            ficha = {"nombre": limpia(t), "filas": []}
            continue
        if ficha is not None:
            if es_cuerpo(r) and dx(r) > 5:
                cerrar_ficha()
            else:
                ficha["filas"].append(r)
                continue
        if f == "GillSans-SemiBold" and abs(sz - 10.5) < 0.05:
            cerrar_par(); cerrar_tabla()
            tabla_titulo = limpia(t)
            continue
        if f.startswith("GillSans") and (abs(sz - 9.2) < 0.05 or abs(sz - 9.5) < 0.05):
            cerrar_par()
            if tabla and abs(sz - 9.2) < 0.05 and any(abs(q["size"] - 9.2) >= 0.05 for q in tabla):
                cerrar_tabla()
                tabla_titulo = None
            if tabla is None:
                tabla = []
            tabla.append(r)
            continue
        cerrar_tabla()
        if f.startswith("Cambria"):
            d = dx(r)
            vineta = t.lstrip().startswith("•")
            lead = es_rotulo(r["spans"]) and not sigue_rotulo
            if vineta:
                nuevo, tipo = True, "li"
            elif lead or par is None:
                nuevo, tipo = True, "p"
            elif 5 < d < 10:
                nuevo, tipo = (not colgante), "p"
            elif d >= 10:
                nuevo, tipo = False, par_tipo
            else:
                nuevo, tipo = (par_tipo == "li" or colgante), "p"
            if nuevo:
                colgante = lead and d < 5
            spans = [list(x) for x in r["spans"]]
            if vineta:
                spans[0][0] = spans[0][0].lstrip().lstrip("•").lstrip("\t ")
                if not spans[0][0]:
                    spans = spans[1:]
            if spans and spans[0][0].startswith("\t"):
                spans[0][0] = spans[0][0].lstrip("\t ")
            linea = a_html(marcar(spans))
            if nuevo:
                cerrar_par()
                par, par_tipo = [linea], tipo
            else:
                par.append(linea)
            spf = r["spans"][-1][1] if r["spans"] else ""
            sigue_rotulo = "Cambria-BoldItalic" in spf
            continue
        cerrar_par()
        bloques.append({"t": "otro", "txt": limpia(t), "font": f, "size": sz})
    cerrar_par(); cerrar_tabla(); cerrar_ficha()
    juntos = []
    for b in bloques:
        if b["t"] == "tabla" and juntos and juntos[-1]["t"] == "tabla" and juntos[-1]["filas"] and b["filas"] \
                and juntos[-1]["filas"][0] == b["filas"][0]:
            juntos[-1]["filas"].extend(b["filas"][1:])
        else:
            juntos.append(b)
    bloques = juntos
    for b in bloques:
        if b["t"] == "p":
            m = re.match(r"<b>([^<]+)</b>", b["txt"])
            if m:
                b["lead"] = m.group(1).strip().rstrip(".:").strip()
                if b["lead"] in SUP[lang]:
                    b["sup"] = "truco" if b["lead"] == SUP[lang][1] else "nivel"
    return bloques


def etiqueta(lang, t):
    """(clave, largo del rotulo con sus dos puntos) si la linea empieza por un rotulo de cabecera."""
    for key, labs in ETIQ[lang].items():
        for lb in labs:
            m = re.match(re.escape(lb) + r"\s?:", t)
            if m:
                return key, m.end()
    return None


def conjuros(lang):
    res = []
    for e in cortar(lang):
        fs = e["filas"]
        k, cab = 0, []
        while k < len(fs) and fs[k]["font"] == "Cambria-Italic":
            cab.append(fs[k]["t"]); k += 1
        campos, actual, resto = {}, None, []
        for r in fs[k:]:
            t = limpia(r["t"])
            hit = etiqueta(lang, t) if not resto else None
            if hit and not resto:
                actual = hit[0]
                crudo = r["t"].replace("\t", " ").lstrip()
                m = re.match(r"(.*?)\s?:", crudo)
                campos[actual] = [crudo[m.end():] if m else crudo]
            elif actual and not resto and r["font"].startswith("GillSans") and abs(r["size"] - 9.5) < 0.05 \
                    and not r["t"].startswith("\t"):
                campos[actual].append(r["t"])
            else:
                actual = None
                resto.append(r)
        campos = {k2: une(v) for k2, v in campos.items()}
        res.append({"nombre": e["nombre"], "p": e["p"], "cabecera": une(cab), **campos,
                    "bloques": cuerpo(lang, resto)})
    return res


# Parrafos que la maqueta coloco en otro conjuro: (idioma, conjuro donde sale, principio del parrafo, conjuro
# al que pertenece). Comprobado contra los otros cuatro idiomas.
MOVER = [
    # el tercer parrafo de Nuage incendiaire sale al final de Nuee de meteores, el conjuro que va detras
    ("fr", "Nuée de météores", "Le nuage s’éloigne de 3 m de vous", "Nuage incendiaire"),
]


def mover_parrafos(lang, lista, avisos):
    por = {c["nombre"]: c for c in lista}
    for l, desde, prefijo, hacia in MOVER:
        if l != lang:
            continue
        a, b = por.get(desde), por.get(hacia)
        bl = next((x for x in (a or {}).get("bloques", []) if x["t"] == "p" and x["txt"].startswith(prefijo)), None)
        if a is None or b is None or bl is None:
            avisos.append(f"{lang}: no se pudo mover '{prefijo}' de {desde} a {hacia}")
            continue
        a["bloques"].remove(bl)
        b["bloques"].append(bl)


def main():
    salida = {}
    for l in LANGS:
        c = conjuros(l)
        avisos = []
        mover_parrafos(l, c, avisos)
        for a in avisos:
            print("  ", a)
        faltan = [x["nombre"] for x in c if not all(k in x for k in ("tiempo", "alcance", "comp", "dur"))]
        otros = sum(1 for x in c for b in x["bloques"] if b["t"] == "otro")
        sup = sum(1 for x in c for b in x["bloques"] if b.get("sup"))
        print(f"{l}: {len(c)} conjuros; sin algun campo de cabecera {len(faltan)} {faltan[:5]}; "
              f"bloques sin clasificar {otros}; parrafos de nivel superior o truco {sup}")
        salida[l] = c
    with open(os.path.join(DATOS, "_conjuros_crudo.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(salida, f, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
