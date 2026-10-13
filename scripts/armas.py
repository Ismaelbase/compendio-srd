# -*- coding: utf-8 -*-
"""Una nota por arma y por armadura, sacada de las filas de sus tablas (las secciones "Armas" y "Armaduras" del
capitulo de equipo), emparejadas entre idiomas.

Las tablas van por categorias (armas cuerpo a cuerpo sencillas, a distancia sencillas...; armaduras ligeras,
medias, pesadas, escudo), en el mismo orden en los cinco SRD; dentro de cada una, cada idioma ordena por su
alfabeto. Se casan como las demas notas de grupo (emparejar_reglas.emparejar_por_huella): glosario de T-0107 en
espanol y aleman; cifras (dados, CA, peso y precio), nombre parecido al espanol y textos en que salen, en frances e
italiano.

Cada nota: {"nombre", "categoria", "bloques": [{"t": "campos", "filas": [[rotulo de la columna, valor], ...]}]}.
"""
import re

from marcas import sin_marcas


def filas_por_categoria(tabla):
    """[(categoria, [fila, ...]), ...] y la cabecera. La fila de categoria lleva texto solo en la primera celda."""
    cab = tabla["filas"][0]
    cats = []
    for f in tabla["filas"][1:]:
        if f[0] and not any(x.strip() for x in f[1:]):
            cats.append((sin_marcas(f[0]).strip(), []))
        elif cats and f[0]:
            if f in cats[-1][1]:
                continue  # fila repetida en la maqueta (estoque y tridente del SRD italiano)
            cats[-1][1].append(f)
    return cab, cats


def notas_de_tabla(nota, tipo):
    tabla = next(b for b in nota["bloques"] if b["t"] == "tabla" and len(b["filas"]) > 10)
    cab, cats = filas_por_categoria(tabla)
    out = []
    for k, (cat, filas) in enumerate(cats):
        for f in filas:
            out.append({"nombre": sin_marcas(f[0]).strip(), "categoria": cat, "grupo": f"{tipo}.{k}", "tipo": tipo,
                        "p": tabla.get("p"), "bloques": [{"t": "campos", "filas": [[cab[c], f[c]] for c in
                                                                                     range(1, len(cab))]}]})
    return out


def comun_arma(n):
    """Datos del ingles: dados y tipo de dano, propiedades, maestria, peso en libras y precio en piezas de cobre."""
    v = dict(n["bloques"][0]["filas"])
    m = re.match(r"(\d+(?:d\d+)?)\s+(\w+)", v.get("Damage", ""))
    return {"categoria": n["categoria"], "dano": m.group(1) if m else None, "tipo_dano": m.group(2) if m else None,
            "propiedades": [p.strip() for p in re.split(r",\s*(?![^()]*\))", v.get("Properties", "")) if p.strip()
                            and p.strip() != "—"], "maestria": v.get("Mastery")}


def comun_armadura(n):
    v = dict(n["bloques"][0]["filas"])
    return {"categoria": n["categoria"], "ca": v.get("Armor Class (AC)"), "fuerza": v.get("Strength"),
            "sigilo": v.get("Stealth")}
