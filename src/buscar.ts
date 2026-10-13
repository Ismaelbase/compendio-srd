import { FuzzySuggestModal, Notice, normalizePath, TFile, type App, type FuzzyMatch } from "obsidian";
import { raizDe } from "./ajustes";
import { comunDe, datosComunes, datosIdioma } from "./datos";
import { Escritor } from "./importar";
import type CompendioSrd from "./main";
import { Generador, type OpcionesNotas } from "./notas";
import { TEXTOS } from "./textos";
import type { Clase, ComunConjuro, ComunCriatura, Idioma } from "./tipos";
import { t } from "./ui";

export interface Elemento {
	clave: string;
	k: Clase;
	nombre: string;
	detalle: string;
}

/** Todas las entradas de un idioma (o solo las de una clase) para elegirlas por su nombre. */
export function elementos(idioma: Idioma, solo?: Clase): Elemento[] {
	const T = TEXTOS[idioma];
	const d = datosIdioma(idioma);
	const out: Elemento[] = [];
	for (const c of datosComunes().entradas) {
		if (solo && c.k !== solo) continue;
		const clave = `${c.k}/${c.id}`;
		const e = d.entradas[clave];
		if (!e) continue;
		let detalle = T.clases[c.k];
		if (c.k === "criatura") {
			const cc = c.c as ComunCriatura;
			detalle = `${T.ficha.vd} ${cc.vd} · ${cc.px} ${T.px}`;
		} else if (c.k === "conjuro") {
			const cc = c.c as ComunConjuro;
			detalle = `${T.clases.conjuro} · ${cc.nivel === 0 ? T.trucos : T.nivelConjuro(cc.nivel)}`;
		}
		out.push({ clave, k: c.k, nombre: e.nombre, detalle });
	}
	return out;
}

/** Abre la nota de una entrada; si no esta en la boveda, la crea primero (solo esa). */
export async function abrirEntrada(app: App, plugin: CompendioSrd, clave: string, idioma: Idioma): Promise<void> {
	const a = plugin.ajustes;
	const op: OpcionesNotas = { raiz: raizDe(a.carpeta), pies: a.pies, fantasy: a.fantasy, enlazarEstados: a.enlazarEstados };
	const escritor = new Escritor(app, plugin);
	const previa = new Generador(idioma, op, () => false);
	const propia = previa.rutas.get(clave);
	if (!propia) return;
	let f = app.vault.getAbstractFileByPath(normalizePath(`${propia}.md`));
	if (!(f instanceof TFile)) {
		const g = new Generador(idioma, op, (r) => r === propia || escritor.existe(r));
		const n = g.nota(clave);
		if (!n) return;
		await escritor.escribir(n.ruta, n.contenido, false);
		await plugin.guardar();
		f = app.vault.getAbstractFileByPath(normalizePath(`${propia}.md`));
		new Notice(t().creada(datosIdioma(idioma).entradas[clave]?.nombre ?? clave));
	}
	if (f instanceof TFile) await app.workspace.getLeaf(false).openFile(f);
}

export class ModalBuscar extends FuzzySuggestModal<Elemento> {
	private readonly lista: Elemento[];

	constructor(
		app: App,
		private readonly plugin: CompendioSrd,
		private readonly elegir?: (e: Elemento) => void,
		solo?: Clase,
	) {
		super(app);
		this.lista = elementos(plugin.ajustes.idioma, solo);
		this.setPlaceholder(t().buscarAyuda);
	}

	getItems(): Elemento[] {
		return this.lista;
	}

	getItemText(e: Elemento): string {
		return e.nombre;
	}

	renderSuggestion(m: FuzzyMatch<Elemento>, el: HTMLElement): void {
		super.renderSuggestion(m, el);
		el.addClass("srd-sugerencia");
		el.createEl("small", { text: m.item.detalle, cls: "srd-sugerencia-detalle" });
	}

	onChooseItem(e: Elemento): void {
		if (this.elegir) {
			this.elegir(e);
			return;
		}
		if (comunDe(e.clave)) void abrirEntrada(this.app, this.plugin, e.clave, this.plugin.ajustes.idioma);
	}
}
