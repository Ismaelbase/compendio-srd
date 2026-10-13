# -*- coding: utf-8 -*-
"""Pagina de revision de la fase 1 (para Ismael): resumen, lo que tiene que mirar, la muestra con el recorte del PDF
oficial al lado de lo extraido (en metros y en pies), las erratas corregidas y los fallos de maquetacion arreglados.

Uso: py -3.14 pagina_revision.py <salida.html>
"""
import collections
import html
import json
import os
import re
import sys

import muestra as M

AQUI = os.path.dirname(os.path.abspath(__file__))
DATOS = os.path.join(os.path.dirname(AQUI), "datos")
IDIOMA = {"es": "español", "en": "inglés", "de": "alemán", "fr": "francés", "it": "italiano"}
TIPO = {"criaturas": "Criatura", "conjuros": "Conjuro", "objetos": "Objeto mágico", "estados": "Estado"}

MAQUETACION = [
    ("Italiano", "Las debilidades del vampiro y del engendro vampírico salen mezcladas, por orden alfabético, con los demás rasgos. Se juntan en su rasgo."),
    ("Italiano", "En 42 fichas, la lista de conjuros de una criatura pone «1/giorno» antes que «A volontà». Se ponen en el orden del inglés."),
    ("Italiano", "En la esfinge del valor, «Primo ruggito» cae dentro de los conjuros. En el aboleth, el segundo párrafo de su nube mucosa sale detrás de otro rasgo. En el tricerátops, el texto de una acción va en negrita. Se recoloca y se arregla."),
    ("Francés", "El tercer párrafo de Nuage incendiaire sale al final de Nuée de météores, el conjuro que va detrás. Vuelve a su sitio."),
    ("Alemán", "La tabla de palancas del aparato del crustáceo sale en mitad del amuleto de los planos, dos objetos antes. Vuelve a su sitio y el párrafo cortado se une."),
    ("Los cinco", "Las tablas que ocupan las dos columnas de la página (palancas del aparato) se leían partidas. Se leen enteras."),
    ("Los cinco", "Las tablas de temperatura y viento de Controlar el clima, una al lado de la otra, se fundían con la de precipitaciones. Salen como tres tablas con su título."),
    ("Inglés", "La tabla del pergamino de conjuro, con las columnas centradas, salía revuelta. Sale bien."),
    ("Español", "La primera línea de la cota de escamas de dragón va en cursiva por error y se colaba en la cabecera. Es texto normal."),
    ("Los cinco", "Espacios que el PDF se come («veneno;asustado», «13,000in lair») y el punto del nombre de un rasgo en letra normal."),
]


def correcciones():
    out = []
    for fichero, tipo, origen in (("correcciones_criaturas.json", "criaturas", "comparación de cifras"),
                                  ("correcciones_conjuros_revision.json", "conjuros", "comparación de cifras"),
                                  ("correcciones_objetos.json", "objetos", "comparación de cifras"),
                                  ("correcciones_conjuros.json", "conjuros", "cartas de hechizos")):
        for c in json.load(open(os.path.join(DATOS, fichero), encoding="utf-8"))["correcciones"]:
            out.append(dict(c, tipo=tipo, origen=origen))
    return out


def nombres():
    out = {}
    for t in ("criaturas", "conjuros", "objetos", "estados"):
        for r in json.load(open(os.path.join(DATOS, f"{t}.json"), encoding="utf-8")):
            out[(t, r["id"])] = {l: r[l]["nombre"] for l in ("es", "en", "de", "fr", "it") if l in r}
    return out


def limpio(t):
    return html.escape(re.sub(r"<[^>]+>", "", t or ""))


def tabla_correcciones(lista, nom):
    filas = []
    for c in lista:
        n = nom.get((c["tipo"], c["id"]), {})
        nombre = n.get(c["idioma"], c["id"])
        antes = limpio(c.get("antes")) or "<em>(no estaba)</em>"
        despues = c.get("despues") or c.get("insertar", {}).get("txt", "")
        filas.append(f"<tr><td>{IDIOMA[c['idioma']]}</td><td>{html.escape(nombre)}<div class='nota'>{html.escape(n.get('es', ''))}</div></td>"
                     f"<td><span class='antes'>{antes}</span></td><td><span class='despues'>{limpio(despues)}</span></td>"
                     f"<td class='nota'>{html.escape(c.get('por_que', ''))}</td></tr>")
    return ("<div class='tabla'><table><thead><tr><th>Idioma</th><th>Entrada</th><th>Decía</th><th>Dice ahora</th>"
            "<th>Por qué</th></tr></thead><tbody>" + "".join(filas) + "</tbody></table></div>")


def tarjeta(t, k):
    imgs = "".join(f"<figure><img src='data:image/jpeg;base64,{b64}' alt='Página {p} del SRD en {IDIOMA[t['lang']]}' "
                   f"loading='lazy'><figcaption>Página {p}</figcaption></figure>" for p, b64 in t["imgs"])
    pies = ""
    botones = ""
    if t["html_pies"]:
        botones = (f"<div class='cambio' role='group' aria-label='Medidas'>"
                   f"<button type='button' aria-pressed='true' data-ver='m' data-t='{k}'>Metros (SRD)</button>"
                   f"<button type='button' aria-pressed='false' data-ver='p' data-t='{k}'>Pies</button></div>")
        pies = f"<div class='extraido' id='p{k}' hidden>{t['html_pies']}</div>"
    corr = f"<div class='corr'><b>Corregido en esta entrada:</b><ul>{t['corr']}</ul></div>" if t["corr"] else ""
    return (f"<article class='entrada' id='e{k}'><header><span class='etiqueta'>{TIPO[t['tipo']]} · {IDIOMA[t['lang']]}</span>"
            f"<h3>{html.escape(t['nombre'])}</h3><p class='nota'>{html.escape(t['en'])} en inglés. {html.escape(t['porque'])}</p></header>"
            f"{corr}<div class='lado'><div class='pdf'><h4>PDF oficial</h4>{imgs}</div>"
            f"<div class='nuestro'><h4>Extraído</h4>{botones}<div class='extraido' id='m{k}'>{t['html']}</div>{pies}</div></div></article>")


def main():
    salida = sys.argv[1]
    tmp = salida + ".muestra"
    sys.argv = [sys.argv[0], tmp]
    M.main()
    import pickle
    tarjetas = pickle.load(open(tmp + ".pkl", "rb"))
    for ext in (".pkl", ".json"):
        os.remove(tmp + ext)
    cs = correcciones()
    nom = nombres()
    por = collections.Counter((c["tipo"], c["idioma"]) for c in cs if c["origen"] != "cartas de hechizos")
    propias = [c for c in cs if c["origen"] != "cartas de hechizos"]
    cartas = [c for c in cs if c["origen"] == "cartas de hechizos"]
    rev = {t: len(json.load(open(os.path.join(DATOS, f"revisados_{t}.json"), encoding="utf-8"))["revisados"])
           for t in ("criaturas", "conjuros", "objetos")}
    indice = "".join(f"<li><a href='#e{k}'>{html.escape(t['nombre'])}</a> <span class='nota'>({TIPO[t['tipo']].lower()}, {IDIOMA[t['lang']]})</span></li>"
                     for k, t in enumerate(tarjetas))
    maq = "".join(f"<li><b>{html.escape(a)}.</b> {html.escape(b)}</li>" for a, b in MAQUETACION)
    cuerpo = PLANTILLA.format(
        tarjetas="".join(tarjeta(t, k) for k, t in enumerate(tarjetas)), indice=indice, maquetacion=maq,
        n_propias=len(propias), n_cartas=len(cartas),
        tabla_criaturas=tabla_correcciones([c for c in propias if c["tipo"] == "criaturas"], nom),
        tabla_conjuros=tabla_correcciones([c for c in propias if c["tipo"] == "conjuros"], nom),
        tabla_objetos=tabla_correcciones([c for c in propias if c["tipo"] == "objetos"], nom),
        tabla_cartas=tabla_correcciones(cartas, nom),
        cri_de=por[("criaturas", "de")], cri_it=por[("criaturas", "it")], cri_fr=por[("criaturas", "fr")],
        rev_cri=rev["criaturas"], rev_con=rev["conjuros"], rev_obj=rev["objetos"],
    )
    # comillas rectas en lo que se lee en una web (decision C de la T-0111)
    cuerpo = cuerpo.replace("«", '"').replace("»", '"')
    open(salida, "w", encoding="utf-8", newline="\n").write(cuerpo)
    print(salida, round(len(cuerpo) / 1e6, 2), "MB")


PLANTILLA = """<title>Datos del Compendio SRD</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,650&family=Public+Sans:ital,wght@0,400;0,600;0,700;1,400&display=swap">
<style>
/* Lectura en una columna; en la muestra, el PDF oficial y lo extraido lado a lado (uno encima del otro en el movil). */
:root {{
  --papel: #f3f4f7; --hoja: #ffffff; --tinta: #1c1f2a; --tenue: #5a5f6f; --linea: #d8dbe3;
  --acento: #5a3fc2; --oro: #8f6b10; --suave: #ece9f8; --rojo: #a3342b; --verde: #2f6b3a;
  --display: "Fraunces", Georgia, "Times New Roman", serif;
  --texto: "Public Sans", "Segoe UI", system-ui, sans-serif;
}}
@media (prefers-color-scheme: dark) {{
  :root:not([data-theme="light"]) {{
    --papel: #14151b; --hoja: #1b1d26; --tinta: #e6e7ee; --tenue: #a0a5b6; --linea: #2c2f3b;
    --acento: #ab97ff; --oro: #d9b34c; --suave: #262238; --rojo: #f08a7f; --verde: #8fd19b; color-scheme: dark;
  }}
}}
:root[data-theme="dark"] {{
  --papel: #14151b; --hoja: #1b1d26; --tinta: #e6e7ee; --tenue: #a0a5b6; --linea: #2c2f3b;
  --acento: #ab97ff; --oro: #d9b34c; --suave: #262238; --rojo: #f08a7f; --verde: #8fd19b; color-scheme: dark;
}}
* {{ box-sizing: border-box; }}
body {{ background: var(--papel); color: var(--tinta); font-family: var(--texto); font-size: 16px; line-height: 1.6; }}
.pagina {{ max-width: 72rem; margin: 0 auto; padding-inline: 18px; padding-block: 40px 72px; display: flex; flex-direction: column; gap: 44px; }}
.lectura {{ max-width: 46rem; display: flex; flex-direction: column; gap: 16px; }}
h1, h2, h3, h4 {{ font-family: var(--display); font-weight: 650; line-height: 1.15; text-wrap: balance; margin: 0; }}
h1 {{ font-size: clamp(2rem, 5vw, 2.7rem); letter-spacing: -0.01em; }}
h2 {{ font-size: 1.55rem; }}
h3 {{ font-size: 1.3rem; }}
h4 {{ font-size: 0.95rem; font-family: var(--texto); font-weight: 700; color: var(--tenue); letter-spacing: 0.04em; text-transform: uppercase; }}
h5 {{ margin: 8px 0 0; font-size: 0.95rem; }}
p {{ margin: 0; }}
a {{ color: var(--acento); text-underline-offset: 2px; }}
a:focus-visible, button:focus-visible, summary:focus-visible {{ outline: 2px solid var(--acento); outline-offset: 2px; border-radius: 3px; }}
.fecha {{ color: var(--tenue); font-size: 0.92rem; letter-spacing: 0.02em; }}
.entrada-txt {{ font-size: 1.08rem; color: var(--tenue); }}
.resumen {{ background: var(--suave); border-radius: 10px; padding: 18px 20px; display: flex; flex-direction: column; gap: 10px; }}
.cifras {{ display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 0; border-top: 2px solid var(--oro); border-bottom: 2px solid var(--oro); padding-block: 10px; }}
.cifras div {{ display: flex; flex-direction: column; align-items: center; }}
.cifras b {{ font-family: var(--display); font-size: 1.6rem; font-variant-numeric: tabular-nums; }}
.cifras span {{ font-size: 0.85rem; color: var(--tenue); }}
@media (max-width: 460px) {{ .cifras {{ grid-template-columns: repeat(2, minmax(0, 1fr)); row-gap: 8px; }} }}
ul, ol {{ margin: 0; padding-left: 1.25rem; display: flex; flex-direction: column; gap: 6px; }}
.pruebas li {{ padding-left: 4px; }}
.nota {{ font-size: 0.9rem; color: var(--tenue); }}
.indice {{ columns: 2 16rem; display: block; }}
.indice li {{ break-inside: avoid; margin-bottom: 4px; }}
.entrada {{ background: var(--hoja); border: 1px solid var(--linea); border-radius: 12px; padding: 20px; display: flex; flex-direction: column; gap: 14px; scroll-margin-top: 16px; }}
.entrada header {{ display: flex; flex-direction: column; gap: 4px; }}
.etiqueta {{ font-size: 0.78rem; font-weight: 700; letter-spacing: 0.06em; text-transform: uppercase; color: var(--oro); }}
.lado {{ display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1fr); gap: 20px; align-items: start; }}
@media (max-width: 820px) {{ .lado {{ grid-template-columns: minmax(0, 1fr); }} }}
.pdf, .nuestro {{ min-width: 0; display: flex; flex-direction: column; gap: 10px; }}
figure {{ margin: 0; display: flex; flex-direction: column; gap: 4px; }}
figure img {{ width: 100%; height: auto; border: 1px solid var(--linea); border-radius: 6px; background: #fff; }}
figcaption {{ font-size: 0.8rem; color: var(--tenue); }}
.extraido {{ font-size: 0.95rem; display: flex; flex-direction: column; gap: 8px; }}
.extraido .tipo {{ font-style: italic; color: var(--tenue); }}
.extraido h4 {{ margin-top: 8px; color: var(--oro); border-bottom: 1px solid var(--oro); padding-bottom: 2px; text-transform: none; letter-spacing: 0; font-family: var(--display); font-size: 1.05rem; }}
.extraido table.car {{ border-collapse: collapse; width: 100%; font-variant-numeric: tabular-nums; }}
.extraido table.car th, .extraido table.car td {{ border: 1px solid var(--linea); text-align: center; padding: 4px; font-size: 0.85rem; }}
.extraido .ficha {{ border: 1px solid var(--linea); border-radius: 8px; padding: 10px 12px; display: flex; flex-direction: column; gap: 4px; }}
.extraido ul {{ gap: 4px; }}
.cambio {{ display: flex; gap: 6px; }}
.cambio button {{ font: inherit; font-size: 0.85rem; padding: 4px 12px; border-radius: 999px; border: 1px solid var(--linea); background: var(--papel); color: var(--tinta); cursor: pointer; }}
.cambio button[aria-pressed="true"] {{ background: var(--acento); border-color: var(--acento); color: var(--hoja); }}
.corr {{ background: var(--suave); border-radius: 8px; padding: 10px 14px; font-size: 0.92rem; }}
.antes {{ color: var(--rojo); }}
.despues {{ color: var(--verde); }}
.tabla {{ overflow-x: auto; }}
table {{ border-collapse: collapse; width: 100%; font-size: 0.9rem; }}
th, td {{ text-align: left; padding: 7px 8px; border-bottom: 1px solid var(--linea); vertical-align: top; }}
th {{ color: var(--tenue); font-weight: 600; font-size: 0.82rem; }}
caption {{ text-align: left; font-weight: 700; padding-bottom: 4px; }}
details {{ border-top: 1px solid var(--linea); padding-top: 12px; }}
summary {{ cursor: pointer; font-weight: 600; }}
details > div {{ margin-top: 12px; display: flex; flex-direction: column; gap: 10px; }}
@media (prefers-reduced-motion: reduce) {{ * {{ scroll-behavior: auto !important; }} }}
</style>

<main class="pagina">
  <header class="lectura">
    <p class="fecha">T-0164 · fase 1 · 13 de octubre de 2026</p>
    <h1>Datos del Compendio SRD</h1>
    <p class="entrada-txt">Criaturas, conjuros, objetos mágicos y estados del SRD 5.2.1 oficial, sacados de los cinco PDF y comprobados. Abajo tienes una muestra con la página del PDF al lado para que la compares tú.</p>
  </header>

  <section class="lectura" aria-labelledby="t-res">
    <h2 id="t-res">En resumen</h2>
    <div class="cifras" role="list">
      <div role="listitem"><b>330</b><span>criaturas</span></div>
      <div role="listitem"><b>339</b><span>conjuros</span></div>
      <div role="listitem"><b>258</b><span>objetos mágicos</span></div>
      <div role="listitem"><b>15</b><span>estados</span></div>
    </div>
    <div class="resumen">
      <p>Están todos, en español, inglés, alemán, francés e italiano, y emparejados entre idiomas. Las 330 criaturas de cada idioma coinciden nombre a nombre con el índice de perfiles de su PDF. Conjuros y objetos son los del glosario de la T-0107.</p>
      <p>He corregido {n_propias} erratas de las traducciones oficiales en las que la cifra o la regla contradice al inglés y a los otros idiomas, más {n_cartas} en conjuros que ya habíamos encontrado para las cartas de hechizos. El español casi no tenía. Las demás diferencias con el inglés (unas 300) están revisadas una a una y no son errata: números con letra, conversiones de unidades o listas en otro orden.</p>
      <p>Cada texto con medidas tiene también su versión en pies, que es la que saldrá por defecto. Cada cifra en pies está buscada en el SRD inglés de la misma entrada, y ninguna queda sin respaldo.</p>
      <p>El comprobador de estilo de la T-0111 da 0 errores en español, inglés y alemán. Se aplican tus normas: DM y no GM, estados con mayúscula y nada de raya.</p>
    </div>
  </section>

  <section class="lectura" aria-labelledby="t-mira">
    <h2 id="t-mira">Lo que tienes que mirar</h2>
    <ol class="pruebas">
      <li><b>Compara tres o cuatro entradas de la muestra</b> con su página del PDF. Deberías leer el mismo texto palabra por palabra. Las únicas diferencias son DM por GM, los estados con mayúscula y las erratas, que salen marcadas en rojo y verde encima de cada entrada.</li>
      <li><b>Pulsa «Pies» en dos o tres entradas en español</b> (el dragón rojo, la bola de fuego o la bolsa de contención) y mira si se lee natural: «a 30 pies o menos», «una esfera de 20 pies de radio», «1 onza».</li>
      <li><b>Repasa las erratas corregidas</b> de criaturas, conjuros y objetos, por si alguna te parece discutible.</li>
      <li><b>Dime si dejo el párrafo añadido al italiano.</b> El SRD italiano no trae la propiedad «Resistere all'ammaliamento» del bastón del encanto. La he añadido con las fórmulas del propio SRD italiano, pero es texto mío.</li>
      <li><b>Dime si te encaja lo del francés y el italiano.</b> En el plan dije que irían tal cual, y he corregido sus cifras cuando contradicen al inglés y a los otros tres idiomas (por ejemplo, un daño de 2d6 + 8 que en inglés es 2d8 + 8). No he tocado su redacción.</li>
    </ol>
    <p class="nota">Con tu visto bueno empiezo la fase 2, el plugin. Antes del primer npm install te pediré el permiso para node_modules.</p>
  </section>

  <section class="bloque" aria-labelledby="t-muestra" style="display:flex;flex-direction:column;gap:20px">
    <div class="lectura">
      <h2 id="t-muestra">La muestra</h2>
      <p>Diecinueve entradas elegidas por difíciles: fichas legendarias, listas de conjuros, tablas, una ficha dentro de un conjuro, la tabla ancha del aparato y las erratas corregidas en alemán e italiano. Las he revisado a mano contra el PDF y coinciden.</p>
      <ul class="indice">{indice}</ul>
    </div>
    {tarjetas}
  </section>

  <section class="lectura" aria-labelledby="t-err">
    <h2 id="t-err">Erratas corregidas</h2>
    <p>Manda el inglés (tu decisión 34 de la T-0111). Cada una sale de comparar las cifras de cada rasgo, acción, conjuro u objeto con el inglés y está revisada contra los otros cuatro idiomas y contra el PDF.</p>
    <details open><summary>Criaturas ({cri_de} en alemán, {cri_it} en italiano, {cri_fr} en francés, ninguna en español)</summary><div>{tabla_criaturas}</div></details>
    <details><summary>Conjuros, encontradas ahora</summary><div>{tabla_conjuros}</div></details>
    <details><summary>Objetos mágicos</summary><div>{tabla_objetos}</div></details>
    <details><summary>Conjuros, de las cartas de hechizos ({n_cartas})</summary><div><p class="nota">Las encontraron los revisores de las cartas (T-0108) comparando el español, el inglés y el alemán. Solo vienen las que corrigen el SRD (mecánica, erratas, unidades, términos y formato), no las de redacción propia de las cartas.</p>{tabla_cartas}</div></details>
    <p class="nota">Diferencias revisadas que no son errata: {rev_cri} en criaturas, {rev_con} en conjuros y {rev_obj} en objetos. Quedan apuntadas para que no vuelvan a avisar.</p>
  </section>

  <section class="lectura" aria-labelledby="t-maq">
    <h2 id="t-maq">Fallos de maquetación del PDF arreglados</h2>
    <p>No son erratas del texto: el PDF coloca algo fuera de su sitio y el lector lo devuelve. Cada uno está comprobado contra los otros idiomas.</p>
    <ul>{maquetacion}</ul>
  </section>

  <details class="lectura">
    <summary>Cómo está comprobado</summary>
    <div>
      <ul>
        <li><b>Recuento</b>: las fichas de cada idioma contra el índice de perfiles de su PDF, nombre a nombre; conjuros, objetos y estados contra el glosario de la T-0107.</li>
        <li><b>Emparejado entre idiomas</b>: español, inglés y alemán por el glosario. Francés e italiano por huella: cifras, nivel, escuela, clases, rareza, sintonización y, en los objetos, el parecido del nombre con el español. El método se probó en español y alemán contra el glosario: 330 de 330 criaturas y 339 de 339 conjuros. Los 70 objetos con el nombre menos parecido los repasé a mano.</li>
        <li><b>Campos y estructura</b>: cada ficha con CA, iniciativa, PG, velocidad, características, sentidos, idiomas y VD, y las mismas secciones, rasgos y párrafos que la inglesa.</li>
        <li><b>Cifras</b>: dados, CD, bonificadores, usos y medidas de cada rasgo, acción, conjuro y objeto contra el inglés, con sus medidas pasadas a metros.</li>
        <li><b>Pies</b>: cada medida pasada se busca en el inglés de la misma entrada, y una prueba de punta a punta compara cada entrada en pies con el inglés tal cual.</li>
        <li><b>Estilo</b>: revisar_estilo.py con --metros. Los avisos que quedan son texto del SRD tal cual: «impactar» dicho de una munición que choca, y siete formas alemanas del propio SRD.</li>
        <li>Todo se rehace desde los PDF con una orden (construir_datos.py) y queda en git.</li>
      </ul>
    </div>
  </details>
</main>
<script>
document.querySelectorAll('.cambio button').forEach(function (b) {{
  b.addEventListener('click', function () {{
    var k = b.getAttribute('data-t'), ver = b.getAttribute('data-ver');
    document.getElementById('m' + k).hidden = ver !== 'm';
    document.getElementById('p' + k).hidden = ver !== 'p';
    b.parentNode.querySelectorAll('button').forEach(function (x) {{ x.setAttribute('aria-pressed', x === b ? 'true' : 'false'); }});
  }});
}});
</script>
"""

if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
