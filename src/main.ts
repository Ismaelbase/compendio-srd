import { Notice, Plugin, type WorkspaceLeaf } from "obsidian";
import { PestanaAjustes, porDefecto, raizDe, type Ajustes } from "./ajustes";
import { ModalBuscar } from "./buscar";
import { comunDe, datosIdioma, liberarDatos } from "./datos";
import { ModalImportar, ModalQuitar, sinCambiar } from "./importar";
import { IDIOMAS } from "./tipos";
import { t } from "./ui";
import { VISTA_ENCUENTRO, VistaEncuentro } from "./vista";

export default class CompendioSrd extends Plugin {
	ajustes: Ajustes = porDefecto();

	async onload(): Promise<void> {
		await this.cargar();
		const ui = t();
		this.registerView(VISTA_ENCUENTRO, (leaf) => new VistaEncuentro(leaf, this));
		this.addRibbonIcon("swords", ui.cmdEncuentro, () => void this.abrirEncuentro());
		this.addCommand({ id: "importar", name: ui.cmdImportar, callback: () => this.abrirImportar() });
		this.addCommand({ id: "buscar", name: ui.cmdBuscar, callback: () => new ModalBuscar(this.app, this).open() });
		this.addCommand({ id: "abrir-encuentro", name: ui.cmdEncuentro, callback: () => void this.abrirEncuentro() });
		this.addCommand({
			id: "anadir-criatura",
			name: ui.cmdAnadir,
			checkCallback: (comprobando) => {
				const clave = this.criaturaActiva();
				if (comprobando) return clave !== null;
				if (clave) this.anadirCriatura(clave);
				return true;
			},
		});
		this.addCommand({
			id: "quitar-notas",
			name: ui.cmdQuitar,
			callback: async () => {
				const notas = await sinCambiar(this.app, this);
				if (!notas.length) new Notice(t().quitarNada);
				else new ModalQuitar(this.app, this, notas).open();
			},
		});
		this.addSettingTab(new PestanaAjustes(this.app, this));
	}

	onunload(): void {
		liberarDatos();
	}

	private async cargar(): Promise<void> {
		const guardado = (await this.loadData()) as Partial<Ajustes> | null;
		const base = porDefecto();
		this.ajustes = { ...base, ...guardado, encuentro: { ...base.encuentro, ...guardado?.encuentro } };
		if (!IDIOMAS.includes(this.ajustes.idioma)) this.ajustes.idioma = base.idioma;
		this.ajustes.carpeta = raizDe(this.ajustes.carpeta);
	}

	async guardar(): Promise<void> {
		await this.saveData(this.ajustes);
	}

	abrirImportar(): void {
		new ModalImportar(this.app, this).open();
	}

	async abrirEncuentro(): Promise<void> {
		const { workspace } = this.app;
		let hoja: WorkspaceLeaf | null = workspace.getLeavesOfType(VISTA_ENCUENTRO)[0] ?? null;
		if (!hoja) {
			hoja = workspace.getRightLeaf(false);
			await hoja?.setViewState({ type: VISTA_ENCUENTRO, active: true });
		}
		if (hoja) await workspace.revealLeaf(hoja);
	}

	refrescarVistas(): void {
		for (const hoja of this.app.workspace.getLeavesOfType(VISTA_ENCUENTRO)) {
			if (hoja.view instanceof VistaEncuentro) hoja.view.pintar();
		}
	}

	/** La criatura del compendio de la nota abierta (su propiedad "srd"), si lo es. */
	private criaturaActiva(): string | null {
		const f = this.app.workspace.getActiveFile();
		if (!f) return null;
		const srd: unknown = this.app.metadataCache.getFileCache(f)?.frontmatter?.srd;
		return typeof srd === "string" && srd.startsWith("criatura/") && comunDe(srd) ? srd : null;
	}

	anadirCriatura(clave: string): void {
		const lista = this.ajustes.encuentro.criaturas;
		const x = lista.find((c) => c.clave === clave);
		if (x) x.n++;
		else lista.push({ clave, n: 1 });
		void this.guardar();
		this.refrescarVistas();
		void this.abrirEncuentro();
		new Notice(t().anadida(datosIdioma(this.ajustes.idioma).entradas[clave]?.nombre ?? clave));
	}
}
