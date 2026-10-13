// Las notas de un idioma: rutas, propiedades y texto en Markdown. No usa la API de Obsidian (se prueba en Node).
import { comunDe, conUnidades, datosComunes, datosIdioma } from "./datos";
import { bloques, callout, enlace, enLinea, escapar, sinMarcas, type Contexto, type Enlaces } from "./markdown";
import { TEXTOS, type Propiedad, type Textos } from "./textos";
import {
	SECCION_DE, type Bloque, type CampoCriatura, type Clase, type ComunConjuro, type ComunCriatura,
	type ComunObjeto, type DatosIdioma, type Entrada, type EntradaComun, type Idioma, type ItemFicha, type Seccion,
} from "./tipos";

export interface Nota {
	/** ruta en la boveda, sin ".md" */
	ruta: string;
	contenido: string;
}

export interface OpcionesNotas {
	/** carpeta raiz del compendio, sin "/" al final */
	raiz: string;
	pies: boolean;
	fantasy: boolean;
	enlazarEstados: boolean;
}

/** Normaliza un nombre para buscarlo: minusculas, sin tildes, apostrofos rectos. */
export function normal(s: string): string {
	return s.toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "").replace(/[’‘]/g, "'").replace(/\s+/g, " ").trim();
}

function limpiarNombre(n: string): string {
	return n
		.replace(/[\\/]/g, "-")
		.replace(/[:*?"<>|#^[\]]/g, "")
		.replace(/\s+/g, " ")
		.replace(/[. ]+$/, "")
		.trim();
}

const CON_PRECIO: ReadonlySet<Clase> = new Set<Clase>(["equipo", "herramienta", "veneno"]);

/** "Ácido (25 po)" -> ["Ácido", "25 po"] */
function sinPrecio(nombre: string): [string, string | null] {
	const m = nombre.match(/^(.*?)\s*\(([^()]*)\)$/);
	return m ? [m[1] ?? nombre, m[2] ?? null] : [nombre, null];
}

export function archivoDe(k: Clase, e: Entrada): string {
	let n = e.nombre;
	if (k === "subclase" && e.nombre_corto) n = e.nombre_corto;
	if (CON_PRECIO.has(k)) n = sinPrecio(n)[0];
	if (k === "glosario") n = n.replace(/\[([^\]]*)\]/g, "($1)");
	return limpiarNombre(n) || limpiarNombre(e.nombre) || "SRD";
}

export function carpetaIdioma(raiz: string, idioma: Idioma): string {
	return `${raiz}/${TEXTOS[idioma].idioma}`;
}

/** Ruta (sin ".md") de cada entrada de un idioma. */
export function rutasDe(idioma: Idioma, raiz: string): Map<string, string> {
	const T = TEXTOS[idioma];
	const d = datosIdioma(idioma);
	const base = carpetaIdioma(raiz, idioma);
	const out = new Map<string, string>();
	const usadas = new Set<string>();
	for (const c of datosComunes().entradas) {
		const clave = `${c.k}/${c.id}`;
		const e = d.entradas[clave];
		if (!e) continue;
		let ruta = `${base}/${T.carpetas[c.k]}/${archivoDe(c.k, e)}`;
		for (let i = 2; usadas.has(ruta.toLowerCase()); i++) ruta = `${base}/${T.carpetas[c.k]}/${archivoDe(c.k, e)} (${i})`;
		usadas.add(ruta.toLowerCase());
		out.set(clave, ruta);
	}
	return out;
}

/** Ruta de la nota indice de una carpeta ("Criaturas/Criaturas"). */
export function rutaIndice(raiz: string, idioma: Idioma, carpeta: string): string {
	const ultima = carpeta.split("/").pop() ?? carpeta;
	return `${carpetaIdioma(raiz, idioma)}/${carpeta}/${ultima}`;
}

/** Carpetas con nota indice de cada seccion. */
function carpetasIndice(T: Textos, s: Seccion): string[] {
	switch (s) {
		case "criaturas": return [T.carpetas.criatura];
		case "conjuros": return [T.carpetas.conjuro];
		case "objetos": return [T.carpetas.objeto];
		case "estados": return [T.carpetas.estado];
		case "reglas": return [T.carpetas.regla, T.carpetas.glosario, T.carpetas.veneno, T.carpetas.trampa];
		case "personajes": return [T.grupos.personajes];
		case "equipo": return [T.grupos.equipo];
	}
}

/** Todas las rutas (sin ".md") que escribe una importacion de un idioma: entradas, indices, inicio y creditos. */
export function rutasPlan(idioma: Idioma, secciones: ReadonlySet<Seccion>, raiz: string): string[] {
	const T = TEXTOS[idioma];
	const out: string[] = [];
	for (const [k, ruta] of rutasDe(idioma, raiz)) {
		if (secciones.has(SECCION_DE[k.split("/")[0] as Clase])) out.push(ruta);
	}
	for (const s of secciones) for (const c of carpetasIndice(T, s)) out.push(rutaIndice(raiz, idioma, c));
	const base = carpetaIdioma(raiz, idioma);
	out.push(`${base}/${T.inicio}`, `${base}/${T.creditos}`);
	return out;
}

// ---------------------------------------------------------------- propiedades (YAML)

type Valor = string | number | boolean | null | undefined | Valor[] | { [k: string]: Valor };

function escalar(v: string | number | boolean): string {
	return typeof v === "string" ? JSON.stringify(v) : String(v);
}

function clave(k: string): string {
	return /^[\p{L}\p{N}_-]+$/u.test(k) ? k : JSON.stringify(k);
}

function vacio(v: Valor): boolean {
	return v === undefined || v === null || v === "" || (Array.isArray(v) && v.length === 0);
}

export function yaml(props: [string, Valor][]): string {
	const out = ["---"];
	const vistas = new Set<string>();
	for (const [k, v] of props) {
		if (vacio(v) || vistas.has(k)) continue;
		vistas.add(k);
		if (Array.isArray(v)) {
			out.push(`${clave(k)}:`);
			for (const x of v) {
				if (x !== null && typeof x === "object" && !Array.isArray(x)) {
					const pares = Object.entries(x).filter(([, y]) => !vacio(y));
					pares.forEach(([kk, y], i) => out.push(`${i === 0 ? "  - " : "    "}${clave(kk)}: ${escalar(y as string)}`));
				} else if (!vacio(x)) {
					out.push(`  - ${escalar(x as string)}`);
				}
			}
		} else if (typeof v === "string" || typeof v === "number" || typeof v === "boolean") {
			out.push(`${clave(k)}: ${escalar(v)}`);
		}
	}
	out.push("---");
	return out.join("\n");
}

// ---------------------------------------------------------------- estados en el texto

interface Estado {
	rx: RegExp;
	ruta: string;
}

/** Las formas de un estado en el texto de cada SRD: en español y en italiano con genero y numero
 * ("Envenenada", "avvelenati"), en frances con -e y -s, en aleman con las terminaciones del adjetivo. */
function formas(nombre: string, idioma: Idioma): string {
	const e = nombre.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
	if (idioma === "es") {
		if (/o$/.test(nombre)) return `${e.slice(0, -1)}(?:o|a|os|as)`;
		if (/e$/.test(nombre)) return `${e}s?`;
		return e;
	}
	if (idioma === "it") {
		const palabras = e.split(" ");
		const p0 = palabras[0] ?? e;
		const resto = palabras.slice(1).join(" ");
		const f = /o$/.test(p0) ? `${p0.slice(0, -1)}(?:o|a|i|e)` : /e$/.test(p0) ? `${p0.slice(0, -1)}(?:e|i)` : p0;
		return resto ? `${f} ${resto}` : f;
	}
	if (idioma === "fr") return nombre.includes(" ") || /ment$/.test(nombre) ? e : `${e}(?:e|s|es)?`;
	if (idioma === "de") return /ung$/.test(nombre) ? e : `${e}(?:e|en|er|es|em)?`;
	return e;
}

/** En aleman y en italiano el SRD escribe los estados con minuscula cuando los usa como adjetivo. */
function sinMayusculas(idioma: Idioma): boolean {
	return idioma === "de" || idioma === "it";
}

// ---------------------------------------------------------------- generador

const ORDEN_RAREZA = ["Common", "Uncommon", "Rare", "Very Rare", "Legendary", "Artifact"];
const CAMPOS_FICHA: CampoCriatura[] = ["hab", "vul", "res", "inm", "equipo", "sen", "idi", "vd"];
const FS_SECCION: Record<string, string> = {
	rasgos: "traits", acciones: "actions", adicionales: "bonus_actions", reacciones: "reactions",
	legendarias: "legendary_actions",
};

export function valorVd(vd: string): number {
	const m = vd.match(/^(\d+)\/(\d+)$/);
	return m ? Number(m[1]) / Number(m[2]) : Number(vd);
}

export class Generador {
	readonly T: Textos;
	readonly datos: DatosIdioma;
	readonly rutas: Map<string, string>;
	private readonly enlaces: Enlaces;
	private readonly porNombre: Record<"conjuro" | "objeto" | "criatura", Map<string, string>>;

	/**
	 * @param existe si una nota (ruta sin ".md") existira al acabar: se va a escribir o ya estaba
	 * @param otros rutas de las mismas entradas en los otros idiomas, para enlazarlas al pie
	 */
	constructor(
		readonly idioma: Idioma,
		readonly op: OpcionesNotas,
		private readonly existe: (ruta: string) => boolean,
		private readonly otros: { idioma: Idioma; rutas: Map<string, string> }[] = [],
	) {
		this.T = TEXTOS[idioma];
		this.datos = datosIdioma(idioma);
		this.rutas = rutasDe(idioma, op.raiz);
		this.porNombre = { conjuro: new Map(), objeto: new Map(), criatura: new Map() };
		const estados: Estado[] = [];
		const flags = sinMayusculas(idioma) ? "iu" : "u";
		for (const [k, ruta] of this.rutas) {
			const tipo = k.split("/")[0] as Clase;
			const e = this.datos.entradas[k];
			if (!e) continue;
			if (tipo === "conjuro" || tipo === "objeto" || tipo === "criatura") this.porNombre[tipo].set(normal(e.nombre), ruta);
			if (tipo === "estado") estados.push({ rx: new RegExp(`^(?:${formas(e.nombre, idioma)})$`, flags), ruta });
		}
		const alternativas = Object.keys(this.datos.entradas)
			.filter((k) => k.startsWith("estado/"))
			.map((k) => this.datos.entradas[k]?.nombre ?? "")
			.filter(Boolean)
			.sort((a, b) => b.length - a.length)
			.map((n) => formas(n, idioma));
		this.enlaces = {
			buscar: (tipo, texto) => this.buscar(tipo, texto),
			estados: op.enlazarEstados && alternativas.length
				? {
					rx: new RegExp(`(^|[^\\p{L}\\p{N}])(${alternativas.join("|")})(?![\\p{L}\\p{N}])`, `g${flags}`),
					ruta: (palabra) => {
						const est = estados.find((x) => x.rx.test(palabra));
						return est && this.existe(est.ruta) ? est.ruta : null;
					},
				}
				: null,
		};
	}

	private buscar(tipo: "conjuro" | "objeto" | "criatura", texto: string): string | null {
		const mapa = this.porNombre[tipo];
		const n = normal(texto);
		let ruta = mapa.get(n);
		if (!ruta && tipo === "criatura") {
			// plurales: "púdines negros" -> "pudin negro", "goblins" -> "goblin"
			const palabras = n.split(" ");
			if (palabras.length <= 3) {
				const fin = this.idioma === "de" ? ["", "n", "en", "e", "s"] : ["", "s", "es"];
				let candidatos = [""];
				for (const p of palabras) {
					const vs = fin.filter((f) => !f || p.endsWith(f)).map((f) => (f ? p.slice(0, -f.length) : p));
					candidatos = candidatos.flatMap((c) => vs.map((v) => (c ? `${c} ${v}` : v)));
				}
				for (const c of candidatos) {
					ruta = mapa.get(c);
					if (ruta) break;
				}
			}
		}
		return ruta && this.existe(ruta) ? ruta : null;
	}

	contexto(actual: string): Contexto {
		return { enlaces: this.enlaces, actual, vistos: new Set(), dosPuntos: this.T.dosPuntos };
	}

	private entrada(clave: string): Entrada | null {
		const e = this.datos.entradas[clave];
		return e ? conUnidades(e, this.op.pies) : null;
	}

	/** El nombre de una nota enlazado si existe; si no, en texto. */
	private enlaceA(clave: string, texto?: string): string {
		const ruta = this.rutas.get(clave);
		const nombre = texto ?? this.datos.entradas[clave]?.nombre ?? clave;
		return ruta && this.existe(ruta) ? enlace(ruta, nombre) : escapar(nombre);
	}

	private pie(clave: string): string | null {
		const enlaces: string[] = [];
		for (const o of this.otros) {
			const ruta = o.rutas.get(clave);
			if (ruta && this.existe(ruta)) enlaces.push(enlace(ruta, TEXTOS[o.idioma].idioma));
		}
		return enlaces.length ? `**${this.T.otrosIdiomas}${this.T.dosPuntos}** ${enlaces.join(" · ")}` : null;
	}

	private p(k: Propiedad): string {
		return this.T.props[k];
	}

	/** Todas las notas de las secciones elegidas, con sus indices, la de inicio y la de creditos. */
	notas(secciones: ReadonlySet<Seccion>): Nota[] {
		const out: Nota[] = [];
		for (const c of datosComunes().entradas) {
			if (!secciones.has(SECCION_DE[c.k])) continue;
			const n = this.nota(`${c.k}/${c.id}`);
			if (n) out.push(n);
		}
		out.push(...this.indices(secciones), this.inicio(secciones), this.creditos());
		return out;
	}

	nota(claveEntrada: string): Nota | null {
		const c = comunDe(claveEntrada);
		const ruta = this.rutas.get(claveEntrada);
		const e = this.entrada(claveEntrada);
		if (!c || !ruta || !e) return null;
		const ctx = this.contexto(ruta);
		const T = this.T;
		const props: [string, Valor][] = [["srd", claveEntrada]];
		const archivo = ruta.split("/").pop() ?? "";
		if (normal(archivo) !== normal(e.nombre)) props.push(["aliases", [e.nombre]]);
		props.push(["tags", [`srd/${T.clases[c.k].toLowerCase().replace(/\s+/g, "-")}`]]);
		const cuerpo: string[] = [];
		const op = { titulo: 2, ficha: (b: Bloque) => this.fichaConjuro(b, ctx) };
		switch (c.k) {
			case "criatura": {
				const cc = c.c as ComunCriatura;
				props.push(
					[this.p("tipo"), e.tipo], [this.p("grupo"), e.grupo], [this.p("vd"), cc.vd], [this.p("px"), cc.px],
					[this.p("ca"), cc.ca], [this.p("pg"), cc.pg], [this.p("iniciativa"), cc.iniciativa],
				);
				if (this.op.fantasy) props.push(...this.fantasy(e, cc, ctx));
				cuerpo.push(this.fichaCriatura(e, ctx));
				for (const s of e.secciones ?? []) {
					cuerpo.push(`## ${enLinea(s.titulo, ctx)}`);
					if (s.intro) cuerpo.push(enLinea(s.intro, ctx));
					for (const it of s.items) cuerpo.push(...this.rasgo(it, ctx));
				}
				break;
			}
			case "conjuro": {
				const cc = c.c as ComunConjuro;
				props.push(
					[this.p("nivel"), cc.nivel],
					[this.p("escuela"), this.datos.nombres.escuelas[cc.escuela]],
					[this.p("clases"), cc.clases.map((cl) => this.propEnlace(`clase/${cl.toLowerCase()}`))],
					[this.p("ritual"), cc.ritual],
					[this.p("concentracion"), cc.concentracion],
				);
				const dp = T.dosPuntos;
				cuerpo.push(callout("srd-conjuro", escapar(e.nombre), [
					`*${enLinea(e.cabecera ?? "", ctx)}*`,
					`**${T.conjuro.tiempo}${dp}** ${enLinea(e.tiempo ?? "", ctx)}`,
					`**${T.conjuro.alcance}${dp}** ${enLinea(e.alcance ?? "", ctx)}`,
					`**${T.conjuro.comp}${dp}** ${enLinea(e.comp ?? "", ctx)}`,
					`**${T.conjuro.dur}${dp}** ${enLinea(e.dur ?? "", ctx)}`,
				]));
				cuerpo.push(...bloques(e.bloques ?? [], ctx, op));
				break;
			}
			case "objeto": {
				const cc = c.c as ComunObjeto;
				const rarezas = cc.rarezas.map((r) => this.datos.nombres.rarezas[r] ?? T.rarezaVariable);
				props.push(
					[this.p("categoria"), this.datos.nombres.categorias[cc.categoria]],
					[this.p("rareza"), [...new Set(rarezas)]],
					[this.p("sintonizacion"), cc.sintonizacion],
				);
				cuerpo.push(callout("srd-objeto", escapar(e.nombre), [`*${enLinea(e.cabecera ?? "", ctx)}*`]));
				cuerpo.push(...bloques(e.bloques ?? [], ctx, op));
				break;
			}
			default: {
				if (c.cap && this.datos.nombres.capitulos[c.cap] && (c.k === "regla" || c.k === "glosario")) {
					props.push([this.p("capitulo"), this.datos.nombres.capitulos[c.cap]]);
				}
				if (e.categoria) props.push([this.p("categoria"), e.categoria]);
				if (CON_PRECIO.has(c.k)) {
					const precio = sinPrecio(e.nombre)[1];
					if (precio) {
						props.push([this.p("precio"), precio]);
						cuerpo.push(`**${T.precio}${T.dosPuntos}** ${escapar(precio)}`);
					}
				}
				if (c.k === "subclase" && e.clase) {
					const cl = this.claveDeClase(e.clase);
					props.push([this.p("clase"), cl ? this.propEnlace(cl) : e.clase]);
				}
				cuerpo.push(...bloques(e.bloques ?? [], ctx, op));
				if (c.k === "clase") {
					const subs = this.subclasesDe(e.nombre);
					if (subs.length) {
						cuerpo.push(`## ${T.subclases}`);
						cuerpo.push(subs.map((s) => `- ${this.enlaceA(s, this.datos.entradas[s]?.nombre_corto ?? undefined)}`).join("\n"));
					}
				}
			}
		}
		const pie = this.pie(claveEntrada);
		if (pie) cuerpo.push("---", pie);
		return { ruta, contenido: `${yaml(props)}\n\n${cuerpo.filter((x) => x.trim()).join("\n\n")}\n` };
	}

	/** Valor de una propiedad que apunta a otra nota: enlace si existe, nombre si no. */
	private propEnlace(clave: string): string {
		const ruta = this.rutas.get(clave);
		const nombre = this.datos.entradas[clave]?.nombre ?? clave.split("/")[1] ?? clave;
		return ruta && this.existe(ruta) ? `[[${ruta}|${nombre}]]` : nombre;
	}

	private claveDeClase(nombre: string): string | null {
		for (const k of this.rutas.keys()) {
			if (k.startsWith("clase/") && normal(this.datos.entradas[k]?.nombre ?? "") === normal(nombre)) return k;
		}
		return null;
	}

	private subclasesDe(clase: string): string[] {
		return [...this.rutas.keys()].filter(
			(k) => k.startsWith("subclase/") && normal(this.datos.entradas[k]?.clase ?? "") === normal(clase),
		);
	}

	// ------------------------------------------------------------ fichas

	private tablaCaracteristicas(car: [string, number, string, string][]): string {
		const T = this.T;
		const cab = ["", "", T.ficha.mod, T.ficha.salv];
		const filas: string[] = [];
		filas.push(`| ${[...cab, ...cab, ...cab].map((c) => c || " ").join(" | ")} |`);
		filas.push(`| ${Array.from({ length: 12 }, () => "---").join(" | ")} |`);
		for (let i = 0; i < car.length; i += 3) {
			const celdas: string[] = [];
			for (const [abr, punt, mod, salv] of car.slice(i, i + 3)) {
				celdas.push(`**${escapar(abr, true)}**`, String(punt), escapar(mod, true), escapar(salv, true));
			}
			filas.push(`| ${celdas.join(" | ")} |`);
		}
		return filas.join("\n");
	}

	private fichaCriatura(e: Entrada, ctx: Contexto): string {
		const T = this.T;
		const c = e.campos ?? {};
		const linea = (k: CampoCriatura) => (c[k] ? `**${T.ficha[k]}** ${enLinea(c[k] ?? "", ctx)}` : "");
		const trozos = [
			e.tipo ? `*${enLinea(e.tipo, ctx)}*` : "",
			[linea("ca"), linea("ini")].filter(Boolean).join(" · "),
			linea("pg"),
			linea("vel"),
			e.car?.length ? this.tablaCaracteristicas(e.car) : "",
			...CAMPOS_FICHA.map(linea),
		];
		return callout("srd-ficha", escapar(e.nombre), trozos.filter(Boolean));
	}

	private rasgo(it: ItemFicha, ctx: Contexto): string[] {
		const nombre = `***${escapar(it.nombre)}${this.T.finRasgo}***`;
		const [primero, ...resto] = it.bloques;
		if (primero && primero.t === "p" && primero.txt) {
			return [`${nombre} ${enLinea(primero.txt, ctx)}`, ...bloques(resto, ctx, { titulo: 3 })];
		}
		return [nombre, ...bloques(it.bloques, ctx, { titulo: 3 })];
	}

	/** Las fichas que vienen dentro de un conjuro (Animar objetos, Invocar...). */
	private fichaConjuro(b: Bloque, ctx: Contexto): string {
		const T = this.T;
		const trozos: string[] = [];
		if (b.tipo) trozos.push(`*${enLinea(b.tipo, ctx)}*`);
		const ca = b.ca ? `**${T.ficha.ca}** ${enLinea(b.ca, ctx)}` : "";
		if (ca) trozos.push(ca);
		if (b.pg) trozos.push(`**${T.ficha.pg}** ${enLinea(b.pg, ctx)}`);
		if (b.vel) trozos.push(`**${T.ficha.vel}** ${enLinea(b.vel, ctx)}`);
		if (b.car?.length) trozos.push(this.tablaCaracteristicas(b.car));
		for (const [rotulo, valor] of b.rasgos ?? []) trozos.push(`**${escapar(rotulo)}** ${enLinea(valor, ctx)}`);
		for (const s of b.secciones ?? []) {
			trozos.push(`**${enLinea(s.titulo, ctx)}**`);
			for (const [n, txt] of s.items) trozos.push(`***${escapar(n)}${T.finRasgo}*** ${enLinea(txt, ctx)}`);
		}
		return callout("srd-ficha", escapar(b.nombre ?? ""), trozos);
	}

	/** Las propiedades que lee Fantasy Statblocks ("statblock: true"; nombres de campo del diseño Basic 5e). */
	private fantasy(e: Entrada, cc: ComunCriatura, ctx: Contexto): [string, Valor][] {
		const c = e.campos ?? {};
		const texto = (k: CampoCriatura) => (c[k] ? sinMarcas(c[k] ?? "") : undefined);
		const md = (bs: Bloque[]) => bloques(bs, { ...ctx, vistos: new Set() }, { titulo: 3 }).join("\n\n");
		const out: [string, Valor][] = [
			["statblock", true],
			["name", e.nombre],
			["type", e.tipo],
			["ac", cc.ca],
			["hp", cc.pg],
			["hit_dice", cc.dados_golpe],
			["modifier", cc.iniciativa],
			["speed", texto("vel")],
			["stats", cc.car],
		];
		const salvaciones = (e.car ?? [])
			.map((x, i) => [x[0], cc.salv[i] ?? 0, cc.mod[i] ?? 0] as const)
			.filter(([, s, m]) => s !== m)
			.map(([abr, s]) => ({ [abr]: s }));
		out.push(["saves", salvaciones]);
		const hab = texto("hab");
		if (hab) {
			out.push(["skillsaves", hab.split(/,\s*/).map((h) => {
				const m = h.match(/^(.*?)\s*([+−-]\d+)$/);
				return m ? { [m[1] ?? h]: Number((m[2] ?? "0").replace("−", "-")) } : { [h]: 0 };
			})]);
		}
		out.push(["damage_vulnerabilities", texto("vul")], ["damage_resistances", texto("res")]);
		const inm = texto("inm");
		if (inm) {
			const [dano, estados] = inm.includes(";") ? inm.split(/;\s*/, 2) : [inm, undefined];
			out.push(["damage_immunities", dano], ["condition_immunities", estados]);
		}
		out.push(["senses", texto("sen")], ["languages", texto("idi")]);
		out.push(["cr", /^\d+$/.test(cc.vd) ? Number(cc.vd) : cc.vd]);
		for (const s of e.secciones ?? []) {
			const k = FS_SECCION[s.clave];
			if (!k) continue;
			if (s.clave === "legendarias" && s.intro) out.push(["legendary_description", sinMarcas(s.intro)]);
			out.push([k, s.items.map((it) => ({ name: it.nombre, desc: md(it.bloques) }))]);
		}
		return out;
	}

	// ------------------------------------------------------------ indices

	private entradasDe(k: Clase): { clave: string; c: EntradaComun; e: Entrada; ruta: string }[] {
		const out = [];
		for (const c of datosComunes().entradas) {
			if (c.k !== k) continue;
			const clave = `${c.k}/${c.id}`;
			const e = this.datos.entradas[clave];
			const ruta = this.rutas.get(clave);
			if (e && ruta && this.existe(ruta)) out.push({ clave, c, e: conUnidades(e, this.op.pies), ruta });
		}
		return out;
	}

	private alfabetico<T extends { e: Entrada }>(xs: T[]): T[] {
		return [...xs].sort((a, b) => a.e.nombre.localeCompare(b.e.nombre, this.idioma, { sensitivity: "base" }));
	}

	private lista(xs: { e: Entrada; ruta: string }[], texto?: (e: Entrada) => string): string {
		return xs.map((x) => `- ${enlace(x.ruta, texto ? texto(x.e) : x.e.nombre)}`).join("\n");
	}

	private tabla(cab: string[], filas: string[][]): string {
		const f = (r: string[]) => `| ${r.map((x) => x || " ").join(" | ")} |`;
		return [f(cab), f(cab.map(() => "---")), ...filas.map(f)].join("\n");
	}

	private indice(carpeta: string, trozos: string[]): Nota {
		const ruta = rutaIndice(this.op.raiz, this.idioma, carpeta);
		const props = yaml([["tags", [this.T.etiquetaIndice]]]);
		return { ruta, contenido: `${props}\n\n${trozos.filter(Boolean).join("\n\n")}\n` };
	}

	indices(secciones: ReadonlySet<Seccion>): Nota[] {
		const T = this.T;
		const out: Nota[] = [];
		const nombre = (ruta: string, texto: string) => enlace(ruta, texto, true);
		if (secciones.has("criaturas")) {
			const xs = this.alfabetico(this.entradasDe("criatura"));
			const porVd = new Map<string, typeof xs>();
			for (const x of xs) {
				const vd = (x.c.c as ComunCriatura).vd;
				porVd.set(vd, [...(porVd.get(vd) ?? []), x]);
			}
			const trozos: string[] = [];
			for (const vd of [...porVd.keys()].sort((a, b) => valorVd(a) - valorVd(b))) {
				trozos.push(`## ${T.ficha.vd} ${vd}`);
				trozos.push(this.tabla(T.cabeceras.criaturas, (porVd.get(vd) ?? []).map((x) => [
					nombre(x.ruta, x.e.nombre), escapar(x.e.tipo ?? "", true), String((x.c.c as ComunCriatura).px),
				])));
			}
			out.push(this.indice(T.carpetas.criatura, trozos));
		}
		if (secciones.has("conjuros")) {
			const xs = this.alfabetico(this.entradasDe("conjuro"));
			const trozos: string[] = [];
			for (let n = 0; n <= 9; n++) {
				const nivel = xs.filter((x) => (x.c.c as ComunConjuro).nivel === n);
				if (!nivel.length) continue;
				trozos.push(`## ${n === 0 ? T.trucos : T.nivelConjuro(n)}`);
				trozos.push(this.tabla(T.cabeceras.conjuros, nivel.map((x) => {
					const cc = x.c.c as ComunConjuro;
					return [
						nombre(x.ruta, x.e.nombre),
						escapar(this.datos.nombres.escuelas[cc.escuela] ?? "", true),
						escapar(cc.clases.map((cl) => this.datos.entradas[`clase/${cl.toLowerCase()}`]?.nombre ?? cl).join(", "), true),
						cc.concentracion ? T.si : "",
						cc.ritual ? T.si : "",
					];
				})));
			}
			out.push(this.indice(T.carpetas.conjuro, trozos));
		}
		if (secciones.has("objetos")) {
			const xs = this.alfabetico(this.entradasDe("objeto"));
			const grupos = new Map<string, typeof xs>();
			for (const x of xs) {
				const r = (x.c.c as ComunObjeto).rarezas;
				const g = r.length === 1 && ORDEN_RAREZA.includes(r[0] ?? "") ? (r[0] ?? "") : "";
				grupos.set(g, [...(grupos.get(g) ?? []), x]);
			}
			const trozos: string[] = [];
			for (const g of [...ORDEN_RAREZA, ""]) {
				const ys = grupos.get(g);
				if (!ys?.length) continue;
				trozos.push(`## ${g ? this.datos.nombres.rarezas[g] ?? g : T.rarezaVariable}`);
				trozos.push(this.tabla(T.cabeceras.objetos, ys.map((x) => {
					const cc = x.c.c as ComunObjeto;
					return [nombre(x.ruta, x.e.nombre), escapar(this.datos.nombres.categorias[cc.categoria] ?? "", true), cc.sintonizacion ? T.si : ""];
				})));
			}
			out.push(this.indice(T.carpetas.objeto, trozos));
		}
		if (secciones.has("estados")) {
			out.push(this.indice(T.carpetas.estado, [this.lista(this.alfabetico(this.entradasDe("estado")))]));
		}
		if (secciones.has("reglas")) {
			const reglas = this.entradasDe("regla");
			const trozos: string[] = [];
			const caps: string[] = [];
			for (const x of reglas) if (x.c.cap && !caps.includes(x.c.cap)) caps.push(x.c.cap);
			for (const cap of caps) {
				trozos.push(`## ${escapar(this.datos.nombres.capitulos[cap] ?? cap)}`);
				trozos.push(this.lista(reglas.filter((x) => x.c.cap === cap)));
			}
			out.push(this.indice(T.carpetas.regla, trozos));
			const glosario = this.alfabetico(this.entradasDe("glosario"));
			const porLetra = new Map<string, typeof glosario>();
			for (const x of glosario) {
				const l = normal(x.e.nombre).charAt(0).toUpperCase();
				porLetra.set(l, [...(porLetra.get(l) ?? []), x]);
			}
			out.push(this.indice(T.carpetas.glosario, [...porLetra].flatMap(([l, ys]) => [`## ${l}`, this.lista(ys)])));
			out.push(this.indice(T.carpetas.veneno, [this.lista(this.alfabetico(this.entradasDe("veneno")))]));
			out.push(this.indice(T.carpetas.trampa, [this.lista(this.alfabetico(this.entradasDe("trampa")))]));
		}
		if (secciones.has("personajes")) {
			const trozos: string[] = [];
			const clases = this.alfabetico(this.entradasDe("clase"));
			if (clases.length) {
				trozos.push(`## ${escapar(this.datos.nombres.capitulos.clases ?? T.clases.clase)}`);
				trozos.push(clases.map((x) => {
					const subs = this.subclasesDe(x.e.nombre).map((s) => `  - ${this.enlaceA(s, this.datos.entradas[s]?.nombre_corto ?? undefined)}`);
					return [`- ${enlace(x.ruta, x.e.nombre)}`, ...subs].join("\n");
				}).join("\n"));
			}
			for (const k of ["especie", "trasfondo"] as const) {
				const xs = this.alfabetico(this.entradasDe(k));
				if (!xs.length) continue;
				trozos.push(`## ${T.carpetas[k].split("/").pop() ?? ""}`, this.lista(xs));
			}
			const dotes = this.entradasDe("dote");
			if (dotes.length) {
				trozos.push(`## ${escapar(this.datos.nombres.capitulos.dotes ?? T.clases.dote)}`);
				const cats: string[] = [];
				for (const x of dotes) if (x.e.categoria && !cats.includes(x.e.categoria)) cats.push(x.e.categoria);
				for (const cat of cats) {
					trozos.push(`### ${escapar(cat)}`, this.lista(this.alfabetico(dotes.filter((x) => x.e.categoria === cat))));
				}
			}
			out.push(this.indice(T.grupos.personajes, trozos));
		}
		if (secciones.has("equipo")) {
			const trozos: string[] = [];
			for (const [k, regla] of [["arma", "regla/weapons"], ["armadura", "regla/armor"]] as const) {
				const xs = this.entradasDe(k);
				if (!xs.length) continue;
				trozos.push(`## ${T.carpetas[k].split("/").pop() ?? ""}`);
				if (this.rutas.get(regla) && this.existe(this.rutas.get(regla) ?? "")) trozos.push(this.enlaceA(regla));
				const cats: string[] = [];
				for (const x of xs) if (x.e.categoria && !cats.includes(x.e.categoria)) cats.push(x.e.categoria);
				for (const cat of cats) {
					const ys = xs.filter((x) => x.e.categoria === cat);
					const campos = ys[0]?.e.bloques?.find((b) => b.t === "campos")?.filas ?? [];
					trozos.push(`### ${escapar(cat)}`);
					trozos.push(this.tabla(
						[T.clases[k], ...campos.map((f) => escapar(f[0] ?? "", true))],
						ys.map((x) => {
							const fs = x.e.bloques?.find((b) => b.t === "campos")?.filas ?? [];
							const ctx = { ...this.contexto(x.ruta), enTabla: true };
							return [nombre(x.ruta, x.e.nombre), ...campos.map((_, i) => enLinea(fs[i]?.[1] ?? "", ctx))];
						}),
					));
				}
			}
			for (const [k, regla] of [["herramienta", "regla/tools"], ["equipo", "regla/adventuring-gear"]] as const) {
				const xs = this.entradasDe(k);
				if (!xs.length) continue;
				trozos.push(`## ${T.carpetas[k].split("/").pop() ?? ""}`);
				if (this.rutas.get(regla) && this.existe(this.rutas.get(regla) ?? "")) trozos.push(this.enlaceA(regla));
				const cats: string[] = [];
				for (const x of xs) if (x.e.categoria && !cats.includes(x.e.categoria)) cats.push(x.e.categoria);
				if (cats.length) {
					for (const cat of cats) {
						trozos.push(`### ${escapar(cat)}`, this.lista(this.alfabetico(xs.filter((x) => x.e.categoria === cat)), (e) => e.nombre));
					}
				} else {
					trozos.push(this.lista(this.alfabetico(xs), (e) => e.nombre));
				}
			}
			out.push(this.indice(T.grupos.equipo, trozos));
		}
		return out;
	}

	inicio(secciones: ReadonlySet<Seccion>): Nota {
		const T = this.T;
		const raiz = carpetaIdioma(this.op.raiz, this.idioma);
		const lineas: string[] = [];
		const item = (carpeta: string, cuantas: number) => {
			if (cuantas) lineas.push(`- ${enlace(rutaIndice(this.op.raiz, this.idioma, carpeta), carpeta.split("/").pop() ?? carpeta)} (${cuantas})`);
		};
		const cuenta = (...ks: Clase[]) => ks.reduce((n, k) => n + this.entradasDe(k).length, 0);
		if (secciones.has("criaturas")) item(T.carpetas.criatura, cuenta("criatura"));
		if (secciones.has("conjuros")) item(T.carpetas.conjuro, cuenta("conjuro"));
		if (secciones.has("objetos")) item(T.carpetas.objeto, cuenta("objeto"));
		if (secciones.has("estados")) item(T.carpetas.estado, cuenta("estado"));
		if (secciones.has("reglas")) {
			item(T.carpetas.regla, cuenta("regla"));
			item(T.carpetas.glosario, cuenta("glosario"));
			item(T.carpetas.veneno, cuenta("veneno"));
			item(T.carpetas.trampa, cuenta("trampa"));
		}
		if (secciones.has("personajes")) item(T.grupos.personajes, cuenta("clase", "subclase", "especie", "trasfondo", "dote"));
		if (secciones.has("equipo")) item(T.grupos.equipo, cuenta("arma", "armadura", "herramienta", "equipo"));
		const otros = this.otros
			.filter((o) => this.existe(`${carpetaIdioma(this.op.raiz, o.idioma)}/${TEXTOS[o.idioma].inicio}`))
			.map((o) => enlace(`${carpetaIdioma(this.op.raiz, o.idioma)}/${TEXTOS[o.idioma].inicio}`, TEXTOS[o.idioma].idioma));
		const trozos = [
			yaml([["tags", [T.etiquetaIndice]]]),
			T.inicioIntro,
			lineas.join("\n"),
			T.inicioEncuentro,
			`${enlace(`${raiz}/${T.creditos}`, T.creditos)}: ${T.inicioCreditos}.`,
			otros.length ? `**${T.otrosIdiomas}${T.dosPuntos}** ${otros.join(" · ")}` : "",
		];
		return { ruta: `${raiz}/${T.inicio}`, contenido: `${trozos.filter(Boolean).join("\n\n")}\n` };
	}

	creditos(): Nota {
		const T = this.T;
		const raiz = carpetaIdioma(this.op.raiz, this.idioma);
		const cambios = [T.cambioNotas];
		if (this.op.pies && T.cambioPies) cambios.push(T.cambioPies);
		cambios.push(...T.cambiosCasa);
		const trozos = [
			`## ${T.licencia}`,
			escapar(this.datos.atribucion),
			`## ${T.cambios}`,
			T.cambiosIntro,
			cambios.map((c) => `- ${c}`).join("\n"),
		];
		const erratas = this.datos.correcciones.filter((c) => c.antes && this.rutas.has(c.clave));
		if (erratas.length) {
			trozos.push(`## ${T.erratas}`, T.erratasIntro);
			trozos.push(this.tabla(T.cabeceraErratas, erratas.map((c) => [
				this.enlaceTabla(c.clave),
				escapar(sinMarcas(c.antes), true),
				escapar(sinMarcas(c.despues), true),
			])));
			if (this.op.pies && T.erratasMetros) trozos.push(T.erratasMetros);
		}
		trozos.push(`*${T.hechoCon}*`);
		return { ruta: `${raiz}/${T.creditos}`, contenido: `${trozos.join("\n\n")}\n` };
	}

	private enlaceTabla(clave: string): string {
		const ruta = this.rutas.get(clave);
		const nombre = this.datos.entradas[clave]?.nombre ?? clave;
		return ruta && this.existe(ruta) ? enlace(ruta, nombre, true) : escapar(nombre, true);
	}
}
