# -*- coding: utf-8 -*-
"""Pagina de revision de la fase 1: una muestra de entradas con el recorte del PDF oficial al lado de lo extraido.

Uso: py -3.14 muestra.py <salida.html>
Los recortes salen del PDF de cada idioma (zona de las lineas de la entrada, columna a columna), en JPEG.
"""
import base64
import html
import json
import os
import re
import sys

import fitz

import conjuros as C
import criaturas as K
import estados as E
from srd import PDFS, SRD_DIR, limpia, rango, en_paginas

AQUI = os.path.dirname(os.path.abspath(__file__))
DATOS = os.path.join(os.path.dirname(AQUI), "datos")

# (tipo, id, idioma, por que esta en la muestra)
MUESTRA = [
    ("criaturas", "adult-red-dragon", "es", "Ficha legendaria: acciones legendarias, aliento con recarga, lanzamiento de conjuros, PX en la guarida."),
    ("criaturas", "archmage", "es", "Lanzamiento de conjuros con listas (a voluntad, 2/día, 1/día) y conjuros en cursiva."),
    ("criaturas", "vampire", "es", "Rasgo con lista de debilidades; acciones adicionales y legendarias."),
    ("criaturas", "gibbering-mouther", "es", "Rasgo con tabla de 1d8 hecha lista."),
    ("criaturas", "wolf", "es", "Animal sencillo, del capítulo de animales."),
    ("criaturas", "balor", "de", "Alemán con errata corregida: dados de golpe 23W12+161 pasan a +138, como el inglés."),
    ("criaturas", "vampire", "it", "Italiano con la maqueta del PDF corregida: las debilidades salen mezcladas con los rasgos."),
    ("conjuros", "fireball", "es", "Conjuro con párrafo de nivel superior."),
    ("conjuros", "fire-bolt", "es", "Truco con mejora de truco."),
    ("conjuros", "control-weather", "es", "Conjuro con tres tablas."),
    ("conjuros", "summon-dragon", "es", "Conjuro con una ficha de criatura dentro."),
    ("conjuros", "wish", "es", "Conjuro largo con lista de puntos."),
    ("conjuros", "teleport", "it", "Italiano con errata corregida (2d12 chilometri pasa a 2d12 × 1,5 chilometri, como los otros idiomas)."),
    ("objetos", "bag-of-holding", "es", "Objeto maravilloso sencillo."),
    ("objetos", "apparatus-of-the-crab", "es", "Tabla que ocupa las dos columnas de la página."),
    ("objetos", "spell-scroll", "es", "Objeto con tabla de rareza, CD y bonificador."),
    ("objetos", "weapon-1-2-or-3", "es", "Objeto con rareza que depende del bonificador."),
    ("objetos", "staff-of-charming", "it", "Italiano: el SRD italiano no trae la propiedad Resistere all'ammaliamento y se ha añadido."),
    ("estados", "grappled", "es", "Estado del glosario de reglas, con sus efectos en lista."),
]

ROTULOS = {
    "es": dict(ca="CA", ini="Iniciativa", pg="PG", vel="Velocidad", hab="Habilidades", res="Resistencias",
               vul="Vulnerabilidades", inm="Inmunidades", equipo="Equipo", sen="Sentidos", idi="Idiomas", vd="VD",
               tiempo="Tiempo de lanzamiento", alcance="Alcance", comp="Componentes", dur="Duración"),
    "de": dict(ca="RK", ini="Initiative", pg="TP", vel="Bewegungsrate", hab="Fertigkeiten", res="Resistenzen",
               vul="Anfälligkeiten", inm="Immunitäten", equipo="Ausrüstung", sen="Sinne", idi="Sprachen", vd="HG",
               tiempo="Zeitaufwand", alcance="Reichweite", comp="Komponenten", dur="Wirkungsdauer"),
    "it": dict(ca="CA", ini="Iniziativa", pg="PF", vel="Velocità", hab="Abilità", res="Resistenze",
               vul="Vulnerabilità", inm="Immunità", equipo="Attrezzatura", sen="Sensi", idi="Lingue", vd="GS",
               tiempo="Tempo di lancio", alcance="Gittata", comp="Componenti", dur="Durata"),
}
IDIOMA = {"es": "español", "en": "inglés", "de": "alemán", "fr": "francés", "it": "italiano"}


def filas_entrada(tipo, lang, nombre):
    """Lineas del PDF de una entrada (titulo y cuerpo)."""
    if tipo == "criaturas":
        ents, _ = K.cortar(lang)
        e = next(x for x in ents if x["nombre"] == nombre)
        todas = []
        for cap in ("monstruos_az", "animales"):
            p0, p1 = rango(lang, cap)
            todas += en_paginas(lang, p0, p1)
        i0 = next(k for k, r in enumerate(todas) if r["p"] == e["p"] and limpia(r["t"]) == limpia(nombre.split()[0]) or
                  (r["p"] == e["p"] and K.es(r, "GillSans-SemiBold", 14.8) and limpia(nombre).startswith(limpia(r["t"]))))
        return [todas[i0]] + e["_filas"]
    if tipo in ("conjuros", "objetos"):
        ents = C.cortar(lang, tipo)
        e = next(x for x in ents if x["nombre"] == nombre)
        p0, p1 = rango(lang, tipo)
        todas = en_paginas(lang, p0, p1)
        t = [r for r in todas if r["p"] == e["p"] and C.es_nombre(r) and limpia(nombre).startswith(limpia(r["t"]))][:1]
        return t + e["filas"]
    p0, p1 = rango(lang, "glosario")
    todas = en_paginas(lang, p0, p1)
    out, dentro = [], False
    for r in todas:
        tit = r["font"].startswith("GillSans-SemiBold") and r["size"] >= 12
        if tit:
            if dentro:
                break
            dentro = limpia(r["t"]).startswith(nombre) and bool(re.search(E.ETIQUETA[lang], limpia(r["t"]), re.I))
        if dentro:
            out.append(r)
    return out


def recortes(lang, filas):
    """Un recorte por pagina y columna, como JPEG en base64."""
    doc = fitz.open(os.path.join(SRD_DIR, PDFS[lang]))
    grupos = {}
    for r in filas:
        grupos.setdefault((r["p"], r["col"]), []).append(r)
    out = []
    for (p, col), rs in sorted(grupos.items()):
        page = doc[p - 1]
        x0 = min(r["x"] for r in rs) - 6
        x1 = max(r["x1"] for r in rs) + 6
        y0 = min(r["y"] for r in rs) - 6
        y1 = max(r["yb"] for r in rs) + 6
        x1 = max(x1, x0 + 250)
        pix = page.get_pixmap(clip=fitz.Rect(x0, y0, x1, y1), matrix=fitz.Matrix(2, 2))
        jpg = pix.tobytes("jpeg", jpg_quality=82)
        out.append((p, base64.b64encode(jpg).decode()))
    return out


def md_a_html(t):
    """Las marcas del texto (<i>, <b>, <strong>) ya son HTML; el resto se escapa."""
    partes = re.split(r"(</?(?:i|b|strong)>)", t)
    return "".join(x if re.fullmatch(r"</?(?:i|b|strong)>", x) else html.escape(x) for x in partes)


def bloques_html(bloques):
    out = []
    lista = False
    for b in bloques:
        if b["t"] == "li":
            if not lista:
                out.append("<ul>"); lista = True
            out.append(f"<li>{md_a_html(b['txt'])}</li>")
            continue
        if lista:
            out.append("</ul>"); lista = False
        if b["t"] in ("p", "nota"):
            if b.get("txt", "").strip():
                out.append(f"<p class='{'nota' if b['t'] == 'nota' else ''}'>{md_a_html(b['txt'])}</p>")
        elif b["t"] == "tabla":
            filas = b["filas"]
            cab = f"<caption>{html.escape(b['titulo'])}</caption>" if b.get("titulo") else ""
            th = "".join(f"<th>{md_a_html(c)}</th>" for c in filas[0]) if filas else ""
            tds = "".join("<tr>" + "".join(f"<td>{md_a_html(c)}</td>" for c in f) + "</tr>" for f in filas[1:])
            out.append(f"<div class='tabla'><table>{cab}<thead><tr>{th}</tr></thead><tbody>{tds}</tbody></table></div>")
        elif b["t"] == "ficha":
            car = " ".join(f"{c[0]} {c[1]} ({c[2]}, salv. {c[3]})" for c in b.get("car", []))
            rasgos = "".join(f"<div><b>{html.escape(r)}:</b> {md_a_html(v)}</div>" for r, v in b.get("rasgos", []))
            secs = "".join(f"<h5>{html.escape(s['titulo'])}</h5>" + "".join(
                f"<p><b><i>{html.escape(n)}.</i></b> {md_a_html(t)}</p>" for n, t in s["items"]) for s in b.get("secciones", []))
            out.append(f"<div class='ficha'><h4>{html.escape(b['nombre'])}</h4><div class='tipo'>{html.escape(b.get('tipo',''))}</div>"
                       f"<div><b>CA</b> {md_a_html(b.get('ca',''))} · <b>PG</b> {md_a_html(b.get('pg',''))} · "
                       f"<b>Vel.</b> {md_a_html(b.get('vel',''))}</div><div class='car'>{html.escape(car)}</div>{rasgos}{secs}</div>")
    if lista:
        out.append("</ul>")
    return "".join(out)


def extraido_html(tipo, x, lang):
    rot = ROTULOS.get(lang, ROTULOS["es"])
    if tipo == "criaturas":
        campos = "".join(f"<div><b>{rot.get(k, k)}:</b> {md_a_html(v)}</div>" for k, v in x["campos"].items()
                         if k not in ("ca", "ini", "pg", "vel"))
        car = "<table class='car'><tr>" + "".join(f"<th>{c[0]}</th>" for c in x["car"]) + "</tr><tr>" + "".join(
            f"<td>{c[1]}<br><small>{c[2]} / {c[3]}</small></td>" for c in x["car"]) + "</tr></table>"
        secs = ""
        for s in x["secciones"]:
            secs += f"<h4>{html.escape(s['titulo'])}</h4>"
            if s["intro"]:
                secs += f"<p><i>{md_a_html(s['intro'])}</i></p>"
            for it in s["items"]:
                cuerpo = bloques_html(it["bloques"])
                cuerpo = cuerpo.replace("<p class=''>", f"<p class=''><b><i>{html.escape(it['nombre'])}.</i></b> ", 1)
                secs += cuerpo
        return (f"<div class='tipo'>{html.escape(x['tipo'])}</div>"
                f"<div><b>{rot['ca']}:</b> {md_a_html(x['campos']['ca'])} · <b>{rot['ini']}:</b> {md_a_html(x['campos']['ini'])}</div>"
                f"<div><b>{rot['pg']}:</b> {md_a_html(x['campos']['pg'])}</div><div><b>{rot['vel']}:</b> {md_a_html(x['campos']['vel'])}</div>"
                f"{car}{campos}{secs}")
    if tipo == "conjuros":
        cab = "".join(f"<div><b>{rot[k]}:</b> {md_a_html(x[k])}</div>" for k in ("tiempo", "alcance", "comp", "dur"))
        return f"<div class='tipo'>{html.escape(x['cabecera'])}</div>{cab}{bloques_html(x['bloques'])}"
    if tipo == "objetos":
        return f"<div class='tipo'>{html.escape(x['cabecera'])}</div>{bloques_html(x['bloques'])}"
    return bloques_html(x["bloques"])


def main():
    salida = sys.argv[1]
    datos = {t: {r["id"]: r for r in json.load(open(os.path.join(DATOS, f"{t}.json"), encoding="utf-8"))}
             for t in ("criaturas", "conjuros", "objetos", "estados")}
    tarjetas = []
    for tipo, i, lang, porque in MUESTRA:
        r = datos[tipo][i]
        x = r[lang]
        filas = filas_entrada(tipo, lang, x["nombre"])
        imgs = recortes(lang, filas)
        corr = [c for c in r.get("correcciones", []) if c["idioma"] == lang]
        corr_html = "".join(f"<li><span class='antes'>{html.escape(c['antes'] or '(no estaba)')}</span> pasa a "
                            f"<span class='despues'>{html.escape(re.sub(r'<[^>]+>', '', c['despues']))}</span>. "
                            f"{html.escape(c['por_que'])}</li>" for c in corr)
        paginas = sorted({p for p, _ in imgs})
        tarjetas.append({"tipo": tipo, "id": i, "lang": lang, "nombre": x["nombre"], "en": r["en"]["nombre"],
                         "porque": porque, "imgs": imgs, "html": extraido_html(tipo, x, lang), "corr": corr_html,
                         "paginas": paginas})
    json.dump([{k: v for k, v in t.items() if k != "imgs"} | {"imgs": [p for p, _ in t["imgs"]]} for t in tarjetas],
              open(salida + ".json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    import pickle
    pickle.dump(tarjetas, open(salida + ".pkl", "wb"))
    print(len(tarjetas), "entradas en la muestra ->", salida + ".pkl")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
