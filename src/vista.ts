import { ItemView, MarkdownView, Notice, normalizePath, setIcon, TFile, type WorkspaceLeaf } from "obsidian";
import { raizDe } from "./ajustes";
import { abrirEntrada, ModalBuscar } from "./buscar";
import { comunDe, datosIdioma } from "./datos";
import { bloqueEncounter, calcular, criaturasIT, tablaPresupuesto, type Aviso } from "./encuentro";
import type CompendioSrd from "./main";
import { rutasDe } from "./notas";
import { TEXTOS } from "./textos";
import type { ComunCriatura } from "./tipos";
import { t } from "./ui";

export const VISTA_ENCUENTRO = "compendio-srd-encuentro";
const VISTA_IT = "initiative-tracker-view";

interface ApiIT {
	newEncounter(estado: { name?: string; creatures: unknown[]; roll?: boolean }): void;
}

function apiIT(): ApiIT | null {
	const api = (window as unknown as { InitiativeTracker?: ApiIT }).InitiativeTracker;
	return api && typeof api.newEncounter === "function" ? api : null;
}

export class VistaEncuentro extends ItemView {
	constructor(leaf: WorkspaceLeaf, private readonly plugin: CompendioSrd) {
		super(leaf);
	}

	getViewType(): string {
		return VISTA_ENCUENTRO;
	}

	getDisplayText(): string {
		return t().encuentro;
	}

	getIcon(): string {
		return "swords";
	}

	async onOpen(): Promise<void> {
		this.pintar();
		await Promise.resolve();
	}

	async onClose(): Promise<void> {
		this.contentEl.empty();
		await Promise.resolve();
	}

	private async cambiar(): Promise<void> {
		await this.plugin.guardar();
		this.pintar();
	}

	pintar(): void {
		const ui = t();
		const idioma = this.plugin.ajustes.idioma;
		const T = TEXTOS[idioma];
		const enc = this.plugin.ajustes.encuentro;
		const tabla = tablaPresupuesto(idioma);
		const datos = datosIdioma(idioma);
		const raiz = raizDe(this.plugin.ajustes.carpeta);
		const rutas = rutasDe(idioma, raiz);
		const nota = (clave: string): TFile | null => {
			const r = rutas.get(clave);
			const f = r ? this.app.vault.getAbstractFileByPath(normalizePath(`${r}.md`)) : null;
			return f instanceof TFile ? f : null;
		};
		const el = this.contentEl;
		el.empty();
		el.addClass("srd-encuentro");

		// grupo
		el.createEl("h4", { text: ui.grupo });
		const grupo = el.createDiv({ cls: "srd-filas" });
		enc.grupo.forEach((p, i) => {
			const fila = grupo.createDiv({ cls: "srd-fila" });
			const n = fila.createEl("input", { type: "number", cls: "srd-numero", attr: { min: "1", max: "20", "aria-label": ui.personajes } });
			n.value = String(p.n);
			n.addEventListener("change", () => {
				p.n = Math.max(1, Math.min(20, Math.round(Number(n.value)) || 1));
				void this.cambiar();
			});
			fila.createSpan({ text: ui.personajes.toLowerCase(), cls: "srd-texto" });
			const nivel = fila.createEl("select", { cls: "dropdown", attr: { "aria-label": ui.nivel } });
			for (let l = 1; l <= 20; l++) nivel.createEl("option", { text: `${ui.nivel} ${l}`, value: String(l) });
			nivel.value = String(p.nivel);
			nivel.addEventListener("change", () => {
				p.nivel = Number(nivel.value);
				void this.cambiar();
			});
			if (enc.grupo.length > 1) this.botonIcono(fila, "x", ui.quitar, () => {
				enc.grupo.splice(i, 1);
				void this.cambiar();
			});
		});
		const masGrupo = el.createEl("button", { text: ui.anadirPersonajes, cls: "srd-boton-texto" });
		masGrupo.addEventListener("click", () => {
			const ultimo = enc.grupo[enc.grupo.length - 1];
			enc.grupo.push({ n: 1, nivel: Math.min(20, (ultimo?.nivel ?? 0) + 1) });
			void this.cambiar();
		});

		// criaturas
		el.createEl("h4", { text: ui.criaturas });
		const lista = el.createDiv({ cls: "srd-filas" });
		if (!enc.criaturas.length) lista.createEl("p", { text: ui.sinCriaturas, cls: "srd-vacio" });
		enc.criaturas.forEach((x, i) => {
			const c = comunDe(x.clave)?.c as ComunCriatura | undefined;
			const e = datos.entradas[x.clave];
			if (!c || !e) return;
			const fila = lista.createDiv({ cls: "srd-fila srd-criatura" });
			this.botonIcono(fila, "minus", "−", () => {
				x.n = Math.max(1, x.n - 1);
				void this.cambiar();
			});
			fila.createSpan({ text: String(x.n), cls: "srd-cantidad" });
			this.botonIcono(fila, "plus", "+", () => {
				x.n++;
				void this.cambiar();
			});
			const nombre = fila.createDiv({ cls: "srd-nombre" });
			const f = nota(x.clave);
			const enlace = nombre.createEl("a", { text: e.nombre, cls: "srd-enlace" });
			enlace.addEventListener("click", () => {
				if (f) void this.app.workspace.getLeaf(false).openFile(f);
				else void abrirEntrada(this.app, this.plugin, x.clave, idioma);
			});
			nombre.createEl("small", { text: `${T.ficha.vd} ${c.vd} · ${c.px * x.n} ${T.px}` });
			this.botonIcono(fila, "x", ui.quitar, () => {
				enc.criaturas.splice(i, 1);
				void this.cambiar();
			});
		});
		const masCriatura = el.createEl("button", { text: ui.anadirCriatura, cls: "mod-cta" });
		masCriatura.addEventListener("click", () => {
			new ModalBuscar(this.app, this.plugin, (elegido) => {
				this.plugin.anadirCriatura(elegido.clave);
			}, "criatura").open();
		});

		// presupuesto
		const r = calcular(enc.grupo, enc.criaturas, tabla);
		el.createEl("h4", { text: ui.presupuesto });
		const pres = el.createDiv({ cls: "srd-presupuesto" });
		tabla.etiquetas.forEach((etq, i) => {
			const fila = pres.createDiv({ cls: "srd-banda" });
			if (r.dificultad === i) fila.addClass("is-active");
			fila.createSpan({ text: etq });
			fila.createSpan({ text: `${(r.presupuesto[i] ?? 0).toLocaleString(idioma)} ${T.px}`, cls: "srd-cifra" });
		});
		const max = Math.max(r.presupuesto[2], r.total, 1);
		const barra = pres.createDiv({ cls: "srd-barra" });
		barra.createDiv({ cls: "srd-barra-relleno" }).setCssProps({ "--srd-ancho": `${Math.min(100, (r.total / max) * 100)}%` });
		for (const v of r.presupuesto) barra.createDiv({ cls: "srd-barra-marca" }).setCssProps({ "--srd-pos": `${(v / max) * 100}%` });
		const gasto = pres.createDiv({ cls: "srd-banda srd-gasto" });
		gasto.createSpan({ text: ui.gasto });
		gasto.createSpan({ text: `${r.total.toLocaleString(idioma)} ${T.px}`, cls: "srd-cifra" });
		if (r.dificultad === 3) {
			gasto.addClass("is-over");
			pres.createEl("p", { text: ui.porEncima(`${(r.total - r.presupuesto[2]).toLocaleString(idioma)} ${T.px}`), cls: "srd-aviso" });
		}

		// consejos de "Solucion de problemas"
		if (r.avisos.length) {
			const regla = rutas.get("regla/combat-encounters");
			el.createEl("h4", { text: ui.consejos });
			const ul = el.createEl("ul", { cls: "srd-consejos" });
			const textos: Record<Aviso, [string, string]> = {
				muchas: [ui.avisoMuchas, tabla.consejos[0]],
				vd0: [ui.avisoVd0, tabla.consejos[1]],
				perfiles: [ui.avisoPerfiles, tabla.consejos[2]],
				poderosas: [ui.avisoPoderosas, tabla.consejos[3]],
			};
			for (const a of r.avisos) {
				const [texto, titulo] = textos[a];
				const li = ul.createEl("li", { text: `${texto} ` });
				const enlace = li.createEl("a", { text: titulo, cls: "srd-enlace" });
				enlace.addEventListener("click", () => {
					if (regla && this.app.vault.getAbstractFileByPath(normalizePath(`${regla}.md`))) {
						void this.app.workspace.openLinkText(`${regla}#${titulo}`, "", false);
					} else {
						void abrirEntrada(this.app, this.plugin, "regla/combat-encounters", idioma);
					}
				});
			}
		}

		// salida
		const acciones = el.createDiv({ cls: "srd-acciones" });
		const boton = (texto: string, cta: boolean, fn: () => void) => {
			const b = acciones.createEl("button", { text: texto, cls: cta ? "mod-cta" : "" });
			b.disabled = !enc.criaturas.length;
			b.addEventListener("click", fn);
		};
		boton(ui.enviarIT, true, () => void this.enviarIT());
		boton(ui.copiarBloque, false, () => {
			const texto = bloqueEncounter(ui.nombreEncuentro, enc.criaturas, idioma);
			navigator.clipboard.writeText(texto).then(() => new Notice(ui.copiado), () => new Notice(texto));
		});
		boton(ui.insertarBloque, false, () => this.insertar());
		boton(ui.vaciar, false, () => {
			enc.criaturas = [];
			void this.cambiar();
		});
	}

	private botonIcono(padre: HTMLElement, icono: string, etiqueta: string, fn: () => void): void {
		const b = padre.createEl("button", { cls: "clickable-icon srd-icono", attr: { "aria-label": etiqueta } });
		setIcon(b, icono);
		b.addEventListener("click", fn);
	}

	private async enviarIT(): Promise<void> {
		const ui = t();
		const api = apiIT();
		if (!api) {
			new Notice(ui.itNoEsta);
			return;
		}
		const criaturas = criaturasIT(this.plugin.ajustes.encuentro.criaturas, this.plugin.ajustes.idioma);
		api.newEncounter({ name: ui.nombreEncuentro, creatures: criaturas, roll: true });
		let hoja = this.app.workspace.getLeavesOfType(VISTA_IT)[0] ?? null;
		if (!hoja) {
			hoja = this.app.workspace.getRightLeaf(false);
			await hoja?.setViewState({ type: VISTA_IT, active: true });
		}
		if (hoja) await this.app.workspace.revealLeaf(hoja);
		new Notice(ui.enviado(criaturas.length));
	}

	private insertar(): void {
		const ui = t();
		const hoja = this.app.workspace.getMostRecentLeaf();
		const vista = hoja?.view;
		if (!(vista instanceof MarkdownView) || vista.getMode() !== "source") {
			new Notice(ui.sinNota);
			return;
		}
		const texto = bloqueEncounter(ui.nombreEncuentro, this.plugin.ajustes.encuentro.criaturas, this.plugin.ajustes.idioma);
		vista.editor.replaceSelection(`${texto}\n`);
	}
}
