# -*- coding: utf-8 -*-
"""Texto con marcas a partir de los tramos del PDF.

Dentro del texto se guardan tres marcas, que luego se pasan a Markdown:
    <i>...</i>   cursiva (conjuro citado, "Acierto:", "Fallo:")
    <b>...</b>   negrita (rotulo de una lista, "A voluntad:")
    <strong>...</strong>  criatura citada en negrita (en los conjuros)
"""
import re

from srd import une


def a_html(tramos):
    """[(marca, texto)] -> texto con etiquetas, dejando los espacios de los bordes fuera de la etiqueta."""
    s = ""
    for e, t in tramos:
        if e and t.strip():
            lead = t[:len(t) - len(t.lstrip())]
            tail = t[len(t.rstrip()):]
            s += lead + f"<{e}>" + t.strip() + f"</{e}>" + tail
        else:
            s += t
    return s


def unir_html(lineas):
    """Une las lineas de un parrafo (ya con etiquetas) deshaciendo los cortes de palabra, y funde etiquetas
    iguales seguidas ("<i>Dispel</i> <i>Magic</i>" -> "<i>Dispel Magic</i>")."""
    lineas = [re.sub("\u00ad(</(?:i|b|strong)>)\\s*$", "\\1\u00ad", l) for l in lineas]
    juntas = []
    for l in lineas:
        if juntas:
            a = juntas[-1].rstrip()
            m = re.search(r"([^\W\d])-(</(i|b|strong)>)$", a)
            if m and l.lstrip().startswith(f"<{m.group(3)}>") and l.lstrip()[len(m.group(3)) + 2:][:1].islower():
                juntas[-1] = a[:m.start() + 1] + l.lstrip()[len(m.group(3)) + 2:]
                continue
            if re.search(r"\d-$", a) and l.lstrip()[:1].islower():
                juntas[-1] = a + l.lstrip()
                continue
        juntas.append(l)
    s = une(juntas)
    for e in ("i", "b", "strong"):
        s = re.sub(rf"</{e}>(\s*)<{e}>", r"\1", s)
        s = re.sub(rf"</{e}>-<{e}>", "-", s)
        s = s.replace(f"<{e}></{e}>", "")
    # rotulo pegado al texto que sigue ("<b>A voluntad:</b><i>armadura de mago</i>"): el PDF no trae el espacio
    s = re.sub(r":</(i|b|strong)>(?=[<\w(+\-−–\d])", r":</\1> ", s)
    return s.strip()


def sin_marcas(s):
    return re.sub(r"</?(i|b|strong)>", "", s)
