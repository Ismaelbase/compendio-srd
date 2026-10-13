// Lo que se escribe en las notas, en el idioma de cada nota. Los rotulos de las fichas son los de cada SRD.
import type { CampoCriatura, Clase, Idioma } from "./tipos";

export type Propiedad =
	| "vd" | "px" | "ca" | "pg" | "iniciativa" | "tipo" | "grupo"
	| "nivel" | "escuela" | "clases" | "ritual" | "concentracion"
	| "categoria" | "rareza" | "sintonizacion" | "precio" | "capitulo" | "clase";

export interface Textos {
	/** nombre de la carpeta del idioma, en su propio idioma */
	idioma: string;
	inicio: string;
	creditos: string;
	/** carpeta de cada clase de entrada (con "/" si va dentro de otra) */
	carpetas: Record<Clase, string>;
	/** carpetas que agrupan otras (personajes y equipo) */
	grupos: { personajes: string; equipo: string };
	/** nombre de cada clase de entrada en singular (buscador, etiquetas) */
	clases: Record<Clase, string>;
	ficha: Record<CampoCriatura | "mod" | "salv", string>;
	conjuro: { tiempo: string; alcance: string; comp: string; dur: string };
	/** dos puntos tras un rotulo ("Alcance:", en frances "Portée :") */
	dosPuntos: string;
	/** lo que cierra el nombre de un rasgo ("Anfibio.", en aleman "Amphibisch:") */
	finRasgo: string;
	props: Record<Propiedad, string>;
	px: string;
	precio: string;
	si: string;
	trucos: string;
	nivelConjuro: (n: number) => string;
	rarezaVariable: string;
	cabeceras: {
		criaturas: [string, string, string];
		conjuros: [string, string, string, string, string];
		objetos: [string, string, string];
	};
	otrosIdiomas: string;
	subclases: string;
	/** etiqueta de las notas indice */
	etiquetaIndice: string;
	inicioIntro: string;
	inicioEncuentro: string;
	inicioCreditos: string;
	licencia: string;
	cambios: string;
	cambiosIntro: string;
	cambioNotas: string;
	cambioPies: string;
	cambiosCasa: string[];
	erratas: string;
	erratasIntro: string;
	/** tras la tabla de erratas, si las notas van en pies */
	erratasMetros: string;
	cabeceraErratas: [string, string, string];
	hechoCon: string;
}

const ES: Textos = {
	idioma: "Español",
	inicio: "Inicio",
	creditos: "Créditos",
	carpetas: {
		criatura: "Criaturas", conjuro: "Conjuros", objeto: "Objetos mágicos", estado: "Estados",
		regla: "Reglas", glosario: "Glosario", veneno: "Venenos", trampa: "Trampas",
		clase: "Personajes/Clases", subclase: "Personajes/Subclases", especie: "Personajes/Especies",
		trasfondo: "Personajes/Trasfondos", dote: "Personajes/Dotes",
		arma: "Equipo/Armas", armadura: "Equipo/Armaduras", herramienta: "Equipo/Herramientas",
		equipo: "Equipo/Equipo de aventureros",
	},
	grupos: { personajes: "Personajes", equipo: "Equipo" },
	clases: {
		criatura: "Criatura", conjuro: "Conjuro", objeto: "Objeto mágico", estado: "Estado",
		regla: "Regla", glosario: "Glosario", veneno: "Veneno", trampa: "Trampa",
		clase: "Clase", subclase: "Subclase", especie: "Especie", trasfondo: "Trasfondo", dote: "Dote",
		arma: "Arma", armadura: "Armadura", herramienta: "Herramienta", equipo: "Equipo",
	},
	ficha: {
		ca: "CA", ini: "Iniciativa", pg: "PG", vel: "Velocidad", hab: "Habilidades", vul: "Vulnerabilidades",
		res: "Resistencias", inm: "Inmunidades", equipo: "Equipo", sen: "Sentidos", idi: "Idiomas", vd: "VD",
		mod: "MOD.", salv: "SALV.",
	},
	conjuro: { tiempo: "Tiempo de lanzamiento", alcance: "Alcance", comp: "Componentes", dur: "Duración" },
	dosPuntos: ":",
	finRasgo: ".",
	props: {
		vd: "vd", px: "px", ca: "ca", pg: "pg", iniciativa: "iniciativa", tipo: "tipo", grupo: "grupo",
		nivel: "nivel", escuela: "escuela", clases: "clases", ritual: "ritual", concentracion: "concentración",
		categoria: "categoría", rareza: "rareza", sintonizacion: "sintonización", precio: "precio",
		capitulo: "capítulo", clase: "clase",
	},
	px: "PX",
	precio: "Precio",
	si: "Sí",
	trucos: "Trucos",
	nivelConjuro: (n) => `Nivel ${n}`,
	rarezaVariable: "Rareza variable",
	cabeceras: {
		criaturas: ["Criatura", "Tipo", "PX"],
		conjuros: ["Conjuro", "Escuela", "Clases", "Concentración", "Ritual"],
		objetos: ["Objeto", "Categoría", "Sintonización"],
	},
	otrosIdiomas: "Otros idiomas",
	etiquetaIndice: "srd/índice",
	subclases: "Subclases",
	inicioIntro: "El texto oficial del SRD 5.2.1 en español, una nota por entrada y enlazadas entre sí.",
	inicioEncuentro: "Para preparar un combate, abre el encuentro desde la paleta de comandos: calcula el presupuesto de PX de las reglas de 2024 y manda las criaturas a Initiative Tracker.",
	inicioCreditos: "Licencia y cambios respecto al SRD",
	licencia: "Licencia",
	cambios: "Cambios respecto al SRD 5.2.1",
	cambiosIntro: "Estas notas llevan el texto del SRD 5.2.1 en español con estos cambios:",
	cambioNotas: "Cada entrada va en su propia nota, con enlaces a las demás y propiedades para buscar y ordenar; las tablas y los recuadros van en la nota que los cita.",
	cambioPies: "Las medidas están en pies y libras, con las cifras del SRD en inglés.",
	cambiosCasa: [
		"Se dice DM (Dungeon Master) donde el SRD dice GM.",
		"Los nombres de los estados van con mayúscula (quedar Cegado, el estado de Envenenado).",
	],
	erratas: "Erratas corregidas",
	erratasIntro: "Donde el SRD en español no dice lo mismo que el SRD en inglés, se ha corregido con el inglés:",
	erratasMetros: "Las cifras de la tabla están en metros, como en el SRD en español.",
	cabeceraErratas: ["Nota", "Decía", "Dice ahora"],
	hechoCon: "Notas creadas con el plugin Compendio SRD 2024.",
};

const EN: Textos = {
	idioma: "English",
	inicio: "Home",
	creditos: "Credits",
	carpetas: {
		criatura: "Creatures", conjuro: "Spells", objeto: "Magic Items", estado: "Conditions",
		regla: "Rules", glosario: "Glossary", veneno: "Poisons", trampa: "Traps",
		clase: "Characters/Classes", subclase: "Characters/Subclasses", especie: "Characters/Species",
		trasfondo: "Characters/Backgrounds", dote: "Characters/Feats",
		arma: "Equipment/Weapons", armadura: "Equipment/Armor", herramienta: "Equipment/Tools",
		equipo: "Equipment/Adventuring Gear",
	},
	grupos: { personajes: "Characters", equipo: "Equipment" },
	clases: {
		criatura: "Creature", conjuro: "Spell", objeto: "Magic item", estado: "Condition",
		regla: "Rule", glosario: "Glossary", veneno: "Poison", trampa: "Trap",
		clase: "Class", subclase: "Subclass", especie: "Species", trasfondo: "Background", dote: "Feat",
		arma: "Weapon", armadura: "Armor", herramienta: "Tool", equipo: "Gear",
	},
	ficha: {
		ca: "AC", ini: "Initiative", pg: "HP", vel: "Speed", hab: "Skills", vul: "Vulnerabilities",
		res: "Resistances", inm: "Immunities", equipo: "Gear", sen: "Senses", idi: "Languages", vd: "CR",
		mod: "MOD", salv: "SAVE",
	},
	conjuro: { tiempo: "Casting Time", alcance: "Range", comp: "Components", dur: "Duration" },
	dosPuntos: ":",
	finRasgo: ".",
	props: {
		vd: "cr", px: "xp", ca: "ac", pg: "hp", iniciativa: "initiative", tipo: "type", grupo: "group",
		nivel: "level", escuela: "school", clases: "classes", ritual: "ritual", concentracion: "concentration",
		categoria: "category", rareza: "rarity", sintonizacion: "attunement", precio: "cost",
		capitulo: "chapter", clase: "class",
	},
	px: "XP",
	precio: "Cost",
	si: "Yes",
	trucos: "Cantrips",
	nivelConjuro: (n) => `Level ${n}`,
	rarezaVariable: "Rarity Varies",
	cabeceras: {
		criaturas: ["Creature", "Type", "XP"],
		conjuros: ["Spell", "School", "Classes", "Concentration", "Ritual"],
		objetos: ["Item", "Category", "Attunement"],
	},
	otrosIdiomas: "Other languages",
	etiquetaIndice: "srd/index",
	subclases: "Subclasses",
	inicioIntro: "The official text of the SRD 5.2.1 in English, one note per entry, linked to each other.",
	inicioEncuentro: "To prepare a fight, open the encounter builder from the command palette: it works out the 2024 XP budget and sends the creatures to Initiative Tracker.",
	inicioCreditos: "License and changes from the SRD",
	licencia: "License",
	cambios: "Changes from the SRD 5.2.1",
	cambiosIntro: "These notes contain the text of the SRD 5.2.1 in English with these changes:",
	cambioNotas: "Each entry is in its own note, with links to the others and properties to search and sort; tables and sidebars are in the note that refers to them.",
	cambioPies: "",
	cambiosCasa: [
		"DM and Dungeon Master are used where the SRD says GM and Game Master.",
		"Em dashes are replaced by parentheses, commas or colons.",
		"Dice expressions use a minus sign (1d4 − 1).",
	],
	erratas: "Corrected errata",
	erratasIntro: "These typos in the SRD 5.2.1 in English have been corrected:",
	erratasMetros: "",
	cabeceraErratas: ["Note", "Was", "Now"],
	hechoCon: "Notes created with the Compendio SRD 2024 plugin.",
};

const DE: Textos = {
	idioma: "Deutsch",
	inicio: "Start",
	creditos: "Lizenz",
	carpetas: {
		criatura: "Kreaturen", conjuro: "Zauber", objeto: "Magische Gegenstände", estado: "Zustände",
		regla: "Regeln", glosario: "Glossar", veneno: "Gifte", trampa: "Fallen",
		clase: "Charaktere/Klassen", subclase: "Charaktere/Unterklassen", especie: "Charaktere/Spezies",
		trasfondo: "Charaktere/Hintergründe", dote: "Charaktere/Talente",
		arma: "Ausrüstung/Waffen", armadura: "Ausrüstung/Rüstungen", herramienta: "Ausrüstung/Werkzeuge",
		equipo: "Ausrüstung/Abenteurerausrüstung",
	},
	grupos: { personajes: "Charaktere", equipo: "Ausrüstung" },
	clases: {
		criatura: "Kreatur", conjuro: "Zauber", objeto: "Magischer Gegenstand", estado: "Zustand",
		regla: "Regel", glosario: "Glossar", veneno: "Gift", trampa: "Falle",
		clase: "Klasse", subclase: "Unterklasse", especie: "Spezies", trasfondo: "Hintergrund", dote: "Talent",
		arma: "Waffe", armadura: "Rüstung", herramienta: "Werkzeug", equipo: "Ausrüstung",
	},
	ficha: {
		ca: "RK", ini: "Initiative", pg: "TP", vel: "Bewegungsrate", hab: "Fertigkeiten", vul: "Anfälligkeiten",
		res: "Resistenzen", inm: "Immunitäten", equipo: "Ausrüstung", sen: "Sinne", idi: "Sprachen", vd: "HG",
		mod: "MOD", salv: "RW",
	},
	conjuro: { tiempo: "Zeitaufwand", alcance: "Reichweite", comp: "Komponenten", dur: "Wirkungsdauer" },
	dosPuntos: ":",
	finRasgo: ":",
	props: {
		vd: "hg", px: "ep", ca: "rk", pg: "tp", iniciativa: "initiative", tipo: "typ", grupo: "gruppe",
		nivel: "grad", escuela: "schule", clases: "klassen", ritual: "ritual", concentracion: "konzentration",
		categoria: "kategorie", rareza: "seltenheit", sintonizacion: "einstimmung", precio: "kosten",
		capitulo: "kapitel", clase: "klasse",
	},
	px: "EP",
	precio: "Kosten",
	si: "Ja",
	trucos: "Zaubertricks",
	nivelConjuro: (n) => `${n}. Grad`,
	rarezaVariable: "Seltenheit variiert",
	cabeceras: {
		criaturas: ["Kreatur", "Typ", "EP"],
		conjuros: ["Zauber", "Schule", "Klassen", "Konzentration", "Ritual"],
		objetos: ["Gegenstand", "Kategorie", "Einstimmung"],
	},
	otrosIdiomas: "Andere Sprachen",
	etiquetaIndice: "srd/index",
	subclases: "Unterklassen",
	inicioIntro: "Der offizielle Text des SRD 5.2.1 auf Deutsch, eine Notiz pro Eintrag, untereinander verlinkt.",
	inicioEncuentro: "Um einen Kampf vorzubereiten, öffne die Begegnung über die Befehlspalette: Sie berechnet das EP-Budget nach den Regeln von 2024 und schickt die Kreaturen an Initiative Tracker.",
	inicioCreditos: "Lizenz und Änderungen gegenüber dem SRD",
	licencia: "Lizenz",
	cambios: "Änderungen gegenüber dem SRD 5.2.1",
	cambiosIntro: "Diese Notizen enthalten den Text des SRD 5.2.1 auf Deutsch mit diesen Änderungen:",
	cambioNotas: "Jeder Eintrag steht in einer eigenen Notiz, mit Links zu den anderen und Eigenschaften zum Suchen und Sortieren; Tabellen und Kästen stehen in der Notiz, die auf sie verweist.",
	cambioPies: "Die Maße sind in Fuß und Pfund angegeben, mit den Zahlen des englischen SRD.",
	cambiosCasa: [],
	erratas: "Korrigierte Fehler",
	erratasIntro: "Wo das deutsche SRD nicht dasselbe sagt wie das englische, wurde es nach dem englischen korrigiert:",
	erratasMetros: "Die Zahlen in der Tabelle sind in Metern angegeben, wie im deutschen SRD.",
	cabeceraErratas: ["Notiz", "Vorher", "Jetzt"],
	hechoCon: "Notizen erstellt mit dem Plugin Compendio SRD 2024.",
};

const FR: Textos = {
	idioma: "Français",
	inicio: "Accueil",
	creditos: "Crédits",
	carpetas: {
		criatura: "Créatures", conjuro: "Sorts", objeto: "Objets magiques", estado: "États",
		regla: "Règles", glosario: "Glossaire", veneno: "Poisons", trampa: "Pièges",
		clase: "Personnages/Classes", subclase: "Personnages/Sous-classes", especie: "Personnages/Espèces",
		trasfondo: "Personnages/Historiques", dote: "Personnages/Dons",
		arma: "Équipement/Armes", armadura: "Équipement/Armures", herramienta: "Équipement/Outils",
		equipo: "Équipement/Matériel d’aventurier",
	},
	grupos: { personajes: "Personnages", equipo: "Équipement" },
	clases: {
		criatura: "Créature", conjuro: "Sort", objeto: "Objet magique", estado: "État",
		regla: "Règle", glosario: "Glossaire", veneno: "Poison", trampa: "Piège",
		clase: "Classe", subclase: "Sous-classe", especie: "Espèce", trasfondo: "Historique", dote: "Don",
		arma: "Arme", armadura: "Armure", herramienta: "Outil", equipo: "Matériel",
	},
	ficha: {
		ca: "CA", ini: "Initiative", pg: "Pv", vel: "Vitesse", hab: "Compétences", vul: "Vulnérabilités",
		res: "Résistances", inm: "Immunités", equipo: "Équipement", sen: "Sens", idi: "Langues", vd: "FP",
		mod: "MOD", salv: "JS",
	},
	conjuro: { tiempo: "Temps d’incantation", alcance: "Portée", comp: "Composantes", dur: "Durée" },
	dosPuntos: "\u00a0:",
	finRasgo: ".",
	props: {
		vd: "fp", px: "px", ca: "ca", pg: "pv", iniciativa: "initiative", tipo: "type", grupo: "groupe",
		nivel: "niveau", escuela: "école", clases: "classes", ritual: "rituel", concentracion: "concentration",
		categoria: "catégorie", rareza: "rareté", sintonizacion: "harmonisation", precio: "prix",
		capitulo: "chapitre", clase: "classe",
	},
	px: "PX",
	precio: "Prix",
	si: "Oui",
	trucos: "Sorts mineurs",
	nivelConjuro: (n) => `Niveau ${n}`,
	rarezaVariable: "Rareté variable",
	cabeceras: {
		criaturas: ["Créature", "Type", "PX"],
		conjuros: ["Sort", "École", "Classes", "Concentration", "Rituel"],
		objetos: ["Objet", "Catégorie", "Harmonisation"],
	},
	otrosIdiomas: "Autres langues",
	etiquetaIndice: "srd/index",
	subclases: "Sous-classes",
	inicioIntro: "Le texte officiel du SRD 5.2.1 en français, une note par entrée, reliées entre elles.",
	inicioEncuentro: "Pour préparer un combat, ouvrez la rencontre depuis la palette de commandes\u00a0: elle calcule le budget de PX des règles de 2024 et envoie les créatures à Initiative Tracker.",
	inicioCreditos: "Licence et modifications par rapport au SRD",
	licencia: "Licence",
	cambios: "Modifications par rapport au SRD 5.2.1",
	cambiosIntro: "Ces notes reprennent le texte du SRD 5.2.1 en français avec ces modifications\u00a0:",
	cambioNotas: "Chaque entrée a sa propre note, avec des liens vers les autres et des propriétés pour chercher et trier\u00a0; les tableaux et les encadrés sont dans la note qui y renvoie.",
	cambioPies: "Les mesures sont en pieds et en livres, avec les chiffres du SRD en anglais.",
	cambiosCasa: [],
	erratas: "Erreurs corrigées",
	erratasIntro: "Là où le SRD en français ne dit pas la même chose que le SRD en anglais, il a été corrigé d’après l’anglais\u00a0:",
	erratasMetros: "Les chiffres du tableau sont en mètres, comme dans le SRD en français.",
	cabeceraErratas: ["Note", "Avant", "Maintenant"],
	hechoCon: "Notes créées avec le plugin Compendio SRD 2024.",
};

const IT: Textos = {
	idioma: "Italiano",
	inicio: "Inizio",
	creditos: "Crediti",
	carpetas: {
		criatura: "Creature", conjuro: "Incantesimi", objeto: "Oggetti magici", estado: "Condizioni",
		regla: "Regole", glosario: "Glossario", veneno: "Veleni", trampa: "Trappole",
		clase: "Personaggi/Classi", subclase: "Personaggi/Sottoclassi", especie: "Personaggi/Specie",
		trasfondo: "Personaggi/Background", dote: "Personaggi/Talenti",
		arma: "Equipaggiamento/Armi", armadura: "Equipaggiamento/Armature", herramienta: "Equipaggiamento/Strumenti",
		equipo: "Equipaggiamento/Equipaggiamento d'avventura",
	},
	grupos: { personajes: "Personaggi", equipo: "Equipaggiamento" },
	clases: {
		criatura: "Creatura", conjuro: "Incantesimo", objeto: "Oggetto magico", estado: "Condizione",
		regla: "Regola", glosario: "Glossario", veneno: "Veleno", trampa: "Trappola",
		clase: "Classe", subclase: "Sottoclasse", especie: "Specie", trasfondo: "Background", dote: "Talento",
		arma: "Arma", armadura: "Armatura", herramienta: "Strumento", equipo: "Equipaggiamento",
	},
	ficha: {
		ca: "CA", ini: "Iniziativa", pg: "PF", vel: "Velocità", hab: "Abilità", vul: "Vulnerabilità",
		res: "Resistenze", inm: "Immunità", equipo: "Attrezzatura", sen: "Sensi", idi: "Lingue", vd: "GS",
		mod: "MOD", salv: "SALV",
	},
	conjuro: { tiempo: "Tempo di lancio", alcance: "Gittata", comp: "Componenti", dur: "Durata" },
	dosPuntos: ":",
	finRasgo: ".",
	props: {
		vd: "gs", px: "pe", ca: "ca", pg: "pf", iniciativa: "iniziativa", tipo: "tipo", grupo: "gruppo",
		nivel: "livello", escuela: "scuola", clases: "classi", ritual: "rituale", concentracion: "concentrazione",
		categoria: "categoria", rareza: "rarità", sintonizacion: "sintonia", precio: "costo",
		capitulo: "capitolo", clase: "classe",
	},
	px: "PE",
	precio: "Costo",
	si: "Sì",
	trucos: "Trucchetti",
	nivelConjuro: (n) => `Livello ${n}`,
	rarezaVariable: "Rarità variabile",
	cabeceras: {
		criaturas: ["Creatura", "Tipo", "PE"],
		conjuros: ["Incantesimo", "Scuola", "Classi", "Concentrazione", "Rituale"],
		objetos: ["Oggetto", "Categoria", "Sintonia"],
	},
	otrosIdiomas: "Altre lingue",
	etiquetaIndice: "srd/indice",
	subclases: "Sottoclassi",
	inicioIntro: "Il testo ufficiale dell'SRD 5.2.1 in italiano, una nota per voce, collegate tra loro.",
	inicioEncuentro: "Per preparare un combattimento, apri l'incontro dalla tavolozza dei comandi: calcola il budget di PE delle regole del 2024 e invia le creature a Initiative Tracker.",
	inicioCreditos: "Licenza e modifiche rispetto all'SRD",
	licencia: "Licenza",
	cambios: "Modifiche rispetto all'SRD 5.2.1",
	cambiosIntro: "Queste note riportano il testo dell'SRD 5.2.1 in italiano con queste modifiche:",
	cambioNotas: "Ogni voce ha la sua nota, con collegamenti alle altre e proprietà per cercare e ordinare; le tabelle e i riquadri sono nella nota che li cita.",
	cambioPies: "Le misure sono in piedi e libbre, con i numeri dell'SRD in inglese.",
	cambiosCasa: [],
	erratas: "Errori corretti",
	erratasIntro: "Dove l'SRD in italiano non dice la stessa cosa dell'SRD in inglese, è stato corretto secondo l'inglese:",
	erratasMetros: "I numeri della tabella sono in metri, come nell'SRD in italiano.",
	cabeceraErratas: ["Nota", "Prima", "Ora"],
	hechoCon: "Note create con il plugin Compendio SRD 2024.",
};

export const TEXTOS: Record<Idioma, Textos> = { es: ES, en: EN, de: DE, fr: FR, it: IT };
