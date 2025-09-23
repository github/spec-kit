---
description: Voer de implementatieplanning workflow uit met behulp van de plan template om ontwerpartefacten te genereren.
scripts:
  sh: scripts/bash/setup-plan.sh --json
  ps: scripts/powershell/setup-plan.ps1 -Json
---

De gebruikersinvoer kan direct door de agent of als commandoargument worden verstrekt - je **MOET** dit overwegen voordat je doorgaat met de prompt (indien niet leeg).

Gebruikersinvoer:

$ARGUMENTS

Gegeven de implementatiedetails verstrekt als argument, doe dit:

1. Voer `{SCRIPT}` uit vanaf de repo root en parseer JSON voor FEATURE_SPEC, IMPL_PLAN, SPECS_DIR, BRANCH. Alle toekomstige bestandspaden moeten absoluut zijn.
   - VOORDAT je doorgaat, inspecteer FEATURE_SPEC voor een `## Verduidelijkingen` sectie met ten minste één `Sessie` subkop. Indien ontbrekend of duidelijk dubbelzinnige gebieden blijven (vage bijvoeglijke naamwoorden, onopgeloste kritieke keuzes), PAUZEER en instrueer de gebruiker om eerst `/clarify` uit te voeren om herwerk te verminderen. Ga alleen door indien: (a) Verduidelijkingen bestaan OF (b) een expliciete gebruiker override wordt verstrekt (bijv. "ga door zonder verduidelijking"). Probeer niet zelf verduidelijkingen te fabriceren.
2. Lees en analyseer de functiespecificatie om te begrijpen:
   - De functievereisten en gebruikersverhalen
   - Functionele en niet-functionele vereisten
   - Succescriteria en acceptatiecriteria
   - Eventuele technische beperkingen of afhankelijkheden genoemd

3. Lees de grondwet op `/memory/constitution.md` om grondwettelijke vereisten te begrijpen.

4. Voer de implementatieplan template uit:
   - Laad `/templates/plan-template.md` (reeds gekopieerd naar IMPL_PLAN pad)
   - Stel Invoerpad in op FEATURE_SPEC
   - Voer de Uitvoeringsstroom (hoofdfunctie) stappen 1-9 uit
   - De template is zelfstandig en uitvoerbaar
   - Volg foutafhandeling en poortcontroles zoals gespecificeerd
   - Laat de template artefactgeneratie leiden in $SPECS_DIR:
     * Fase 0 genereert research.md
     * Fase 1 genereert data-model.md, contracts/, quickstart.md
     * Fase 2 genereert tasks.md
   - Incorporeer gebruiker-verstrekte details uit argumenten in Technische Context: {ARGS}
   - Update Voortgangsvolging terwijl je elke fase voltooit

5. Verifieer uitvoering voltooid:
   - Controleer Voortgangsvolging toont alle fasen voltooid
   - Zorg dat alle vereiste artefacten gegenereerd werden
   - Bevestig geen FOUT staten in uitvoering

6. Rapporteer resultaten met branch naam, bestandspaden, en gegenereerde artefacten.

Gebruik absolute paden met de repository root voor alle bestandsoperaties om padproblemen te vermijden.
