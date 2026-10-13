import { Modal, Notice, normalizePath, Setting, TFile, TFolder, type App } from "obsidian";
import { CARPETA_POR_DEFECTO, huella, raizDe } from "./ajustes";
import type CompendioSrd from "./main";
import { carpetaIdioma, Generador, rutasPlan, type OpcionesNotas } from "./notas";
import { TEXTOS } from "./textos";
import { IDIOMAS, SECCIONES, type Idioma, type Seccion } from "./tipos";
import { t } from "./ui";

export type Resultado = "creada" | "cambiada" | "igual" | "saltada";

const pausa = () => new Promise<void>((r) => window.setTimeout(r, 0));

/** Escribe notas sin pisar las que el usuario haya cambiado: solo reescribe las que siguen como el plugin las dejo. */
export class Escritor {
	private readonly carpetas = new Set<string>();

	constructor(private readonly app: App, private readonly plugin: CompendioSrd) {}

	existe(ruta: string): boolean {
		return this.app.vault.getAbstractFileByPath(normalizePath(`${ruta}.md`)) instanceof TFile;
	}

	private async carpeta(ruta: string): Promise<void> {
		const partes = ruta.split("/").slice(0, -1);
		for (let i = 1; i <= partes.length; i++) {
			const c = partes.slice(0, i).join("/");
			if (this.carpetas.has(c)) continue;
			const f = this.app.vault.getAbstractFileByPath(c);
			if (!f) await this.app.vault.createFolder(c);
			this.carpetas.add(c);
		}
	}

	async escribir(ruta: string, contenido: string, sobrescribir: boolean): Promise<Resultado> {
		const path = normalizePath(`${ruta}.md`);
		const huellas = this.plugin.ajustes.huellas;
		const f = this.app.vault.getAbstractFileByPath(path);
		if (!f) {
			await this.carpeta(path);
			await this.app.vault.create(path, contenido);
			huellas[path] = huella(contenido);
			return "creada";
		}
		if (!(f instanceof TFile)) return "saltada";
		const actual = await this.app.vault.read(f);
		if (actual === contenido) {
			huellas[path] = huella(contenido);
			return "igual";
		}
		const nuestra = huellas[path] !== undefined && huellas[path] === huella(actual);
		if (!nuestra && !sobrescribir) return "saltada";
		await this.app.vault.modify(f, contenido);
		huellas[path] = huella(contenido);
		return "cambiada";
	}
}

/** Idiomas con su carpeta ya en la boveda (para enlazar sus notas al pie de las nuevas). */
function idiomasPresentes(app: App, raiz: string): Idioma[] {
	return IDIOMAS.filter((l) => app.vault.getAbstractFileByPath(carpetaIdioma(raiz, l)) instanceof TFolder);
}

export class ModalImportar extends Modal {
	private idiomas = new Set<Idioma>();
	private secciones = new Set<Seccion>(SECCIONES);
	private sobrescribir = false;
	private cancelado = false;
	private enMarcha = false;

	constructor(app: App, private readonly plugin: CompendioSrd) {
		super(app);
		this.idiomas.add(plugin.ajustes.idioma);
	}

	onOpen(): void {
		this.pintar();
	}

	onClose(): void {
		this.cancelado = true;
		this.contentEl.empty();
	}

	private pintar(): void {
		const ui = t();
		const a = this.plugin.ajustes;
		const el = this.contentEl;
		el.empty();
		el.addClass("srd-importar");
		this.setTitle(ui.importarTitulo);
		el.createEl("p", { text: ui.importarIntro });

		new Setting(el).setName(ui.idiomas).setHeading();
		for (const l of IDIOMAS) {
			new Setting(el).setName(TEXTOS[l].idioma).addToggle((x) => x.setValue(this.idiomas.has(l)).onChange((v) => {
				if (v) this.idiomas.add(l);
				else this.idiomas.delete(l);
			}));
		}
		new Setting(el).setName(ui.queImportar).setHeading();
		for (const s of SECCIONES) {
			new Setting(el).setName(ui.secciones[s]).addToggle((x) => x.setValue(this.secciones.has(s)).onChange((v) => {
				if (v) this.secciones.add(s);
				else this.secciones.delete(s);
			}));
		}
		new Setting(el).setName(ui.carpeta).setDesc(ui.carpetaDesc).addText((x) => x
			.setPlaceholder(CARPETA_POR_DEFECTO)
			.setValue(a.carpeta)
			.onChange((v) => {
				a.carpeta = raizDe(v);
			}));
		new Setting(el).setName(ui.unidades).setDesc(ui.unidadesDesc).addDropdown((d) => d
			.addOption("pies", ui.pies)
			.addOption("metros", ui.metros)
			.setValue(a.pies ? "pies" : "metros")
			.onChange((v) => {
				a.pies = v === "pies";
			}));
		new Setting(el).setName(ui.sobrescribir).setDesc(ui.sobrescribirDesc).addToggle((x) => x
			.setValue(this.sobrescribir)
			.onChange((v) => {
				this.sobrescribir = v;
			}));
		new Setting(el)
			.addButton((b) => b.setButtonText(ui.cancelar).onClick(() => this.close()))
			.addButton((b) => b.setButtonText(ui.importar).setCta().onClick(() => {
				void this.importar();
			}));
	}

	private async importar(): Promise<void> {
		if (this.enMarcha) return;
		const ui = t();
		if (!this.idiomas.size || !this.secciones.size) {
			new Notice(ui.nadaElegido);
			return;
		}
		this.enMarcha = true;
		this.cancelado = false;
		await this.plugin.guardar();
		const a = this.plugin.ajustes;
		const op: OpcionesNotas = { raiz: raizDe(a.carpeta), pies: a.pies, fantasy: a.fantasy, enlazarEstados: a.enlazarEstados };
		const el = this.contentEl;
		el.empty();
		const estado = el.createEl("p", { text: ui.preparando });
		const barra = el.createEl("progress", { cls: "srd-progreso" });
		const botones = new Setting(el).addButton((b) => b.setButtonText(ui.cancelar).onClick(() => {
			this.cancelado = true;
		}));
		await pausa();

		const escritor = new Escritor(this.app, this.plugin);
		const idiomas = IDIOMAS.filter((l) => this.idiomas.has(l));
		const plan = new Set<string>();
		for (const l of idiomas) for (const r of rutasPlan(l, this.secciones, op.raiz)) plan.add(r);
		const existe = (r: string) => plan.has(r) || escritor.existe(r);
		const conPie = [...new Set([...idiomas, ...idiomasPresentes(this.app, op.raiz)])];
		const rutasDe = new Map(conPie.map((l) => [l, new Generador(l, op, existe).rutas] as const));
		const total = plan.size;
		barra.max = total;
		const cuenta: Record<Resultado, number> = { creada: 0, cambiada: 0, igual: 0, saltada: 0 };
		const errores: string[] = [];
		let hechas = 0;
		for (const l of idiomas) {
			if (this.cancelado) break;
			const otros = conPie.filter((x) => x !== l).map((x) => ({ idioma: x, rutas: rutasDe.get(x) ?? new Map<string, string>() }));
			const g = new Generador(l, op, existe, otros);
			for (const n of g.notas(this.secciones)) {
				if (this.cancelado) break;
				try {
					cuenta[await escritor.escribir(n.ruta, n.contenido, this.sobrescribir)]++;
				} catch (e) {
					cuenta.saltada++;
					errores.push(ui.errorEscribir(n.ruta, e instanceof Error ? e.message : String(e)));
				}
				hechas++;
				if (hechas % 20 === 0) {
					barra.value = hechas;
					estado.setText(ui.escribiendo(hechas, total));
					await pausa();
				}
				if (hechas % 500 === 0) await this.plugin.guardar();
			}
		}
		await this.plugin.guardar();
		this.enMarcha = false;
		barra.value = hechas;
		const resumen = ui.resumen(cuenta.creada, cuenta.cambiada, cuenta.igual, cuenta.saltada);
		estado.setText(this.cancelado ? `${ui.cancelado} ${resumen}` : resumen);
		if (cuenta.saltada) el.createEl("p", { text: ui.saltadasDesc, cls: "setting-item-description" });
		for (const e of errores.slice(0, 5)) el.createEl("p", { text: e, cls: "mod-warning" });
		botones.clear();
		botones.addButton((b) => b.setButtonText(ui.cerrar).setCta().onClick(() => this.close()));
		new Notice(resumen);
		const inicio = this.app.vault.getAbstractFileByPath(normalizePath(`${carpetaIdioma(op.raiz, idiomas[0] ?? "es")}/${TEXTOS[idiomas[0] ?? "es"].inicio}.md`));
		if (!this.cancelado && inicio instanceof TFile && cuenta.creada) await this.app.workspace.getLeaf(false).openFile(inicio);
	}
}

/** Las notas que escribio el plugin y siguen tal cual. */
export async function sinCambiar(app: App, plugin: CompendioSrd): Promise<TFile[]> {
	const out: TFile[] = [];
	for (const [path, h] of Object.entries(plugin.ajustes.huellas)) {
		const f = app.vault.getAbstractFileByPath(path);
		if (f instanceof TFile && huella(await app.vault.read(f)) === h) out.push(f);
	}
	return out;
}

export class ModalQuitar extends Modal {
	constructor(app: App, private readonly plugin: CompendioSrd, private readonly notas: TFile[]) {
		super(app);
	}

	onOpen(): void {
		const ui = t();
		this.setTitle(ui.quitarTitulo);
		this.contentEl.createEl("p", { text: ui.quitarTexto(this.notas.length) });
		new Setting(this.contentEl)
			.addButton((b) => b.setButtonText(ui.cancelar).onClick(() => this.close()))
			.addButton((b) => b.setButtonText(ui.quitar).setWarning().onClick(() => {
				void this.quitar();
			}));
	}

	onClose(): void {
		this.contentEl.empty();
	}

	private async quitar(): Promise<void> {
		const ui = t();
		const carpetas = new Set<TFolder>();
		for (const f of this.notas) {
			if (f.parent) carpetas.add(f.parent);
			await this.app.fileManager.trashFile(f);
			delete this.plugin.ajustes.huellas[f.path];
		}
		// las carpetas que se quedan vacias, de dentro afuera
		const raiz = raizDe(this.plugin.ajustes.carpeta);
		const porProfundidad = [...carpetas].sort((a, b) => b.path.split("/").length - a.path.split("/").length);
		for (const c of porProfundidad) {
			let d: TFolder | null = c;
			while (d && d.path.startsWith(`${raiz}/`) && d.children.length === 0) {
				const arriba: TFolder | null = d.parent;
				await this.app.fileManager.trashFile(d);
				d = arriba;
			}
		}
		const r = this.app.vault.getAbstractFileByPath(raiz);
		if (r instanceof TFolder && r.children.length === 0) await this.app.fileManager.trashFile(r);
		await this.plugin.guardar();
		new Notice(ui.quitado(this.notas.length));
		this.close();
	}
}
