---
description: Voer het implementatieplan uit door alle taken gedefinieerd in tasks.md te verwerken en uit te voeren
scripts:
  sh: scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks
  ps: scripts/powershell/check-prerequisites.ps1 -Json -RequireTasks -IncludeTasks
---

De gebruikersinvoer kan direct door de agent of als commandoargument worden verstrekt - je **MOET** dit overwegen voordat je doorgaat met de prompt (indien niet leeg).

Gebruikersinvoer:

$ARGUMENTS

1. Voer `{SCRIPT}` uit vanaf repo root en parseer FEATURE_DIR en AVAILABLE_DOCS lijst. Alle paden moeten absoluut zijn.

2. Laad en analyseer de implementatiecontext:
   - **VEREIST**: Lees tasks.md voor de complete takenlijst en uitvoeringsplan
   - **VEREIST**: Lees plan.md voor tech stack, architectuur, en bestandsstructuur
   - **INDIEN BESTAAT**: Lees data-model.md voor entiteiten en relaties
   - **INDIEN BESTAAT**: Lees contracts/ voor API specificaties en testvereisten
   - **INDIEN BESTAAT**: Lees research.md voor technische beslissingen en beperkingen
   - **INDIEN BESTAAT**: Lees quickstart.md voor integratiescenario's

3. Parseer tasks.md structuur en extraheer:
   - **Taakfasen**: Setup, Tests, Kern, Integratie, Polish
   - **Taakafhankelijkheden**: Sequentiële vs parallelle uitvoeringsregels
   - **Taakdetails**: ID, beschrijving, bestandspaden, parallelle markeringen [P]
   - **Uitvoeringsstroom**: Volgorde en afhankelijkheidsvereisten

4. Voer implementatie uit volgens het takenplan:
   - **Fase-bij-fase uitvoering**: Voltooi elke fase voor overgang naar de volgende
   - **Respecteer afhankelijkheden**: Voer sequentiële taken op volgorde uit, parallelle taken [P] kunnen samen lopen  
   - **Volg TDD aanpak**: Voer testtaken uit voor hun corresponderende implementatietaken
   - **Bestand-gebaseerde coördinatie**: Taken die dezelfde bestanden beïnvloeden moeten sequentieel lopen
   - **Validatie checkpoints**: Verifieer elke fase voltooiing voor verdergaan

5. Implementatie uitvoeringsregels:
   - **Setup eerst**: Initialiseer projectstructuur, afhankelijkheden, configuratie
   - **Tests voor code**: Indien je tests moet schrijven voor contracten, entiteiten, en integratiescenario's
   - **Kernontwikkeling**: Implementeer modellen, services, CLI commando's, endpoints
   - **Integratiewerk**: Database verbindingen, middleware, logging, externe services
   - **Polish en validatie**: Unit tests, prestatie optimalisatie, documentatie

6. Voortgangsvolging en foutafhandeling:
   - Rapporteer voortgang na elke voltooide taak
   - Stop uitvoering als een niet-parallelle taak faalt
   - Voor parallelle taken [P], ga door met succesvolle taken, rapporteer gefaalde
   - Geef duidelijke foutmeldingen met context voor debugging
   - Stel volgende stappen voor als implementatie niet kan doorgaan
   - **BELANGRIJK** Voor voltooide taken, zorg ervoor de taak af te vinken als [X] in het takenbestand.

7. Voltooiingsvalidatie:
   - Verifieer dat alle vereiste taken voltooid zijn
   - Controleer dat geïmplementeerde functies overeenkomen met de oorspronkelijke specificatie
   - Valideer dat tests slagen en dekking vereisten voldoet
   - Bevestig dat de implementatie het technische plan volgt
   - Rapporteer eindstatus met samenvatting van voltooid werk

Opmerking: Dit commando gaat uit van een complete taakuitsplitsing in tasks.md. Als taken incompleet of ontbrekend zijn, stel voor om eerst `/tasks` uit te voeren om de takenlijst te regenereren.