// Banco de pruebas: genera todas las notas de los cinco idiomas en una carpeta y comprueba que estan bien hechas.
// Uso: npm test [-- carpeta]   (por defecto .test/boveda)
import { mkdirSync, rmSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { Generador, rutasPlan, type Nota, type OpcionesNotas } from "../src/notas";
import { IDIOMAS, SECCIONES, type Idioma } from "../src/tipos";
import { pruebasEncuentro } from "./encuentro";

const salida = process.argv[2] ?? ".test/boveda";
let fallos = 0;
const fallo = (msg: string) => {
	fallos++;
	if (fallos <= 60) console.log("  FALLO", msg);
};

function generar(op: OpcionesNotas, idiomas: readonly Idioma[]): Map<string, string> {
	const secciones = new Set(SECCIONES);
	const plan = new Set<string>();
	for (const l of idiomas) for (const r of rutasPlan(l, secciones, op.raiz)) plan.add(r);
	const existe = (r: string) => plan.has(r);
	const notas = new Map<string, string>();
	for (const l of idiomas) {
		const t0 = Date.now();
		const otros = idiomas.filter((x) => x !== l).map((x) => ({ idioma: x, rutas: new Generador(x, op, existe).rutas }));
		const g = new Generador(l, op, existe, otros);
		const ns: Nota[] = g.notas(secciones);
		for (const n of ns) {
			if (notas.has(n.ruta)) fallo(`ruta repetida ${n.ruta}`);
			notas.set(n.ruta, n.contenido);
		}
		const sinEscribir = [...plan].filter((r) => r.startsWith(`${op.raiz}/${g.T.idioma}/`) && !notas.has(r));
		if (sinEscribir.length) fallo(`${l}: ${sinEscribir.length} rutas del plan sin nota: ${sinEscribir.slice(0, 3).join(", ")}`);
		console.log(`${l}: ${ns.length} notas en ${Date.now() - t0} ms`);
	}
	return notas;
}

function comprobar(notas: Map<string, string>, etiqueta: string): void {
	let enlaces = 0;
	let html = 0;
	const ejemplosHtml: string[] = [];
	for (const [ruta, texto] of notas) {
		// enlaces
		for (const m of texto.matchAll(/\[\[([^\]|#\\]+)(?:#[^\]|\\]*)?(?:\\?\|[^\]]*)?\]\]/g)) {
			enlaces++;
			if (!notas.has(m[1] ?? "")) fallo(`${etiqueta} ${ruta}: enlace roto a ${m[1]}`);
		}
		// marcas de los datos que quedan sin convertir
		const sueltas = texto.match(/<\/?(strong|em)>/g);
		if (sueltas) fallo(`${etiqueta} ${ruta}: etiquetas sin convertir ${sueltas.join(" ")}`);
		const h = texto.match(/<(i|b)>.*?<\/\1>/g) ?? [];
		html += h.length;
		if (h.length && ejemplosHtml.length < 8) ejemplosHtml.push(`${ruta}: ${h[0]}`);
		// propiedades
		if (texto.startsWith("---\n")) {
			const fin = texto.indexOf("\n---\n", 4);
			if (fin < 0) fallo(`${etiqueta} ${ruta}: propiedades sin cerrar`);
			for (const l of texto.slice(4, fin).split("\n")) {
				if (!/^(\S[^:]*: \S.*|\S[^:]*:|  - \S.*|    \S[^:]*: \S.*)$/.test(l)) fallo(`${etiqueta} ${ruta}: linea de propiedades rara: ${l}`);
			}
		}
		// tablas: todas las filas con las mismas columnas
		let cols = -1;
		for (const linea of texto.split("\n")) {
			const l = linea.replace(/^(> ?)+/, "");
			if (!l.startsWith("|")) {
				cols = -1;
				continue;
			}
			const n = l.replace(/\\\|/g, "").split("|").length;
			if (cols < 0) cols = n;
			else if (n !== cols) fallo(`${etiqueta} ${ruta}: fila de tabla con ${n - 2} columnas y no ${cols - 2}: ${l.slice(0, 80)}`);
		}
		// lineas que Markdown leeria como lista numerada sin serlo, o titulos vacios
		for (const linea of texto.split("\n")) {
			if (/^#{1,6}\s*$/.test(linea)) fallo(`${etiqueta} ${ruta}: titulo vacio`);
		}
	}
	console.log(`${etiqueta}: ${notas.size} notas, ${enlaces} enlaces, ${html} enfasis con HTML`);
	for (const e of ejemplosHtml) console.log(`    html: ${e.slice(0, 160)}`);
}

const base: OpcionesNotas = { raiz: "Compendio SRD", pies: true, fantasy: false, enlazarEstados: true };
const todas = generar(base, IDIOMAS);
comprobar(todas, "pies");
rmSync(salida, { recursive: true, force: true });
for (const [ruta, texto] of todas) {
	const f = join(salida, `${ruta}.md`);
	mkdirSync(dirname(f), { recursive: true });
	writeFileSync(f, texto);
}
console.log(`escritas en ${salida}`);

comprobar(generar({ ...base, pies: false, fantasy: true }, ["es", "de"]), "metros y Fantasy Statblocks");
// un idioma solo y solo criaturas: nada puede enlazar a notas que no se escriben
{
	const op = { ...base, raiz: "Solo" };
	const secciones = new Set(["criaturas"] as const);
	const plan = new Set(rutasPlan("fr", secciones, op.raiz));
	const g = new Generador("fr", op, (r) => plan.has(r));
	const notas = new Map(g.notas(secciones).map((n) => [n.ruta, n.contenido]));
	comprobar(notas, "solo criaturas en francés");
}
fallos += pruebasEncuentro();

console.log(fallos ? `${fallos} fallos` : "todo bien");
process.exit(fallos ? 1 : 0);
