# -*- coding: utf-8 -*-
"""Medidas en pies y libras para el ajuste "pies" del plugin (decision de Ismael del 13/10/2026).

El SRD en espanol, aleman, frances e italiano mide en metros (1,5 m por cada 5 pies). Este paso hace, para cada
texto de esos cuatro idiomas que lleva medidas, su version en pies, millas, pulgadas, libras y galones, y la
guarda junto al texto original en "pies": {ruta: texto}.

La cifra no se calcula a ojo: cada medida pasada se busca entre las medidas del SRD ingles de la misma entrada
(que mide en pies). Si esta, va esa cifra; si no esta, va la conversion de la tabla (1,5 m = 5 pies, 1,5 km =
1 milla, 2,5 cm = 1 pulgada, 0,5 kg = 1 libra, 4 l = 1 galon) y sale como aviso para revisarla.

Uso: py -3.14 pies.py [--json F]   (escribe "pies" en datos\\criaturas.json, conjuros.json, objetos.json y
estados.json; sale con 1 si queda alguna medida sin pasar o sin respaldo en el ingles)
"""
import collections
import json
import os
import re
import sys

from marcas import sin_marcas

AQUI = os.path.dirname(os.path.abspath(__file__))
DATOS = os.path.join(os.path.dirname(AQUI), "datos")
LANGS_M = ("es", "de", "fr", "it")

PALABRAS = {
    "es": {"un": 1, "una": 1, "uno": 1, "dos": 2, "tres": 3, "cuatro": 4, "cinco": 5, "seis": 6, "siete": 7,
           "ocho": 8, "nueve": 9, "diez": 10, "doce": 12, "quince": 15, "veinte": 20, "treinta": 30},
    "de": {"ein": 1, "eine": 1, "einen": 1, "einem": 1, "einer": 1, "eines": 1, "zwei": 2, "drei": 3, "vier": 4,
           "fünf": 5, "sechs": 6, "sieben": 7, "acht": 8, "neun": 9, "zehn": 10, "elf": 11, "zwölf": 12,
           "fünfzehn": 15, "achtzehn": 18, "zwanzig": 20, "dreißig": 30},
    "fr": {"un": 1, "une": 1, "deux": 2, "trois": 3, "quatre": 4, "cinq": 5, "six": 6, "sept": 7, "huit": 8,
           "neuf": 9, "dix": 10, "douze": 12, "quinze": 15, "vingt": 20, "trente": 30},
    "it": {"un": 1, "uno": 1, "una": 1, "due": 2, "tre": 3, "quattro": 4, "cinque": 5, "sei": 6, "sette": 7,
           "otto": 8, "nove": 9, "dieci": 10, "dodici": 12, "quindici": 15, "venti": 20, "trenta": 30},
}
# unidad del texto -> clase de medida
UNIDADES = {
    "es": [(r"m2|m²|metros cuadrados", "area"), (r"m3|m³|metros cúbicos", "vol"), (r"km|kilómetros?", "km"),
           (r"cm|centímetros?", "cm"), (r"mm|milímetros?", "mm"), (r"kg|kilos?|kilogramos?", "kg"), (r"g|gramos?", "g"), (r"l|litros?", "l"),
           (r"m|metros?", "m")],
    "de": [(r"Quadratmeter[n]?|m2|m²", "area"), (r"Kubikmeter[n]?|m3|m³", "vol"), (r"km|Kilometer[n]?", "km"),
           (r"cm|Zentimeter[n]?", "cm"), (r"mm|Millimeter[n]?", "mm"), (r"kg|Kilogramm|Kilo", "kg"), (r"g|Gramm", "g"), (r"l|Liter[n]?", "l"),
           (r"m|Meter[n]?", "m")],
    "fr": [(r"m2|m²|mètres carrés", "area"), (r"m3|m³|mètres cubes", "vol"), (r"km|kilomètres?", "km"),
           (r"cm|centimètres?", "cm"), (r"mm|millimètres?", "mm"), (r"kg|kilos?|kilogrammes?", "kg"), (r"g|grammes?", "g"), (r"l|litres?", "l"),
           (r"m|mètres?", "m")],
    "it": [(r"m2|m²|metri quadrati|metri quadri", "area"), (r"m3|m³|metri cubi", "vol"), (r"km|chilometri|chilometro", "km"),
           (r"cm|centimetri|centimetro", "cm"), (r"mm|millimetri|millimetro", "mm"), (r"kg|chili|chilo|chilogrammi", "kg"), (r"g|grammi|grammo", "g"),
           (r"l|litri|litro", "l"), (r"m|metri|metro", "m")],
}
# clase de medida -> [(factor del valor metrico a la unidad inglesa, clase inglesa)]: se elige la que esta en el
# ingles de la misma entrada (los litros pueden ser galones, pintas o pies cubicos; los centimetros, pulgadas o
# pies; los metros, pies o millas); si no esta ninguna, la primera
CANDIDATOS = {"m": [(1 / 0.3, "ft"), (1 / 1500, "mi")], "km": [(1 / 1.5, "mi"), (1000 / 0.3, "ft")],
              "cm": [(1 / 2.5, "in"), (1 / 30, "ft")], "mm": [(1 / 25, "in")], "kg": [(2.0, "lb")], "g": [(1 / 500, "lb"), (1 / 30, "oz")],
              "l": [(0.25, "gal"), (2.0, "pt"), (1 / 28.3, "cuft")],
              "area": [(1 / 0.09, "sqft")], "vol": [(1 / 0.027, "cuft")]}
# palabras de salida: (singular, plural)
SALIDA = {
    "es": {"ft": ("pie", "pies"), "mi": ("milla", "millas"), "in": ("pulgada", "pulgadas"), "lb": ("libra", "libras"),
           "gal": ("galón", "galones"), "sqft": ("pie cuadrado", "pies cuadrados"), "cuft": ("pie cúbico", "pies cúbicos"),
           "pt": ("pinta", "pintas"), "oz": ("onza", "onzas")},
    "de": {"ft": ("Fuß", "Fuß"), "mi": ("Meile", "Meilen"), "in": ("Zoll", "Zoll"), "lb": ("Pfund", "Pfund"),
           "gal": ("Gallone", "Gallonen"), "sqft": ("Quadratfuß", "Quadratfuß"), "cuft": ("Kubikfuß", "Kubikfuß"),
           "pt": ("Pint", "Pints"), "oz": ("Unze", "Unzen")},
    "fr": {"ft": ("pied", "pieds"), "mi": ("mile", "miles"), "in": ("pouce", "pouces"), "lb": ("livre", "livres"),
           "gal": ("gallon", "gallons"), "sqft": ("pied carré", "pieds carrés"), "cuft": ("pied cube", "pieds cubes"),
           "pt": ("pinte", "pintes"), "oz": ("once", "onces")},
    "it": {"ft": ("piede", "piedi"), "mi": ("miglio", "miglia"), "in": ("pollice", "pollici"), "lb": ("libbra", "libbre"),
           "gal": ("gallone", "galloni"), "sqft": ("piede quadrato", "piedi quadrati"), "cuft": ("piede cubo", "piedi cubi"),
           "pt": ("pinta", "pinte"), "oz": ("oncia", "once")},
}
MILES = {"es": " ", "de": ".", "fr": " ", "it": "."}

# medidas inglesas: numero + unidad
EN_MEDIDA = re.compile(r"(\d+(?:,\d{3})*(?:\.\d+)?)(?:\+)?(?:[- ]| )(?:by-\d+-)?"
                       r"(square feet|square foot|cubic feet|cubic foot|feet|foot|ft\.?|miles?|inch(?:es)?|pounds?|lb\.?|gallons?|pints?|ounces?)(?![a-z])")
EN_CLASE = {"square feet": "sqft", "square foot": "sqft", "cubic feet": "cuft", "cubic foot": "cuft", "feet": "ft",
            "foot": "ft", "ft": "ft", "ft.": "ft", "mile": "mi", "miles": "mi", "inch": "in", "inches": "in",
            "pound": "lb", "pounds": "lb", "lb": "lb", "lb.": "lb", "gallon": "gal", "gallons": "gal",
            "pint": "pt", "pints": "pt", "ounce": "oz", "ounces": "oz"}


def medidas_en(texto):
    """Cifras inglesas por clase: {clase: Counter(valor)}."""
    out = collections.defaultdict(collections.Counter)
    t = sin_marcas(texto)
    t = re.sub(r"foot(wide|long|high|tall|deep|square|radius)", r"foot-\1", t)  # erratas "5-footwide"
    t = re.sub(r"\b(\d+) (additional|extra|more) (gallons|feet|pounds|miles)", r"\1 \3", t)
    t = re.sub(r"\bhalf a (mile|inch|foot|pound)\b", r"0.5 \1", t)  # antes que "a mile"
    t = re.sub(r"\b(a|an|one) (cubic foot|square foot|foot|inch|mile|pound|gallon|pint|ounce)\b", r"1 \2", t)
    t = re.sub(r"\bhalf[- ](mile|inch|foot)\b", r"0.5 \1", t)
    t = re.sub(r"\b1/2[- ](inch|foot|mile)\b", r"0.5 \1", t)
    t = re.sub(r"\b1/4[- ](inch|foot|mile)\b", r"0.25 \1", t)
    for m in re.finditer(r"(\d+)/(\d+)(?:[- ]| )(?:feet|ft\.?)", t):  # alcance "20/60 ft."
        out["ft"][float(m.group(1))] += 1
        out["ft"][float(m.group(2))] += 1
    for m in EN_MEDIDA.finditer(t):
        out[EN_CLASE[m.group(2)]][float(m.group(1).replace(",", ""))] += 1
    for m in re.finditer(r"\b(one|two|three|four|five|six|seven|eight|nine|ten)\s+(feet|foot|miles?|inch(?:es)?|pounds?)\b", t):
        n = ["one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten"].index(m.group(1)) + 1
        out[EN_CLASE[m.group(2)]][float(n)] += 1
    return out


def _num(t, lang):
    t = t.strip()
    if t.lower() in PALABRAS[lang]:
        return float(PALABRAS[lang][t.lower()])
    return float(t.replace(MILES[lang] if MILES[lang] != " " else " ", "").replace(" ", "").replace(",", "."))


def _fmt(v, lang):
    v = round(v, 2)
    if v == int(v):
        v = int(v)
        s = str(v)
        if v >= 10000:
            s = f"{v:,}".replace(",", MILES[lang])
        return s
    s = str(v).replace(".", ",")
    return s


def regex_medida(lang):
    pal = "|".join(sorted(PALABRAS[lang], key=len, reverse=True))
    unidades = "|".join(f"(?:{u})" for u, _ in UNIDADES[lang])
    num = r"\d{1,3}(?:[.  ]\d{3})+(?:,\d+)?|\d+(?:,\d+)?|(?:" + pal + r")"
    # "6/18 m" (alcance), "1,5 m", "neun Metern"
    # sin IGNORECASE: en aleman "1 KM" es una moneda de cobre, no un kilometro
    return re.compile(r"(?<![\w,])(?:(" + num + r")/)?(" + num + r")(?:\s| |-)(" + unidades + r")(?![\wäöüßàèéìòù²³’'])")  # "quelqu'un l’éteint" no es un litro


_RX = {}


def clase_de(lang, unidad):
    for u, c in UNIDADES[lang]:
        if re.fullmatch(u, unidad):
            return c
    return None


ESPECIALES = {  # frases en las que no basta con multiplicar (cada una mirada contra el ingles)
    "es": [("cada metro de movimiento te cuesta 1 m adicional", "cada pie de movimiento te cuesta 1 pie adicional"),
           ("cada metro de movimiento le cuesta 1 m adicional", "cada pie de movimiento le cuesta 1 pie adicional"),
           ("cada metro de movimiento cuesta 1 m adicional", "cada pie de movimiento cuesta 1 pie adicional"),
           ("gastar 2 m de movimiento por cada metro", "gastar 2 pies de movimiento por cada pie"),
           ("gastar 4 m de movimiento por cada metro", "gastar 4 pies de movimiento por cada pie"),
           ("por cada metro", "por cada pie"),
           ("un radio de 750 m", "un radio de media milla"),
           ("2d12 × 1,5 km", "2d12 millas"),
           ("barrotes de 1,25 cm de diámetro separados 1,25 cm entre sí",
            "barrotes de media pulgada de diámetro separados media pulgada entre sí"),
           ("por cada 30 cm que te hayas movido", "por cada pie que te hayas movido"),
           ("una cantidad de metros igual a 1,5 ×", "una cantidad de pies igual a 5 ×"),
           ("una cantidad de metros adicionales igual a 3 ×", "una cantidad de pies adicionales igual a 10 ×"),
           ("1d3 × 30 cm", "1d3 pies"),
           ("a 750 m o menos de ti", "a media milla o menos de ti"),
           ("3 m de ancho y 3 de alto", "10 pies de ancho y 10 de alto"),
           ("30 g de pegamento pueden", "1 onza de pegamento puede"),
           ("a unos centímetros del suelo", "a unas pulgadas del suelo")],
    "de": [("für jeden Meter, den sie sich auf dich zubewegt, zwei Meter",
            "für jeden Fuß, den sie sich auf dich zubewegt, zwei Fuß"),
           ("für jeden Meter, den sie sich bewegt, vier Meter", "für jeden Fuß, den sie sich bewegt, vier Fuß"),
           ("Für jeden Meter, den sie sich durch die Wand bewegt, muss sie vier Meter",
            "Für jeden Fuß, den sie sich durch die Wand bewegt, muss sie vier Fuß"),
           ("kostet dich jeder Meter Bewegung zwei Meter", "kostet dich jeder Fuß Bewegung zwei Fuß"),
           ("in einem Radius von 0,8 Kilometern", "in einem Radius von einer halben Meile"),
           ("2W12 mal 1,6 Kilometern", "2W12 Meilen"),
           ("Zwischenräumen von jeweils einem Zentimeter Durchmesser",
            "Zwischenräumen von jeweils einem halben Zoll Durchmesser"),
           ("einen halben Zentimeter dick", "einen Viertelzoll dick"),
           ("324 Liter unbelebten Materials (90 mal 60 mal 60 Zentimeter)",
            "12 Kubikfuß unbelebten Materials (3 mal 2 mal 2 Fuß)"),
           ("einem Bereich von 2,3 Quadratmetern", "einem Bereich von 25 Quadratfuß"),
           ("plus 1,5-mal deinen Zauberwirken-Attributsmodifikator (in Metern)",
            "plus 5-mal deinen Zauberwirken-Attributsmodifikator (in Fuß)"),
           ("um eine Anzahl von Metern in Höhe des 1,5-Fachen deiner Erschöpfungsstufe",
            "um eine Anzahl von Fuß in Höhe des Fünffachen deiner Erschöpfungsstufe"),
           ("des 1,5-Fachen deines Intelligenzmodifikators in Metern", "des Fünffachen deines Intelligenzmodifikators in Fuß"),
           ("eine Anzahl von Metern in Höhe des Dreifachen", "eine Anzahl von Fuß in Höhe des Zehnfachen"),
           ("Drei-Meter-Stange", "Zehn-Fuß-Stange"),
           ("im Abstand von bis zu 800 Metern", "im Abstand von bis zu einer halben Meile")],
    "fr": [("2d12 x 1,5 km", "2d12 miles"),
           ("un rayon de 750 m", "un rayon d’un demi-mile"),
           ("barreaux de 1,25 cm de diamètre", "barreaux d’un demi-pouce de diamètre"),
           ("chaque tranche de 30 cm de ce transfert forcé", "chaque pied de ce transfert forcé"),
           ("30 litres (ou 0,03 m3)", "1 pied cube"),
           ("15 cm3 de sa chair", "1 pouce cube de sa chair"),
           ("un coffre de 90 cm par 60 et 60", "un coffre de 3 pieds par 2 et 2"),
           ("en mètres égale à votre modificateur d’Intelligence x 1,5", "en pieds égale à votre modificateur d’Intelligence x 5"),
           ("pour la déplacer, en mètres, d’un maximum de 3 plus le triple de votre modificateur d’Intelligence",
            "pour la déplacer, en pieds, d’un maximum de 10 plus dix fois votre modificateur d’Intelligence"),
           ("1d3 x 30 cm", "1d3 pieds"),
           ("30 cm de diamètre et 15 de profondeur", "1 pied de diamètre et 6 pouces de profondeur"),
           ("(30 cm de long, 15 de large et de profondeur)", "(1 pied de long, 6 pouces de large et de profondeur)"),
           ("pans de 3 m sur 6", "pans de 10 pieds sur 20"),
           ("3 m sur 3", "10 pieds sur 10")],
    "it": [("per ogni 30 centimetri", "per ogni piede"),
           ("un raggio di 750 metri", "un raggio di mezzo miglio"),
           ("2d12 × 1,5 chilometri", "2d12 miglia"),
           ("sbarre di 1,25 centimetri di diametro disposte a 1,25 centimetri di distanza",
            "sbarre di mezzo pollice di diametro disposte a mezzo pollice di distanza"),
           ("uno spessore di 0,6 centimetri", "uno spessore di un quarto di pollice"),
           ("ogni 30 cm di movimento gli costano 30 cm extra", "ogni piede di movimento gli costa un piede extra"),
           ("del numero di metri di cui si è mosso", "del numero di piedi di cui si è mosso"),
           ("più un numero di metri pari a 1,5 volte", "più un numero di piedi pari a cinque volte"),
           ("di una quantità di metri pari a 1,5 × il suo livello", "di una quantità di piedi pari a 5 × il suo livello"),
           ("un numero di metri pari a 1,5 ×", "un numero di piedi pari a 5 ×"),
           ("1d3 x 30 centimetri", "1d3 piedi")],
}
# "entre 1,5 y 6 m", "zwischen 1,5 und 30 Metern": las dos cifras llevan la unidad del final
DOS = {l: re.compile(r"(?<![\d,])(\d+(?:,\d+)?) (y|o|und|oder|et|ou|e) (\d+(?:,\d+)?) (" +
                     "|".join(u for u, c in UNIDADES[l] if c in ("m", "cm", "km")) + r")(?![\wäöüßàèéìòù²³’'])")
       for l in ("es", "de", "fr", "it")}
# "90 x 60 x 60 cm": cada cifra lleva la unidad del final
TRES = re.compile(r"(\d+(?:,\d+)?)\s?([x×])\s?(\d+(?:,\d+)?)\s?\2\s?(\d+(?:,\d+)?)\s?(cm|m|centimetri|metri|Zentimeter|Metern?)\b")


def pasar(texto, lang, en_medidas, avisos, donde):
    """Version en pies de un texto. en_medidas se va gastando (cada cifra inglesa casa con una sola medida)."""
    if lang not in _RX:
        _RX[lang] = regex_medida(lang)
    t = texto
    for a, b in ESPECIALES[lang]:
        t = t.replace(a, b)

    def tres(m):
        u = m.group(5)
        partes = [pasar(f"{m.group(k)} {u}", lang, en_medidas, avisos, donde) for k in (1, 3, 4)]
        nums = [re.match(r"[\d,/]+", x).group(0) for x in partes]
        palabra = partes[-1][len(nums[-1]) + 1:]
        return f" {m.group(2)} ".join(nums) + " " + palabra
    t = TRES.sub(tres, t)

    def dos(m):
        u = m.group(4)
        a = pasar(f"{m.group(1)} {u}", lang, en_medidas, avisos, donde)
        b = pasar(f"{m.group(3)} {u}", lang, en_medidas, avisos, donde)
        return re.match(r"[\d,/]+", a).group(0) + f" {m.group(2)} " + b
    t = DOS[lang].sub(dos, t)

    def uno(m):
        clase = clase_de(lang, m.group(3))
        if clase is None:
            return m.group(0)
        valores = [m.group(1), m.group(2)] if m.group(1) else [m.group(2)]
        salida = []
        tol = 0.15 if clase in ("area", "vol", "l") else 0.08
        for txt in valores:
            v = _num(txt, lang)
            elegido = None
            # la unidad inglesa que este en la misma entrada con una cifra que case
            for factor, clase_en in CANDIDATOS[clase]:
                cand = v * factor
                for c in sorted(en_medidas.get(clase_en, {}), key=lambda x: abs(x - cand)):
                    if en_medidas[clase_en][c] > 0 and abs(c - cand) <= max(0.3 if cand < 2 else 0.5, cand * tol):
                        elegido = c
                        en_medidas[clase_en][c] -= 1
                        break
                if elegido is not None:
                    break
            if elegido is None:
                # sin cifra en el ingles: la unidad que da la cifra mas redonda (30 g = 1 onza, no 0,06 libras)
                limpias = [(f, c) for f, c in CANDIDATOS[clase] if v * f >= 1 and abs(v * f - round(v * f)) < 0.02]
                factor, clase_en = limpias[0] if limpias else CANDIDATOS[clase][0]
                if clase == "cm" and v >= 30 and v % 30 == 0:  # 30 cm = 1 pie
                    factor, clase_en = 1 / 30, "ft"
                if clase == "l" and v < 4:  # 0,5 l = 1 pinta
                    factor, clase_en = 2.0, "pt"
                cand = v * factor
                elegido = round(cand) if cand >= 1 else round(cand, 2)
                # una cifra limpia (1,5 m = 5 pies, 1,5 km = 1 milla, 0,5 kg = 1 libra) es la conversion del SRD
                # aunque el ingles la escriba con letra o de otra forma; solo avisa la que sale rara
                limpia_ = abs(cand - round(cand)) < 0.02 and clase in ("m", "km", "cm", "mm", "kg", "g", "l")
                if not limpia_:
                    avisos.append({"donde": donde, "medida": m.group(0), "pies": f"{_fmt(elegido, lang)} {clase_en}",
                                   "motivo": "sin cifra igual en el ingles"})
            salida.append((elegido, clase_en))
        sing, plur = SALIDA[lang][salida[-1][1]]
        # pulgadas en fraccion, como el ingles ("1/4 inch", "1/2 inch")
        fracciones = {0.25: "1/4", 0.5: "1/2", 0.75: "3/4"}
        numeros = "/".join(fracciones[v] if c in ("in", "lb", "mi") and v in fracciones else _fmt(v, lang) for v, c in salida)
        palabra = sing if len(salida) == 1 and salida[0][0] <= 1 else plur
        return f"{numeros} {palabra}"

    return _RX[lang].sub(uno, t)


def recorrer(o, ruta=""):
    if isinstance(o, dict):
        for k, v in o.items():
            if k in ("pies", "p", "correcciones"):
                continue
            yield from recorrer(v, f"{ruta}.{k}" if ruta else k)
    elif isinstance(o, list):
        for i, v in enumerate(o):
            yield from recorrer(v, f"{ruta}.{i}")
    elif isinstance(o, str):
        yield ruta, o


# palabras de unidad metrica que no deberian quedar tras pasar a pies (en espanol "meter" es tambien un verbo)
RESTO = {"es": r"metros?|kilómetros?|centímetros?", "de": r"Metern?|Kilometern?|Zentimetern?",
         "fr": r"mètres?|kilomètres?|centimètres?", "it": r"metri|metro|chilometri|centimetri"}


def todo_texto(x):
    return " ".join(t for _, t in recorrer(x))


def main():
    salida_json = sys.argv[sys.argv.index("--json") + 1] if "--json" in sys.argv else None
    informe = {"avisos": [], "sin_pasar": []}
    resumen = collections.Counter()
    tipos = [a for a in sys.argv[1:] if a in ("criaturas", "conjuros", "objetos", "estados")] or         ["criaturas", "conjuros", "objetos", "estados"]
    for tipo in tipos:
        ruta = os.path.join(DATOS, f"{tipo}.json")
        datos = json.load(open(ruta, encoding="utf-8"))
        for r in datos:
            base_en = medidas_en(todo_texto(r["en"]))
            for l in LANGS_M:
                x = r.get(l)
                if x is None:
                    continue
                en_m = {k: collections.Counter(v) for k, v in base_en.items()}
                pies = {}
                avisos = []
                for donde, t in recorrer(x):
                    n = pasar(t, l, en_m, avisos, donde)
                    if n != t:
                        pies[donde] = n
                        resumen[(tipo, l)] += 1
                    # unidades que se quedan sin pasar
                    resto = re.findall(r"\b(\d+(?:,\d+)?\s?(?:m|km|cm|kg))\b|\b(" + RESTO[l] + r")\b", sin_marcas(n))
                    for a, b in resto:
                        informe["sin_pasar"].append({"tipo": tipo, "id": r["id"], "idioma": l, "donde": donde,
                                                     "queda": a or b, "texto": sin_marcas(n)[:200]})
                x["pies"] = pies
                for a in avisos:
                    informe["avisos"].append({"tipo": tipo, "id": r["id"], "idioma": l, **a})
        with open(ruta, "w", encoding="utf-8", newline="\n") as f:
            json.dump(datos, f, ensure_ascii=False, indent=1)
    por = collections.Counter((a["tipo"], a["idioma"]) for a in informe["avisos"])
    sp = collections.Counter((a["tipo"], a["idioma"]) for a in informe["sin_pasar"])
    print("textos pasados a pies:", dict(resumen))
    print(f"{len(informe['avisos'])} medidas sin cifra igual en el ingles:", dict(por))
    print(f"{len(informe['sin_pasar'])} unidades metricas que quedan:", dict(sp))
    if salida_json:
        with open(salida_json, "w", encoding="utf-8") as f:
            json.dump(informe, f, ensure_ascii=False, indent=1)
    return 1 if informe["avisos"] or informe["sin_pasar"] else 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
