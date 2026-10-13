// Encuentros de combate con las reglas de 2024 (SRD 5.2.1, "Encuentros de combate"): presupuesto de PX por
// personaje, gasto sin multiplicadores y los consejos de "Solucion de problemas". Sin API de Obsidian.
import { comunDe, datosIdioma } from "./datos";
import { valorVd } from "./notas";
import type { Bloque, ComunCriatura, Idioma } from "./tipos";

export interface Personajes {
	n: number;
	nivel: number;
}

export interface EnEncuentro {
	clave: string;
	n: number;
}

export interface TablaPresupuesto {
	/** "Baja", "Moderada", "Alta" en el idioma del SRD */
	etiquetas: [string, string, string];
	/** nivel (1-20) -> [baja, moderada, alta] */
	porNivel: Map<number, [number, number, number]>;
	/** titulos de los consejos: [muchas criaturas, VD 0, numero de perfiles, criaturas poderosas] */
	consejos: [string, string, string, string];
}

const REGLA = "regla/combat-encounters";
const cifra = (s: string) => Number(s.replace(/<[^>]+>/g, "").replace(/[^\d]/g, ""));

/** La tabla "Presupuesto de PX por personaje" y los titulos de los consejos, leidos del SRD de cada idioma. */
export function tablaPresupuesto(idioma: Idioma): TablaPresupuesto {
	const e = datosIdioma(idioma).entradas[REGLA] ?? datosIdioma("en").entradas[REGLA];
	const bs: Bloque[] = e?.bloques ?? [];
	const tabla = bs.find((b) => b.t === "tabla" && (b.filas?.length ?? 0) === 21 && b.filas?.[1]?.[0] === "1");
	const filas = tabla?.filas ?? [];
	const cab = filas[0] ?? [];
	const porNivel = new Map<number, [number, number, number]>();
	for (const f of filas.slice(1)) porNivel.set(cifra(f[0] ?? ""), [cifra(f[1] ?? ""), cifra(f[2] ?? ""), cifra(f[3] ?? "")]);
	// los consejos son los titulos de nivel 2 tras el ultimo de nivel 1 ("Solucion de problemas"), en el mismo orden
	// en los cinco SRD: muchas criaturas, ajustes, VD 0, numero de perfiles, criaturas poderosas, rasgos inusuales
	const ultimo1 = bs.map((b) => b.t === "h" && b.n === 1).lastIndexOf(true);
	const tips = bs.slice(ultimo1 + 1).filter((b) => b.t === "h").map((b) => (b.txt ?? "").replace(/<[^>]+>/g, ""));
	return {
		etiquetas: [cab[1] ?? "", cab[2] ?? "", cab[3] ?? ""],
		porNivel,
		consejos: [tips[0] ?? "", tips[2] ?? "", tips[3] ?? "", tips[4] ?? ""],
	};
}

export type Aviso = "muchas" | "vd0" | "perfiles" | "poderosas";
export const AVISOS: readonly Aviso[] = ["muchas", "vd0", "perfiles", "poderosas"];

export interface Resultado {
	personajes: number;
	/** media de los niveles, redondeada hacia abajo */
	nivelGrupo: number;
	presupuesto: [number, number, number];
	total: number;
	criaturas: number;
	/** 0 baja, 1 moderada, 2 alta, 3 por encima de alta; -1 sin criaturas */
	dificultad: number;
	avisos: Aviso[];
}

export function calcular(grupo: Personajes[], lista: EnEncuentro[], tabla: TablaPresupuesto): Resultado {
	const presupuesto: [number, number, number] = [0, 0, 0];
	let personajes = 0;
	let niveles = 0;
	for (const p of grupo) {
		const fila = tabla.porNivel.get(p.nivel);
		if (!fila || p.n <= 0) continue;
		personajes += p.n;
		niveles += p.n * p.nivel;
		for (let i = 0; i < 3; i++) presupuesto[i] = (presupuesto[i] ?? 0) + p.n * (fila[i] ?? 0);
	}
	const nivelGrupo = personajes ? Math.floor(niveles / personajes) : 0;
	let total = 0;
	let criaturas = 0;
	const avisos = new Set<Aviso>();
	for (const x of lista) {
		const c = comunDe(x.clave)?.c as ComunCriatura | undefined;
		if (!c || x.n <= 0) continue;
		total += c.px * x.n;
		criaturas += x.n;
		if (c.vd === "0") avisos.add("vd0");
		if (personajes && valorVd(c.vd) > nivelGrupo) avisos.add("poderosas");
	}
	if (personajes && criaturas > 2 * personajes) avisos.add("muchas");
	if (lista.filter((x) => x.n > 0).length > 3) avisos.add("perfiles");
	let dificultad = -1;
	if (criaturas) dificultad = total <= presupuesto[0] ? 0 : total <= presupuesto[1] ? 1 : total <= presupuesto[2] ? 2 : 3;
	return { personajes, nivelGrupo, presupuesto, total, criaturas, dificultad, avisos: AVISOS.filter((a) => avisos.has(a)) };
}

export interface CriaturaIT {
	name: string;
	hp: number;
	ac: number;
	modifier: number;
	xp: number;
	cr: string;
	stats: number[];
	hit_dice: string;
}

/** Las criaturas como las espera Initiative Tracker (una por copia: no tiene campo de cantidad). */
export function criaturasIT(lista: EnEncuentro[], idioma: Idioma): CriaturaIT[] {
	const d = datosIdioma(idioma);
	const out: CriaturaIT[] = [];
	for (const x of lista) {
		const c = comunDe(x.clave)?.c as ComunCriatura | undefined;
		const e = d.entradas[x.clave];
		if (!c || !e) continue;
		for (let i = 0; i < x.n; i++) {
			out.push({
				name: e.nombre, hp: c.pg, ac: c.ca, modifier: c.iniciativa, xp: c.px, cr: c.vd,
				stats: c.car, hit_dice: c.dados_golpe,
			});
		}
	}
	return out;
}

/** El bloque ```encounter de Initiative Tracker, por si su API no esta (forma de objeto: creature, hp, ac, mod, xp). */
export function bloqueEncounter(nombre: string, lista: EnEncuentro[], idioma: Idioma, jugadores: string[] = []): string {
	const d = datosIdioma(idioma);
	const lineas = ["```encounter", `name: ${JSON.stringify(nombre)}`];
	if (jugadores.length) lineas.push(`players: ${JSON.stringify(jugadores)}`);
	lineas.push("creatures:");
	for (const x of lista) {
		const c = comunDe(x.clave)?.c as ComunCriatura | undefined;
		const e = d.entradas[x.clave];
		if (!c || !e || x.n <= 0) continue;
		lineas.push(`  - ${x.n}: {creature: ${JSON.stringify(e.nombre)}, hp: ${c.pg}, ac: ${c.ca}, mod: ${c.iniciativa}, xp: ${c.px}}`);
	}
	lineas.push("```");
	return lineas.join("\n");
}
