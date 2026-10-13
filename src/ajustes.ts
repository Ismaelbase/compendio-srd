import { normalizePath, PluginSettingTab, Setting, type App } from "obsidian";
import type { EnEncuentro, Personajes } from "./encuentro";
import type CompendioSrd from "./main";
import { TEXTOS } from "./textos";
import { IDIOMAS, type Idioma } from "./tipos";
import { idiomaObsidian, t } from "./ui";

export interface Ajustes {
	/** idioma del buscador y del encuentro, marcado al importar */
	idioma: Idioma;
	carpeta: string;
	pies: boolean;
	fantasy: boolean;
	enlazarEstados: boolean;
	/** ruta de cada nota escrita por el plugin -> huella de lo que escribio (para no pisar lo que cambie el usuario) */
	huellas: Record<string, string>;
	encuentro: { grupo: Personajes[]; criaturas: EnEncuentro[] };
}

export const CARPETA_POR_DEFECTO = "Compendio SRD";

export function porDefecto(): Ajustes {
	return {
		idioma: idiomaObsidian() ?? "es",
		carpeta: CARPETA_POR_DEFECTO,
		pies: true,
		fantasy: false,
		enlazarEstados: true,
		huellas: {},
		encuentro: { grupo: [{ n: 4, nivel: 1 }], criaturas: [] },
	};
}

/** La carpeta raiz sin barras sobrantes ("/Compendio SRD/" -> "Compendio SRD"). */
export function raizDe(carpeta: string): string {
	const r = normalizePath(carpeta.trim() || CARPETA_POR_DEFECTO).replace(/^\/+|\/+$/g, "");
	return r === "/" || !r ? CARPETA_POR_DEFECTO : r;
}

/** Huella corta de un texto (FNV-1a de 32 bits). */
export function huella(texto: string): string {
	let h = 0x811c9dc5;
	for (let i = 0; i < texto.length; i++) {
		h ^= texto.charCodeAt(i);
		h = Math.imul(h, 0x01000193);
	}
	return (h >>> 0).toString(16).padStart(8, "0") + texto.length.toString(16);
}

export class PestanaAjustes extends PluginSettingTab {
	constructor(app: App, private readonly plugin: CompendioSrd) {
		super(app, plugin);
	}

	display(): void {
		const { containerEl } = this;
		const ui = t();
		const a = this.plugin.ajustes;
		containerEl.empty();

		new Setting(containerEl)
			.setName(ui.cmdImportar)
			.setDesc(ui.importarIntro)
			.addButton((b) => b.setButtonText(ui.importar).setCta().onClick(() => this.plugin.abrirImportar()));

		new Setting(containerEl)
			.setName(ui.idiomaPrincipal)
			.setDesc(ui.idiomaPrincipalDesc)
			.addDropdown((d) => {
				for (const l of IDIOMAS) d.addOption(l, TEXTOS[l].idioma);
				d.setValue(a.idioma).onChange(async (v) => {
					a.idioma = v as Idioma;
					await this.plugin.guardar();
					this.plugin.refrescarVistas();
				});
			});

		new Setting(containerEl)
			.setName(ui.carpeta)
			.setDesc(ui.carpetaDesc)
			.addText((x) => x.setPlaceholder(CARPETA_POR_DEFECTO).setValue(a.carpeta).onChange(async (v) => {
				a.carpeta = raizDe(v);
				await this.plugin.guardar();
			}));

		new Setting(containerEl)
			.setName(ui.unidades)
			.setDesc(ui.unidadesDesc)
			.addDropdown((d) => d
				.addOption("pies", ui.pies)
				.addOption("metros", ui.metros)
				.setValue(a.pies ? "pies" : "metros")
				.onChange(async (v) => {
					a.pies = v === "pies";
					await this.plugin.guardar();
				}));

		new Setting(containerEl)
			.setName(ui.estados)
			.setDesc(ui.estadosDesc)
			.addToggle((x) => x.setValue(a.enlazarEstados).onChange(async (v) => {
				a.enlazarEstados = v;
				await this.plugin.guardar();
			}));

		new Setting(containerEl)
			.setName(ui.fantasy)
			.setDesc(ui.fantasyDesc)
			.addToggle((x) => x.setValue(a.fantasy).onChange(async (v) => {
				a.fantasy = v;
				await this.plugin.guardar();
			}));
	}
}
