// Datos del SRD 5.2.1 que van dentro del plugin: se descomprimen al usarlos, nunca al arrancar.
import { gunzipSync, strFromU8 } from "fflate";
import comunGz from "../datos/plugin/comun.json.gz";
import deGz from "../datos/plugin/de.json.gz";
import enGz from "../datos/plugin/en.json.gz";
import esGz from "../datos/plugin/es.json.gz";
import frGz from "../datos/plugin/fr.json.gz";
import itGz from "../datos/plugin/it.json.gz";
import type { Comun, DatosIdioma, Entrada, EntradaComun, Idioma } from "./tipos";

const GZ: Record<Idioma, string> = { es: esGz, en: enGz, de: deGz, fr: frGz, it: itGz };

let comun: Comun | null = null;
let porClave: Map<string, EntradaComun> | null = null;
const idiomas = new Map<Idioma, DatosIdioma>();

function desempaquetar<T>(base64: string): T {
	const bin = atob(base64);
	const bytes = new Uint8Array(bin.length);
	for (let i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i);
	return JSON.parse(strFromU8(gunzipSync(bytes))) as T;
}

export function datosComunes(): Comun {
	if (!comun) comun = desempaquetar<Comun>(comunGz);
	return comun;
}

export function comunDe(clave: string): EntradaComun | undefined {
	if (!porClave) {
		porClave = new Map();
		for (const e of datosComunes().entradas) porClave.set(`${e.k}/${e.id}`, e);
	}
	return porClave.get(clave);
}

export function datosIdioma(idioma: Idioma): DatosIdioma {
	let d = idiomas.get(idioma);
	if (!d) {
		d = desempaquetar<DatosIdioma>(GZ[idioma]);
		idiomas.set(idioma, d);
	}
	return d;
}

/** Suelta la memoria de los datos descomprimidos (unos 10 MB con los cinco idiomas). */
export function liberarDatos(): void {
	comun = null;
	porClave = null;
	idiomas.clear();
}

/** La entrada tal cual (metros y kilos, como el SRD de cada idioma) o con las medidas en pies y libras. */
export function conUnidades(e: Entrada, pies: boolean): Entrada {
	if (!pies || !e.pies) return e;
	const copia = JSON.parse(JSON.stringify(e)) as Entrada & Record<string, unknown>;
	for (const [ruta, cambios] of Object.entries(e.pies)) {
		const partes = ruta.split(".");
		const ultima = partes.pop();
		if (ultima === undefined) continue;
		let o: unknown = copia;
		for (const p of partes) o = (o as Record<string, unknown>)[p];
		const padre = o as Record<string, unknown>;
		const texto = padre[ultima];
		if (typeof texto !== "string") continue;
		let t = texto;
		// de atras adelante, para que las posiciones de los cambios anteriores sigan valiendo
		for (let i = cambios.length - 1; i >= 0; i--) {
			const c = cambios[i];
			if (!c) continue;
			t = t.slice(0, c[0]) + c[2] + t.slice(c[1]);
		}
		padre[ultima] = t;
	}
	delete copia.pies;
	return copia;
}
