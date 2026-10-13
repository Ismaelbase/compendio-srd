// Los tres ejemplos del SRD ("Encuentros de combate", paso 3) tienen que dar la dificultad que dice el texto.
import { comunDe } from "../src/datos";
import { bloqueEncounter, calcular, criaturasIT, tablaPresupuesto } from "../src/encuentro";
import { IDIOMAS } from "../src/tipos";

export function pruebasEncuentro(): number {
	let fallos = 0;
	const mal = (m: string) => {
		fallos++;
		console.log("  FALLO encuentro:", m);
	};
	for (const l of IDIOMAS) {
		const t = tablaPresupuesto(l);
		if (t.porNivel.size !== 20) mal(`${l}: la tabla tiene ${t.porNivel.size} niveles`);
		const n20 = t.porNivel.get(20);
		if (!n20 || n20.join() !== "6400,13200,22000") mal(`${l}: nivel 20 = ${n20?.join()}`);
		console.log(`encuentro ${l}: ${t.etiquetas.join(" / ")}; consejos: ${t.consejos.join(" / ")}`);
		if (t.consejos.some((c) => !c) || t.etiquetas.some((c) => !c)) mal(`${l}: faltan rotulos`);
	}
	const t = tablaPresupuesto("es");
	const ejemplos: [string, number, number, [string, number][], number, number][] = [
		["1", 4, 1, [["criatura/bugbear-warrior", 1]], 200, 0],
		["1b", 4, 1, [["criatura/giant-rat", 6]], 150, 0],
		["2", 5, 3, [["criatura/druid", 2], ["criatura/stirge", 9]], 1125, 1],
		["2b", 5, 3, [["criatura/wight", 1], ["criatura/warhorse-skeleton", 1], ["criatura/skeleton", 6]], 1100, 1],
		["3", 6, 15, [["criatura/adult-red-dragon", 2], ["criatura/fire-giant", 2]], 46000, 2],
	];
	for (const [nombre, n, nivel, criaturas, total, dif] of ejemplos) {
		for (const [k] of criaturas) if (!comunDe(k)) mal(`ejemplo ${nombre}: no existe ${k}`);
		const r = calcular([{ n, nivel }], criaturas.map(([clave, m]) => ({ clave, n: m })), t);
		if (r.total !== total || r.dificultad !== dif) mal(`ejemplo ${nombre}: ${r.total} PX, dificultad ${r.dificultad} (esperado ${total}, ${dif})`);
		console.log(`ejemplo ${nombre}: ${r.total} PX de ${r.presupuesto.join("/")}, dificultad ${r.dificultad}, avisos ${r.avisos.join(",") || "-"}`);
	}
	const r = calcular([{ n: 4, nivel: 1 }], [{ clave: "criatura/ogre", n: 1 }, { clave: "criatura/rat", n: 9 }], t);
	if (!r.avisos.includes("poderosas") || !r.avisos.includes("muchas") || !r.avisos.includes("vd0")) mal(`avisos: ${r.avisos.join(",")}`);
	const it = criaturasIT([{ clave: "criatura/goblin-warrior", n: 3 }], "es");
	if (it.length !== 3 || !it[0]?.name || it[0].modifier === undefined) mal(`initiative tracker: ${JSON.stringify(it[0])}`);
	console.log(JSON.stringify(it[0]));
	console.log(bloqueEncounter("Prueba", [{ clave: "criatura/goblin-warrior", n: 3 }, { clave: "criatura/aboleth", n: 1 }], "es"));
	return fallos;
}
