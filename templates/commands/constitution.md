---
description: Maak of update de projectgrondwet vanuit interactieve of verstrekte principe invoeren, zorg dat alle afhankelijke templates gesynchroniseerd blijven.
---

De gebruikersinvoer kan direct door de agent of als commandoargument worden verstrekt - je **MOET** dit overwegen voordat je doorgaat met de prompt (indien niet leeg).

Gebruikersinvoer:

$ARGUMENTS

Je bent de projectgrondwet aan het bijwerken op `/memory/constitution.md`. Dit bestand is een TEMPLATE met placeholder tokens in vierkante haken (bijv. `[PROJECT_NAME]`, `[PRINCIPLE_1_NAME]`). Je taak is om (a) concrete waarden te verzamelen/afleiden, (b) de template precies in te vullen, en (c) eventuele wijzigingen door te geven aan afhankelijke artefacten.

Volg deze uitvoeringsstroom:

1. Laad de bestaande grondwet template op `/memory/constitution.md`.
   - Identificeer elke placeholder token van de vorm `[ALL_CAPS_IDENTIFIER]`.
   **BELANGRIJK**: De gebruiker kan minder of meer principes nodig hebben dan degene gebruikt in de template. Als een aantal gespecificeerd is, respecteer dat - volg de algemene template. Je zult het document dienovereenkomstig bijwerken.

2. Verzamel/leid waarden af voor placeholders:
   - Als gebruikersinvoer (gesprek) een waarde levert, gebruik die.
   - Anders afleiden uit bestaande repo context (README, docs, eerdere grondwet versies indien ingebed).
   - Voor governance data: `RATIFICATION_DATE` is de oorspronkelijke adoptiedatum (indien onbekend vraag of markeer TODO), `LAST_AMENDED_DATE` is vandaag indien wijzigingen gemaakt, anders behoud vorige.
   - `CONSTITUTION_VERSION` moet incrementeren volgens semantic versioning regels:
     * MAJOR: Achterwaarts incompatibele governance/principe verwijderingen of herdefinities.
     * MINOR: Nieuw principe/sectie toegevoegd of materieel uitgebreide begeleiding.
     * PATCH: Verduidelijkingen, bewoordingen, typfouten fixes, niet-semantische verfijningen.
   - Indien versie bump type dubbelzinnig, stel redenering voor alvorens te finaliseren.

3. Stel de bijgewerkte grondwet inhoud op:
   - Vervang elke placeholder met concrete tekst (geen haakjes tokens over behalve opzettelijk behouden template slots die het project heeft gekozen nog niet te definiëren—rechtvaardig expliciet eventuele overgebleven).
   - Behoud koppenstructuur en opmerkingen kunnen verwijderd worden eenmaal vervangen tenzij ze nog steeds verduidelijkende begeleiding toevoegen.
   - Zorg dat elke Principe sectie: beknopte naamlijn, paragraaf (of bullet lijst) die niet-onderhandelbare regels vastlegt, expliciete rationale indien niet voor de hand liggend.
   - Zorg dat Governance sectie wijzigingsprocedure, versioning beleid, en compliance review verwachtingen vermeldt.

4. Consistentie propagatie checklist (converteer eerdere checklist naar actieve validaties):
   - Lees `/templates/plan-template.md` en zorg dat elke "Grondwetcontrole" of regels afstemmen met bijgewerkte principes.
   - Lees `/templates/spec-template.md` voor bereik/vereisten afstemming—update indien grondwet verplichte secties of beperkingen toevoegt/verwijdert.
   - Lees `/templates/tasks-template.md` en zorg dat taakcategorisatie nieuwe of verwijderde principe-gedreven taaktypes reflecteert (bijv. observeerbaarheid, versioning, test discipline).
   - Lees elk commandobestand in `/templates/commands/*.md` (inclusief deze) om te verifiëren dat geen verouderde referenties (agent-specifieke namen zoals CLAUDE alleen) blijven wanneer generieke begeleiding vereist is.
   - Lees eventuele runtime begeleiding docs (bijv. `README.md`, `docs/quickstart.md`, of agent-specifieke begeleiding bestanden indien aanwezig). Update referenties naar gewijzigde principes.

5. Produceer een Sync Impact Rapport (voeg vooraan toe als HTML commentaar bovenaan het grondwetbestand na update):
   - Versie wijziging: oud → nieuw
   - Lijst van gewijzigde principes (oude titel → nieuwe titel indien hernoemd)
   - Toegevoegde secties
   - Verwijderde secties
   - Templates die updates vereisen (✅ bijgewerkt / ⚠ in behandeling) met bestandspaden
   - Vervolg TODOs indien placeholders opzettelijk uitgesteld.

6. Validatie voor einduitvoer:
   - Geen overgebleven onverklaarde haakjes tokens.
   - Versielijn komt overeen met rapport.
   - Data ISO formaat YYYY-MM-DD.
   - Principes zijn declaratief, testbaar, en vrij van vage taal ("zou" → vervang met MOET/ZOU rationale waar geschikt).

7. Schrijf de voltooide grondwet terug naar `/memory/constitution.md` (overschrijf).

8. Geef een eindsamenvatting uit naar de gebruiker met:
   - Nieuwe versie en bump rationale.
   - Eventuele bestanden gemarkeerd voor handmatige opvolging.
   - Voorgesteld commit bericht (bijv. `docs: wijzig grondwet naar vX.Y.Z (principe toevoegingen + governance update)`).

Formattering & Stijlvereisten:
- Gebruik Markdown koppen precies zoals in de template (demoveer/promoveer niveaus niet).
- Wrap lange rationale regels om leesbaarheid te behouden (<100 tekens ideaal) maar dwing niet hard af met onhandige breaks.
- Houd een enkele lege regel tussen secties.
- Vermijd trailing whitespace.

Indien de gebruiker gedeeltelijke updates levert (bijv. slechts één principe revisie), voer nog steeds validatie en versie beslissing stappen uit.

Indien kritieke info ontbreekt (bijv. ratificatiedatum werkelijk onbekend), voeg `TODO(<FIELD_NAME>): uitleg` in en voeg toe in het Sync Impact Rapport onder uitgestelde items.

Maak geen nieuwe template; opereer altijd op het bestaande `/memory/constitution.md` bestand.
