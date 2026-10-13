// Lo justo de la API de Obsidian para probar la importacion en Node: una boveda en memoria.

export class TAbstractFile {
	constructor(public path: string, protected readonly boveda: Vault) {}
	get name(): string {
		return this.path.split("/").pop() ?? "";
	}
	get parent(): TFolder | null {
		const i = this.path.lastIndexOf("/");
		if (i < 0) return null;
		const f = this.boveda.getAbstractFileByPath(this.path.slice(0, i));
		return f instanceof TFolder ? f : null;
	}
}

export class TFile extends TAbstractFile {}

export class TFolder extends TAbstractFile {
	get children(): TAbstractFile[] {
		const pre = `${this.path}/`;
		const out: TAbstractFile[] = [];
		for (const p of [...this.boveda.ficheros.keys(), ...this.boveda.carpetas]) {
			if (p.startsWith(pre) && !p.slice(pre.length).includes("/")) {
				const f = this.boveda.getAbstractFileByPath(p);
				if (f) out.push(f);
			}
		}
		return out;
	}
}

export class Vault {
	ficheros = new Map<string, string>();
	carpetas = new Set<string>();
	escrituras = 0;
	private objetos = new Map<string, TAbstractFile>();

	getAbstractFileByPath(p: string): TAbstractFile | null {
		const tipo = this.ficheros.has(p) ? TFile : this.carpetas.has(p) ? TFolder : null;
		if (!tipo) return null;
		let o = this.objetos.get(p);
		if (!o || !(o instanceof tipo)) {
			o = new tipo(p, this);
			this.objetos.set(p, o);
		}
		return o;
	}

	async createFolder(p: string): Promise<void> {
		if (this.carpetas.has(p) || this.ficheros.has(p)) throw new Error(`ya existe ${p}`);
		const padre = p.split("/").slice(0, -1).join("/");
		if (padre && !this.carpetas.has(padre)) throw new Error(`no existe la carpeta ${padre}`);
		this.carpetas.add(p);
		await Promise.resolve();
	}

	async create(p: string, texto: string): Promise<TFile> {
		if (this.ficheros.has(p)) throw new Error(`ya existe ${p}`);
		const padre = p.split("/").slice(0, -1).join("/");
		if (padre && !this.carpetas.has(padre)) throw new Error(`no existe la carpeta ${padre}`);
		this.ficheros.set(p, texto);
		this.escrituras++;
		await Promise.resolve();
		return this.getAbstractFileByPath(p) as TFile;
	}

	async read(f: TFile): Promise<string> {
		await Promise.resolve();
		return this.ficheros.get(f.path) ?? "";
	}

	async modify(f: TFile, texto: string): Promise<void> {
		this.ficheros.set(f.path, texto);
		this.escrituras++;
		await Promise.resolve();
	}

	borrar(f: TAbstractFile): void {
		this.ficheros.delete(f.path);
		this.carpetas.delete(f.path);
		this.objetos.delete(f.path);
	}
}

export class App {
	vault = new Vault();
	fileManager = {
		trashFile: async (f: TAbstractFile) => {
			if (f instanceof TFolder && f.children.length) throw new Error(`carpeta no vacia ${f.path}`);
			this.vault.borrar(f);
			await Promise.resolve();
		},
	};
	workspace = { getLeaf: () => ({ openFile: async () => {} }) };
}

export function normalizePath(p: string): string {
	return p.replace(/\\/g, "/").replace(/\/+/g, "/").replace(/^\/|\/$/g, "").normalize("NFC");
}

export function getLanguage(): string {
	return "es";
}

class Componente {
	[k: string]: unknown;
}

export class Modal extends Componente {
	constructor(public app: App) {
		super();
	}
}
export class PluginSettingTab extends Componente {}
export class Setting extends Componente {}
export class FuzzySuggestModal extends Modal {}
export class ItemView extends Componente {}
export class MarkdownView extends Componente {}
export class Plugin extends Componente {}
export class Notice {
	constructor(public mensaje: string) {}
}
export function setIcon(): void {}
