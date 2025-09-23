---
description: Voer een niet-destructieve cross-artifact consistentie en kwaliteitsanalyse uit over spec.md, plan.md en tasks.md na taakgeneratie.
scripts:
  sh: scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks
  ps: scripts/powershell/check-prerequisites.ps1 -Json -RequireTasks -IncludeTasks
---

De gebruikersinvoer kan direct door de agent of als commandoargument worden verstrekt - je **MOET** dit overwegen voordat je doorgaat met de prompt (indien niet leeg).

Gebruikersinvoer:

$ARGUMENTS

Doel: Identificeer inconsistenties, duplicaties, dubbelzinnigheden en ondergespecificeerde items in de drie kernartefacten (`spec.md`, `plan.md`, `tasks.md`) voor implementatie. Dit commando MOET alleen uitgevoerd worden nadat `/tasks` succesvol een complete `tasks.md` heeft geproduceerd.

STRIKT ALLEEN-LEZEN: Wijzig **geen** bestanden. Geef een gestructureerd analyserapport uit. Bied een optioneel herstelplan aan (gebruiker moet expliciet goedkeuren voordat vervolgbewerkingscommando's handmatig zouden worden aangeroepen).

Grondwetautoriteit: De projectgrondwet (`/memory/constitution.md`) is **niet-onderhandelbaar** binnen dit analysebereik. Grondwetconflicten zijn automatisch KRITIEK en vereisen aanpassing van de spec, plan of taken—geen verdunning, herinterpretatie of stilzwijgend negeren van het principe. Als een principe zelf moet veranderen, moet dat plaatsvinden in een aparte, expliciete grondwetupdate buiten `/analyze`.

Uitvoeringsstappen:

1. Voer `{SCRIPT}` eenmaal uit vanaf repo root en parseer JSON voor FEATURE_DIR en AVAILABLE_DOCS. Leid absolute paden af:
   - SPEC = FEATURE_DIR/spec.md
   - PLAN = FEATURE_DIR/plan.md
   - TASKS = FEATURE_DIR/tasks.md
   Breek af met een foutmelding als een vereist bestand ontbreekt (instrueer de gebruiker om het ontbrekende vereiste commando uit te voeren).

2. Laad artefacten:
   - Parseer spec.md secties: Overzicht/Context, Functionele Vereisten, Niet-Functionele Vereisten, Gebruikersverhalen, Randgevallen (indien aanwezig).
   - Parseer plan.md: Architectuur/stack keuzes, Datamodel referenties, Fasen, Technische beperkingen.
   - Parseer tasks.md: Taak IDs, beschrijvingen, fasegroepering, parallelle markeringen [P], gerefereerde bestandspaden.
   - Laad grondwet `/memory/constitution.md` voor principe validatie.

3. Bouw interne semantische modellen:
   - Vereisten inventaris: Elke functionele + niet-functionele vereiste met een stabiele sleutel (leid slug af gebaseerd op imperatieve zin; bijv. "Gebruiker kan bestand uploaden" -> `gebruiker-kan-bestand-uploaden`).
   - Gebruikersverhaal/actie inventaris.
   - Taakdekkingskaart: Koppel elke taak aan een of meer vereisten of verhalen (gevolgtrekking door trefwoord / expliciete referentiepatronen zoals IDs of kernzinnen).
   - Grondwetregelset: Extraheer principenamen en alle MOET/ZOU normatieve uitspraken.

4. Detectiedoorgangen:
   A. Duplicatiedetectie:
      - Identificeer bijna-dubbele vereisten. Markeer lagere-kwaliteit bewoordingen voor consolidatie.
   B. Dubbelzinnigheidsdetectie:
      - Markeer vage bijvoeglijke naamwoorden (snel, schaalbaar, veilig, intuïtief, robuust) die meetbare criteria missen.
      - Markeer onopgeloste placeholders (TODO, TKTK, ???, <placeholder>, etc.).
   C. Onderspecificatie:
      - Vereisten met werkwoorden maar ontbrekend object of meetbare uitkomst.
      - Gebruikersverhalen die acceptatiecriteria-afstemming missen.
      - Taken die verwijzen naar bestanden of componenten niet gedefinieerd in spec/plan.
   D. Grondwetalignment:
      - Elke vereiste of planelement dat conflicteert met een MOET principe.
      - Ontbrekende verplichte secties of kwaliteitspoorten uit grondwet.
   E. Dekkingslacunes:
      - Vereisten met nul geassocieerde taken.
      - Taken zonder gekoppelde vereiste/verhaal.
      - Niet-functionele vereisten niet gereflecteerd in taken (bijv. prestaties, beveiliging).
   F. Inconsistentie:
      - Terminologie drift (hetzelfde concept anders benoemd in verschillende bestanden).
      - Data entiteiten gerefereerd in plan maar afwezig in spec (of omgekeerd).
      - Taakvolgordecontradictie (bijv. integratietaken voor fundamentele setup taken zonder afhankelijkheidsnota).
      - Conflicterende vereisten (bijv. een vereist Next.js te gebruiken terwijl andere zegt Vue als framework te gebruiken).

5. Ernst toewijzingsheuristiek:
   - KRITIEK: Overtreedt grondwet MOET, ontbrekend kernspec artefact, of vereiste met nul dekking die basisfunctionaliteit blokkeert.
   - HOOG: Dubbele of conflicterende vereiste, dubbelzinnig beveiliging/prestatie attribuut, niet-testbaar acceptatiecriterium.
   - MEDIUM: Terminologie drift, ontbrekende niet-functionele taakdekking, ondergespecificeerd randgeval.
   - LAAG: Stijl/bewoordingsverbeteringen, kleine redundantie die uitvoeringsvolgorde niet beïnvloedt.

6. Produceer een Markdown rapport (geen bestandsschrijvingen) met secties:

   ### Specificatie Analyse Rapport
   | ID | Categorie | Ernst | Locatie(s) | Samenvatting | Aanbeveling |
   |----|-----------|-------|------------|--------------|-------------|
   | A1 | Duplicatie | HOOG | spec.md:L120-134 | Twee vergelijkbare vereisten ... | Voeg bewoordingen samen; behoud duidelijkere versie |
   (Voeg een rij toe per bevinding; genereer stabiele IDs voorafgegaan door categorie-initiaal.)

   Aanvullende subsecties:
   - Dekkingssamenvatting Tabel:
     | Vereiste Sleutel | Heeft Taak? | Taak IDs | Opmerkingen |
   - Grondwet Alignment Problemen (indien van toepassing)
   - Ongekoppelde Taken (indien van toepassing)
   - Metrieken:
     * Totaal Vereisten
     * Totaal Taken
     * Dekking % (vereisten met >=1 taak)
     * Dubbelzinnigheid Aantal
     * Duplicatie Aantal
     * Kritieke Problemen Aantal

7. Aan het eind van het rapport, geef een beknopt Volgende Acties blok uit:
   - Indien KRITIEKE problemen bestaan: Beveel oplossen aan voor `/implement`.
   - Indien alleen LAAG/MEDIUM: Gebruiker mag doorgaan, maar geef verbeteringsuggesties.
   - Geef expliciete commandosuggesties: bijv. "Voer /specify uit met verfijning", "Voer /plan uit om architectuur aan te passen", "Bewerk tasks.md handmatig om dekking toe te voegen voor 'prestatie-metrieken'".

8. Vraag de gebruiker: "Wil je dat ik concrete herstelbewerking suggesties geef voor de top N problemen?" (Pas ze NIET automatisch toe.)

Gedragsregels:
- WIJZIG NOOIT bestanden.
- HALLUCINEER NOOIT ontbrekende secties—indien afwezig, rapporteer ze.
- HOUD bevindingen deterministisch: indien opnieuw uitgevoerd zonder wijzigingen, produceer consistente IDs en aantallen.
- BEPERK totale bevindingen in de hoofdtabel tot 50; aggregeer de rest in een samengevatte overflow nota.
- Indien nul problemen gevonden, emit een successrapport met dekkingsstatistieken en doorgaan aanbeveling.

Context: {ARGS}
