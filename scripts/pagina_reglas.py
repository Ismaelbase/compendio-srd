# -*- coding: utf-8 -*-
"""Pagina de revision de la fase 1b (para Ismael): el resto del SRD 5.2.1. Resumen, lo que tiene que mirar, la
muestra con el recorte del PDF oficial al lado de lo extraido (en metros y en pies), las erratas corregidas y los
fallos de maquetacion arreglados.

Uso: py -3.14 pagina_reglas.py <salida.html>
"""
import collections
import html
import json
import os
import pickle
import re
import sys

import muestra_reglas as M
import pagina_revision as P

AQUI = os.path.dirname(os.path.abspath(__file__))
DATOS = os.path.join(os.path.dirname(AQUI), "datos")
IDIOMA = P.IDIOMA
TIPO = M.TIPO
MAX_RECORTES = 4

MAQUETACION = [
    ("Los cinco", "Las tablas de rasgos de cada clase ocupan la página entera y el PDF las parte en dos columnas, a veces con la cabecera en tres líneas y los espacios de conjuro agrupados. Se leen enteras, con su grupo de columnas, y van al principio de su clase."),
    ("Los cinco", "Las tablas flotan: la de equipo de aventureros caía dentro de la nota de los abrojos, la de legados infernales (inglés) en la del humano y la de equipo inicial a niveles superiores (francés) en la de multiclase. Cada tabla va a la nota que la cita."),
    ("Los cinco", "Recuadros grises, listas en columnas (acciones, estados, tipos de criatura), fórmulas («CA base = 10 + ...»), campos con rótulo (herramientas, trasfondos, especies, trampas) y tablas de rótulos a la izquierda (atributos básicos de cada clase) se leen como lo que son."),
    ("Italiano", "La tabla de armas repite dos filas (stocco y tridente). Se quitan las repetidas."),
    ("Italiano", "El SRD italiano no trae la entrada «Save» del glosario, que en inglés solo dice que es otro nombre de la tirada de salvación. Se queda sin ella."),
    ("Inglés", "El recuadro «Running a Monster» va en otra letra y las cabeceras «Weight» y «Cost» de la tabla de armas van en otro cuerpo. Se leen igual que las demás."),
    ("Español", "En la tabla de propósito especial de los objetos conscientes, el «1» de la primera fila va en la letra de la cabecera. Es una fila más."),
    ("Alemán", "En la misma tabla, el rótulo de cada fila («Gesinnung:») parecía una línea de campo. Es parte de la tabla."),
    ("Francés", "Dos tablas que siguen de la página anterior, una en cada columna (multiclase y bagatelas), parecían una sola. Son dos."),
]


def correcciones():
    ruta = os.path.join(DATOS, "correcciones_reglas.json")
    return json.load(open(ruta, encoding="utf-8"))["correcciones"] if os.path.exists(ruta) else []


def nombres():
    out = {}
    for f in M.FICHEROS:
        for r in json.load(open(os.path.join(DATOS, f + ".json"), encoding="utf-8")):
            out[r["id"]] = {l: r[l]["nombre"] for l in IDIOMA if l in r}
    return out


def tabla_correcciones(lista, nom):
    filas = []
    for c in lista:
        n = nom.get(c["id"], {})
        filas.append(f"<tr><td>{IDIOMA[c['idioma']]}</td><td>{html.escape(n.get(c['idioma'], c['id']))}"
                     f"<div class='nota'>{html.escape(n.get('es', ''))}</div></td>"
                     f"<td><span class='antes'>{P.limpio(c.get('antes')) or '<em>(no estaba)</em>'}</span></td>"
                     f"<td><span class='despues'>{P.limpio(c.get('despues'))}</span></td>"
                     f"<td class='nota'>{html.escape(c.get('por_que', ''))}</td></tr>")
    return ("<div class='tabla'><table><thead><tr><th>Idioma</th><th>Nota</th><th>Decía</th><th>Dice ahora</th>"
            "<th>Por qué</th></tr></thead><tbody>" + "".join(filas) + "</tbody></table></div>")


def tarjeta(t, k):
    imgs = t["imgs"][:MAX_RECORTES]
    resto = sorted({p for p, _ in t["imgs"][MAX_RECORTES:]} - {p for p, _ in imgs})
    figs = "".join(f"<figure><img src='data:image/jpeg;base64,{b64}' alt='Página {p} del SRD en {IDIOMA[t['lang']]}' "
                   f"loading='lazy'><figcaption>Página {p}</figcaption></figure>" for p, b64 in imgs)
    if resto:
        figs += f"<p class='nota'>Sigue en la página {', '.join(map(str, resto))} del PDF.</p>"
    botones, pies = "", ""
    if t["html_pies"]:
        botones = (f"<div class='cambio' role='group' aria-label='Medidas'>"
                   f"<button type='button' aria-pressed='true' data-ver='m' data-t='{k}'>Metros (SRD)</button>"
                   f"<button type='button' aria-pressed='false' data-ver='p' data-t='{k}'>Pies</button></div>")
        pies = f"<div class='extraido' id='p{k}' hidden>{t['html_pies']}</div>"
    corr = f"<div class='corr'><b>Corregido en esta nota:</b><ul>{t['corr']}</ul></div>" if t["corr"] else ""
    return (f"<article class='entrada' id='e{k}'><header><span class='etiqueta'>{TIPO[t['tipo']]} · {IDIOMA[t['lang']]}</span>"
            f"<h3>{html.escape(t['nombre'])}</h3><p class='nota'>{html.escape(t['en'])} en inglés. {html.escape(t['porque'])}</p>"
            f"</header>{corr}<div class='lado'><div class='pdf'><h4>PDF oficial</h4>{figs}</div>"
            f"<div class='nuestro'><h4>Extraído</h4>{botones}<div class='extraido' id='m{k}'>{t['html']}</div>{pies}</div>"
            f"</div></article>")


def main():
    salida = sys.argv[1]
    tmp = salida + ".muestra"
    sys.argv = [sys.argv[0], tmp]
    M.main()
    tarjetas = pickle.load(open(tmp + ".pkl", "rb"))
    os.remove(tmp + ".pkl")
    datos = [r for f in M.FICHEROS for r in json.load(open(os.path.join(DATOS, f + ".json"), encoding="utf-8"))]
    cuenta = collections.Counter(r["tipo"] for r in datos)
    cs = correcciones()
    nom = nombres()
    por_idioma = collections.Counter(c["idioma"] for c in cs)
    rev = json.load(open(os.path.join(DATOS, "revisados_reglas.json"), encoding="utf-8"))["revisados"]
    indice = "".join(f"<li><a href='#e{k}'>{html.escape(t['nombre'])}</a> <span class='nota'>({TIPO[t['tipo']].lower()}, "
                     f"{IDIOMA[t['lang']]})</span></li>" for k, t in enumerate(tarjetas))
    maq = "".join(f"<li><b>{html.escape(a)}.</b> {html.escape(b)}</li>" for a, b in MAQUETACION)
    pies_n = sum(1 for r in datos for l in ("es", "de", "fr", "it") if r.get(l, {}).get("pies"))
    estilo = P.PLANTILLA[P.PLANTILLA.index("<style>"):P.PLANTILLA.index("</style>")].replace("{{", "{").replace("}}", "}")
    cuerpo = PLANTILLA.format(
        estilo=estilo + EXTRA_CSS, tarjetas="".join(tarjeta(t, k) for k, t in enumerate(tarjetas)), indice=indice,
        maquetacion=maq, n_tarjetas=len(tarjetas),
        n_reglas=cuenta["regla"], n_glosario=cuenta["glosario"], n_clases=cuenta["clase"],
        n_subclases=cuenta["subclase"], n_especies=cuenta["especie"], n_trasfondos=cuenta["trasfondo"],
        n_dotes=cuenta["dote"], n_armas=cuenta["arma"], n_armaduras=cuenta["armadura"],
        n_herramientas=cuenta["herramienta"], n_equipo=cuenta["equipo"], n_venenos=cuenta["veneno"],
        n_trampas=cuenta["trampa"], n_total=len(datos),
        n_corr=len(cs), corr_por=", ".join(f"{n} en {IDIOMA[l]}" for l, n in por_idioma.most_common()) or "ninguna",
        tabla_corr=tabla_correcciones(cs, nom), n_rev=len(rev), n_pies=pies_n,
    )
    cuerpo = cuerpo.replace("«", '"').replace("»", '"')
    open(salida, "w", encoding="utf-8", newline="\n").write(cuerpo)
    print(salida, round(len(cuerpo) / 1e6, 2), "MB")


EXTRA_CSS = """
.extraido h5, .extraido h6 { margin: 6px 0 0; font-family: var(--display); font-size: 1rem; color: var(--oro); }
.extraido h4 + h5 { margin-top: 0; }
.extraido aside { border-left: 3px solid var(--oro); background: var(--suave); border-radius: 0 8px 8px 0; padding: 8px 12px; display: flex; flex-direction: column; gap: 6px; }
.extraido aside h5 { margin: 0; font-variant: small-caps; letter-spacing: 0.03em; }
.extraido .campos { display: flex; flex-direction: column; gap: 2px; }
.extraido .formula { text-align: center; }
.extraido .sub { font-style: italic; color: var(--tenue); }
.extraido ul.columnas { columns: 3 8rem; display: block; }
.extraido table.vertical th { width: 38%; color: var(--tinta); }
.extraido th.grupo { text-align: center; border-bottom: 1px solid var(--oro); }
.extraido table { font-size: 0.85rem; font-variant-numeric: tabular-nums; }
.extraido td, .extraido th { padding: 4px 6px; }
.cifras.seis { grid-template-columns: repeat(6, minmax(0, 1fr)); }
@media (max-width: 640px) { .cifras.seis { grid-template-columns: repeat(3, minmax(0, 1fr)); row-gap: 8px; } }
"""

PLANTILLA = """<title>Resto del SRD</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,650&family=Public+Sans:ital,wght@0,400;0,600;0,700;1,400&display=swap">
{estilo}</style>

<main class="pagina">
  <header class="lectura">
    <p class="fecha">T-0164 · fase 1b · 13 de octubre de 2026</p>
    <h1>El resto del SRD, en datos</h1>
    <p class="entrada-txt">Clases, especies, trasfondos, dotes, equipo, el glosario de reglas, las herramientas del juego y los capítulos de reglas del SRD 5.2.1 oficial, en los cinco idiomas y comprobados. Abajo tienes una muestra con la página del PDF al lado.</p>
  </header>

  <section class="lectura" aria-labelledby="t-res">
    <h2 id="t-res">En resumen</h2>
    <div class="cifras seis" role="list">
      <div role="listitem"><b>{n_reglas}</b><span>secciones de reglas</span></div>
      <div role="listitem"><b>{n_glosario}</b><span>entradas de glosario</span></div>
      <div role="listitem"><b>{n_clases} + {n_subclases}</b><span>clases y subclases</span></div>
      <div role="listitem"><b>{n_especies} + {n_trasfondos}</b><span>especies y trasfondos</span></div>
      <div role="listitem"><b>{n_dotes}</b><span>dotes</span></div>
      <div role="listitem"><b>{n_armas} + {n_armaduras}</b><span>armas y armaduras</span></div>
      <div role="listitem"><b>{n_herramientas}</b><span>herramientas</span></div>
      <div role="listitem"><b>{n_equipo}</b><span>objetos de equipo</span></div>
      <div role="listitem"><b>{n_venenos}</b><span>venenos</span></div>
      <div role="listitem"><b>{n_trampas}</b><span>trampas</span></div>
    </div>
    <div class="resumen">
      <p>Son {n_total} notas en cada idioma, sacadas de los cinco PDF con el mismo lector y emparejadas entre idiomas. Con lo de la fase 1 (criaturas, conjuros, objetos mágicos y estados) está ya todo el SRD 5.2.1. Los quince estados del glosario no se repiten: ya tienen su nota.</p>
      <p>Las secciones de reglas son las de 18 pt de cada capítulo («Combate», «Multiclase», «Ritmo de viaje», «Encuentros de combate»...). Clases, especies, trasfondos, dotes, herramientas, equipo, armas, armaduras, venenos, trampas y cada entrada del glosario van en su propia nota, para que se puedan enlazar.</p>
      <p>He corregido {n_corr} erratas de las traducciones oficiales ({corr_por}) donde la cifra contradice al inglés. Las otras {n_rev} diferencias de cifras con el inglés están revisadas una a una y no son errata: conversiones de unidades propias de cada traducción, cifras con letra o reglas dichas de otra forma.</p>
      <p>Hay versión en pies de {n_pies} notas con medidas, como en la fase 1: cada cifra se busca en el inglés de la misma nota. También pasan los alcances de las armas («alcance 20/60»), los grados (°F) y las velocidades de los vehículos (millas por hora).</p>
    </div>
  </section>

  <section class="lectura" aria-labelledby="t-mira">
    <h2 id="t-mira">Lo que tienes que mirar</h2>
    <ol class="pruebas">
      <li><b>Compara tres o cuatro notas de la muestra</b> con su página del PDF: el bardo, el dracónido y la trampa italiana son las más difíciles. Deberías leer el mismo texto y las mismas tablas.</li>
      <li><b>Mira la tabla de rasgos del bardo y la del brujo</b>: cada fila es un nivel, con sus espacios de conjuro bajo su grupo de columnas.</li>
      <li><b>Pulsa «Pies» en la espada larga, el dracónido y el ritmo de viaje</b> y mira si se lee natural.</li>
      <li><b>Repasa las erratas corregidas</b> por si alguna te parece discutible.</li>
      <li><b>Dime si te vale cómo van partidas las notas</b>: una por sección de reglas, una por clase (con su subclase aparte), una por especie, trasfondo, dote, arma, armadura, herramienta, objeto de equipo, veneno, trampa y entrada del glosario.</li>
    </ol>
    <p class="nota">Con tu visto bueno empiezo la fase 2, el plugin. Antes del primer npm install te pediré el permiso para node_modules.</p>
  </section>

  <section class="bloque" aria-labelledby="t-muestra" style="display:flex;flex-direction:column;gap:20px">
    <div class="lectura">
      <h2 id="t-muestra">La muestra</h2>
      <p>{n_tarjetas} notas elegidas por difíciles, de todos los tipos y de los cinco idiomas. Las he revisado a mano contra el PDF. En las notas largas solo va el principio del PDF.</p>
      <ul class="indice">{indice}</ul>
    </div>
    {tarjetas}
  </section>

  <section class="lectura" aria-labelledby="t-err">
    <h2 id="t-err">Erratas corregidas</h2>
    <p>Manda el inglés (tu decisión 34 de la T-0111). Salen de comparar las cifras de cada apartado y de cada tabla con el inglés, y cada una está revisada contra los otros cuatro idiomas.</p>
    <details open><summary>Las {n_corr} erratas</summary><div>{tabla_corr}</div></details>
  </section>

  <section class="lectura" aria-labelledby="t-maq">
    <h2 id="t-maq">Fallos de maquetación del PDF arreglados</h2>
    <p>No son erratas del texto: el PDF coloca algo fuera de su sitio o con otra letra, y el lector lo devuelve a su sitio.</p>
    <ul>{maquetacion}</ul>
  </section>

  <details class="lectura">
    <summary>Cómo está comprobado</summary>
    <div>
      <ul>
        <li><b>Estructura</b>: los cinco PDF tienen los mismos títulos en el mismo sitio, capítulo a capítulo, y cada nota tiene los mismos títulos dentro que la inglesa. Las tablas de rasgos de las doce clases tienen sus 20 niveles y las mismas columnas en los cinco idiomas.</li>
        <li><b>Emparejado</b>: las secciones de reglas, por su sitio. Las listas que cada idioma ordena por su alfabeto (clases, glosario, equipo, dotes...), en español y alemán por el glosario de la T-0107; en francés e italiano por huella: cifras, precio, forma, etiqueta del glosario, parecido del nombre con el español y en qué fichas, conjuros y secciones sale cada nombre. Además, francés e italiano se emparejan otra vez desde el español, y donde las dos vías no coinciden lo he mirado a mano. Repasé a ojo los 322 nombres en los cinco idiomas.</li>
        <li><b>Cifras</b>: cada apartado y cada tabla de cada nota contra el inglés, con sus medidas pasadas a metros (y los galones, pies cúbicos, grados y millas por hora a su medida).</li>
        <li><b>Pies</b>: cada medida pasada se busca en el inglés de la misma nota.</li>
        <li><b>Estilo</b>: revisar_estilo.py con --metros en español, inglés y alemán. Tus normas en español e inglés: DM y no GM, estados con mayúscula y nada de raya.</li>
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
