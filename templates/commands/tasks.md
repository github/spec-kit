---
description: Genereer een uitvoerbare, afhankelijkheid-geordende tasks.md voor de functie gebaseerd op beschikbare ontwerpartefacten.
scripts:
  sh: scripts/bash/check-prerequisites.sh --json
  ps: scripts/powershell/check-prerequisites.ps1 -Json
---

De gebruikersinvoer kan direct door de agent of als commandoargument worden verstrekt - je **MOET** dit overwegen voordat je doorgaat met de prompt (indien niet leeg).

Gebruikersinvoer:

$ARGUMENTS

1. Voer `{SCRIPT}` uit vanaf repo root en parseer FEATURE_DIR en AVAILABLE_DOCS lijst. Alle paden moeten absoluut zijn.
2. Laad en analyseer beschikbare ontwerpdocumenten:
   - Lees altijd plan.md voor tech stack en bibliotheken
   - INDIEN BESTAAT: Lees data-model.md voor entiteiten
   - INDIEN BESTAAT: Lees contracts/ voor API endpoints
   - INDIEN BESTAAT: Lees research.md voor technische beslissingen
   - INDIEN BESTAAT: Lees quickstart.md voor testscenario's

   Opmerking: Niet alle projecten hebben alle documenten. Bijvoorbeeld:
   - CLI tools hebben mogelijk geen contracts/
   - Eenvoudige bibliotheken hebben mogelijk geen data-model.md nodig
   - Genereer taken gebaseerd op wat beschikbaar is

3. Genereer taken volgens de template:
   - Gebruik `/templates/tasks-template.md` als basis
   - Vervang voorbeeldtaken met werkelijke taken gebaseerd op:
     * **Setup taken**: Project init, afhankelijkheden, linting
     * **Test taken [P]**: Een per contract, een per integratiescenario
     * **Kerntaken**: Een per entiteit, service, CLI commando, endpoint
     * **Integratietaken**: DB verbindingen, middleware, logging
     * **Polish taken [P]**: Unit tests, prestaties, docs

4. Taakgeneratieregels:
   - Elk contractbestand → contract testtaak gemarkeerd [P]
   - Elke entiteit in data-model → modelcreatietaak gemarkeerd [P]
   - Elk endpoint → implementatietaak (niet parallel bij gedeelde bestanden)
   - Elk gebruikersverhaal → integratietest gemarkeerd [P]
   - Verschillende bestanden = kunnen parallel [P]
   - Zelfde bestand = sequentieel (geen [P])

5. Orden taken op afhankelijkheden:
   - Setup voor alles
   - Tests voor implementatie (TDD)
   - Modellen voor services
   - Services voor endpoints
   - Kern voor integratie
   - Alles voor polish

6. Voeg parallelle uitvoeringsvoorbeelden toe:
   - Groepeer [P] taken die samen kunnen lopen
   - Toon werkelijke Taak agent commando's

7. Maak FEATURE_DIR/tasks.md met:
   - Correcte functienaam uit implementatieplan
   - Genummerde taken (T001, T002, etc.)
   - Duidelijke bestandspaden voor elke taak
   - Afhankelijkheidsnotities
   - Parallelle uitvoeringsbegeleiding

Context voor taakgeneratie: {ARGS}

De tasks.md zou onmiddellijk uitvoerbaar moeten zijn - elke taak moet specifiek genoeg zijn dat een LLM het kan voltooien zonder aanvullende context.
