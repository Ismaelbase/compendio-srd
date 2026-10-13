// La importacion contra una boveda en memoria: crear, volver a importar, respetar lo que cambia el usuario, quitar.
import { porDefecto } from "../src/ajustes";
import { importarNotas, sinCambiar, type Informe } from "../src/importar";
import type CompendioSrd from "../src/main";
import { SECCIONES, type Idioma, type Seccion } from "../src/tipos";
import { App, TFile } from "./obsidian-falso";

export async function pruebasImportar(): Promise<number> {
	let fallos = 0;
	const mal = (m: string) => {
		fallos++;
		console.log("  FALLO importar:", m);
	};
	const app = new App();
	const plugin = { ajustes: porDefecto(), guardar: async () => {} } as unknown as CompendioSrd;
	const todo = new Set<Seccion>(SECCIONES);
	const importar = async (idiomas: Idioma[], sobrescribir = false, secciones = todo): Promise<Informe> => {
		const r = await importarNotas(app as never, plugin, { idiomas: new Set(idiomas), secciones, sobrescribir }, () => {}, () => false);
		const c = r.cuenta;
		console.log(`importar ${idiomas.join("+")}${sobrescribir ? " sobrescribiendo" : ""}: ${c.creada} creadas, ${c.cambiada} cambiadas, ${c.igual} iguales, ${c.saltada} saltadas de ${r.total}${r.errores.length ? `; ${r.errores.length} errores: ${r.errores[0]}` : ""}`);
		if (r.errores.length) mal(r.errores[0] ?? "");
		return r;
	};

	// un fichero del usuario con el mismo nombre que una nota del compendio: no se toca
	await app.vault.createFolder("Compendio SRD");
	await app.vault.createFolder("Compendio SRD/Español");
	await app.vault.createFolder("Compendio SRD/Español/Conjuros");
	await app.vault.create("Compendio SRD/Español/Conjuros/Luz.md", "mis notas sobre la luz");

	let r = await importar(["es"]);
	if (r.cuenta.creada !== r.total - 1 || r.cuenta.saltada !== 1) mal("la primera importacion no crea todo menos la nota del usuario");
	if (app.vault.ficheros.get("Compendio SRD/Español/Conjuros/Luz.md") !== "mis notas sobre la luz") mal("piso la nota del usuario");

	r = await importar(["es"]);
	if (r.cuenta.igual !== r.total - 1 || app.vault.escrituras !== r.total - 1 + 1) mal("volver a importar igual reescribe notas");

	// el usuario cambia una nota
	const aboleth = "Compendio SRD/Español/Criaturas/Aboleth.md";
	app.vault.ficheros.set(aboleth, `${app.vault.ficheros.get(aboleth) ?? ""}\nMi aboleth vive en el lago.\n`);
	// las unidades cambian: se reescribe lo que tiene medidas, salvo lo cambiado
	plugin.ajustes.pies = false;
	r = await importar(["es"]);
	if (r.cuenta.cambiada < 500 || r.cuenta.saltada !== 2) mal("al pasar a metros no se actualizan las notas, o se pisa la cambiada");
	if (!app.vault.ficheros.get(aboleth)?.includes("Mi aboleth")) mal("piso la nota cambiada");
	if (!app.vault.ficheros.get("Compendio SRD/Español/Criaturas/Kraken.md")?.includes(" m,")) mal("el kraken no esta en metros");

	r = await importar(["es"], true);
	if (app.vault.ficheros.get(aboleth)?.includes("Mi aboleth")) mal("sobrescribir no sobrescribe");

	// importar luego solo las criaturas no quita las otras secciones del inicio
	const inicioAntes = app.vault.ficheros.get("Compendio SRD/Español/Inicio.md") ?? "";
	await importar(["es"], false, new Set<Seccion>(["criaturas"]));
	if (app.vault.ficheros.get("Compendio SRD/Español/Inicio.md") !== inicioAntes) mal("importar solo criaturas cambia el inicio");

	// otro idioma despues: sus notas enlazan a las del primero
	r = await importar(["de"]);
	const de = app.vault.ficheros.get("Compendio SRD/Deutsch/Kreaturen/Aboleth.md") ?? "";
	if (!de.includes("[[Compendio SRD/Español/Criaturas/Aboleth|Español]]")) mal("la nota alemana no enlaza a la española");

	// quitar lo que no se ha cambiado
	app.vault.ficheros.set(aboleth, "cambiada otra vez");
	const quitar = await sinCambiar(app as never, plugin);
	const total = Object.keys(plugin.ajustes.huellas).length;
	if (quitar.length !== total - 1) mal(`sin cambiar: ${quitar.length} de ${total}`);
	for (const f of quitar) await app.fileManager.trashFile(f as unknown as TFile);
	const quedan = [...app.vault.ficheros.keys()];
	console.log(`tras quitar quedan: ${quedan.join(", ")}`);
	// "Luz" ya es del plugin: la sobrescribio la importacion con "sobrescribir"
	if (quedan.length !== 1 || quedan[0] !== aboleth) mal("quitar deja notas de mas o de menos");
	return fallos;
}
