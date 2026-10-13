// Initiative Tracker: sus jugadores (para el presupuesto y para mandarlos con las criaturas), su API y el bloque
// encounter. Leido en su codigo (13.0.21): src/api/api.ts, src/settings/settings.types.ts y src/encounter/index.ts.
import { MarkdownView, Notice, type App, type Editor } from "obsidian";
import { bloqueEncounter, criaturasIT, type Personajes } from "./encuentro";
import type CompendioSrd from "./main";
import { t } from "./ui";

export const VISTA_IT = "initiative-tracker-view";

export interface JugadorIT {
	name: string;
	level?: number;
	player?: boolean;
	[k: string]: unknown;
}

interface DatosIT {
	players?: JugadorIT[];
	parties?: { name: string; players: string[] }[];
	defaultParty?: string;
}

interface ApiIT {
	newEncounter(estado: { name?: string; creatures: unknown[]; roll?: boolean }): void;
}

function datosIT(app: App): DatosIT | null {
	const plugins = (app as unknown as { plugins?: { getPlugin?: (id: string) => unknown } }).plugins;
	const p = plugins?.getPlugin?.("initiative-tracker") as { data?: DatosIT } | null | undefined;
	return p?.data ?? null;
}

export function apiIT(): ApiIT | null {
	const api = (window as unknown as { InitiativeTracker?: ApiIT }).InitiativeTracker;
	return api && typeof api.newEncounter === "function" ? api : null;
}

/** Los jugadores de Initiative Tracker: los de su grupo por defecto si lo tiene; si no, todos los de sus ajustes.
 * porDefecto dice si Initiative Tracker ya los mete el solo en un encuentro nuevo (lo hace con el grupo por defecto). */
export function jugadoresIT(app: App): { jugadores: JugadorIT[]; porDefecto: boolean } {
	const d = datosIT(app);
	const todos = (d?.players ?? []).filter((p) => p && typeof p.name === "string" && p.name);
	const grupo = d?.defaultParty ? d.parties?.find((g) => g.name === d.defaultParty) : undefined;
	if (grupo?.players?.length) {
		const suyos = grupo.players.map((n) => todos.find((p) => p.name === n)).filter((p): p is JugadorIT => !!p);
		return { jugadores: suyos, porDefecto: true };
	}
	return { jugadores: todos, porDefecto: false };
}

/** El grupo que cuenta para el presupuesto: los jugadores de Initiative Tracker (si se usan y hay) o el propio. */
export function grupoDelEncuentro(app: App, plugin: CompendioSrd): { grupo: Personajes[]; jugadores: JugadorIT[] } {
	const enc = plugin.ajustes.encuentro;
	const { jugadores } = jugadoresIT(app);
	if (!enc.usarIT || !jugadores.length) return { grupo: enc.grupo, jugadores: [] };
	const porNivel = new Map<number, number>();
	for (const j of jugadores) {
		const nivel = Number(j.level);
		if (Number.isInteger(nivel) && nivel >= 1 && nivel <= 20) porNivel.set(nivel, (porNivel.get(nivel) ?? 0) + 1);
	}
	return { grupo: [...porNivel].map(([nivel, n]) => ({ n, nivel })), jugadores };
}

export async function enviarIT(app: App, plugin: CompendioSrd): Promise<void> {
	const ui = t();
	const api = apiIT();
	if (!api) {
		new Notice(ui.itNoEsta);
		return;
	}
	const enc = plugin.ajustes.encuentro;
	const criaturas: unknown[] = criaturasIT(enc.criaturas, plugin.ajustes.idioma);
	// con grupo por defecto, Initiative Tracker mete a sus jugadores el solo; si no, van con las criaturas
	const { jugadores, porDefecto } = jugadoresIT(app);
	const conJugadores = enc.usarIT && !porDefecto ? jugadores.map((j) => ({ ...j, player: true })) : [];
	api.newEncounter({ name: ui.nombreEncuentro, creatures: [...conJugadores, ...criaturas], roll: true });
	let hoja = app.workspace.getLeavesOfType(VISTA_IT)[0] ?? null;
	if (!hoja) {
		hoja = app.workspace.getRightLeaf(true);
		await hoja?.setViewState({ type: VISTA_IT, active: true });
	}
	if (hoja) await app.workspace.revealLeaf(hoja);
	new Notice(ui.enviado(criaturas.length));
}

export function bloqueDelEncuentro(app: App, plugin: CompendioSrd): string {
	const enc = plugin.ajustes.encuentro;
	const { jugadores } = grupoDelEncuentro(app, plugin);
	return bloqueEncounter(t().nombreEncuentro, enc.criaturas, plugin.ajustes.idioma, jugadores.map((j) => j.name));
}

export function copiarBloque(app: App, plugin: CompendioSrd): void {
	const ui = t();
	const texto = bloqueDelEncuentro(app, plugin);
	navigator.clipboard.writeText(texto).then(() => new Notice(ui.copiado), () => new Notice(texto));
}

/** Inserta el bloque en el editor dado o, si no hay, en la ultima nota abierta en modo de edicion. */
export function insertarBloque(app: App, plugin: CompendioSrd, editor?: Editor): void {
	const ui = t();
	let ed = editor;
	if (!ed) {
		const vista = app.workspace.getMostRecentLeaf()?.view;
		if (vista instanceof MarkdownView && vista.getMode() === "source") ed = vista.editor;
	}
	if (!ed) {
		new Notice(ui.sinNota);
		return;
	}
	ed.replaceSelection(`${bloqueDelEncuentro(app, plugin)}\n`);
}
