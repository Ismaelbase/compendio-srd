// Del texto de los datos (con <i>, <b> y <strong>) a Markdown de Obsidian, con enlaces a las otras notas.
import type { Bloque } from "./tipos";

export type Citable = "conjuro" | "objeto" | "criatura";

export interface Enlaces {
	/** Ruta (sin ".md") de la nota de algo citado por su nombre, o null si no hay nota. */
	buscar(tipo: Citable, texto: string): string | null;
	/** Los estados en el texto corrido: la expresion los encuentra y ruta() da su nota. */
	estados: { rx: RegExp; ruta: (palabra: string) => string | null } | null;
}

export interface Contexto {
	enlaces: Enlaces;
	/** nota que se esta escribiendo: no se enlaza a si misma */
	actual: string;
	/** estados ya enlazados en esta nota (solo se enlaza la primera vez) */
	vistos: Set<string>;
	/** "Alcance:" o, en frances, "Portée :" */
	dosPuntos: string;
	enTabla?: boolean;
}

type Marca = "i" | "b" | "strong";
interface Nodo {
	tag: Marca;
	hijos: Hijo[];
}
type Hijo = Nodo | string;

function arbol(txt: string): Hijo[] {
	const raiz: Hijo[] = [];
	const pila: Nodo[] = [];
	let actual = raiz;
	const rx = /<(\/?)(i|b|strong)>/g;
	let pos = 0;
	let m: RegExpExecArray | null;
	while ((m = rx.exec(txt)) !== null) {
		if (m.index > pos) actual.push(txt.slice(pos, m.index));
		pos = rx.lastIndex;
		const tag = m[2] as Marca;
		if (m[1] !== "/") {
			const n: Nodo = { tag, hijos: [] };
			actual.push(n);
			pila.push(n);
			actual = n.hijos;
		} else {
			const i = pila.map((x) => x.tag).lastIndexOf(tag);
			if (i < 0) continue; // cierre sin apertura: fuera
			pila.length = i;
			const arriba = pila[pila.length - 1];
			actual = arriba ? arriba.hijos : raiz;
		}
	}
	if (pos < txt.length) actual.push(txt.slice(pos));
	return raiz;
}

function plano(hijos: Hijo[]): string {
	return hijos.map((h) => (typeof h === "string" ? h : plano(h.hijos))).join("");
}

/** Texto sin las marcas de los datos. */
export function sinMarcas(txt: string): string {
	return txt.replace(/<\/?(i|b|strong)>/g, "");
}

/** Escapa lo que Obsidian leeria como formato: negrita, enlaces, etiquetas, formulas, resaltado... */
export function escapar(t: string, enTabla = false): string {
	let s = t
		.replace(/[\\*_[\]`$<#]/g, "\\$&")
		.replace(/==/g, "=\\=")
		.replace(/~~/g, "~\\~")
		.replace(/%%/g, "%\\%");
	if (enTabla) s = s.replace(/\|/g, "\\|");
	return s;
}

export function enlace(ruta: string, texto: string, enTabla = false): string {
	const visible = texto.replace(/[[\]|]/g, " ").replace(/\s+/g, " ").trim();
	return `[[${ruta}${enTabla ? "\\|" : "|"}${visible}]]`;
}

function conEstados(t: string, ctx: Contexto): string {
	const est = ctx.enlaces.estados;
	if (!est) return escapar(t, ctx.enTabla);
	let out = "";
	let pos = 0;
	est.rx.lastIndex = 0;
	for (const m of t.matchAll(est.rx)) {
		const antes = m[1] ?? "";
		const palabra = m[2] ?? "";
		const inicio = (m.index ?? 0) + antes.length;
		const ruta = est.ruta(palabra);
		if (!ruta || ruta === ctx.actual || ctx.vistos.has(ruta)) continue;
		ctx.vistos.add(ruta);
		out += escapar(t.slice(pos, inicio), ctx.enTabla) + enlace(ruta, palabra, ctx.enTabla);
		pos = inicio + palabra.length;
	}
	return out + escapar(t.slice(pos), ctx.enTabla);
}

interface Trozo {
	md: string;
	/** marca de enfasis ("*" o "**") si el trozo es un enfasis; su interior va en md */
	marca?: string;
	html?: string;
}

const LETRA = /[\p{L}\p{N}]/u;
const PUNTUACION = /[\p{P}\p{S}]/u;

function trozos(hijos: Hijo[], ctx: Contexto): Trozo[] {
	const out: Trozo[] = [];
	for (const h of hijos) {
		if (typeof h === "string") {
			out.push({ md: conEstados(h, ctx) });
			continue;
		}
		const p = plano(h.hijos);
		const limpio = p.trim();
		let ruta: string | null = null;
		if (limpio) {
			if (h.tag === "i") ruta = ctx.enlaces.buscar("conjuro", limpio) ?? ctx.enlaces.buscar("objeto", limpio);
			else if (h.tag === "strong") ruta = ctx.enlaces.buscar("criatura", limpio);
			else if (limpio.length <= 40 && !/[.:]$/.test(limpio)) ruta = ctx.enlaces.buscar("criatura", limpio);
		}
		if (ruta === ctx.actual) ruta = null;
		const interior = ruta ? enlace(ruta, limpio, ctx.enTabla) : unir(trozos(h.hijos, ctx));
		const marca = h.tag === "i" ? "*" : "**";
		const html = h.tag === "i" ? "i" : "b";
		// los espacios de los bordes van fuera de la marca ("<i>Acierto: </i>" -> "*Acierto:* ")
		const ini = interior.match(/^\s*/)?.[0] ?? "";
		const fin = interior.slice(ini.length).match(/\s*$/)?.[0] ?? "";
		const centro = interior.slice(ini.length, interior.length - fin.length);
		if (ini) out.push({ md: ini });
		if (centro) out.push({ md: centro, marca, html });
		if (fin) out.push({ md: fin });
	}
	return out;
}

/** Une los trozos: un enfasis que Markdown no cerraria bien (pegado a una letra por un signo, o pegado a otro
 * enfasis) va con etiquetas HTML, que Obsidian tambien pinta. */
function unir(ts: Trozo[]): string {
	let out = "";
	for (let i = 0; i < ts.length; i++) {
		const t = ts[i];
		if (!t) continue;
		if (!t.marca) {
			out += t.md;
			continue;
		}
		const antes = out.slice(-1);
		const sig = ts[i + 1];
		const despues = sig ? (sig.marca ? sig.marca[0] ?? "" : sig.md.slice(0, 1)) : "";
		const primero = t.md.slice(0, 1);
		const ultimo = t.md.slice(-1);
		const abreMal = PUNTUACION.test(primero) && !t.md.startsWith("[[") && LETRA.test(antes);
		const cierraMal = PUNTUACION.test(ultimo) && !t.md.endsWith("]]") && LETRA.test(despues);
		const pegado = antes === "*" || despues === "*";
		if (abreMal || cierraMal || pegado) out += `<${t.html}>${t.md}</${t.html}>`;
		else out += t.marca + t.md + t.marca;
	}
	return out;
}

/** Una linea de texto de los datos en Markdown. */
export function enLinea(txt: string, ctx: Contexto): string {
	// "<strong>.</strong>", "<i>.”</i>": un signo suelto con enfasis es letra de la maqueta, no una cita; y tras un
	// rotulo en negrita va un espacio aunque el PDF lo pierda ("<b>Oscuridad.</b>La oscuridad")
	const t = txt
		.replace(/<(strong|b|i)>([^\p{L}\p{N}<]{1,3})<\/\1>/gu, "$2")
		.replace(/([.:])<\/(b|strong)>(?=[\p{L}\p{N}]|<[ib]>)/gu, "$1</$2> ");
	return unir(trozos(arbol(t), ctx));
}

/** Lo que al principio de una linea Markdown leeria como lista, cita o titulo. */
export function inicioSeguro(linea: string): string {
	return linea
		.replace(/^\s+/, "")
		.replace(/^(\d+)([.)])(\s)/, "$1\\$2$3")
		.replace(/^([-+])(\s)/, "\\$1$2")
		.replace(/^>/, "\\>");
}

export function parrafo(txt: string, ctx: Contexto): string {
	return inicioSeguro(enLinea(txt, ctx));
}

/** Pone un bloque de lineas dentro de una cita o un callout. */
export function citar(trozos: string[]): string[] {
	const out: string[] = [];
	trozos.forEach((t, i) => {
		if (i > 0) out.push(">");
		for (const l of t.split("\n")) out.push(l ? `> ${l}` : ">");
	});
	return out;
}

export function callout(tipo: string, titulo: string, trozos: string[]): string {
	return [`> [!${tipo}] ${titulo}`, ...citar(trozos)].join("\n");
}

function celda(txt: string, ctx: Contexto): string {
	const md = enLinea(txt, { ...ctx, enTabla: true }).trim();
	return md || " ";
}

function tablaMd(b: Bloque, ctx: Contexto): string[] {
	const filas = b.filas ?? [];
	if (filas.length === 0) return [];
	const n = Math.max(...filas.map((f) => f.length));
	const fila = (f: string[]) => `| ${Array.from({ length: n }, (_, i) => celda(f[i] ?? "", ctx)).join(" | ")} |`;
	const raya = `| ${Array.from({ length: n }, () => "---").join(" | ")} |`;
	const out: string[] = [];
	if (b.titulo) out.push(`**${enLinea(b.titulo, ctx)}**`);
	if (b.vertical) {
		// rotulo a la izquierda: un recuadro con "rotulo: valor"
		return [callout("srd-recuadro", b.titulo ? enLinea(b.titulo, ctx) : "",
			filas.map((f) => `**${enLinea(f[0] ?? "", ctx)}${ctx.dosPuntos}** ${enLinea(f.slice(1).join(" "), ctx)}`))];
	}
	if (b.sin_cabecera) {
		if (n === 2) {
			out.push(filas.map((f) => `- ${enLinea(f[0] ?? "", ctx)} ${enLinea(f[1] ?? "", ctx)}`).join("\n"));
			return out;
		}
		out.push([`| ${Array.from({ length: n }, () => " ").join(" | ")} |`, raya, ...filas.map(fila)].join("\n"));
		return out;
	}
	const [cab, ...cuerpo] = filas;
	if (!cab) return out;
	if (b.grupos?.length) {
		// Markdown no junta celdas: la fila de los grupos va de cabecera y la de las columnas, en negrita, debajo
		const g = Array.from({ length: n }, () => "");
		for (const [texto, desde] of b.grupos) g[desde] = texto;
		const columnas = cab.map((c) => (c.trim() ? `<b>${c}</b>` : c));
		out.push([fila(g), raya, fila(columnas), ...cuerpo.map(fila)].join("\n"));
		return out;
	}
	out.push([fila(cab), raya, ...cuerpo.map(fila)].join("\n"));
	return out;
}

export interface Opciones {
	/** "##" para los titulos de nivel 1 de los datos */
	titulo: number;
	/** fichas de criatura dentro de un conjuro */
	ficha?: (b: Bloque) => string;
}

/** Los bloques de una nota en trozos de Markdown (se separan con una linea en blanco). */
export function bloques(bs: Bloque[], ctx: Contexto, op: Opciones): string[] {
	const out: string[] = [];
	let lista: string[] = [];
	const cerrarLista = () => {
		if (lista.length) out.push(lista.join("\n"));
		lista = [];
	};
	for (const b of bs) {
		if (b.t === "li") {
			lista.push(`- ${enLinea(b.txt ?? "", ctx)}`);
			continue;
		}
		if (b.t === "columnas") {
			for (const it of b.items ?? []) lista.push(`- ${enLinea(it, ctx)}`);
			continue;
		}
		cerrarLista();
		switch (b.t) {
			case "p":
			case "formula":
			case "nota":
				if (b.txt?.trim()) out.push(parrafo(b.txt, ctx));
				break;
			case "h":
				out.push(`${"#".repeat(Math.min(6, op.titulo + (b.n ?? 1) - 1))} ${enLinea(b.txt ?? "", ctx)}`);
				break;
			case "campos":
				for (const [rotulo, valor] of b.filas ?? []) {
					out.push(`**${enLinea(rotulo ?? "", ctx)}${ctx.dosPuntos}** ${enLinea(valor ?? "", ctx)}`);
				}
				break;
			case "tabla":
				out.push(...tablaMd(b, ctx));
				break;
			case "recuadro":
				out.push(callout("srd-recuadro", enLinea(b.titulo ?? "", ctx), bloques(b.bloques ?? [], ctx, op)));
				break;
			case "ficha":
				if (op.ficha) out.push(op.ficha(b));
				break;
		}
	}
	cerrarLista();
	return out;
}
