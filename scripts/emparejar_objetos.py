# -*- coding: utf-8 -*-
"""Empareja los objetos magicos de los cinco idiomas y saca sus datos comunes.

Espanol, ingles y aleman: por el glosario de T-0107 (258 objetos). Frances e italiano: por huella con el ingles
(categoria, rareza y sintonizacion de la cabecera, cifras con las medidas inglesas en metros y forma de los
bloques), con asignacion optima. El metodo se prueba en espanol y aleman contra el glosario.

Datos comunes (del ingles): categoria, rarezas, sintonizacion.

Uso: py -3.14 emparejar_objetos.py   (lee datos\\_objetos_crudo.json y deja datos\\objetos.json)
"""
import collections
import csv
import json
import os
import re
import sys

from casa import aplicar_casa
from cifras import cifras, cifras_en
from corregir import aplicar
from emparejar import GLOSARIO, slug
from emparejar_conjuros import forma, texto
from srd import LANGS

AQUI = os.path.dirname(os.path.abspath(__file__))
DATOS = os.path.join(os.path.dirname(AQUI), "datos")

CATEGORIAS = ["Wondrous Item", "Armor", "Weapon", "Potion", "Ring", "Rod", "Scroll", "Staff", "Wand"]
RAREZAS = ["Common", "Uncommon", "Rare", "Very Rare", "Legendary", "Artifact", "Rarity Varies"]
CATEGORIAS_L = {
    "en": {c.lower(): c for c in CATEGORIAS},
    "es": {"objeto maravilloso": "Wondrous Item", "armadura": "Armor", "arma": "Weapon", "poción": "Potion",
           "anillo": "Ring", "vara": "Rod", "pergamino": "Scroll", "bastón": "Staff", "varita": "Wand"},
    "de": {"wundersamer gegenstand": "Wondrous Item", "rüstung": "Armor", "waffe": "Weapon", "trank": "Potion",
           "ring": "Ring", "zepter": "Rod", "schriftrolle": "Scroll", "stab": "Staff", "zauberstab": "Wand"},
    "fr": {"objet merveilleux": "Wondrous Item", "armure": "Armor", "arme": "Weapon", "potion": "Potion",
           "anneau": "Ring", "sceptre": "Rod", "parchemin": "Scroll", "bâton": "Staff", "baguette": "Wand"},
    "it": {"oggetto meraviglioso": "Wondrous Item", "armatura": "Armor", "arma": "Weapon", "pozione": "Potion",
           "anello": "Ring", "verga": "Rod", "pergamena": "Scroll", "bastone": "Staff", "bacchetta": "Wand"},
}


def categoria(cab, lang):
    c = cab.lower()
    for k in sorted(CATEGORIAS_L[lang], key=len, reverse=True):
        if c.startswith(k):
            return CATEGORIAS_L[lang][k]
    return None


def comun_en(o):
    cab = o["cabecera"]
    cuerpo_cab = re.sub(r"\(Requires Attunement[^)]*\)", "", cab)
    rarezas = [r for r in sorted(RAREZAS, key=len, reverse=True) if re.search(rf"\b{r}\b", cuerpo_cab)]
    if "Very Rare" in rarezas and not re.search(r"(?<!Very )\bRare\b", cuerpo_cab):
        rarezas.remove("Rare")
    if "Uncommon" in rarezas and not re.search(r"(?<!Un)\bcommon\b|\bCommon\b", cuerpo_cab.replace("Uncommon", "")):
        rarezas = [r for r in rarezas if r != "Common"]
    orden = {r: k for k, r in enumerate(RAREZAS)}
    m = re.search(r"\(Requires Attunement([^)]*)\)", cab)
    return {"categoria": categoria(cab, "en"), "rarezas": sorted(set(rarezas), key=orden.get),
            "sintonizacion": bool(m), "sintonizacion_por": (m.group(1).strip() or None) if m else None}


def glosario():
    with open(GLOSARIO, encoding="utf-8-sig") as f:
        return [r for r in csv.DictReader(f, delimiter=";") if r["categoria"] == "Objetos mágicos"
                and not r["subcategoria"].startswith("título")]


RAREZAS_L = {  # de la mas larga a la mas corta: "muy rara" antes que "rara"
    "en": [("very rare", "VR"), ("uncommon", "U"), ("rarity varies", "V"), ("rare", "R"), ("common", "C"),
           ("legendary", "L"), ("artifact", "A")],
    "es": [("muy rar[oa]", "VR"), ("infrecuente", "U"), ("rareza variable", "V"), ("rar[oa]", "R"),
           ("común", "C"), ("legendari[oa]", "L"), ("artefacto", "A")],
    "de": [("sehr selten", "VR"), ("ungewöhnlich", "U"), ("seltenheit variiert", "V"), ("selten", "R"),
           ("gewöhnlich", "C"), ("legendär", "L"), ("artefakt", "A")],
    "fr": [("très rare", "VR"), ("peu courante?", "U"), ("rareté variable", "V"), ("rare", "R"),
           ("courante?", "C"), ("légendaire", "L"), ("artefact", "A")],
    "it": [("molto rar[oa]", "VR"), ("non comune", "U"), ("rarità variabile", "V"), ("rar[oa]", "R"),
           ("comune", "C"), ("leggendari[oa]", "L"), ("manufatto", "A")],
}
SINTONIA = {"en": "attunement", "es": "sintonización", "de": "einstimmung", "fr": "harmonisation", "it": "sintonia"}


def rarezas(cab, lang):
    t = re.sub(r"\([^)]*\)", " ", cab.lower())
    out = set()
    for rx, k in RAREZAS_L[lang]:
        if re.search(r"\b" + rx + r"\b", t):
            out.add(k)
            t = re.sub(r"\b" + rx + r"\b", " ", t)
    return frozenset(out)


# Caracteristicas nombradas en el texto: distinguen objetos con las mismas cifras (los tomos, los manuales)
CARACT_L = {
    "en": ["strength", "dexterity", "constitution", "intelligence", "wisdom", "charisma"],
    "es": ["fuerza", "destreza", "constitución", "inteligencia", "sabiduría", "carisma"],
    "de": ["stärke", "geschicklichkeit", "konstitution", "intelligenz", "weisheit", "charisma"],
    "fr": ["force", "dextérité", "constitution", "intelligence", "sagesse", "charisme"],
    "it": ["forza", "destrezza", "costituzione", "intelligenza", "saggezza", "carisma"],
}


def caracteristicas_citadas(o, lang):
    t = texto_objeto(o).lower()
    return frozenset(k for k, w in enumerate(CARACT_L[lang]) if re.search(r"\b" + w, t))


def _norm(t):
    import unicodedata
    t = unicodedata.normalize("NFKD", t.lower()).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z ]", " ", t)


def emparejar_por_huella(en, otro, lang, problemas, nombres_ref=None):
    """Indice en 'otro' para cada objeto ingles. nombres_ref: nombre en espanol de cada objeto ingles, para
    comparar con los nombres franceses e italianos (lenguas hermanas: "Arco del juramento" y "Arco del
    giuramento")."""
    from difflib import SequenceMatcher
    from scipy.optimize import linear_sum_assignment
    res = [None] * len(en)
    cats = sorted({categoria(o["cabecera"], "en") for o in en}, key=str)
    for cat in cats:
        ie = [k for k, o in enumerate(en) if categoria(o["cabecera"], "en") == cat]
        io = [k for k, o in enumerate(otro) if categoria(o["cabecera"], lang) == cat]
        if len(ie) != len(io):
            problemas.append(f"{lang}: categoria {cat}: {len(io)} objetos y {len(ie)} en ingles")
        ce = {k: cifras_en(en[k]["cabecera"] + " " + texto_objeto(en[k])) for k in ie}
        co = {k: cifras(otro[k]["cabecera"] + " " + texto_objeto(otro[k]), lang) for k in io}
        le = {k: len(texto_objeto(en[k])) for k in ie}
        lo = {k: len(texto_objeto(otro[k])) for k in io}
        re_ = {k: rarezas(en[k]["cabecera"], "en") for k in ie}
        ro = {k: rarezas(otro[k]["cabecera"], lang) for k in io}
        se = {k: SINTONIA["en"] in en[k]["cabecera"].lower() for k in ie}
        so = {k: SINTONIA[lang] in otro[k]["cabecera"].lower() for k in io}
        be = {k: collections.Counter(b["t"] for b in en[k]["bloques"]) for k in ie}
        bo = {k: collections.Counter(b["t"] for b in otro[k]["bloques"]) for k in io}
        ke = {k: caracteristicas_citadas(en[k], "en") for k in ie}
        ko = {k: caracteristicas_citadas(otro[k], lang) for k in io}
        coste = []
        for a in ie:
            fila = []
            for b in io:
                u = sum((ce[a] | co[b]).values())
                jac = sum((ce[a] & co[b]).values()) / u if u else 1.0
                s = 0.25 * jac + 0.1 * (be[a] == bo[b]) + 0.12 * (re_[a] == ro[b]) + 0.1 * (se[a] == so[b]) + \
                    0.13 * min(le[a], lo[b]) / max(le[a], lo[b], 1) + 0.1 * (ke[a] == ko[b])
                if nombres_ref:
                    s += 0.2 * SequenceMatcher(None, _norm(nombres_ref[a]), _norm(otro[b]["nombre"])).ratio()
                else:
                    s *= 1 / 0.8
                fila.append(-s)
            coste.append(fila)
        if not ie or not io:
            continue
        filas, cols = linear_sum_assignment(coste)
        for f, c in zip(filas, cols):
            res[ie[f]] = io[c]
            if -coste[f][c] < 0.6 and (lang, otro[io[c]]["nombre"]) not in PARECIDO_BAJO_REVISADO:
                problemas.append(f"{lang}: {otro[io[c]]['nombre']} = {en[ie[f]]['nombre']} con parecido "
                                 f"{-coste[f][c]:.2f}")
    return res


# Emparejados con poco parecido revisados a mano el 13/10/2026: el nombre es la traduccion correcta y las cifras
# distintas son de la propia traduccion (se miran en comprobar_objetos.py)
PARECIDO_BAJO_REVISADO = {("fr", "Armure de résistance"), ("it", "Armatura della resistenza"),
                          ("it", "Arco del giuramento"), ("fr", "Bottes des terres gelées"),
                          ("it", "Stivali dell'inverno"), ("fr", "Tarot mystérieux"), ("it", "Mazzo delle meraviglie"),
                          ("fr", "Talisman du bien ultime"), ("it", "Specchio imprigionante")}


def texto_objeto(o):
    return texto(dict(o, tiempo="", alcance="", comp="", dur=""))


def construir():
    crudo = json.load(open(os.path.join(DATOS, "_objetos_crudo.json"), encoding="utf-8"))
    en = crudo["en"]
    problemas = []
    for l in LANGS:
        sin = [o["nombre"] for o in crudo[l] if categoria(o["cabecera"], l) is None]
        if sin:
            problemas.append(f"{l}: categoria sin reconocer en {sin[:5]}")
    pareja = {"en": list(range(len(en)))}
    col = {"en": "ingles", "es": "espanol", "de": "aleman"}
    idx = {l: {o["nombre"]: k for k, o in enumerate(crudo[l])} for l in col}
    for l in ("es", "de"):
        pareja[l] = [None] * len(en)
    for row in glosario():
        k = idx["en"].get(row["ingles"])
        if k is None:
            problemas.append(f"glosario: '{row['ingles']}' no esta en el SRD ingles")
            continue
        for l in ("es", "de"):
            j = idx[l].get(row[col[l]])
            if j is None:
                problemas.append(f"glosario: '{row[col[l]]}' ({l}) no esta en su SRD")
            pareja[l][k] = j
    nombres_es = [crudo["es"][pareja["es"][k]]["nombre"] if pareja["es"][k] is not None else "" for k in range(len(en))]
    for l in ("fr", "it"):
        pareja[l] = emparejar_por_huella(en, crudo[l], l, problemas, nombres_es)
    for l in ("es", "de"):
        prueba = emparejar_por_huella(en, crudo[l], l, [])
        mal = [en[k]["nombre"] for k in range(len(en)) if prueba[k] != pareja[l][k]]
        print(f"prueba del emparejado por huella en {l}: {len(en) - len(mal)} de {len(en)} como el glosario"
              + (f"; distintos: {mal[:10]}" if mal else ""))
    salida, ids = [], set()
    for k, o in enumerate(en):
        rec = {"id": slug(o["nombre"]), "comun": comun_en(o)}
        if rec["id"] in ids:
            problemas.append(f"id repetido {rec['id']}")
        ids.add(rec["id"])
        for l in LANGS:
            j = pareja[l][k]
            if j is None:
                problemas.append(f"{o['nombre']}: sin pareja en {l}")
                continue
            x = crudo[l][j]
            rec[l] = x
            # los bloques pueden ir en otro orden o partidos de otra manera (cada SRD ordena las cartas de las
            # barajas por su alfabeto y parte las tablas donde le cae): lo cuenta comprobar_objetos.py
        salida.append(rec)
    print("normas de casa:", aplicar_casa(salida))
    return salida, problemas


def main():
    salida, problemas = construir()
    err = aplicar(salida, "correcciones_objetos.json")
    problemas += [f"correccion: {e}" for e in err]
    print(f"{sum(len(r.get('correcciones', [])) for r in salida)} erratas de traduccion corregidas")
    with open(os.path.join(DATOS, "objetos.json"), "w", encoding="utf-8", newline="\n") as fh:
        json.dump(salida, fh, ensure_ascii=False, indent=1)
    print(f"{len(salida)} objetos -> datos\\objetos.json; {len(problemas)} problemas")
    for p in problemas:
        print("  ", p)
    return 1 if problemas else 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
