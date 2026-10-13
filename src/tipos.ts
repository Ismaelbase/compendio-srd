// Forma de los datos empaquetados (scripts/exportar_plugin.py).

export type Idioma = "es" | "en" | "de" | "fr" | "it";
export const IDIOMAS: readonly Idioma[] = ["es", "en", "de", "fr", "it"];

export type Clase =
	| "criatura" | "conjuro" | "objeto" | "estado"
	| "regla" | "glosario" | "veneno" | "trampa"
	| "clase" | "subclase" | "especie" | "trasfondo" | "dote"
	| "arma" | "armadura" | "herramienta" | "equipo";

/** Los grupos que se eligen al importar (uno por fichero de datos). */
export type Seccion = "criaturas" | "conjuros" | "objetos" | "estados" | "reglas" | "personajes" | "equipo";
export const SECCIONES: readonly Seccion[] = ["criaturas", "conjuros", "objetos", "estados", "reglas", "personajes", "equipo"];

export const SECCION_DE: Record<Clase, Seccion> = {
	criatura: "criaturas", conjuro: "conjuros", objeto: "objetos", estado: "estados",
	regla: "reglas", glosario: "reglas", veneno: "reglas", trampa: "reglas",
	clase: "personajes", subclase: "personajes", especie: "personajes", trasfondo: "personajes", dote: "personajes",
	arma: "equipo", armadura: "equipo", herramienta: "equipo", equipo: "equipo",
};

export interface Bloque {
	t: "p" | "li" | "h" | "tabla" | "campos" | "formula" | "nota" | "columnas" | "recuadro" | "ficha";
	txt?: string;
	/** parrafo de mejora ("nivel": con un espacio de nivel superior; "truco": mejora de truco) */
	sup?: string;
	/** subtitulo en cursiva bajo el titulo ("Dote de origen", "Veneno ingerido") */
	sub?: boolean;
	/** nivel de un titulo dentro de la nota (1 o 2) */
	n?: number;
	titulo?: string | null;
	filas?: string[][];
	/** titulo que abarca varias columnas: [texto, primera, ultima] */
	grupos?: [string, number, number][];
	sin_cabecera?: boolean;
	/** tabla de rotulos a la izquierda ("Atributos basicos de barbaro") */
	vertical?: boolean;
	items?: string[];
	bloques?: Bloque[];
	// ficha de criatura dentro de un conjuro (los conjuros de invocar)
	nombre?: string;
	tipo?: string;
	ca?: string;
	pg?: string;
	vel?: string;
	car?: Caracteristica[];
	rasgos?: [string, string][];
	secciones?: { titulo: string; items: [string, string][] }[];
}

/** [abreviatura, puntuacion, modificador, salvacion] */
export type Caracteristica = [string, number, string, string];

export interface ItemFicha {
	nombre: string;
	bloques: Bloque[];
}

export interface SeccionFicha {
	clave: "rasgos" | "acciones" | "adicionales" | "reacciones" | "legendarias";
	titulo: string;
	intro: string | null;
	items: ItemFicha[];
}

export type CampoCriatura = "ca" | "ini" | "pg" | "vel" | "hab" | "vul" | "res" | "inm" | "equipo" | "sen" | "idi" | "vd";

/** Cambios para pasar el texto de metros a pies: {ruta: [[desde, hasta, texto], ...]} */
export type Pies = Record<string, [number, number, string][]>;

export interface Entrada {
	nombre: string;
	pies?: Pies;
	bloques?: Bloque[];
	// criatura
	grupo?: string;
	tipo?: string;
	campos?: Partial<Record<CampoCriatura, string>>;
	car?: Caracteristica[];
	secciones?: SeccionFicha[];
	// conjuro y objeto
	cabecera?: string;
	tiempo?: string;
	alcance?: string;
	comp?: string;
	dur?: string;
	// reglas, personajes y equipo
	categoria?: string;
	nombre_corto?: string;
	etiqueta?: string | null;
	clase?: string;
}

export interface ComunCriatura {
	ca: number;
	iniciativa: number;
	iniciativa_puntuacion: number;
	pg: number;
	dados_golpe: string;
	car: number[];
	mod: number[];
	salv: number[];
	vd: string;
	px: number;
	px_guarida: number | null;
	bc: number;
	percepcion_pasiva: number;
	tamano: string[];
	tipo: string;
	enjambre: boolean;
	etiquetas: string[];
	alineamiento: string;
}

export interface ComunConjuro {
	nivel: number;
	escuela: string;
	clases: string[];
	ritual: boolean;
	concentracion: boolean;
	componentes: string[];
}

export interface ComunObjeto {
	categoria: string;
	rarezas: string[];
	sintonizacion: boolean;
}

export interface EntradaComun {
	k: Clase;
	id: string;
	c?: ComunCriatura | ComunConjuro | ComunObjeto | Record<string, unknown>;
	cap?: string;
}

export interface Comun {
	version: number;
	entradas: EntradaComun[];
}

export interface Correccion {
	clave: string;
	antes: string;
	despues: string;
	por_que: string;
}

export interface Nombres {
	capitulos: Record<string, string>;
	escuelas: Record<string, string>;
	rarezas: Record<string, string>;
	categorias: Record<string, string>;
}

export interface DatosIdioma {
	entradas: Record<string, Entrada>;
	correcciones: Correccion[];
	atribucion: string;
	nombres: Nombres;
}
