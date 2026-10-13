// Textos de la interfaz, en el idioma de Obsidian (ingles si no es uno de los cinco).
import { getLanguage } from "obsidian";
import type { Idioma, Seccion } from "./tipos";

interface Ui {
	cmdImportar: string;
	bienvenida: string;
	cmdBuscar: string;
	cmdEncuentro: string;
	cmdAnadir: string;
	cmdQuitar: string;
	cmdEnviar: string;
	cmdCopiar: string;
	cmdInsertar: string;
	usarIT: string;
	sinNivel: string;
	jugadoresIT: string;
	importarTitulo: string;
	importarIntro: string;
	idiomas: string;
	queImportar: string;
	secciones: Record<Seccion, string>;
	carpeta: string;
	carpetaDesc: string;
	unidades: string;
	unidadesDesc: string;
	pies: string;
	metros: string;
	sobrescribir: string;
	sobrescribirDesc: string;
	importar: string;
	cancelar: string;
	cerrar: string;
	preparando: string;
	escribiendo: (n: number, total: number) => string;
	resumen: (creadas: number, cambiadas: number, iguales: number, saltadas: number) => string;
	saltadasDesc: string;
	cancelado: string;
	errorEscribir: (ruta: string, msg: string) => string;
	nadaElegido: string;
	idiomaPrincipal: string;
	idiomaPrincipalDesc: string;
	fantasy: string;
	fantasyDesc: string;
	estados: string;
	estadosDesc: string;
	reimportar: string;
	buscarAyuda: string;
	creada: (nombre: string) => string;
	encuentro: string;
	grupo: string;
	personajes: string;
	nivel: string;
	anadirPersonajes: string;
	criaturas: string;
	anadirCriatura: string;
	sinCriaturas: string;
	quitar: string;
	presupuesto: string;
	gasto: string;
	porEncima: (n: string) => string;
	consejos: string;
	avisoMuchas: string;
	avisoVd0: string;
	avisoPerfiles: string;
	avisoPoderosas: string;
	enviarIT: string;
	copiarBloque: string;
	insertarBloque: string;
	vaciar: string;
	itNoEsta: string;
	enviado: (n: number) => string;
	copiado: string;
	sinNota: string;
	noEsCriatura: string;
	anadida: (nombre: string) => string;
	quitarTitulo: string;
	quitarTexto: (n: number) => string;
	quitarNada: string;
	quitado: (n: number) => string;
	nombreEncuentro: string;
}

const EN: Ui = {
	usarIT: "Use the Initiative Tracker players",
	sinNivel: "no level",
	jugadoresIT: "Change them in the Initiative Tracker settings.",
	cmdEnviar: "Send the encounter to Initiative Tracker",
	cmdCopiar: "Copy the encounter block",
	cmdInsertar: "Insert the encounter block",
	cmdImportar: "Import the SRD",
	bienvenida: "Compendio SRD 2024 is ready. The notes are created when you import the SRD.",
	cmdBuscar: "Search the compendium",
	cmdEncuentro: "Open the encounter builder",
	cmdAnadir: "Add this creature to the encounter",
	cmdQuitar: "Remove the compendium notes you have not edited",
	importarTitulo: "Import the SRD 5.2.1",
	importarIntro: "Creates one note per entry, linked to each other. Notes you have edited are left as they are.",
	idiomas: "Languages",
	queImportar: "What to import",
	secciones: {
		criaturas: "Creatures",
		conjuros: "Spells",
		objetos: "Magic items",
		estados: "Conditions",
		reglas: "Rules, glossary, poisons and traps",
		personajes: "Classes, species, backgrounds and feats",
		equipo: "Equipment",
	},
	carpeta: "Folder",
	carpetaDesc: "The compendium goes in this folder, one subfolder per language.",
	unidades: "Units",
	unidadesDesc: "Feet and pounds, or the meters and kilograms of the SRD in Spanish, German, French and Italian (the English SRD is always in feet). Import again to change notes you already have.",
	pies: "Feet and pounds",
	metros: "Meters and kilograms",
	sobrescribir: "Overwrite notes I have edited",
	sobrescribirDesc: "Off: a note you have changed since it was imported is skipped.",
	importar: "Import",
	cancelar: "Cancel",
	cerrar: "Close",
	preparando: "Preparing the notes…",
	escribiendo: (n, total) => `Writing ${n} of ${total}…`,
	resumen: (c, m, i, s) => `${c} created, ${m} updated, ${i} unchanged, ${s} skipped.`,
	saltadasDesc: "Skipped notes are the ones you have edited, or files with the same name that the plugin did not create.",
	cancelado: "Import canceled.",
	errorEscribir: (r, m) => `Could not write ${r}: ${m}`,
	nadaElegido: "Choose at least one language and one section.",
	idiomaPrincipal: "Main language",
	idiomaPrincipalDesc: "Used by the search and the encounter builder, and selected by default when you import.",
	fantasy: "Fantasy Statblocks properties",
	fantasyDesc: "Adds the stat block to the properties of each creature note so Fantasy Statblocks can read it (turn on its option to parse frontmatter for creatures). The import also saves a 2024 stat block layout in the language folder (a .json file): import it in Fantasy Statblocks, Layouts, Import From JSON.",
	estados: "Link conditions",
	estadosDesc: "Links the first mention of each condition in a note to the condition's note. Import again to apply.",
	reimportar: "Import again to apply the change to notes you already have.",
	buscarAyuda: "Search the SRD 5.2.1",
	creada: (n) => `Created ${n}.`,
	encuentro: "Encounter",
	grupo: "Party",
	personajes: "Characters",
	nivel: "Level",
	anadirPersonajes: "Add characters of another level",
	criaturas: "Creatures",
	anadirCriatura: "Add creature",
	sinCriaturas: "No creatures yet. Add them here or from a creature note.",
	quitar: "Remove",
	presupuesto: "Budget",
	gasto: "Spent",
	porEncima: (n) => `${n} over the high budget`,
	consejos: "Troubleshooting",
	avisoMuchas: "More than two creatures per character.",
	avisoVd0: "There are creatures with CR 0.",
	avisoPerfiles: "More than three different stat blocks.",
	avisoPoderosas: "A creature's CR is higher than the party's level.",
	enviarIT: "Send to Initiative Tracker",
	copiarBloque: "Copy encounter block",
	insertarBloque: "Insert into note",
	vaciar: "Clear",
	itNoEsta: "Initiative Tracker is not turned on. Use the encounter block instead.",
	enviado: (n) => (n === 1 ? "Sent 1 creature to Initiative Tracker." : `Sent ${n} creatures to Initiative Tracker.`),
	copiado: "Encounter block copied.",
	sinNota: "Open a note in edit mode to insert the block.",
	noEsCriatura: "This note is not a creature from the compendium.",
	anadida: (n) => `${n} added to the encounter.`,
	quitarTitulo: "Remove compendium notes",
	quitarTexto: (n) => `${n} notes were imported and have not been edited since. They will go to the trash.`,
	quitarNada: "There are no unedited compendium notes to remove.",
	quitado: (n) => `${n} notes moved to the trash.`,
	nombreEncuentro: "Encounter",
};

const ES: Ui = {
	usarIT: "Usar los jugadores de Initiative Tracker",
	sinNivel: "sin nivel",
	jugadoresIT: "Se cambian en los ajustes de Initiative Tracker.",
	cmdEnviar: "Mandar el encuentro a Initiative Tracker",
	cmdCopiar: "Copiar el bloque encounter",
	cmdInsertar: "Insertar el bloque encounter",
	cmdImportar: "Importar el SRD",
	bienvenida: "Compendio SRD 2024 está listo. Las notas se crean al importar el SRD.",
	cmdBuscar: "Buscar en el compendio",
	cmdEncuentro: "Abrir el encuentro",
	cmdAnadir: "Añadir esta criatura al encuentro",
	cmdQuitar: "Quitar las notas del compendio que no has cambiado",
	importarTitulo: "Importar el SRD 5.2.1",
	importarIntro: "Crea una nota por entrada, enlazadas entre sí. Las notas que hayas cambiado se quedan como están.",
	idiomas: "Idiomas",
	queImportar: "Qué importar",
	secciones: {
		criaturas: "Criaturas",
		conjuros: "Conjuros",
		objetos: "Objetos mágicos",
		estados: "Estados",
		reglas: "Reglas, glosario, venenos y trampas",
		personajes: "Clases, especies, trasfondos y dotes",
		equipo: "Equipo",
	},
	carpeta: "Carpeta",
	carpetaDesc: "El compendio va en esta carpeta, con una subcarpeta por idioma.",
	unidades: "Unidades",
	unidadesDesc: "Pies y libras, o los metros y kilos del SRD en español, alemán, francés e italiano (el SRD en inglés va siempre en pies). Vuelve a importar para cambiar las notas que ya tienes.",
	pies: "Pies y libras",
	metros: "Metros y kilos",
	sobrescribir: "Sobrescribir las notas que he cambiado",
	sobrescribirDesc: "Apagado: una nota que hayas cambiado desde que se importó no se toca.",
	importar: "Importar",
	cancelar: "Cancelar",
	cerrar: "Cerrar",
	preparando: "Preparando las notas…",
	escribiendo: (n, total) => `Escribiendo ${n} de ${total}…`,
	resumen: (c, m, i, s) => `${c} creadas, ${m} actualizadas, ${i} sin cambios, ${s} sin tocar.`,
	saltadasDesc: "Las que no se tocan son las que has cambiado, o ficheros con el mismo nombre que no creó el plugin.",
	cancelado: "Importación cancelada.",
	errorEscribir: (r, m) => `No se pudo escribir ${r}: ${m}`,
	nadaElegido: "Elige al menos un idioma y una sección.",
	idiomaPrincipal: "Idioma principal",
	idiomaPrincipalDesc: "El del buscador y el encuentro, y el que sale marcado al importar.",
	fantasy: "Propiedades para Fantasy Statblocks",
	fantasyDesc: "Añade la ficha a las propiedades de cada criatura para que Fantasy Statblocks la lea (activa en él la opción de leer las propiedades de las criaturas). Al importar se guarda también un diseño de ficha 2024 en la carpeta del idioma (un fichero .json): impórtalo en Fantasy Statblocks, Layouts, Import From JSON.",
	estados: "Enlazar los estados",
	estadosDesc: "Enlaza la primera vez que una nota nombra cada estado con la nota de ese estado. Vuelve a importar para aplicarlo.",
	reimportar: "Vuelve a importar para aplicar el cambio a las notas que ya tienes.",
	buscarAyuda: "Buscar en el SRD 5.2.1",
	creada: (n) => `Creada ${n}.`,
	encuentro: "Encuentro",
	grupo: "Grupo",
	personajes: "Personajes",
	nivel: "Nivel",
	anadirPersonajes: "Añadir personajes de otro nivel",
	criaturas: "Criaturas",
	anadirCriatura: "Añadir criatura",
	sinCriaturas: "Todavía no hay criaturas. Añádelas aquí o desde la nota de una criatura.",
	quitar: "Quitar",
	presupuesto: "Presupuesto",
	gasto: "Gasto",
	porEncima: (n) => `${n} por encima del presupuesto de dificultad alta`,
	consejos: "Solución de problemas",
	avisoMuchas: "Más de dos criaturas por personaje.",
	avisoVd0: "Hay criaturas con VD 0.",
	avisoPerfiles: "Más de tres perfiles distintos.",
	avisoPoderosas: "Una criatura tiene un VD mayor que el nivel del grupo.",
	enviarIT: "Mandar a Initiative Tracker",
	copiarBloque: "Copiar el bloque encounter",
	insertarBloque: "Insertar en la nota",
	vaciar: "Vaciar",
	itNoEsta: "Initiative Tracker no está activado. Usa el bloque encounter.",
	enviado: (n) => (n === 1 ? "1 criatura mandada a Initiative Tracker." : `${n} criaturas mandadas a Initiative Tracker.`),
	copiado: "Bloque encounter copiado.",
	sinNota: "Abre una nota en modo de edición para insertar el bloque.",
	noEsCriatura: "Esta nota no es una criatura del compendio.",
	anadida: (n) => `${n} añadida al encuentro.`,
	quitarTitulo: "Quitar notas del compendio",
	quitarTexto: (n) => `Hay ${n} notas importadas que no has cambiado desde entonces. Irán a la papelera.`,
	quitarNada: "No hay notas del compendio sin cambiar que quitar.",
	quitado: (n) => (n === 1 ? "1 nota a la papelera." : `${n} notas a la papelera.`),
	nombreEncuentro: "Encuentro",
};

const DE: Ui = {
	usarIT: "Die Spieler aus Initiative Tracker verwenden",
	sinNivel: "ohne Stufe",
	jugadoresIT: "Sie werden in den Einstellungen von Initiative Tracker geändert.",
	cmdEnviar: "Begegnung an Initiative Tracker senden",
	cmdCopiar: "Encounter-Block kopieren",
	cmdInsertar: "Encounter-Block einfügen",
	cmdImportar: "SRD importieren",
	bienvenida: "Compendio SRD 2024 ist bereit. Die Notizen entstehen, wenn du das SRD importierst.",
	cmdBuscar: "Im Kompendium suchen",
	cmdEncuentro: "Begegnung öffnen",
	cmdAnadir: "Diese Kreatur zur Begegnung hinzufügen",
	cmdQuitar: "Unveränderte Kompendium-Notizen entfernen",
	importarTitulo: "SRD 5.2.1 importieren",
	importarIntro: "Legt für jeden Eintrag eine Notiz an, untereinander verlinkt. Notizen, die du geändert hast, bleiben, wie sie sind.",
	idiomas: "Sprachen",
	queImportar: "Was importiert wird",
	secciones: {
		criaturas: "Kreaturen",
		conjuros: "Zauber",
		objetos: "Magische Gegenstände",
		estados: "Zustände",
		reglas: "Regeln, Glossar, Gifte und Fallen",
		personajes: "Klassen, Spezies, Hintergründe und Talente",
		equipo: "Ausrüstung",
	},
	carpeta: "Ordner",
	carpetaDesc: "Das Kompendium kommt in diesen Ordner, mit einem Unterordner pro Sprache.",
	unidades: "Maßeinheiten",
	unidadesDesc: "Fuß und Pfund oder die Meter und Kilogramm des SRD auf Deutsch, Spanisch, Französisch und Italienisch (das englische SRD ist immer in Fuß). Importiere erneut, um vorhandene Notizen zu ändern.",
	pies: "Fuß und Pfund",
	metros: "Meter und Kilogramm",
	sobrescribir: "Geänderte Notizen überschreiben",
	sobrescribirDesc: "Aus: Eine Notiz, die du seit dem Import geändert hast, wird übersprungen.",
	importar: "Importieren",
	cancelar: "Abbrechen",
	cerrar: "Schließen",
	preparando: "Notizen werden vorbereitet…",
	escribiendo: (n, total) => `Schreibe ${n} von ${total}…`,
	resumen: (c, m, i, s) => `${c} erstellt, ${m} aktualisiert, ${i} unverändert, ${s} übersprungen.`,
	saltadasDesc: "Übersprungen werden Notizen, die du geändert hast, und Dateien gleichen Namens, die nicht vom Plugin stammen.",
	cancelado: "Import abgebrochen.",
	errorEscribir: (r, m) => `${r} konnte nicht geschrieben werden: ${m}`,
	nadaElegido: "Wähle mindestens eine Sprache und einen Bereich.",
	idiomaPrincipal: "Hauptsprache",
	idiomaPrincipalDesc: "Für die Suche und die Begegnung; beim Import vorausgewählt.",
	fantasy: "Eigenschaften für Fantasy Statblocks",
	fantasyDesc: "Fügt den Wertekasten in die Eigenschaften jeder Kreatur ein, damit Fantasy Statblocks ihn liest (dort die Option zum Lesen der Eigenschaften von Kreaturen einschalten). Beim Import wird auch ein Layout für Wertekästen von 2024 im Ordner der Sprache gespeichert (eine .json-Datei): importiere es in Fantasy Statblocks unter Layouts, Import From JSON.",
	estados: "Zustände verlinken",
	estadosDesc: "Verlinkt die erste Erwähnung jedes Zustands in einer Notiz mit der Notiz des Zustands. Importiere erneut, um es anzuwenden.",
	reimportar: "Importiere erneut, um die Änderung auf vorhandene Notizen anzuwenden.",
	buscarAyuda: "Im SRD 5.2.1 suchen",
	creada: (n) => `${n} erstellt.`,
	encuentro: "Begegnung",
	grupo: "Gruppe",
	personajes: "Charaktere",
	nivel: "Stufe",
	anadirPersonajes: "Charaktere einer anderen Stufe hinzufügen",
	criaturas: "Kreaturen",
	anadirCriatura: "Kreatur hinzufügen",
	sinCriaturas: "Noch keine Kreaturen. Füge sie hier oder aus der Notiz einer Kreatur hinzu.",
	quitar: "Entfernen",
	presupuesto: "Budget",
	gasto: "Verbraucht",
	porEncima: (n) => `${n} über dem hohen Budget`,
	consejos: "Problemlösungen",
	avisoMuchas: "Mehr als zwei Kreaturen pro Charakter.",
	avisoVd0: "Es gibt Kreaturen mit HG 0.",
	avisoPerfiles: "Mehr als drei verschiedene Wertekästen.",
	avisoPoderosas: "Der HG einer Kreatur ist höher als die Stufe der Gruppe.",
	enviarIT: "An Initiative Tracker senden",
	copiarBloque: "Encounter-Block kopieren",
	insertarBloque: "In die Notiz einfügen",
	vaciar: "Leeren",
	itNoEsta: "Initiative Tracker ist nicht aktiviert. Nutze den Encounter-Block.",
	enviado: (n) => (n === 1 ? "1 Kreatur an Initiative Tracker gesendet." : `${n} Kreaturen an Initiative Tracker gesendet.`),
	copiado: "Encounter-Block kopiert.",
	sinNota: "Öffne eine Notiz im Bearbeitungsmodus, um den Block einzufügen.",
	noEsCriatura: "Diese Notiz ist keine Kreatur aus dem Kompendium.",
	anadida: (n) => `${n} zur Begegnung hinzugefügt.`,
	quitarTitulo: "Kompendium-Notizen entfernen",
	quitarTexto: (n) => `${n} importierte Notizen wurden seitdem nicht geändert. Sie kommen in den Papierkorb.`,
	quitarNada: "Es gibt keine unveränderten Kompendium-Notizen zu entfernen.",
	quitado: (n) => `${n} Notizen in den Papierkorb verschoben.`,
	nombreEncuentro: "Begegnung",
};

const FR: Ui = {
	usarIT: "Utiliser les joueurs d’Initiative Tracker",
	sinNivel: "sans niveau",
	jugadoresIT: "Ils se modifient dans les réglages d’Initiative Tracker.",
	cmdEnviar: "Envoyer la rencontre à Initiative Tracker",
	cmdCopiar: "Copier le bloc encounter",
	cmdInsertar: "Insérer le bloc encounter",
	cmdImportar: "Importer le SRD",
	bienvenida: "Compendio SRD 2024 est prêt. Les notes sont créées quand vous importez le SRD.",
	cmdBuscar: "Rechercher dans le compendium",
	cmdEncuentro: "Ouvrir la rencontre",
	cmdAnadir: "Ajouter cette créature à la rencontre",
	cmdQuitar: "Retirer les notes du compendium que vous n’avez pas modifiées",
	importarTitulo: "Importer le SRD 5.2.1",
	importarIntro: "Crée une note par entrée, reliées entre elles. Les notes que vous avez modifiées restent telles quelles.",
	idiomas: "Langues",
	queImportar: "Contenu à importer",
	secciones: {
		criaturas: "Créatures",
		conjuros: "Sorts",
		objetos: "Objets magiques",
		estados: "États",
		reglas: "Règles, glossaire, poisons et pièges",
		personajes: "Classes, espèces, historiques et dons",
		equipo: "Équipement",
	},
	carpeta: "Dossier",
	carpetaDesc: "Le compendium va dans ce dossier, avec un sous-dossier par langue.",
	unidades: "Unités",
	unidadesDesc: "Pieds et livres, ou les mètres et kilos du SRD en français, espagnol, allemand et italien (le SRD en anglais est toujours en pieds). Importez à nouveau pour modifier les notes existantes.",
	pies: "Pieds et livres",
	metros: "Mètres et kilos",
	sobrescribir: "Écraser les notes que j’ai modifiées",
	sobrescribirDesc: "Désactivé\u00a0: une note modifiée depuis l’import n’est pas touchée.",
	importar: "Importer",
	cancelar: "Annuler",
	cerrar: "Fermer",
	preparando: "Préparation des notes…",
	escribiendo: (n, total) => `Écriture de ${n} sur ${total}…`,
	resumen: (c, m, i, s) => `${c} créées, ${m} mises à jour, ${i} inchangées, ${s} ignorées.`,
	saltadasDesc: "Les notes ignorées sont celles que vous avez modifiées, ou des fichiers du même nom que le plugin n’a pas créés.",
	cancelado: "Import annulé.",
	errorEscribir: (r, m) => `Impossible d’écrire ${r}\u00a0: ${m}`,
	nadaElegido: "Choisissez au moins une langue et une section.",
	idiomaPrincipal: "Langue principale",
	idiomaPrincipalDesc: "Celle de la recherche et de la rencontre, cochée par défaut à l’import.",
	fantasy: "Propriétés pour Fantasy Statblocks",
	fantasyDesc: "Ajoute le profil aux propriétés de chaque créature pour que Fantasy Statblocks le lise (activez son option de lecture des propriétés des créatures). L’import enregistre aussi une mise en page de profil 2024 dans le dossier de la langue (un fichier .json)\u00a0: importez-la dans Fantasy Statblocks, Layouts, Import From JSON.",
	estados: "Relier les états",
	estadosDesc: "Relie la première mention de chaque état dans une note à la note de cet état. Importez à nouveau pour l’appliquer.",
	reimportar: "Importez à nouveau pour appliquer le changement aux notes existantes.",
	buscarAyuda: "Rechercher dans le SRD 5.2.1",
	creada: (n) => `${n} créée.`,
	encuentro: "Rencontre",
	grupo: "Groupe",
	personajes: "Personnages",
	nivel: "Niveau",
	anadirPersonajes: "Ajouter des personnages d’un autre niveau",
	criaturas: "Créatures",
	anadirCriatura: "Ajouter une créature",
	sinCriaturas: "Aucune créature pour l’instant. Ajoutez-les ici ou depuis la note d’une créature.",
	quitar: "Retirer",
	presupuesto: "Budget",
	gasto: "Dépensé",
	porEncima: (n) => `${n} au-dessus du budget élevé`,
	consejos: "Résolution de problèmes",
	avisoMuchas: "Plus de deux créatures par personnage.",
	avisoVd0: "Il y a des créatures de FP 0.",
	avisoPerfiles: "Plus de trois profils différents.",
	avisoPoderosas: "Le FP d’une créature dépasse le niveau du groupe.",
	enviarIT: "Envoyer à Initiative Tracker",
	copiarBloque: "Copier le bloc encounter",
	insertarBloque: "Insérer dans la note",
	vaciar: "Vider",
	itNoEsta: "Initiative Tracker n’est pas activé. Utilisez le bloc encounter.",
	enviado: (n) => (n === 1 ? "1 créature envoyée à Initiative Tracker." : `${n} créatures envoyées à Initiative Tracker.`),
	copiado: "Bloc encounter copié.",
	sinNota: "Ouvrez une note en mode édition pour insérer le bloc.",
	noEsCriatura: "Cette note n’est pas une créature du compendium.",
	anadida: (n) => `${n} ajoutée à la rencontre.`,
	quitarTitulo: "Retirer les notes du compendium",
	quitarTexto: (n) => `${n} notes importées n’ont pas été modifiées depuis. Elles iront à la corbeille.`,
	quitarNada: "Aucune note du compendium non modifiée à retirer.",
	quitado: (n) => `${n} notes mises à la corbeille.`,
	nombreEncuentro: "Rencontre",
};

const IT: Ui = {
	usarIT: "Usa i giocatori di Initiative Tracker",
	sinNivel: "senza livello",
	jugadoresIT: "Si cambiano nelle impostazioni di Initiative Tracker.",
	cmdEnviar: "Invia l'incontro a Initiative Tracker",
	cmdCopiar: "Copia il blocco encounter",
	cmdInsertar: "Inserisci il blocco encounter",
	cmdImportar: "Importa l'SRD",
	bienvenida: "Compendio SRD 2024 è pronto. Le note vengono create quando importi l'SRD.",
	cmdBuscar: "Cerca nel compendio",
	cmdEncuentro: "Apri l'incontro",
	cmdAnadir: "Aggiungi questa creatura all'incontro",
	cmdQuitar: "Rimuovi le note del compendio che non hai modificato",
	importarTitulo: "Importa l'SRD 5.2.1",
	importarIntro: "Crea una nota per voce, collegate tra loro. Le note che hai modificato restano come sono.",
	idiomas: "Lingue",
	queImportar: "Cosa importare",
	secciones: {
		criaturas: "Creature",
		conjuros: "Incantesimi",
		objetos: "Oggetti magici",
		estados: "Condizioni",
		reglas: "Regole, glossario, veleni e trappole",
		personajes: "Classi, specie, background e talenti",
		equipo: "Equipaggiamento",
	},
	carpeta: "Cartella",
	carpetaDesc: "Il compendio va in questa cartella, con una sottocartella per lingua.",
	unidades: "Unità",
	unidadesDesc: "Piedi e libbre, oppure i metri e chili dell'SRD in italiano, spagnolo, tedesco e francese (l'SRD in inglese è sempre in piedi). Importa di nuovo per cambiare le note che hai già.",
	pies: "Piedi e libbre",
	metros: "Metri e chili",
	sobrescribir: "Sovrascrivi le note che ho modificato",
	sobrescribirDesc: "Disattivato: una nota modificata dopo l'importazione non viene toccata.",
	importar: "Importa",
	cancelar: "Annulla",
	cerrar: "Chiudi",
	preparando: "Preparazione delle note…",
	escribiendo: (n, total) => `Scrittura di ${n} su ${total}…`,
	resumen: (c, m, i, s) => `${c} create, ${m} aggiornate, ${i} invariate, ${s} saltate.`,
	saltadasDesc: "Quelle saltate sono le note che hai modificato, o file con lo stesso nome che il plugin non ha creato.",
	cancelado: "Importazione annullata.",
	errorEscribir: (r, m) => `Impossibile scrivere ${r}: ${m}`,
	nadaElegido: "Scegli almeno una lingua e una sezione.",
	idiomaPrincipal: "Lingua principale",
	idiomaPrincipalDesc: "Quella della ricerca e dell'incontro, selezionata di default quando importi.",
	fantasy: "Proprietà per Fantasy Statblocks",
	fantasyDesc: "Aggiunge la scheda alle proprietà di ogni creatura perché Fantasy Statblocks la legga (attiva la sua opzione per leggere le proprietà delle creature). L'importazione salva anche un layout di scheda 2024 nella cartella della lingua (un file .json): importalo in Fantasy Statblocks, Layouts, Import From JSON.",
	estados: "Collega le condizioni",
	estadosDesc: "Collega la prima volta che una nota nomina ogni condizione alla nota di quella condizione. Importa di nuovo per applicarlo.",
	reimportar: "Importa di nuovo per applicare la modifica alle note che hai già.",
	buscarAyuda: "Cerca nell'SRD 5.2.1",
	creada: (n) => `Creata ${n}.`,
	encuentro: "Incontro",
	grupo: "Gruppo",
	personajes: "Personaggi",
	nivel: "Livello",
	anadirPersonajes: "Aggiungi personaggi di un altro livello",
	criaturas: "Creature",
	anadirCriatura: "Aggiungi creatura",
	sinCriaturas: "Ancora nessuna creatura. Aggiungile qui o dalla nota di una creatura.",
	quitar: "Rimuovi",
	presupuesto: "Budget",
	gasto: "Speso",
	porEncima: (n) => `${n} oltre il budget difficile`,
	consejos: "Risoluzione dei problemi",
	avisoMuchas: "Più di due creature per personaggio.",
	avisoVd0: "Ci sono creature con GS 0.",
	avisoPerfiles: "Più di tre schede delle statistiche diverse.",
	avisoPoderosas: "Il GS di una creatura è superiore al livello del gruppo.",
	enviarIT: "Invia a Initiative Tracker",
	copiarBloque: "Copia il blocco encounter",
	insertarBloque: "Inserisci nella nota",
	vaciar: "Svuota",
	itNoEsta: "Initiative Tracker non è attivo. Usa il blocco encounter.",
	enviado: (n) => (n === 1 ? "1 creatura inviata a Initiative Tracker." : `${n} creature inviate a Initiative Tracker.`),
	copiado: "Blocco encounter copiato.",
	sinNota: "Apri una nota in modalità modifica per inserire il blocco.",
	noEsCriatura: "Questa nota non è una creatura del compendio.",
	anadida: (n) => `${n} aggiunta all'incontro.`,
	quitarTitulo: "Rimuovi le note del compendio",
	quitarTexto: (n) => `${n} note importate non sono state modificate da allora. Andranno nel cestino.`,
	quitarNada: "Non ci sono note del compendio non modificate da rimuovere.",
	quitado: (n) => `${n} note spostate nel cestino.`,
	nombreEncuentro: "Incontro",
};

const UI: Record<Idioma, Ui> = { en: EN, es: ES, de: DE, fr: FR, it: IT };

/** El idioma de Obsidian si es uno de los cinco del SRD. */
export function idiomaObsidian(): Idioma | null {
	const l = getLanguage().slice(0, 2).toLowerCase();
	return l === "es" || l === "en" || l === "de" || l === "fr" || l === "it" ? l : null;
}

export function t(): Ui {
	return UI[idiomaObsidian() ?? "en"];
}
