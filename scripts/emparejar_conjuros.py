# -*- coding: utf-8 -*-
"""Empareja los conjuros de los cinco idiomas y saca sus datos comunes.

Espanol, ingles y aleman: por el glosario de T-0107 (339 conjuros). Frances e italiano no estan en el glosario: se
emparejan con el ingles por huella dentro de cada nivel (numero de clases, cifras del conjuro con las medidas
inglesas pasadas a metros y forma de los bloques), con asignacion optima. Un emparejado con poco parecido sale
como problema para mirarlo.

Datos comunes (del ingles): nivel, escuela, clases, ritual, concentracion, componentes V/S/M y coste del
material.

Uso: py -3.14 emparejar_conjuros.py   (lee datos\\_conjuros_crudo.json y deja datos\\conjuros.json)
"""
import csv
import json
import os
import re
import sys

from casa import aplicar_casa
from cifras import cifras, cifras_en
from corregir import aplicar
from emparejar import GLOSARIO, slug
from srd import LANGS

AQUI = os.path.dirname(os.path.abspath(__file__))
DATOS = os.path.join(os.path.dirname(AQUI), "datos")

ESCUELAS = ["Abjuration", "Conjuration", "Divination", "Enchantment", "Evocation", "Illusion", "Necromancy",
            "Transmutation"]
CLASES = ["Bard", "Cleric", "Druid", "Paladin", "Ranger", "Sorcerer", "Warlock", "Wizard"]


# Clases y escuelas en la cabecera de cada idioma (para emparejar el frances y el italiano)
CLASES_L = {
    "en": {c.lower(): c for c in CLASES},
    "es": {"bardo": "Bard", "clérigo": "Cleric", "druida": "Druid", "paladín": "Paladin", "explorador": "Ranger",
           "hechicero": "Sorcerer", "brujo": "Warlock", "mago": "Wizard"},
    "de": {"barde": "Bard", "kleriker": "Cleric", "druide": "Druid", "paladin": "Paladin", "waldläufer": "Ranger",
           "zauberer": "Sorcerer", "hexenmeister": "Warlock", "magier": "Wizard"},
    "fr": {"barde": "Bard", "clerc": "Cleric", "druide": "Druid", "paladin": "Paladin", "rôdeur": "Ranger",
           "ensorceleur": "Sorcerer", "occultiste": "Warlock", "magicien": "Wizard"},
    "it": {"bardo": "Bard", "chierico": "Cleric", "druido": "Druid", "paladino": "Paladin", "ranger": "Ranger",
           "stregone": "Sorcerer", "warlock": "Warlock", "mago": "Wizard"},
}
ESCUELAS_L = {  # principio de la palabra -> escuela (en italiano, Conjuration es Evocazione y Evocation es Invocazione)
    "en": {e.lower(): e for e in ESCUELAS},
    "es": {"abjuración": "Abjuration", "conjuración": "Conjuration", "adivinación": "Divination",
           "encantamiento": "Enchantment", "evocación": "Evocation", "ilusión": "Illusion",
           "nigromancia": "Necromancy", "transmutación": "Transmutation"},
    "de": {"bann": "Abjuration", "beschwörung": "Conjuration", "erkenntnis": "Divination",
           "verzauberung": "Enchantment", "hervorrufung": "Evocation", "illusion": "Illusion",
           "nekromantie": "Necromancy", "verwandlung": "Transmutation"},
    "fr": {"abjuration": "Abjuration", "invocation": "Conjuration", "divination": "Divination",
           "enchantement": "Enchantment", "évocation": "Evocation", "illusion": "Illusion",
           "nécromancie": "Necromancy", "transmutation": "Transmutation"},
    "it": {"abiurazione": "Abjuration", "evocazione": "Conjuration", "divinazione": "Divination",
           "ammaliamento": "Enchantment", "invocazione": "Evocation", "illusione": "Illusion",
           "necromanzia": "Necromancy", "trasmutazione": "Transmutation"},
}


def clases_y_escuela(c, lang):
    cab = c["cabecera"].lower()
    m = re.search(r"\((.*)\)", cab)
    clases = frozenset(CLASES_L[lang].get(x.strip()) for x in m.group(1).split(",")) if m else frozenset()
    sin_clases = re.sub(r"\(.*\)", "", cab)
    escuela = next((e for k, e in ESCUELAS_L[lang].items() if re.search(r"\b" + k, sin_clases)), None)
    return clases, escuela


def nivel(cabecera):
    m = re.search(r"\d", cabecera)
    return int(m.group(0)) if m else 0


def n_clases(cabecera):
    m = re.search(r"\((.*)\)", cabecera)
    return len(m.group(1).split(",")) if m else 0


def texto(c):
    partes = [c.get(k, "") for k in ("tiempo", "alcance", "comp", "dur")]
    for b in c["bloques"]:
        if b["t"] in ("p", "li"):
            partes.append(b["txt"])
        elif b["t"] == "tabla":
            partes += [x for fila in b["filas"] for x in fila]
        elif b["t"] == "ficha":
            partes += [b.get("ca", ""), b.get("pg", "")]
    return " ".join(partes)


def forma(c):
    return tuple(b["t"] + (b.get("sup") or "") for b in c["bloques"])


def comun_en(c):
    cab = c["cabecera"]
    m = re.search(r"\((.*)\)", cab)
    clases = [x.strip() for x in m.group(1).split(",")] if m else []
    comp = c["comp"]
    mat = re.search(r"M \((.*)\)", comp)
    coste = None
    if mat:
        mc = re.search(r"([\d,]+)\+? GP", mat.group(1))
        coste = int(mc.group(1).replace(",", "")) if mc else None
    return {
        "nivel": nivel(cab),
        "escuela": next((e for e in ESCUELAS if e in cab), None),
        "clases": clases,
        "ritual": "Ritual" in c["tiempo"],
        "concentracion": c["dur"].startswith("Concentration"),
        "componentes": [x for x in ("V", "S", "M") if re.search(rf"(^|, ){x}\b", comp)],
        "material_po": coste,
        "material_consume": bool(mat and "consume" in mat.group(1)),
    }


def glosario():
    g = []
    with open(GLOSARIO, encoding="utf-8-sig") as f:
        for row in csv.DictReader(f, delimiter=";"):
            if row["categoria"] == "Conjuros":
                g.append(row)
    return g


def emparejar_por_huella(en, otro, lang, problemas):
    """Indice en 'otro' para cada conjuro ingles, por nivel y parecido."""
    from scipy.optimize import linear_sum_assignment
    res = [None] * len(en)
    for nv in range(10):
        ie = [k for k, c in enumerate(en) if nivel(c["cabecera"]) == nv]
        io = [k for k, c in enumerate(otro) if nivel(c["cabecera"]) == nv]
        if len(ie) != len(io):
            problemas.append(f"{lang}: nivel {nv}: {len(io)} conjuros y {len(ie)} en ingles")
        ce = {k: cifras_en(texto(en[k])) for k in ie}
        co = {k: cifras(texto(otro[k]), lang) for k in io}
        ke = {k: clases_y_escuela(en[k], "en") for k in ie}
        ko = {k: clases_y_escuela(otro[k], lang) for k in io}
        for k in io:
            if None in ko[k][0] or ko[k][1] is None:
                problemas.append(f"{lang}: {otro[k]['nombre']}: clase o escuela sin reconocer en '{otro[k]['cabecera']}'")
        coste = []
        for a in ie:
            fila = []
            for b in io:
                union = sum((ce[a] | co[b]).values())
                jac = sum((ce[a] & co[b]).values()) / union if union else 1.0
                s = 0.4 * jac + 0.15 * (forma(en[a]) == forma(otro[b])) + \
                    0.25 * (ke[a][0] == ko[b][0]) + 0.2 * (ke[a][1] == ko[b][1])
                fila.append(-s)
            coste.append(fila)
        filas, cols = linear_sum_assignment(coste)
        for f, c in zip(filas, cols):
            res[ie[f]] = io[c]
            if -coste[f][c] < 0.6:
                problemas.append(f"{lang}: {otro[io[c]]['nombre']} = {en[ie[f]]['nombre']} con parecido "
                                 f"{-coste[f][c]:.2f}")
    return res


def construir():
    """Conjuros emparejados y con las normas de casa, sin las erratas (las pone main)."""
    crudo = json.load(open(os.path.join(DATOS, "_conjuros_crudo.json"), encoding="utf-8"))
    en = crudo["en"]
    problemas = []
    pareja = {"en": list(range(len(en)))}
    # glosario para espanol y aleman
    g = glosario()
    col = {"en": "ingles", "es": "espanol", "de": "aleman"}
    idx = {l: {c["nombre"]: k for k, c in enumerate(crudo[l])} for l in col}
    for l in ("es", "de"):
        pareja[l] = [None] * len(en)
    for row in g:
        k = idx["en"].get(row["ingles"])
        if k is None:
            problemas.append(f"glosario: '{row['ingles']}' no esta en el SRD ingles")
            continue
        for l in ("es", "de"):
            j = idx[l].get(row[col[l]])
            if j is None:
                problemas.append(f"glosario: '{row[col[l]]}' ({l}) no esta en su SRD")
            pareja[l][k] = j
    for l in ("fr", "it"):
        pareja[l] = emparejar_por_huella(en, crudo[l], l, problemas)
    # el emparejado por huella tiene que dar lo mismo que el glosario en espanol y aleman (prueba del metodo)
    for l in ("es", "de"):
        prueba = emparejar_por_huella(en, crudo[l], l, [])
        mal = [en[k]["nombre"] for k in range(len(en)) if prueba[k] != pareja[l][k]]
        print(f"prueba del emparejado por huella en {l}: {len(en) - len(mal)} de {len(en)} como el glosario"
              + (f"; distintos: {mal[:8]}" if mal else ""))
    salida, ids = [], set()
    for k, c in enumerate(en):
        rec = {"id": slug(c["nombre"]), "comun": comun_en(c)}
        if rec["id"] in ids:
            problemas.append(f"id repetido {rec['id']}")
        ids.add(rec["id"])
        for l in LANGS:
            j = pareja[l][k]
            if j is None:
                problemas.append(f"{c['nombre']}: sin pareja en {l}")
                continue
            x = crudo[l][j]
            rec[l] = x
            if l != "en" and nivel(x["cabecera"]) != rec["comun"]["nivel"]:
                problemas.append(f"{l}: {x['nombre']}: nivel distinto del ingles")
            if l != "en" and forma(x) != forma(c):
                problemas.append(f"{l}: {x['nombre']}: bloques {forma(x)} frente a {forma(c)}")
        salida.append(rec)
    # primero las normas de casa: las erratas de las cartas estan escritas sobre el texto ya con ellas
    print("normas de casa:", aplicar_casa(salida))
    return salida, problemas


def main():
    salida, problemas = construir()
    err = aplicar(salida, "correcciones_conjuros.json") + aplicar(salida, "correcciones_conjuros_revision.json")
    problemas += [f"correccion: {e}" for e in err]
    print(f"{sum(len(r.get('correcciones', [])) for r in salida)} erratas de traduccion corregidas")
    with open(os.path.join(DATOS, "conjuros.json"), "w", encoding="utf-8", newline="\n") as fh:
        json.dump(salida, fh, ensure_ascii=False, indent=1)
    print(f"{len(salida)} conjuros -> datos\\conjuros.json; {len(problemas)} problemas")
    for p in problemas:
        print("  ", p)
    return 1 if problemas else 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
