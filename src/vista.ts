import { ItemView, normalizePath, setIcon, TFile, type HoverParent, type HoverPopover, type WorkspaceLeaf } from "obsidian";
import { raizDe } from "./ajustes";
import { abrirEntrada, ModalBuscar } from "./buscar";
import { comunDe, datosIdioma } from "./datos";
import { calcular, tablaPresupuesto, type Aviso } from "./encuentro";
import { copiarBloque, enviarIT, grupoDelEncuentro, insertarBloque, jugadoresIT } from "./it";
import type CompendioSrd from "./main";
import { rutasDe } from "./notas";
import { TEXTOS } from "./textos";
import type { ComunCriatura } from "./tipos";
import { t } from "./ui";

export const VISTA_ENCUENTRO = "compendio-srd-encuentro";

export class VistaEncuentro extends ItemView implements HoverParent {
	hoverPopover: HoverPopover | null = null;

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

		// grupo: los jugadores de Initiative Tracker (si tiene y se usan) o un grupo propio
		el.createEl("h4", { text: ui.grupo });
		const { jugadores } = jugadoresIT(this.app);
		if (jugadores.length) {
			const fila = el.createEl("label", { cls: "srd-fila srd-usar-it" });
			const marca = fila.createEl("input", { type: "checkbox" });
			marca.checked = enc.usarIT;
			marca.addEventListener("change", () => {
				enc.usarIT = marca.checked;
				void this.cambiar();
			});
			fila.createSpan({ text: ui.usarIT });
		}
		if (jugadores.length && enc.usarIT) {
			const lista = el.createDiv({ cls: "srd-filas srd-jugadores" });
			for (const j of jugadores) {
				const nivel = Number(j.level);
				const fila = lista.createDiv({ cls: "srd-fila" });
				fila.createSpan({ text: j.name, cls: "srd-nombre" });
				fila.createSpan({
					text: Number.isInteger(nivel) && nivel >= 1 ? `${ui.nivel} ${nivel}` : ui.sinNivel,
					cls: "srd-texto",
				});
			}
			el.createEl("p", { text: ui.jugadoresIT, cls: "srd-vacio" });
		} else {
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
		}

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
			if (f) this.vistaPrevia(enlace, f.path);
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
		const r = calcular(grupoDelEncuentro(this.app, this.plugin).grupo, enc.criaturas, tabla);
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
				if (regla && this.app.vault.getAbstractFileByPath(normalizePath(`${regla}.md`))) this.vistaPrevia(enlace, `${regla}#${titulo}`);
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
		boton(ui.enviarIT, true, () => void enviarIT(this.app, this.plugin));
		boton(ui.copiarBloque, false, () => copiarBloque(this.app, this.plugin));
		boton(ui.insertarBloque, false, () => insertarBloque(this.app, this.plugin));
		boton(ui.vaciar, false, () => {
			enc.criaturas = [];
			void this.cambiar();
		});
	}

	/** La ventanita de "Vista previa de página" al pasar por un enlace, como en las notas. */
	private vistaPrevia(el: HTMLElement, linktext: string): void {
		el.addEventListener("mouseover", (event) => {
			this.app.workspace.trigger("hover-link", {
				event, source: VISTA_ENCUENTRO, hoverParent: this, targetEl: el, linktext, sourcePath: "",
			});
		});
	}

	private botonIcono(padre: HTMLElement, icono: string, etiqueta: string, fn: () => void): void {
		const b = padre.createEl("button", { cls: "clickable-icon srd-icono", attr: { "aria-label": etiqueta } });
		setIcon(b, icono);
		b.addEventListener("click", fn);
	}
}
