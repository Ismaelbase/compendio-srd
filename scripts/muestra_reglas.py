# -*- coding: utf-8 -*-
"""Muestra de la fase 1b (el resto del SRD): notas con el recorte del PDF oficial al lado de lo extraido.

Uso: py -3.14 muestra_reglas.py <salida>   (deja <salida>.pkl para pagina_reglas.py)
Los recortes salen del PDF de cada idioma: de la linea del titulo de la nota hasta el siguiente titulo de su nivel o
mas alto, columna a columna (las tablas que ocupan la pagina, enteras). Las armas y armaduras, que salen de las
filas de su tabla, se recortan en su fila.
"""
import base64
import html
import json
import os
import pickle
import re
import sys

import fitz

import documento as D
from muestra import con_pies, md_a_html
from srd import CAP, PDFS, SRD_DIR, en_paginas, limpia, rango

AQUI = os.path.dirname(os.path.abspath(__file__))
DATOS = os.path.join(os.path.dirname(AQUI), "datos")
FICHEROS = ("reglas", "personajes", "equipo")

# (id, idioma, por que esta en la muestra)
MUESTRA = [
    ("bard", "es", "Clase con sus dos tablas: atributos básicos (rótulos a la izquierda) y rasgos, que ocupa la página entera y lleva los espacios de conjuro agrupados."),
    ("path-of-the-berserker", "es", "Subclase: cada rasgo con su nivel."),
    ("dragonborn", "es", "Especie con sus campos, su tabla de ancestros (en dos mitades en el PDF) y los atributos especiales."),
    ("acolyte", "fr", "Trasfondo en francés: líneas de campo con rótulo."),
    ("alert", "it", "Dote de origen en italiano."),
    ("longsword", "es", "Arma: una nota por fila de la tabla de armas."),
    ("chain-mail", "de", "Armadura en alemán, de la tabla de armaduras."),
    ("smiths-tools", "es", "Herramienta: característica, peso, uso y fabricación."),
    ("rope", "es", "Equipo de aventureros: la descripción; el peso y el precio están en la tabla de equipo."),
    ("grappling", "es", "Entrada del glosario de reglas con rótulos en negrita."),
    ("help", "en", "Entrada del glosario con etiqueta ([Action]) en inglés."),
    ("assassins-blood", "es", "Veneno: tipo en cursiva y efecto."),
    ("hidden-pit", "it", "Trampa en italiano: gravedad, activador y duración, y tabla de niveles superiores."),
    ("rhythm-of-play", "es", "Regla con lista numerada y recuadro gris («Las excepciones se imponen...»)."),
    ("combat-encounters", "es", "Las reglas de encuentros de 2024 que usará el plugin para el presupuesto de PX."),
    ("travel-pace", "es", "Tabla a todo el ancho con media cabecera en letra normal, notas al pie y fórmulas."),
    ("warlock", "en", "Clase en inglés con tabla de rasgos partida en las dos columnas y lista de invocaciones."),
    ("trinkets", "de", "Tabla larga de 1W100 (bagatelas) en alemán."),
]
TIPO = {"regla": "Regla", "glosario": "Glosario de reglas", "veneno": "Veneno", "trampa": "Trampa", "clase": "Clase",
        "subclase": "Subclase", "especie": "Especie", "trasfondo": "Trasfondo", "dote": "Dote",
        "herramienta": "Herramienta", "equipo": "Equipo de aventureros", "arma": "Arma", "armadura": "Armadura"}
NIVEL_NOTA = {"regla": 1, "clase": 1, "subclase": 2, "especie": 3, "trasfondo": 3, "dote": 3, "herramienta": 3,
              "equipo": 3, "glosario": 3, "veneno": 3, "trampa": 3}
CAP_DE = {"juego": "juego", "creacion": "creacion", "conjuros": "conjuros", "clases": "clases", "origenes": "origenes",
          "dotes": "dotes", "equipo": "equipo", "glosario": "glosario", "herramientas": "herramientas",
          "objetos": "objetos", "monstruos": "monstruos"}


def filas_nota(lang, cap, x, tipo):
    """Lineas del PDF de una nota: desde su titulo hasta el siguiente titulo de su nivel o mas alto."""
    p0, p1 = rango(lang, cap)
    rows, _ = D.recolocar_tablas_anchas(en_paginas(lang, p0, p1))
    nivel = NIVEL_NOTA[tipo]
    nombre = limpia(x["nombre"])
    ini = None
    for k, r in enumerate(rows):
        if D.es_titulo(r) and D.NIVEL_TITULO[round(r["size"], 1)] == nivel and r["p"] == x["p"]:
            t = limpia(r["t"])
            sig = rows[k + 1] if k + 1 < len(rows) else None
            junto = t + (" " + limpia(sig["t"]) if sig is not None and D.es_titulo(sig) and D.tam(sig, r["size"]) else "")
            if nombre.startswith(t) or junto.startswith(nombre) or nombre.startswith(junto):
                ini = k
                break
    if ini is None:
        return []
    fin = len(rows)
    for k in range(ini + 1, len(rows)):
        r = rows[k]
        if D.es_titulo(r) and D.NIVEL_TITULO[round(r["size"], 1)] <= nivel and \
                not (r["p"] == rows[ini]["p"] and r["col"] == rows[ini]["col"] and 0 < r["yb"] - rows[k - 1]["yb"] < 26
                     and D.es_titulo(rows[k - 1])):
            fin = k
            break
    h = rows[ini]
    # la tabla a todo el ancho que la maqueta pone al pie de la primera pagina, en la columna de antes del titulo (la
    # de rasgos del bardo): tambien es de la nota
    if h["col"] != 1:
        return rows[ini:fin]
    anchas = [r for r in rows[:ini] if r["p"] == h["p"] and r["col"] == 0 and r.get("_ancha")]
    if not anchas:
        return rows[ini:fin]
    arriba = min(r["yb"] for r in anchas)
    antes = [r for r in rows[:ini] if r["p"] == h["p"] and r["col"] == 0 and r["yb"] >= arriba - 40 and
             (D.es_fila_tabla(r) or D.es_titulo_tabla(r) or r.get("_ancha"))]
    return antes + rows[ini:fin]


def filas_de_fila(lang, cap, nombre):
    """Lineas de la fila de una tabla (armas y armaduras): todo lo que esta a la altura de su primera celda."""
    p0, p1 = rango(lang, cap)
    rows = en_paginas(lang, p0, p1)
    r0 = next((r for r in rows if limpia(r["t"]) == limpia(nombre) and r["font"].startswith("GillSans")
               and D.tam(r, 9.5)), None)
    if r0 is None:
        return []
    cab = [r for r in rows if r["p"] == r0["p"] and r["font"] == "GillSans-SemiBold" and D.tam(r, 9.2) and
           r["yb"] < r0["yb"] and r0["yb"] - r["yb"] < 900]
    cab = [r for r in cab if r["yb"] >= max(c["yb"] for c in cab) - 1] if cab else []
    fila = [r for r in rows if r["p"] == r0["p"] and abs(r["yb"] - r0["yb"]) < 14 and r["yb"] >= r0["yb"] - 1]
    return cab + fila


def recortes(lang, filas, ancho_pagina=False):
    doc = fitz.open(os.path.join(SRD_DIR, PDFS[lang]))
    grupos = {}
    for r in filas:
        grupos.setdefault((r["p"], 0 if ancho_pagina else r["col"]), []).append(r)
    out = []
    for (p, col), rs in sorted(grupos.items()):
        page = doc[p - 1]
        x0 = min(r["x"] for r in rs) - 6
        x1 = max(max(r["x1"] for r in rs) + 6, x0 + 250)
        y0 = min(r["y"] for r in rs) - 6
        y1 = max(r["yb"] for r in rs) + 6
        pix = page.get_pixmap(clip=fitz.Rect(x0, y0, x1, y1), matrix=fitz.Matrix(1.6, 1.6))
        out.append((p, base64.b64encode(pix.tobytes("jpeg", jpg_quality=76)).decode()))
    return out


def tabla_html(b):
    filas = b["filas"]
    cab = f"<caption>{html.escape(b['titulo'])}</caption>" if b.get("titulo") else ""
    if b.get("vertical"):
        tds = "".join(f"<tr><th>{md_a_html(a)}</th><td>{md_a_html(v)}</td></tr>" for a, v in filas)
        return f"<div class='tabla'><table class='vertical'>{cab}<tbody>{tds}</tbody></table></div>"
    if b.get("sin_cabecera"):
        tds = "".join("<tr>" + "".join(f"<td>{md_a_html(c)}</td>" for c in f) + "</tr>" for f in filas)
        return f"<div class='tabla'><table>{cab}<tbody>{tds}</tbody></table></div>"
    grupos = ""
    if b.get("grupos"):
        n = len(filas[0])
        celdas, k = [], 0
        for txt, a, z in sorted(b["grupos"], key=lambda g: g[1]):
            if a > k:
                celdas.append(f"<th colspan='{a - k}'></th>")
            celdas.append(f"<th colspan='{z - a + 1}' class='grupo'>{html.escape(txt)}</th>")
            k = z + 1
        if k < n:
            celdas.append(f"<th colspan='{n - k}'></th>")
        grupos = "<tr>" + "".join(celdas) + "</tr>"
    th = "".join(f"<th>{md_a_html(c)}</th>" for c in filas[0]) if filas else ""
    tds = "".join("<tr>" + "".join(f"<td>{md_a_html(c)}</td>" for c in f) + "</tr>" for f in filas[1:])
    return f"<div class='tabla'><table>{cab}<thead>{grupos}<tr>{th}</tr></thead><tbody>{tds}</tbody></table></div>"


def bloques_html(bloques):
    out, lista = [], False
    for b in bloques:
        if b["t"] == "li":
            if not lista:
                out.append("<ul>")
                lista = True
            out.append(f"<li>{md_a_html(b['txt'])}</li>")
            continue
        if lista:
            out.append("</ul>")
            lista = False
        t = b["t"]
        if t == "h":
            n = min(6, 3 + b["n"])
            out.append(f"<h{n}>{html.escape(b['txt'])}</h{n}>")
        elif t in ("p", "nota", "formula") and b.get("txt", "").strip():
            clase = {"nota": "nota", "formula": "formula"}.get(t, "sub" if b.get("sub") else "")
            out.append(f"<p class='{clase}'>{md_a_html(b['txt'])}</p>")
        elif t == "tabla":
            out.append(tabla_html(b))
        elif t == "campos":
            out.append("<div class='campos'>" + "".join(f"<div><b>{html.escape(a)}:</b> {md_a_html(v)}</div>"
                                                         for a, v in b["filas"]) + "</div>")
        elif t == "recuadro":
            out.append(f"<aside><h5>{html.escape(b['titulo'])}</h5>{bloques_html(b['bloques'])}</aside>")
        elif t == "columnas":
            out.append("<ul class='columnas'>" + "".join(f"<li>{md_a_html(i)}</li>" for i in b["items"]) + "</ul>")
    if lista:
        out.append("</ul>")
    return "".join(out)


def main():
    salida = sys.argv[1]
    datos = {r["id"]: r for f in FICHEROS for r in json.load(open(os.path.join(DATOS, f + ".json"), encoding="utf-8"))}
    tarjetas = []
    for i, lang, porque in MUESTRA:
        if porque is None or i not in datos:
            continue
        r = datos[i]
        x = r[lang]
        if r["tipo"] in ("arma", "armadura"):
            filas = filas_de_fila(lang, "equipo", x["nombre"])
            imgs = recortes(lang, filas, ancho_pagina=True)
        else:
            filas = filas_nota(lang, CAP_DE[r["cap"]], x, r["tipo"])
            imgs = recortes(lang, filas)
        if not imgs:
            print("sin recorte:", i, lang)
        corr = [c for c in r.get("correcciones", []) if c["idioma"] == lang]
        corr_html = "".join(f"<li><span class='antes'>{html.escape(c['antes'] or '(no estaba)')}</span> pasa a "
                            f"<span class='despues'>{html.escape(re.sub(r'<[^>]+>', '', c['despues']))}</span>. "
                            f"{html.escape(c['por_que'])}</li>" for c in corr)
        extra = ""
        if x.get("categoria") and r["tipo"] in ("arma", "armadura", "dote", "herramienta"):
            extra = f"<div class='tipo'>{html.escape(x['categoria'])}</div>"
        html_m = extra + bloques_html(x["bloques"])
        html_p = extra + bloques_html(con_pies(x)["bloques"]) if x.get("pies") else None
        tarjetas.append({"tipo": r["tipo"], "id": i, "lang": lang, "nombre": x["nombre"], "en": r["en"]["nombre"],
                         "porque": porque, "imgs": imgs, "html": html_m, "html_pies": html_p, "corr": corr_html,
                         "paginas": sorted({p for p, _ in imgs})})
    pickle.dump(tarjetas, open(salida + ".pkl", "wb"))
    print(len(tarjetas), "notas en la muestra ->", salida + ".pkl")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
