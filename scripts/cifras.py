# -*- coding: utf-8 -*-
"""Cifras de un texto para comparar idiomas: dados, CD, bonificadores, usos y distancias.

El ingles mide en pies y los otros cuatro SRD en metros (5 pies = 1,5 m; 1 milla = 1,5 km; 1 pulgada = 2,5 cm;
1 libra = 0,5 kg), asi que las medidas inglesas se pasan a metros antes de comparar.
"""
import collections
import re

from marcas import sin_marcas

DIST_EN = re.compile(r"(\d+(?:,\d{3})*)\+?(?:[- ]| )(feet|foot[a-z]*|ft\.?|miles?|mile|inch(?:es)?|pounds?|lb\.?)(?!\w)")
CM = re.compile(r"(\d+(?:,\d+)?)\s?(?:cm|Zentimeter[n]?|centim[eè]tr[eoi]s?|centímetros?)\b")
ALCANCE_EN = re.compile(r"(\d+)/(\d+)(?:[- ]| )(feet|ft\.?)")  # "range 20/60 ft."
NUMERO = re.compile(r"\d+(?:[.,]\d+)?")
FACTOR = {"f": 0.3, "m": 1.5, "i": 2.5, "p": 0.5, "l": 0.5}

# Numeros con letra delante de una unidad ("neun Metern", "eine Minute"): el ingles los pone con cifra.
PALABRAS = {
    "en": ({"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9,
            "ten": 10},
           r"(?:minutes?|hours?|rounds?|days?|years?)"),
    "de":({"ein": 1, "eine": 1, "einen": 1, "einem": 1, "einer": 1, "zwei": 2, "drei": 3, "vier": 4, "fünf": 5,
            "sechs": 6, "sieben": 7, "acht": 8, "neun": 9, "zehn": 10, "elf": 11, "zwölf": 12, "zwanzig": 20,
            "dreißig": 30, "hundert": 100},
           r"(?:Meter|Metern|Minute|Minuten|Stunde|Stunden|Runde|Runden|Tag|Tage|Tagen|Kilometer|Kilometern|"
           r"Zentimeter|Zentimetern|Kilogramm|Jahr|Jahre|Jahren)"),
    "es": ({"un": 1, "una": 1, "dos": 2, "tres": 3, "cuatro": 4, "cinco": 5, "seis": 6, "siete": 7, "ocho": 8,
            "nueve": 9, "diez": 10},
           r"(?:metros?|minutos?|horas?|asaltos?|días?|kilómetros?|centímetros?|años?)"),
    "fr": ({"un": 1, "une": 1, "deux": 2, "trois": 3, "quatre": 4, "cinq": 5, "six": 6, "sept": 7, "huit": 8,
            "neuf": 9, "dix": 10},
           r"(?:mètres?|minutes?|heures?|rounds?|jours?|kilomètres?|centimètres?|ans?)"),
    "it": ({"un": 1, "una": 1, "uno": 1, "due": 2, "tre": 3, "quattro": 4, "cinque": 5, "sei": 6, "sette": 7,
            "otto": 8, "nove": 9, "dieci": 10},
           r"(?:metr[oi]|minut[oi]|or[ae]|round|giorn[oi]|chilometr[oi]|centimetr[oi]|ann[oi])"),
}


def _palabras_a_cifras(t, lang):
    if lang not in PALABRAS:
        return t
    mapa, unidades = PALABRAS[lang]
    rx = re.compile(r"\b(" + "|".join(sorted(mapa, key=len, reverse=True)) + r")\s+(?=" + unidades + r"\b)",
                    re.IGNORECASE)
    return rx.sub(lambda m: str(mapa[m.group(1).lower()]) + " ", t)


def _fmt(x):
    x = round(x, 2)
    return str(int(x)) if x == int(x) else str(x)


def cifras_en(txt):
    """Numeros del texto ingles, con las medidas ya en el sistema metrico."""
    t = _palabras_a_cifras(sin_marcas(txt), "en")
    out = []

    def medida(m):
        n = int(m.group(1).replace(",", ""))
        out.append(_fmt(n * FACTOR[m.group(2)[0]]))
        return " "

    def alcance(m):
        out.extend([_fmt(int(m.group(1)) * 0.3), _fmt(int(m.group(2)) * 0.3)])
        return " "

    t = ALCANCE_EN.sub(alcance, t)
    t = DIST_EN.sub(medida, t)
    t = re.sub(r"(\d),(\d{3})", r"\1\2", t)
    out += [_fmt(float(x.replace(",", "."))) for x in NUMERO.findall(t)]
    return collections.Counter(out)


def cifras(txt, lang=None):
    """Numeros de un texto en espanol, aleman, frances o italiano."""
    t = _palabras_a_cifras(sin_marcas(txt), lang)
    t = re.sub(r"(\d)[.   ](\d{3})\b", r"\1\2", t)  # millares

    def cm(m):
        n = float(m.group(1).replace(",", "."))
        return _fmt(n / 100) + " m" if n >= 30 else m.group(0)  # 30 cm = 1 pie; 2,5 cm = 1 pulgada se queda

    t = CM.sub(cm, t)
    t = re.sub(r"(\d)W(\d)", r"\1d\2", t)  # dados alemanes
    return collections.Counter(_fmt(float(x.replace(",", "."))) for x in NUMERO.findall(t))


def texto_item(it):
    return " ".join([it["nombre"]] + [b["txt"] for b in it["bloques"]])


def emparejar_items(items_en, items_l, lang):
    """Orden de items_l que corresponde a items_en (cada SRD ordena los rasgos por su alfabeto), por parecido de
    cifras, de parrafos y de largo."""
    from scipy.optimize import linear_sum_assignment
    n = len(items_en)
    if n <= 1 or len(items_l) != n:
        return list(range(min(n, len(items_l))))
    ce = [cifras_en(texto_item(i)) for i in items_en]
    cl = [cifras(texto_item(i), lang) for i in items_l]
    le = [len(sin_marcas(texto_item(i))) for i in items_en]
    ll = [len(sin_marcas(texto_item(i))) for i in items_l]
    coste = []
    for a in range(n):
        fila = []
        for b in range(n):
            union = sum((ce[a] | cl[b]).values())
            jac = sum((ce[a] & cl[b]).values()) / union if union else 1.0
            par = 1.0 if len(items_en[a]["bloques"]) == len(items_l[b]["bloques"]) else 0.0
            largo = min(le[a], ll[b]) / max(le[a], ll[b])
            fila.append(-(0.6 * jac + 0.15 * par + 0.25 * largo))
        coste.append(fila)
    _, cols = linear_sum_assignment(coste)
    return list(cols)


def clave_punto(txt):
    """Clave de un punto de lista para ordenarlo como el ingles: el primer numero del rotulo ("2/Day Each:"
    -> 2) o 0 si no lleva ("At Will:")."""
    m = re.match(r"\s*<b>(.*?)</b>", txt)
    rot = m.group(1) if m else ""
    n = re.search(r"\d+", rot)
    return int(n.group(0)) if n else 0
