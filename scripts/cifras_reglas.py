# -*- coding: utf-8 -*-
"""Cifras de los capitulos de reglas para comparar idiomas: las de cifras.py mas las medidas que solo salen aqui.

El ingles escribe "Range 20/60" sin unidad en la tabla de armas, "costs 1 extra foot", "5–7 feet tall",
"100 degrees Fahrenheit", "1/4 gallon", "1/4 lb.", "58½ lb.", "1-ounce", "2 cubic feet" y "8 mph"; los otros SRD dan
metros, centimetros ("150–210 cm"), grados centigrados, litros (1 galon = 4 l y 1 pie cubico = 30 l en sus tablas),
gramos y km/h (1 mph = 1,5 km/h). Todo se pasa a la misma medida antes de comparar. No cambia cifras.py, que usan las
comprobaciones de criaturas, conjuros y objetos.
"""
import re

from cifras import cifras, cifras_en
from marcas import sin_marcas

FRACCION = {"½": 0.5, "¼": 0.25, "¾": 0.75, "⅓": 1 / 3, "⅔": 2 / 3}


def _num(t):
    t = t.strip()
    extra = 0.0
    if t and t[-1] in FRACCION:
        extra, t = FRACCION[t[-1]], t[:-1]
    if "/" in t:
        a, b = t.split("/")
        return int(a) / int(b) + extra
    return (float(t.replace(",", ".")) if t else 0.0) + extra


def _fmt(x, coma=False):
    x = round(x, 3)
    s = str(int(x)) if x == int(x) else str(x)
    return s.replace(".", ",") if coma else s


NUM_EN = r"(\d+(?:/\d+)?[½¼¾⅓⅔]?|[½¼¾])"

# Numeros con letra (del 2 al 12 y el 20): "10 Candles" frente a "zehn Kerzen", "Choose 2" frente a "Elige dos".
# El 1 no, porque es tambien el articulo; "sei" italiano tampoco ("se sei..."), ni "neuf" frances ("nuevo").
LETRAS = {
    "en": "two three four five six seven eight nine ten eleven twelve twenty",
    "es": "dos tres cuatro cinco seis siete ocho nueve diez once doce veinte",
    "de": "zwei drei vier fünf sechs sieben acht neun zehn elf zwölf zwanzig",
    "fr": "deux trois quatre cinq six sept huit - dix onze douze vingt",
    "it": "due tre quattro cinque - sette otto nove dieci undici dodici venti",
}
VALOR = [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 20]


def letras_a_cifras(t, lang):
    for w, v in zip(LETRAS[lang].split(), VALOR):
        if w != "-":
            t = re.sub(rf"\b{w}\b", str(v), t, flags=re.IGNORECASE if lang != "de" else 0)
    return t


def prepara_en(t):
    t = letras_a_cifras(sin_marcas(t), "en")
    t = re.sub(r"\bD(\d+) per\b", r"1d\1 per", t)  # "D12 per Barbarian level"
    t = re.sub(r"\b(Range|range) (\d+)/(\d+)(?!\s*(?:feet|ft))", r"\1 \2/\3 ft.", t)
    t = re.sub(r"(\d+) extra (feet|foot)", r"\1 \2 extra", t)
    t = re.sub(r"(\d+)\s*[–-]\s*(\d+)(\s*)(feet|foot|ft\.?|miles?|pounds?|lb\.?)(?!\w)", r"\1 \4–\2\3\4", t)
    t = re.sub(r"(\d+[½¼¾]?) by (\d+[½¼¾]?) (feet|foot)", r"\1 \3 by \2 \3", t)  # "2½ by 2½ feet"
    t = re.sub(r"(\d+[½¼¾])[- ](feet|foot)\b", lambda m: _fmt(_num(m.group(1)) * 0.3) + " m", t)
    t = re.sub(r"\bhalf a cubic foot", "15 l", t)
    t = re.sub(r"(-?\d+) degrees Fahrenheit", lambda m: _fmt(round((int(m.group(1)) - 32) * 5 / 9)) + " °C", t)
    t = re.sub(NUM_EN + r" gallons?", lambda m: _fmt(_num(m.group(1)) * 4) + " l", t)
    t = re.sub(NUM_EN + r"[- ]cubic (?:feet|foot)", lambda m: _fmt(_num(m.group(1)) * 30) + " l", t)
    t = re.sub(NUM_EN + r" mph", lambda m: _fmt(_num(m.group(1)) * 1.5) + " km/h", t)
    t = re.sub(r"(\d+(?:/\d+)?[½¼¾]|\d+/\d+) (lb\.|pounds?)", lambda m: _fmt(_num(m.group(1)) * 0.5) + " kg", t)
    t = re.sub(r"(\d+)[- ]ounces?", lambda m: _fmt(int(m.group(1)) * 0.03) + " kg", t)
    return t


CM_PAL = r"(cm|centimetri|centimètres|centímetros|Zentimeter)\b"


def prepara_otro(t, lang):
    t = letras_a_cifras(sin_marcas(t), lang)
    t = re.sub(r"(\d+(?:[.,]\d+)?)\s?(?:g|Gramm|gramos?|grammes?|grammi)\b",
               lambda m: _fmt(_num(m.group(1)) / 1000, coma=True) + " kg", t)
    t = re.sub(r"(\d+)\s*(?:[–-]|y|e|et|und|bis)\s*(\d+)\s?" + CM_PAL, r"\1 \3–\2 \3", t)
    t = re.sub(r"(\d+(?:[.,]\d+)?)\s?(?:m³|m3|metri cubi|mètres? cubes?|metros cúbicos|Kubikmeter)",
               lambda m: _fmt(_num(m.group(1)) * 1000, coma=True) + " l", t)
    t = re.sub(r"(\d+)([½¼¾])", lambda m: _fmt(_num(m.group(0)), coma=True), t)
    t = re.sub(r"−\s?(\d)", r"\1", t)  # "−18 °C"
    return t


def cifras_r_en(t):
    return cifras_en(prepara_en(t))


def cifras_r(t, lang):
    return cifras(prepara_otro(t, lang), lang)
