// Diseño de ficha 2024 para Fantasy Statblocks, uno por idioma, sin JavaScript (Fantasy Statblocks avisa al
// importar diseños con codigo). Las lineas de la ficha van ya escritas en las propiedades de cada criatura
// (initiative_text, hp_text, stats_table...) y el diseño solo las coloca. Formato leido en su codigo 4.10.3:
// src/layouts/layout.types.ts y src/layouts/basic 5e/basic5e.ts.
import { datosIdioma } from "./datos";
import { TEXTOS } from "./textos";
import type { Idioma, SeccionFicha } from "./tipos";

export function nombreDiseno(idioma: Idioma): string {
	return `Compendio SRD 2024 (${TEXTOS[idioma].idioma})`;
}

/** Los titulos de seccion de las fichas en cada SRD ("Atributos", "Acciones", "Aktionen"...). */
function titulosSecciones(idioma: Idioma): Record<SeccionFicha["clave"], string> {
	const out: Partial<Record<SeccionFicha["clave"], string>> = {};
	for (const e of Object.values(datosIdioma(idioma).entradas)) {
		for (const s of e.secciones ?? []) if (!out[s.clave]) out[s.clave] = s.titulo.replace(/<[^>]+>/g, "");
	}
	return {
		rasgos: out.rasgos ?? "", acciones: out.acciones ?? "", adicionales: out.adicionales ?? "",
		reacciones: out.reacciones ?? "", legendarias: out.legendarias ?? "",
	};
}

interface Bloque {
	type: string;
	id: string;
	properties: string[];
	[k: string]: unknown;
}

export function disenoFS(idioma: Idioma): { name: string; id: string; blocks: Bloque[] } {
	const T = TEXTOS[idioma];
	const titulos = titulosSecciones(idioma);
	let n = 0;
	const id = () => `compendio-srd-${idioma}-${++n}`;
	const linea = (prop: string, rotulo: string): Bloque => (
		{ type: "property", id: id(), properties: [prop], display: rotulo, conditioned: true, markdown: true }
	);
	const rasgos = (prop: string, titulo: string): Bloque => (
		{ type: "traits", id: id(), properties: [prop], heading: titulo, conditioned: true, dice: true, markdown: true }
	);
	const blocks: Bloque[] = [
		{
			type: "group", id: id(), properties: ["name", "type"], conditioned: true, hasRule: true, nested: [
				{ type: "heading", id: id(), properties: ["name"], conditioned: true, size: 1 },
				{ type: "subheading", id: id(), properties: ["type"], conditioned: true, separator: ", " },
			],
		},
		{
			type: "group", id: id(), properties: ["ac", "initiative_text", "hp_text", "speed"], conditioned: true, hasRule: true,
			nested: [
				{
					type: "inline", id: id(), properties: [], conditioned: true, nested: [
						linea("ac", T.ficha.ca),
						linea("initiative_text", T.ficha.ini),
					],
				},
				linea("hp_text", T.ficha.pg),
				linea("speed", T.ficha.vel),
			],
		},
		{ type: "text", id: id(), properties: ["stats_table"], text: null, conditioned: true, markdown: true, hasRule: true },
		{
			type: "group", id: id(), conditioned: true, hasRule: true,
			properties: ["skills_text", "damage_vulnerabilities", "damage_resistances", "immunities_text", "gear", "senses", "languages", "cr_text"],
			nested: [
				linea("skills_text", T.ficha.hab),
				linea("damage_vulnerabilities", T.ficha.vul),
				linea("damage_resistances", T.ficha.res),
				linea("immunities_text", T.ficha.inm),
				linea("gear", T.ficha.equipo),
				linea("senses", T.ficha.sen),
				linea("languages", T.ficha.idi),
				linea("cr_text", T.ficha.vd),
			],
		},
		rasgos("traits", titulos.rasgos),
		rasgos("actions", titulos.acciones),
		rasgos("bonus_actions", titulos.adicionales),
		rasgos("reactions", titulos.reacciones),
		{
			type: "group", id: id(), properties: ["legendary_description", "legendary_actions"], heading: titulos.legendarias,
			conditioned: true, nested: [
				{ type: "text", id: id(), properties: ["legendary_description"], text: null, conditioned: true, markdown: true },
				{ type: "traits", id: id(), properties: ["legendary_actions"], conditioned: true, dice: true, markdown: true },
			],
		},
	];
	return { name: nombreDiseno(idioma), id: `compendio-srd-2024-${idioma}`, blocks };
}
