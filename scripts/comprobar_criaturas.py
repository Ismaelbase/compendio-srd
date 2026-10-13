# -*- coding: utf-8 -*-
"""Comprueba datos\\criaturas.json contra los PDF y entre idiomas.

1. Recuento: las fichas de cada idioma frente al "Indice de perfiles" de su SRD (paginas 2 a 4), nombre a nombre.
2. Campos: cada ficha con CA, iniciativa, PG, velocidad, sentidos, idiomas, VD y las seis caracteristicas, y los
   mismos campos de cabecera que la inglesa.
3. Estructura: las mismas secciones, el mismo numero de rasgos y acciones, y de parrafos en cada uno.
4. Cifras: en cada rasgo y accion, los dados, CD, bonificadores y medidas tienen que ser los del ingles.
5. Glosario: los nombres en espanol, ingles y aleman estan en el glosario de T-0107 (lo hace emparejar.py).

Uso: py -3.14 comprobar_criaturas.py [--json F]   Sale con 1 si hay errores.
Las diferencias de cifras salen como AVISO: son candidatas a errata de traduccion (manda el ingles) y se revisan
a mano antes de corregir nada (revisar_cifras.py).
"""
import collections
import json
import os
import re
import sys

from cifras import cifras, cifras_en, emparejar_items, texto_item
from srd import LANGS, en_paginas, limpia

AQUI = os.path.dirname(os.path.abspath(__file__))
DATOS = os.path.join(os.path.dirname(AQUI), "datos")
CAMPOS_CIFRAS = ("vel", "sen", "hab", "inm", "res", "vul")


def indice(lang):
    """Nombres del indice de perfiles de un idioma (paginas 2 a 4), en orden de columnas de texto."""
    rows = en_paginas(lang, 2, 4)
    dentro = False
    nombres, pendientes = [], []
    for r in rows:
        t = limpia(r["t"])
        if r["font"].startswith("GillSans-SemiBold") and r["size"] >= 20:
            dentro = dentro or r["col"] == 1 or "ndice" in t or "Index" in t or "Verzeichnis" in t
            continue
        if not dentro:
            continue
        m = re.match(r"^(.*?)\.{3,}\s*(\d+)$", t)
        if m:
            # un nombre en dos lineas: la primera queda justo encima, a la misma x (el indice tiene columnas
            # estrechas y el orden de lectura las mezcla)
            arriba = next((q for q in pendientes if -3 < r["x"] - q["x"] < 9 and q["p"] == r["p"]
                           and 0 < r["yb"] - q["yb"] < 14), None)
            if arriba is not None:
                pendientes.remove(arriba)
                nombres.append(limpia(limpia(arriba["t"]) + " " + m.group(1)))
            elif pendientes and pendientes[-1]["yb"] > 700 and r["yb"] < 120:
                # nombre partido entre el pie de una columna y la cabeza de la siguiente
                nombres.append(limpia(limpia(pendientes.pop()["t"]) + " " + m.group(1)))
            else:
                nombres.append(limpia(m.group(1)))
        elif not re.fullmatch(r"\d+", t) and "5.2" not in t:
            pendientes.append(r)
    return nombres


def main():
    salida_json = sys.argv[sys.argv.index("--json") + 1] if "--json" in sys.argv else None
    datos = json.load(open(os.path.join(DATOS, "criaturas.json"), encoding="utf-8"))
    errores, avisos = [], []
    # 1. indice
    for l in LANGS:
        idx = indice(l)
        nombres = [r[l]["nombre"] for r in datos if l in r]
        faltan = sorted(set(idx) - set(nombres))
        sobran = sorted(set(nombres) - set(idx))
        print(f"{l}: indice {len(idx)}, fichas {len(nombres)}; en el indice y sin ficha {len(faltan)}, "
              f"ficha y no en el indice {len(sobran)}")
        errores += [f"{l}: '{n}' esta en el indice y no hay ficha con ese nombre" for n in faltan]
        errores += [f"{l}: ficha '{n}' que no esta en el indice" for n in sobran]
    # 2 a 4
    for r in datos:
        base = r["en"]
        forma_en = [(s["clave"], len(s["items"]), bool(s["intro"])) for s in base["secciones"]]
        for l in LANGS:
            x = r.get(l)
            if x is None:
                errores.append(f"{r['id']}: falta el idioma {l}")
                continue
            for c in ("ca", "ini", "pg", "vel", "sen", "idi", "vd"):
                if not x["campos"].get(c):
                    errores.append(f"{l}: {x['nombre']}: falta {c}")
            if len(x["car"]) != 6 or any(len(c) != 4 for c in x["car"]):
                errores.append(f"{l}: {x['nombre']}: caracteristicas incompletas")
            if set(x["campos"]) != set(base["campos"]):
                errores.append(f"{l}: {x['nombre']}: campos {sorted(x['campos'])} frente a {sorted(base['campos'])}")
            forma = [(s["clave"], len(s["items"]), bool(s["intro"])) for s in x["secciones"]]
            if forma != forma_en:
                errores.append(f"{l}: {x['nombre']}: secciones {forma} frente a {forma_en}")
                continue
            if l == "en":
                continue
            for se, sx in zip(base["secciones"], x["secciones"]):
                orden = emparejar_items(se["items"], sx["items"], l)
                for ie, ix in zip(se["items"], [sx["items"][k] for k in orden]):
                    if [b["t"] for b in ie["bloques"]] != [b["t"] for b in ix["bloques"]]:
                        errores.append(f"{l}: {x['nombre']}: '{ix['nombre']}' tiene los parrafos "
                                       f"{[b['t'] for b in ix['bloques']]} y '{ie['nombre']}' "
                                       f"{[b['t'] for b in ie['bloques']]}")
                    te, tx = texto_item(ie), texto_item(ix)
                    ce, cx = cifras_en(te), cifras(tx, l)
                    if ce != cx:
                        avisos.append({"id": r["id"], "idioma": l, "ficha": x["nombre"], "seccion": sx["titulo"],
                                       "elemento": ix["nombre"], "elemento_en": ie["nombre"],
                                       "solo_en_ingles": dict(ce - cx), "solo_en_este": dict(cx - ce),
                                       "texto": tx, "texto_en": te})
                if se["intro"]:
                    ce, cx = cifras_en(se["intro"]), cifras(sx["intro"], l)
                    if ce != cx:
                        avisos.append({"id": r["id"], "idioma": l, "ficha": x["nombre"], "seccion": sx["titulo"],
                                       "elemento": "(introduccion)", "elemento_en": "(intro)",
                                       "solo_en_ingles": dict(ce - cx), "solo_en_este": dict(cx - ce),
                                       "texto": sx["intro"], "texto_en": se["intro"]})
            for c in CAMPOS_CIFRAS:
                if c in base["campos"]:
                    ce, cx = cifras_en(base["campos"][c]), cifras(x["campos"].get(c, ""), l)
                    if ce != cx:
                        avisos.append({"id": r["id"], "idioma": l, "ficha": x["nombre"], "seccion": "cabecera",
                                       "elemento": c, "elemento_en": c, "solo_en_ingles": dict(ce - cx),
                                       "solo_en_este": dict(cx - ce), "texto": x["campos"].get(c, ""),
                                       "texto_en": base["campos"][c]})
    # las diferencias ya revisadas a mano y que no son errata no se vuelven a avisar
    rev = json.load(open(os.path.join(DATOS, "revisados_criaturas.json"), encoding="utf-8"))["revisados"]
    claves_rev = {(x["id"], x["idioma"], x["elemento"]) for x in rev}
    usados = {(a["id"], a["idioma"], a["elemento"]) for a in avisos} & claves_rev
    for x in sorted(claves_rev - usados):
        errores.append(f"revisado que ya no sale (sobra en revisados_criaturas.json): {x}")
    revisados = [a for a in avisos if (a["id"], a["idioma"], a["elemento"]) in claves_rev]
    avisos = [a for a in avisos if (a["id"], a["idioma"], a["elemento"]) not in claves_rev]
    por_idioma = collections.Counter(a["idioma"] for a in avisos)
    print(f"{len(errores)} errores; {len(avisos)} avisos de cifras sin revisar {dict(por_idioma)}; "
          f"{len(revisados)} revisados sin errata")
    for e in errores[:60]:
        print("  ERROR", e)
    if salida_json:
        with open(salida_json, "w", encoding="utf-8") as f:
            json.dump({"errores": errores, "avisos": avisos}, f, ensure_ascii=False, indent=1)
    return 1 if errores else 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
