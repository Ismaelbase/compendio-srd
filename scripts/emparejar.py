# -*- coding: utf-8 -*-
"""Empareja las fichas de criatura de los cinco idiomas y saca los datos comunes.

Emparejado: por la huella de cifras de cada ficha (CA, PG y sus dados, caracteristicas, VD, PX e iniciativa),
que es la misma en los cinco SRD. Despues se contrasta con el glosario ES-EN-DE de T-0107: si el glosario
casa otro nombre, es un error.

Datos comunes (sacados del ingles y comprobados en los otros cuatro): tamano, tipo, etiquetas, alineamiento,
CA, iniciativa, PG, dados de golpe, caracteristicas, salvaciones, VD, PX, PX en la guarida, BC y percepcion
pasiva.

Uso: py -3.14 emparejar.py   (lee datos\\_criaturas_crudo.json y deja datos\\criaturas.json)
"""
import csv
import json
import os
import re
import sys
import unicodedata

from cifras import clave_punto, emparejar_items
from corregir import aplicar
from srd import LANGS

AQUI = os.path.dirname(os.path.abspath(__file__))
DATOS = os.path.join(os.path.dirname(AQUI), "datos")
GLOSARIO = os.environ.get("GLOSARIO", r"G:\General\Tareas\material\T-0107-recursos-rol-aleman\glosario_es_en_de.csv")

MENOS = "\u2212\u2013-"
NUM = r"\d{1,3}(?:[.,\u00a0\u202f ]\d{3})+|\d+"


def entero(t):
    return int(re.sub(r"[.,\u00a0\u202f ]", "", t))


def signo(t):
    t = t.strip()
    m = re.match(rf"([+{MENOS}])\s*(\d+)", t)
    if not m:
        return None
    return -int(m.group(2)) if m.group(1) in MENOS else int(m.group(2))


def parse_vd(t):
    """'10 (5900 PX o 7200 en la guarida; BC +4)' -> vd, px, px_guarida, bc. El BC es el ultimo +N; algunas
    fichas alemanas lo separan con coma en vez de punto y coma."""
    m = re.match(r"\s*(\d+/\d+|\d+)\s*\((.*)\)\s*$", t)
    if not m:
        return None
    cr, dentro = m.group(1), m.group(2)
    bcs = list(re.finditer(r"\+\s*(\d+)", dentro))
    pb = int(bcs[-1].group(1)) if bcs else None
    resto = dentro[:bcs[-1].start()] if bcs else dentro
    xps = [entero(x) for x in re.findall(NUM, resto)]
    return {"vd": cr, "px": xps[0] if xps else None, "px_guarida": xps[1] if len(xps) > 1 else None, "bc": pb}


def parse_pg(t):
    m = re.match(r"\s*(\d+)\s*(?:\((.*)\))?", t)
    if not m:
        return None, None
    dados = None
    if m.group(2):
        dados = re.sub(r"\s+", "", m.group(2)).replace("W", "d").replace(MENOS[0], "-").replace(MENOS[1], "-")
    return int(m.group(1)), dados


def parse_ini(t):
    m = re.match(rf"\s*([+{MENOS}]\s*\d+)\s*\((\d+)\)", t)
    if not m:
        return None, None
    return signo(m.group(1)), int(m.group(2))


def huella(f, nivel=0):
    """Huella de cifras de una ficha. Nivel 0: todo; 1: sin PG ni dados (por si una traduccion trae mal los
    dados); 2: solo caracteristicas, VD y PX."""
    c = f["campos"]
    pg, dados = parse_pg(c.get("pg", ""))
    ini, ini_p = parse_ini(c.get("ini", ""))
    vd = parse_vd(c.get("vd", "")) or {}
    ca = re.match(r"\s*(\d+)", c.get("ca", ""))
    car = tuple(x[1] for x in f["car"])
    if nivel == 2:
        return (car, vd.get("vd"), vd.get("px"))
    if nivel == 1:
        return (int(ca.group(1)) if ca else None, car, vd.get("vd"), vd.get("px"), ini)
    return (int(ca.group(1)) if ca else None, pg, dados, car, vd.get("vd"), vd.get("px"), vd.get("px_guarida"), ini)


TAM_EN = ["Tiny", "Small", "Medium", "Large", "Huge", "Gargantuan"]
TIPOS_EN = ["Aberration", "Beast", "Celestial", "Construct", "Dragon", "Elemental", "Fey", "Fiend", "Giant",
            "Humanoid", "Monstrosity", "Ooze", "Plant", "Undead"]


def parse_tipo_en(t):
    """'Medium or Small Humanoid (Wizard), Neutral' -> tamanos, tipo, etiquetas, alineamiento."""
    cuerpo, _, alin = t.rpartition(",")
    m = re.match(r"(.*?)\s*\((.*)\)\s*$", cuerpo)
    etiquetas = []
    if m:
        cuerpo, etiquetas = m.group(1), [x.strip() for x in m.group(2).split(",")]
    tam = [s for s in TAM_EN if re.search(rf"\b{s}\b", cuerpo.split(" of ")[0])]
    enjambre = " of " in cuerpo
    tipo = [x for x in TIPOS_EN if re.search(rf"\b{x}s?\b", cuerpo)]
    return {"tamano": tam, "tipo": tipo[0] if tipo else None, "enjambre": enjambre, "etiquetas": etiquetas,
            "alineamiento": alin.strip()}


def pasiva(sen):
    """Percepcion pasiva: 'Percepción pasiva 20', 'Passive Perception 20', 'Passive Wahrnehmung 20',
    'Perception passive 20', 'Percezione passiva 20' (en italiano va al principio de los sentidos)."""
    m = re.search(r"(?:pasiva|passiva|Perception|passive|Wahrnehmung)\s+(\d+)", re.sub(r"<[^>]+>", "", sen))
    return int(m.group(1)) if m else None


def slug(t):
    t = unicodedata.normalize("NFKD", t).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", t.lower()).strip("-")


def ordenar_listas(rec, avisos):
    """El SRD italiano ordena por el alfabeto los puntos de algunas listas ("1/giorno" antes que "A volonta").
    Si un rasgo tiene los mismos puntos que el ingles en otro orden, se ponen en el orden del ingles."""
    for l in LANGS:
        if l == "en" or l not in rec:
            continue
        for se, sx in zip(rec["en"]["secciones"], rec[l]["secciones"]):
            if len(se["items"]) != len(sx["items"]):
                continue
            orden = emparejar_items(se["items"], sx["items"], l)
            for ie, k in zip(se["items"], orden):
                ix = sx["items"][k]
                pe = [b for b in ie["bloques"] if b["t"] == "li"]
                px = [b for b in ix["bloques"] if b["t"] == "li"]
                if len(pe) < 2 or len(pe) != len(px):
                    continue
                ke = [clave_punto(b["txt"]) for b in pe]
                kx = [clave_punto(b["txt"]) for b in px]
                if ke == kx or sorted(ke) != sorted(kx) or len(set(ke)) != len(ke):
                    continue
                nuevos = [px[kx.index(c)] for c in ke]
                it = iter(nuevos)
                ix["bloques"] = [next(it) if b["t"] == "li" else b for b in ix["bloques"]]
                avisos.append(f"{l}: {rec[l]['nombre']}: '{ix['nombre']}' con los puntos en el orden del ingles")


def glosario():
    g = []
    with open(GLOSARIO, encoding="utf-8-sig") as f:
        for row in csv.DictReader(f, delimiter=";"):
            if row["categoria"] == "Criaturas":
                g.append(row)
    return g


def main():
    crudo = json.load(open(os.path.join(DATOS, "_criaturas_crudo.json"), encoding="utf-8"))
    en = crudo["en"]
    por_huella = [{}, {}, {}]
    for k, f in enumerate(en):
        for n in range(3):
            por_huella[n].setdefault(huella(f, n), []).append(k)
    repetidas = {h: v for h, v in por_huella[0].items() if len(v) > 1}
    if repetidas:
        print("huellas repetidas en ingles:", [[en[k]["nombre"] for k in v] for v in repetidas.values()])
    pareja = {l: [None] * len(en) for l in LANGS}
    pareja["en"] = list(range(len(en)))
    problemas, aproximadas = [], []
    for l in LANGS:
        if l == "en":
            continue
        pendientes = []
        for j, f in enumerate(crudo[l]):
            cands = por_huella[0].get(huella(f, 0), [])
            k = next((c for c in cands if pareja[l][c] is None), None)
            if k is None:
                pendientes.append(j)
            else:
                pareja[l][k] = j
        # segunda vuelta: huella parcial, solo si deja un unico candidato libre
        for j in pendientes:
            f = crudo[l][j]
            k = None
            for n in (1, 2):
                libres = [c for c in por_huella[n].get(huella(f, n), []) if pareja[l][c] is None]
                if len(libres) == 1:
                    k = libres[0]
                    break
            if k is None:
                problemas.append(f"{l}: {f['nombre']} (p. {f['p']}) sin pareja inglesa; huella {huella(f)}")
                continue
            pareja[l][k] = j
            aproximadas.append(f"{l}: {f['nombre']} = {en[k]['nombre']} (huella parcial)")
    for l in LANGS:
        sin = [en[k]["nombre"] for k in range(len(en)) if pareja[l][k] is None]
        if sin:
            problemas.append(f"{l}: {len(sin)} fichas inglesas sin pareja: {sin[:10]}")
    # contraste con el glosario
    g = glosario()
    col = {"en": "ingles", "es": "espanol", "de": "aleman"}
    nombres = {l: {crudo[l][j]["nombre"]: k for k, j in enumerate(pareja[l]) if j is not None} for l in ("en", "es", "de")}
    en_glosario = 0
    fuera_glosario = []
    for row in g:
        ks = {l: nombres[l].get(row[col[l]]) for l in col}
        if all(v is None for v in ks.values()):
            fuera_glosario.append(row["ingles"])
            continue
        en_glosario += 1
        if len(set(ks.values())) != 1:
            problemas.append(f"glosario casa distinto: {row['espanol']} / {row['ingles']} / {row['aleman']} -> {ks}")
    nombres_glosario = {l: {row[col[l]] for row in g} for l in col}
    for l in col:
        for f in crudo[l]:
            if f["nombre"] not in nombres_glosario[l]:
                problemas.append(f"{l}: {f['nombre']} no esta en el glosario")
    print(f"glosario: {len(g)} criaturas, {en_glosario} casan con fichas de A a Z y animales; "
          f"fuera (fichas dentro de conjuros u objetos): {fuera_glosario}")
    # registros
    salida = []
    ids = set()
    reordenadas = []
    for k, f in enumerate(en):
        pg, dados = parse_pg(f["campos"]["pg"])
        ini, ini_p = parse_ini(f["campos"]["ini"])
        vd = parse_vd(f["campos"]["vd"])
        rec_id = slug(f["nombre"])
        if rec_id in ids:
            problemas.append(f"id repetido: {rec_id}")
        ids.add(rec_id)
        comun = {"ca": int(re.match(r"\s*(\d+)", f["campos"]["ca"]).group(1)), "iniciativa": ini,
                 "iniciativa_puntuacion": ini_p, "pg": pg, "dados_golpe": dados,
                 "car": [x[1] for x in f["car"]], "mod": [signo(x[2]) for x in f["car"]],
                 "salv": [signo(x[3]) for x in f["car"]], **vd,
                 "percepcion_pasiva": pasiva(f["campos"]["sen"]), **parse_tipo_en(f["tipo"]),
                 "capitulo": f["cap"]}
        rec = {"id": rec_id, "comun": comun}
        for l in LANGS:
            j = pareja[l][k]
            if j is None:
                continue
            x = dict(crudo[l][j])
            x.pop("errores", None)
            x.pop("cap", None)
            rec[l] = x
        ordenar_listas(rec, reordenadas)
        salida.append(rec)
    err_corr = aplicar(salida, "correcciones_criaturas.json")
    problemas += [f"correccion: {e}" for e in err_corr]
    print(f"{sum(len(r.get('correcciones', [])) for r in salida)} erratas de traduccion corregidas")
    # despues de corregir, las cifras de la cabecera de cada idioma tienen que ser las del ingles
    for rec in salida:
        c = rec["comun"]
        for l in LANGS:
            x = rec.get(l)
            if x is None:
                continue
            pg_l, dados_l = parse_pg(x["campos"]["pg"])
            ini_l, inip_l = parse_ini(x["campos"]["ini"])
            vd_l = parse_vd(x["campos"]["vd"])
            vd_c = {k: c[k] for k in ("vd", "px", "px_guarida", "bc")}
            if (pg_l, dados_l, ini_l, inip_l, vd_l) != (c["pg"], c["dados_golpe"], c["iniciativa"],
                                                       c["iniciativa_puntuacion"], vd_c):
                problemas.append(f"{l}: {x['nombre']}: cifras de cabecera distintas del ingles")
            if [signo(k[3]) for k in x["car"]] != c["salv"] or [signo(k[2]) for k in x["car"]] != c["mod"]:
                problemas.append(f"{l}: {x['nombre']}: modificadores o salvaciones distintos del ingles")
            if pasiva(x["campos"]["sen"]) != c["percepcion_pasiva"]:
                problemas.append(f"{l}: {x['nombre']}: percepcion pasiva distinta")
    with open(os.path.join(DATOS, "criaturas.json"), "w", encoding="utf-8") as fh:
        json.dump(salida, fh, ensure_ascii=False, indent=1)
    print(f"{len(salida)} criaturas emparejadas -> datos\\criaturas.json")
    print(f"{len(reordenadas)} listas puestas en el orden del ingles")
    print(f"{len(problemas)} problemas")
    for p in problemas:
        print("  ", p)
    return 1 if problemas else 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
