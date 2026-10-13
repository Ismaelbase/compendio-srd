# -*- coding: utf-8 -*-
"""Rehace todos los datos del SRD desde los PDF y pasa todas las comprobaciones, en orden.

    py -3.14 construir_datos.py            rehace y comprueba
    py -3.14 construir_datos.py --estilo   y ademas pasa revisar_estilo.py (T-0111) por el texto en ES, EN y DE

Sale con 1 si algun paso falla. Los datos que usa el plugin quedan en datos\\criaturas.json, conjuros.json,
objetos.json, estados.json, reglas.json, personajes.json y equipo.json.
"""
import json
import os
import subprocess
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
PASOS = [
    ("volcado de los PDF", ["srd.py"]),
    ("criaturas", ["criaturas.py"]),
    ("criaturas: emparejado, erratas y normas de casa", ["emparejar.py"]),
    ("criaturas: comprobacion", ["comprobar_criaturas.py"]),
    ("conjuros", ["conjuros.py"]),
    ("conjuros: emparejado, erratas y normas de casa", ["emparejar_conjuros.py"]),
    ("conjuros: comprobacion", ["comprobar_conjuros.py"]),
    ("objetos", ["objetos.py"]),
    ("objetos: emparejado, erratas y normas de casa", ["emparejar_objetos.py"]),
    ("objetos: comprobacion", ["comprobar_objetos.py"]),
    ("estados", ["estados.py"]),
    ("reglas: notas de los capitulos de reglas", ["capitulos.py"]),
    ("reglas: emparejado, erratas y normas de casa", ["emparejar_reglas.py"]),
    ("reglas: comprobacion", ["comprobar_reglas.py"]),
    ("medidas en pies (comprobadas contra el ingles)", ["pies.py"]),
    ("pies: prueba de punta a punta", ["comprobar_pies.py"]),
]
ESTILO = os.environ.get("ESTILO_DIR", r"G:\General\Tareas\material\T-0111-estilo-rol-es-en")


def correr(args):
    r = subprocess.run([sys.executable] + args, cwd=AQUI, capture_output=True, text=True, encoding="utf-8")
    ultima = [l for l in r.stdout.strip().splitlines() if l.strip()][-1:] or [""]
    return r.returncode, ultima[0], r.stdout + r.stderr


def main():
    fallos = 0
    for nombre, args in PASOS:
        code, ultima, todo = correr(args)
        estado = "bien" if code == 0 else "FALLA"
        print(f"{estado:5}  {nombre}: {ultima}")
        if code != 0:
            fallos += 1
            print(todo[-3000:])
    if "--estilo" in sys.argv:
        salida = os.path.join(os.environ.get("LOCALAPPDATA", AQUI), "compendio-srd", "textos")
        exc = json.load(open(os.path.join(os.path.dirname(AQUI), "datos", "excepciones_estilo.json"), encoding="utf-8"))
        aceptados = {(x["tipo"], x["idioma"], x["regla"], x["encontrado"]) for x in exc["aceptados"]}
        for tipo in ("criaturas", "conjuros", "objetos", "estados", "reglas", "personajes", "equipo"):
            correr(["exportar_textos.py", tipo, salida])
            for l in ("es", "en", "de"):
                js = os.path.join(salida, f"estilo_{tipo}_{l}.json")
                subprocess.run([sys.executable, os.path.join(ESTILO, "revisar_estilo.py"),
                                os.path.join(salida, f"{tipo}_{l}.txt"), "--idioma", l, "--metros", "--json", js],
                               capture_output=True, text=True, encoding="utf-8")
                hallazgos = [h for v in json.load(open(js, encoding="utf-8")).values() for h in v["hallazgos"]]
                errores = [h for h in hallazgos if h["nivel"] == "ERROR"
                           and (tipo, l, h["regla"], h["encontrado"]) not in aceptados]
                avisos = sum(1 for h in hallazgos if h["nivel"] != "ERROR")
                print(f"{'bien' if not errores else 'FALLA':5}  estilo {tipo} {l}: {len(errores)} errores, {avisos} avisos")
                for h in errores[:10]:
                    print("        ", h["regla"], h["encontrado"], "|", h["contexto"][:90])
                fallos += bool(errores)
    return 1 if fallos else 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
