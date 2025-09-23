---
description: Identificeer ondergespecificeerde gebieden in de huidige functiespec door maximaal 5 zeer gerichte verduidelijkingsvragen te stellen en antwoorden terug te coderen in de spec.
scripts:
   sh: scripts/bash/check-prerequisites.sh --json --paths-only
   ps: scripts/powershell/check-prerequisites.ps1 -Json -PathsOnly
---

De gebruikersinvoer kan direct door de agent of als commandoargument worden verstrekt - je **MOET** dit overwegen voordat je doorgaat met de prompt (indien niet leeg).

Gebruikersinvoer:

$ARGUMENTS

Doel: Detecteer en verminder dubbelzinnigheid of ontbrekende beslissingspunten in de actieve functiespecificatie en registreer de verduidelijkingen direct in het specbestand.

Opmerking: Deze verduidelijkingsworkflow wordt verwacht uit te voeren (en te voltooien) VOORDAT `/plan` wordt aangeroepen. Als de gebruiker expliciet stelt dat ze verduidelijking overslaan (bijv. verkennende spike), mag je doorgaan, maar moet waarschuwen dat downstream herwerk risico toeneemt.

Uitvoeringsstappen:

1. Voer `{SCRIPT}` uit vanaf repo root **eenmaal** (gecombineerde `--json --paths-only` mode / `-Json -PathsOnly`). Parseer minimale JSON payload velden:
   - `FEATURE_DIR`
   - `FEATURE_SPEC`
   - (Optioneel vastleggen `IMPL_PLAN`, `TASKS` voor toekomstige gekoppelde flows.)
   - Indien JSON parsing faalt, breek af en instrueer gebruiker om `/specify` opnieuw uit te voeren of functie branch omgeving te verifiëren.

2. Laad het huidige specbestand. Voer een gestructureerde dubbelzinnigheid & dekkingsscan uit met behulp van deze taxonomie. Voor elke categorie, markeer status: Duidelijk / Gedeeltelijk / Ontbrekend. Produceer een interne dekkingskaart gebruikt voor prioritering (geef ruwe kaart niet uit tenzij geen vragen gesteld worden).

   Functionele Bereik & Gedrag:
   - Kern gebruikersdoelen & succescriteria
   - Expliciete buiten-bereik verklaringen
   - Gebruikersrollen / persona's differentiatie

   Domein & Datamodel:
   - Entiteiten, attributen, relaties
   - Identiteit & uniciteitsregels
   - Levenscyclus/staat transities
   - Datavolume / schaal aannames

   Interactie & UX Flow:
   - Kritieke gebruikersreizen / sequenties
   - Fout/leeg/laad staten
   - Toegankelijkheid of lokalisatie notities

   Niet-Functionele Kwaliteitsattributen:
   - Prestaties (latentie, doorvoer doelen)
   - Schaalbaarheid (horizontaal/verticaal, limieten)
   - Betrouwbaarheid & beschikbaarheid (uptime, herstel verwachtingen)
   - Observeerbaarheid (logging, metrieken, tracing signalen)
   - Beveiliging & privacy (authN/Z, gegevensbescherming, dreigingsaannames)
   - Compliance / regulatoire beperkingen (indien van toepassing)

   Integratie & Externe Afhankelijkheden:
   - Externe services/API's en faalmodi
   - Data import/export formaten
   - Protocol/versioning aannames

   Randgevallen & Faalafhandeling:
   - Negatieve scenario's
   - Rate limiting / throttling
   - Conflictoplossing (bijv. gelijktijdige bewerkingen)

   Beperkingen & Afwegingen:
   - Technische beperkingen (taal, opslag, hosting)
   - Expliciete afwegingen of afgewezen alternatieven

   Terminologie & Consistentie:
   - Canonieke glossarium termen
   - Vermeden synoniemen / afgekeurde termen

   Voltooiingssignalen:
   - Acceptatiecriteria testbaarheid
   - Meetbare Definition of Done stijl indicatoren

   Misc / Placeholders:
   - TODO markeringen / onopgeloste beslissingen
   - Dubbelzinnige bijvoeglijke naamwoorden ("robuust", "intuïtief") die kwantificatie missen

   Voor elke categorie met Gedeeltelijke of Ontbrekende status, voeg een kandidaat vraagmogelijkheid toe tenzij:
   - Verduidelijking zou implementatie of validatiestrategie niet materieel veranderen
   - Informatie is beter uitgesteld naar planningsfase (noteer intern)

3. Genereer (intern) een geprioriteerde wachtrij van kandidaat verduidelijkingsvragen (maximaal 5). Geef ze NIET allemaal tegelijk uit. Pas deze beperkingen toe:
    - Maximaal 5 totale vragen over de hele sessie.
    - Elke vraag moet beantwoordbaar zijn met OFWEL:
       * Een korte meerkeuze selectie (2–5 onderscheiden, wederzijds exclusieve opties), OF
       * Een één-woord / korte-zin antwoord (expliciet beperken: "Antwoord in <=5 woorden").
   - Voeg alleen vragen toe waarvan antwoorden materieel impact hebben op architectuur, datamodellering, taakdecompositie, testontwerp, UX gedrag, operationele gereedheid, of compliance validatie.
   - Zorg voor categorie dekkingsbalans: probeer eerst de hoogste impact onopgeloste categorieën te dekken; vermijd twee lage-impact vragen te stellen wanneer een enkele hoge-impact gebied (bijv. beveiligingshouding) onopgelost is.
   - Sluit reeds beantwoorde vragen, triviale stilistische voorkeuren, of plan-niveau uitvoeringsdetails uit (tenzij correctheid blokkeren).
   - Geef voorkeur aan verduidelijkingen die downstream herwerk risico verminderen of misgelijnde acceptatietests voorkomen.
   - Indien meer dan 5 categorieën onopgelost blijven, selecteer de top 5 door (Impact * Onzekerheid) heuristiek.

4. Sequentiële vragenloop (interactief):
    - Presenteer PRECIES ÉÉN vraag tegelijk.
    - Voor meerkeuze vragen render opties als een Markdown tabel:

       | Optie | Beschrijving |
       |-------|-------------|
       | A | <Optie A beschrijving> |
       | B | <Optie B beschrijving> |
       | C | <Optie C beschrijving> | (voeg D/E toe indien nodig tot 5)
       | Kort | Geef een ander kort antwoord (<=5 woorden) | (Voeg alleen toe indien vrije-vorm alternatief geschikt is)

    - Voor kort-antwoord stijl (geen betekenisvolle discrete opties), geef een enkele regel uit na de vraag: `Formaat: Kort antwoord (<=5 woorden)`.
    - Na het antwoord van de gebruiker:
       * Valideer dat het antwoord naar een optie wijst of binnen de <=5 woorden beperking past.
       * Indien dubbelzinnig, vraag om snelle disambiguatie (tel hoort nog steeds bij dezelfde vraag; ga niet verder).
       * Eenmaal bevredigend, registreer het in werkgeheugen (schrijf nog niet naar schijf) en ga naar de volgende wachtrijvraag.
    - Stop met verdere vragen stellen wanneer:
       * Alle kritieke dubbelzinnigheden vroeg opgelost (overgebleven wachtrij items worden onnodig), OF
       * Gebruiker geeft voltooiing aan ("klaar", "goed", "geen meer"), OF
       * Je bereikt 5 gestelde vragen.
    - Onthul nooit toekomstige wachtrijvragen vooraf.
    - Indien geen geldige vragen bestaan bij start, rapporteer onmiddellijk geen kritieke dubbelzinnigheden.

5. Integratie na ELK geaccepteerd antwoord (incrementele update aanpak):
    - Onderhoud in-geheugen representatie van de spec (eenmaal geladen bij start) plus de ruwe bestandsinhoud.
    - Voor het eerste geïntegreerde antwoord in deze sessie:
       * Zorg dat een `## Verduidelijkingen` sectie bestaat (maak het net na de hoogste-niveau contextuele/overzicht sectie per de spec template indien ontbrekend).
       * Daaronder, maak (indien niet aanwezig) een `### Sessie YYYY-MM-DD` subkop voor vandaag.
    - Voeg onmiddellijk na acceptatie een bullet regel toe: `- V: <vraag> → A: <eindantwoord>`.
    - Pas dan onmiddellijk de verduidelijking toe op de meest geschikte sectie(s):
       * Functionele dubbelzinnigheid → Update of voeg een bullet toe in Functionele Vereisten.
       * Gebruikersinteractie / actor onderscheid → Update Gebruikersverhalen of Actoren subsectie (indien aanwezig) met verduidelijkte rol, beperking, of scenario.
       * Data vorm / entiteiten → Update Datamodel (voeg velden, types, relaties toe) behoud volgorde; noteer toegevoegde beperkingen beknopt.
       * Niet-functionele beperking → Voeg toe/wijzig meetbare criteria in Niet-Functionele / Kwaliteitsattributen sectie (converteer vage bijvoeglijk naamwoord naar metriek of expliciet doel).
       * Randgeval / negatieve flow → Voeg nieuwe bullet toe onder Randgevallen / Foutafhandeling (of maak dergelijke subsectie indien template placeholder ervoor biedt).
       * Terminologie conflict → Normaliseer term over spec; behoud origineel alleen indien nodig door `(voorheen aangeduid als "X")` eenmaal toe te voegen.
    - Indien de verduidelijking een eerdere dubbelzinnige uitspraak ongeldig maakt, vervang die uitspraak in plaats van dupliceren; laat geen verouderde tegenstrijdige tekst achter.
    - Bewaar het specbestand NA elke integratie om risico van contextverlies te minimaliseren (atomische overschrijving).
    - Behoud formattering: herorden geen ongerelateerde secties; houd koppenstructuur intact.
    - Houd elke ingevoegde verduidelijking minimaal en testbaar (vermijd narratieve drift).

6. Validatie (uitgevoerd na ELKE schrijving plus eindpass):
   - Verduidelijkingensessie bevat precies één bullet per geaccepteerd antwoord (geen duplicaten).
   - Totaal gestelde (geaccepteerde) vragen ≤ 5.
   - Bijgewerkte secties bevatten geen achtergebleven vage placeholders die het nieuwe antwoord moest oplossen.
   - Geen tegenstrijdige eerdere uitspraak blijft (scan voor nu-ongeldige alternatieve keuzes verwijderd).
   - Markdown structuur geldig; alleen toegestane nieuwe koppen: `## Verduidelijkingen`, `### Sessie YYYY-MM-DD`.
   - Terminologie consistentie: dezelfde canonieke term gebruikt over alle bijgewerkte secties.

7. Schrijf de bijgewerkte spec terug naar `FEATURE_SPEC`.

8. Rapporteer voltooiing (na vragenloop beëindiging of vroege beëindiging):
   - Aantal vragen gesteld & beantwoord.
   - Pad naar bijgewerkte spec.
   - Aangeraakte secties (lijst namen).
   - Dekkingssamenvatting tabel met elke taxonomie categorie met Status: Opgelost (was Gedeeltelijk/Ontbrekend en aangepakt), Uitgesteld (overschrijdt vragen quota of beter geschikt voor planning), Duidelijk (reeds voldoende), Uitstaand (nog steeds Gedeeltelijk/Ontbrekend maar lage impact).
   - Indien Uitstaand of Uitgesteld blijven, beveel aan of door te gaan naar `/plan` of `/clarify` opnieuw later na-plan uit te voeren.
   - Voorgesteld volgend commando.

Gedragsregels:
- Indien geen betekenisvolle dubbelzinnigheden gevonden (of alle potentiële vragen zouden lage-impact zijn), antwoord: "Geen kritieke dubbelzinnigheden gedetecteerd die formele verduidelijking waard zijn." en stel doorgaan voor.
- Indien specbestand ontbreekt, instrueer gebruiker om eerst `/specify` uit te voeren (maak hier geen nieuwe spec).
- Overschrijd nooit 5 totale gestelde vragen (verduidelijking herhalingen voor één vraag tellen niet als nieuwe vragen).
- Vermijd speculatieve tech stack vragen tenzij afwezigheid functionele duidelijkheid blokkeert.
- Respecteer gebruiker vroege beëindigingssignalen ("stop", "klaar", "doorgaan").
 - Indien geen vragen gesteld vanwege volledige dekking, geef compacte dekkingssamenvatting uit (alle categorieën Duidelijk) stel dan vooruitgang voor.
 - Indien quota bereikt met onopgeloste hoge-impact categorieën overgebleven, markeer ze expliciet onder Uitgesteld met rationale.

Context voor prioritering: {ARGS}
