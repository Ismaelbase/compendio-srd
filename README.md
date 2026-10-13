# Compendio SRD 2024

Import the official System Reference Document 5.2.1 (the 2024 rules of the fifth edition) into your vault as linked notes, in Spanish, English, German, French or Italian.

[Versión en español más abajo.](#español)

## What it does

- **One note per entry**: 330 creatures, 339 spells, 258 magic items, the 15 conditions, the rules chapters, the rules glossary, classes and subclasses, species, backgrounds, feats, weapons, armor, tools, adventuring gear, poisons and traps. About 1,370 notes per language.
- **Linked notes**: spells cited in a stat block link to the spell, creatures cited in a spell link to the creature, the first mention of each condition links to the condition, and every note links to the same entry in the other languages you import.
- **2024 stat blocks** drawn in plain Markdown (they read fine without the plugin), with properties to sort and filter: challenge rating, XP, AC, HP, initiative, spell level, school, classes, rarity and more.
- **Index notes** for each section: creatures by challenge rating, spells by level, magic items by rarity, rules in the order of the SRD.
- **Encounter builder** with the 2024 rules: XP budget per character (Low, Moderate, High), no multipliers, and the troubleshooting tips of the SRD (many creatures, CR 0 creatures, number of stat blocks, powerful creatures).
- **Initiative Tracker**: send the encounter to the [Initiative Tracker](https://github.com/Obsidian-TTRPG-Community/initiative-tracker) plugin, or copy an `encounter` block for it.
- **Fantasy Statblocks** (optional): adds the stat block to each creature's properties so [Fantasy Statblocks](https://github.com/Obsidian-TTRPG-Community/fantasy-statblocks) can read it, and saves a 2024 stat block layout for it in each language folder (`Compendio SRD 2024 (English).json` and so on). Import that file in Fantasy Statblocks, Layouts, Import From JSON, and turn on its option to parse frontmatter for creatures: the creatures then show with the 2024 layout in your language, also in Initiative Tracker.
- **Units**: feet and pounds, or the meters and kilograms of the SRD in Spanish, German, French and Italian.

The text is the official translation of each SRD. Where a translation says something different from the English SRD (a wrong number, a missing word), it has been corrected to match the English one; every correction is listed in the credits note of each language.

## How to use it

1. Run **Import the SRD** from the command palette (or the button in the plugin settings).
2. Choose the languages, the sections and the folder, and press **Import**.
3. Open **Home** in the language folder to start browsing.
4. To build a fight, run **Open the encounter builder**. Set the party, add creatures (from the builder, or with **Add this creature to the encounter** in a creature note) and send them to Initiative Tracker.

**Search the compendium** finds any entry by name and opens its note, creating just that note if you have not imported its section.

Importing again updates the notes that are still as the plugin left them. Notes you have edited are skipped, unless you turn on **Overwrite notes I have edited**. **Remove the compendium notes you have not edited** moves the unedited notes to the trash.

## Privacy and files

- No network access: all the data is inside the plugin.
- No telemetry and no accounts.
- It only writes notes in the folder you choose inside your vault, and its own settings file.
- Works on desktop and mobile.

## License

The plugin code is under the MIT license (see `LICENSE`).

The notes contain text from the SRD 5.2.1. Each language's credits note carries the attribution of its SRD:

This work includes material from the System Reference Document 5.2.1 ("SRD 5.2.1") by Wizards of the Coast LLC, available at https://www.dndbeyond.com/srd. The SRD 5.2.1 is licensed under the Creative Commons Attribution 4.0 International License, available at https://creativecommons.org/licenses/by/4.0/legalcode.

This plugin is compatible with fifth edition.

---

## Español

Importa el documento de referencia del sistema 5.2.1 oficial (las reglas de 2024 de la quinta edición) en tu bóveda como notas enlazadas, en español, inglés, alemán, francés o italiano.

### Qué hace

- **Una nota por entrada**: 330 criaturas, 339 conjuros, 258 objetos mágicos, los 15 estados, los capítulos de reglas, el glosario, clases y subclases, especies, trasfondos, dotes, armas, armaduras, herramientas, equipo, venenos y trampas. Unas 1370 notas por idioma.
- **Notas enlazadas**: los conjuros que cita una ficha enlazan al conjuro, las criaturas que cita un conjuro enlazan a la criatura, la primera vez que se nombra un estado enlaza al estado, y cada nota enlaza a la misma entrada en los otros idiomas que importes.
- **Fichas de 2024** en Markdown normal (se leen bien sin el plugin), con propiedades para ordenar y filtrar: VD, PX, CA, PG, iniciativa, nivel de conjuro, escuela, clases, rareza y más.
- **Índices** de cada sección: criaturas por VD, conjuros por nivel, objetos mágicos por rareza, reglas en el orden del SRD.
- **Encuentros** con las reglas de 2024: presupuesto de PX por personaje (baja, moderada, alta), sin multiplicadores, y los consejos de "Solución de problemas" del SRD.
- **Initiative Tracker**: manda el encuentro al plugin [Initiative Tracker](https://github.com/Obsidian-TTRPG-Community/initiative-tracker) o copia un bloque `encounter` para él.
- **Fantasy Statblocks** (opcional): añade la ficha a las propiedades de cada criatura para que [Fantasy Statblocks](https://github.com/Obsidian-TTRPG-Community/fantasy-statblocks) la lea, y guarda en la carpeta de cada idioma un diseño de ficha 2024 para él (`Compendio SRD 2024 (Español).json`, etc.). Importa ese fichero en Fantasy Statblocks, Layouts, Import From JSON, y activa en él la lectura de las propiedades de las criaturas: las criaturas salen con la ficha de 2024 en tu idioma, también en Initiative Tracker.
- **Unidades**: pies y libras, o los metros y kilos del SRD en español, alemán, francés e italiano.

El texto es la traducción oficial de cada SRD. Donde una traducción no dice lo mismo que el SRD en inglés (una cifra equivocada, una palabra que falta), se ha corregido con el inglés; cada corrección está en la nota de créditos de su idioma.

### Cómo se usa

1. Lanza **Importar el SRD** desde la paleta de comandos (o con el botón de los ajustes del plugin).
2. Elige los idiomas, las secciones y la carpeta, y pulsa **Importar**.
3. Abre **Inicio** en la carpeta del idioma.
4. Para preparar un combate, lanza **Abrir el encuentro**. Pon el grupo, añade criaturas (desde el encuentro o con **Añadir esta criatura al encuentro** en la nota de una criatura) y mándalas a Initiative Tracker.

**Buscar en el compendio** encuentra cualquier entrada por su nombre y abre su nota; si no has importado esa sección, crea solo esa nota.

Volver a importar actualiza las notas que siguen como las dejó el plugin. Las que hayas cambiado no se tocan, salvo que actives **Sobrescribir las notas que he cambiado**. **Quitar las notas del compendio que no has cambiado** manda a la papelera las que siguen sin cambios.

### Privacidad y ficheros

- No se conecta a internet: los datos van dentro del plugin.
- Sin telemetría ni cuentas.
- Solo escribe notas en la carpeta que elijas dentro de tu bóveda, y su propio fichero de ajustes.
- Funciona en escritorio y en el móvil.

### Licencia

El código del plugin va con licencia MIT (ver `LICENSE`).

Las notas llevan texto del SRD 5.2.1. La nota de créditos de cada idioma lleva la atribución de su SRD:

Esta obra incluye material procedente del documento de referencia del sistema 5.2.1 ("SRD 5.2.1") de Wizards of the Coast LLC, disponible en https://www.dndbeyond.com/srd. La licencia sobre el SRD 5.2.1 se concede de acuerdo con la licencia internacional de atribución/reconocimiento 4.0 de Creative Commons, disponible en https://creativecommons.org/licenses/by/4.0/legalcode.

Este plugin es compatible con la quinta edición.

---

Made by Ismael Sevilla, [The Obsidian Die](https://theobsidiandie.com).
