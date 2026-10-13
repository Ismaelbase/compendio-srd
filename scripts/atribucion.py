# -*- coding: utf-8 -*-
"""La declaracion de atribucion de cada SRD, palabra por palabra, de su pagina 1 -> datos\\atribucion.json.

Es el parrafo sangrado (empieza por un tabulador) que la licencia pide copiar en cualquier obra. Las lineas se unen
con un espacio, salvo cuando la linea corta una direccion ("https://creativecommons.org/" + "licenses/...").

Uso: py -3.14 atribucion.py
"""
import json
import os
import sys

import fitz

from srd import LANGS, PDFS, SRD_DIR

AQUI = os.path.dirname(os.path.abspath(__file__))
SALIDA = os.path.join(os.path.dirname(AQUI), "datos", "atribucion.json")


def atribucion(lang):
    lineas = fitz.open(os.path.join(SRD_DIR, PDFS[lang]))[0].get_text().split("\n")
    i = next(k for k, l in enumerate(lineas) if l.startswith("\t"))
    out = lineas[i].lstrip("\t ").rstrip()
    while "legalcode" not in out:
        i += 1
        sig = lineas[i].strip()
        out = out + sig if out.endswith("/") else out + " " + sig
    assert out.endswith((".", ").")), out
    assert "SRD 5.2.1" in out and "https://www.dndbeyond.com/srd" in out, out
    return out


def main():
    datos = {l: atribucion(l) for l in LANGS}
    with open(SALIDA, "w", encoding="utf-8", newline="\n") as f:
        json.dump(datos, f, ensure_ascii=False, indent=1)
        f.write("\n")
    for l, t in datos.items():
        print(l, t)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
