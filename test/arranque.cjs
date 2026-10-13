// Prueba de humo del main.js compilado: se carga con una API de Obsidian falsa y se ejecuta onload().
// Uso: node test/arranque.cjs (despues de npm run build)
const Module = require("module");
const path = require("path");

const registro = { comandos: [], vistas: [], cintas: [], pestanas: 0 };
class Componente {}
class Plugin {
	constructor(app, manifest) {
		this.app = app;
		this.manifest = manifest;
	}
	async loadData() {
		return null;
	}
	async saveData(d) {
		this.guardado = d;
	}
	addCommand(c) {
		registro.comandos.push(c);
		return c;
	}
	registerView(tipo) {
		registro.vistas.push(tipo);
	}
	addRibbonIcon(icono, titulo) {
		registro.cintas.push(`${icono}: ${titulo}`);
	}
	addSettingTab() {
		registro.pestanas++;
	}
}
const falso = {
	Plugin, Modal: Componente, Setting: Componente, PluginSettingTab: Componente, FuzzySuggestModal: Componente,
	ItemView: Componente, MarkdownView: Componente, Notice: Componente, TFile: Componente, TFolder: Componente,
	normalizePath: (p) => p, setIcon: () => {}, getLanguage: () => "es",
};
const cargar = Module._load;
Module._load = function (pedido, ...resto) {
	if (pedido === "obsidian") return falso;
	return cargar.call(this, pedido, ...resto);
};

(async () => {
	const t0 = Date.now();
	// main.js es CommonJS, pero package.json dice "type": "module": se carga una copia .cjs
	const copia = path.resolve(__dirname, "..", ".test", "main.cjs");
	require("fs").mkdirSync(path.dirname(copia), { recursive: true });
	require("fs").copyFileSync(path.resolve(__dirname, "..", "main.js"), copia);
	const Clase = require(copia).default;
	const t1 = Date.now();
	const app = { workspace: { getActiveFile: () => null, getLeavesOfType: () => [] }, metadataCache: {} };
	const p = new Clase(app, { id: "compendio-srd" });
	await p.onload();
	console.log(`main.js cargado en ${t1 - t0} ms, onload en ${Date.now() - t1} ms`);
	console.log("comandos:", registro.comandos.map((c) => `${c.id} (${c.name})`).join("; "));
	console.log("vistas:", registro.vistas.join(", "), "| cinta:", registro.cintas.join(", "), "| pestañas:", registro.pestanas);
	console.log("ajustes:", JSON.stringify({ ...p.ajustes, huellas: undefined }));
	const activo = registro.comandos.find((c) => c.id === "anadir-criatura").checkCallback(true);
	if (activo !== false) throw new Error("el comando de añadir criatura sale sin una criatura abierta");
	p.onunload();
	console.log("arranque bien");
})().catch((e) => {
	console.error("FALLO", e);
	process.exit(1);
});
