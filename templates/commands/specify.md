---
description: Maak of update de functiespecificatie vanuit een natuurlijke taal functiebeschrijving.
scripts:
  sh: scripts/bash/create-new-feature.sh --json "{ARGS}"
  ps: scripts/powershell/create-new-feature.ps1 -Json "{ARGS}"
---

De gebruikersinvoer kan direct door de agent of als commandoargument worden verstrekt - je **MOET** dit overwegen voordat je doorgaat met de prompt (indien niet leeg).

Gebruikersinvoer:

$ARGUMENTS

De tekst die de gebruiker typte na `/specify` in het triggerend bericht **is** de functiebeschrijving. Neem aan dat je het altijd beschikbaar hebt in dit gesprek zelfs als `{ARGS}` letterlijk hieronder verschijnt. Vraag de gebruiker niet het te herhalen tenzij ze een leeg commando gaven.

Gegeven die functiebeschrijving, doe dit:

1. Voer het script `{SCRIPT}` uit vanaf repo root en parseer zijn JSON uitvoer voor BRANCH_NAME en SPEC_FILE. Alle bestandspaden moeten absoluut zijn.
  **BELANGRIJK** Je moet dit script slechts eenmaal uitvoeren. De JSON wordt verstrekt in de terminal als uitvoer - verwijs er altijd naar om de werkelijke inhoud te krijgen die je zoekt.
2. Laad `templates/spec-template.md` om vereiste secties te begrijpen.
3. Schrijf de specificatie naar SPEC_FILE met behulp van de template structuur, vervang placeholders met concrete details afgeleid uit de functiebeschrijving (argumenten) terwijl sectievolgorde en koppen behouden blijven.
4. Rapporteer voltooiing met branch naam, spec bestandspad, en gereedheid voor de volgende fase.

Opmerking: Het script maakt en checkt de nieuwe branch uit en initialiseert het spec bestand voor schrijven.
