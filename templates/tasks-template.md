# Taken: [FEATURE NAME]

**Invoer**: Ontwerpdocumenten van `/specs/[###-feature-name]/`
**Vereisten**: plan.md (vereist), research.md, data-model.md, contracts/

## Uitvoeringsstroom (hoofdfunctie)
```
1. Laad plan.md van functiemap
   → Indien niet gevonden: FOUT "Geen implementatieplan gevonden"
   → Extraheer: tech stack, bibliotheken, structuur
2. Laad optionele ontwerpdocumenten:
   → data-model.md: Extraheer entiteiten → modeltaken
   → contracts/: Elk bestand → contract testtaak
   → research.md: Extraheer beslissingen → setup taken
3. Genereer taken per categorie:
   → Setup: project init, afhankelijkheden, linting
   → Tests: contract tests, integratietests
   → Kern: modellen, services, CLI commando's
   → Integratie: DB, middleware, logging
   → Polish: unit tests, prestaties, docs
4. Pas taakregels toe:
   → Verschillende bestanden = markeer [P] voor parallel
   → Zelfde bestand = sequentieel (geen [P])
   → Tests voor implementatie (TDD)
5. Nummer taken sequentieel (T001, T002...)
6. Genereer afhankelijkheidsgrafiek
7. Maak parallelle uitvoeringsvoorbeelden
8. Valideer taakvolledigheid:
   → Hebben alle contracten tests?
   → Hebben alle entiteiten modellen?
   → Zijn alle endpoints geïmplementeerd?
9. Retourneer: SUCCES (taken klaar voor uitvoering)
```

## Formaat: `[ID] [P?] Beschrijving`
- **[P]**: Kan parallel uitgevoerd worden (verschillende bestanden, geen afhankelijkheden)
- Voeg exacte bestandspaden toe in beschrijvingen

## Padconventies
- **Enkel project**: `src/`, `tests/` op repository root
- **Web app**: `backend/src/`, `frontend/src/`
- **Mobiel**: `api/src/`, `ios/src/` of `android/src/`
- Paden hieronder getoond gaan uit van enkel project - aanpassen gebaseerd op plan.md structuur

## Fase 3.1: Setup
- [ ] T001 Maak projectstructuur volgens implementatieplan
- [ ] T002 Initialiseer [taal] project met [framework] afhankelijkheden
- [ ] T003 [P] Configureer linting en formatting tools

## Fase 3.2: Tests Eerst (TDD) ⚠️ MOET VOLTOOID ZIJN VOOR 3.3
**KRITIEK: Deze tests MOETEN geschreven worden en MOETEN FALEN voor ELKE implementatie**
- [ ] T004 [P] Contract test POST /api/users in tests/contract/test_users_post.py
- [ ] T005 [P] Contract test GET /api/users/{id} in tests/contract/test_users_get.py
- [ ] T006 [P] Integratietest gebruikersregistratie in tests/integration/test_registration.py
- [ ] T007 [P] Integratietest auth flow in tests/integration/test_auth.py

## Fase 3.3: Kernimplementatie (ALLEEN nadat tests falen)
- [ ] T008 [P] Gebruikersmodel in src/models/user.py
- [ ] T009 [P] UserService CRUD in src/services/user_service.py
- [ ] T010 [P] CLI --create-user in src/cli/user_commands.py
- [ ] T011 POST /api/users endpoint
- [ ] T012 GET /api/users/{id} endpoint
- [ ] T013 Invoervalidatie
- [ ] T014 Foutafhandeling en logging

## Fase 3.4: Integratie
- [ ] T015 Verbind UserService met DB
- [ ] T016 Auth middleware
- [ ] T017 Request/response logging
- [ ] T018 CORS en beveiligingsheaders

## Fase 3.5: Polish
- [ ] T019 [P] Unit tests voor validatie in tests/unit/test_validation.py
- [ ] T020 Prestatietests (<200ms)
- [ ] T021 [P] Update docs/api.md
- [ ] T022 Verwijder duplicatie
- [ ] T023 Voer manual-testing.md uit

## Afhankelijkheden
- Tests (T004-T007) voor implementatie (T008-T014)
- T008 blokkeert T009, T015
- T016 blokkeert T018
- Implementatie voor polish (T019-T023)

## Parallel Voorbeeld
```
# Start T004-T007 samen:
Taak: "Contract test POST /api/users in tests/contract/test_users_post.py"
Taak: "Contract test GET /api/users/{id} in tests/contract/test_users_get.py"
Taak: "Integratietest registratie in tests/integration/test_registration.py"
Taak: "Integratietest auth in tests/integration/test_auth.py"
```

## Opmerkingen
- [P] taken = verschillende bestanden, geen afhankelijkheden
- Verifieer dat tests falen voor implementatie
- Commit na elke taak
- Vermijd: vage taken, zelfde bestand conflicten

## Taakgeneratieregels
*Toegepast tijdens main() uitvoering*

1. **Van Contracten**:
   - Elk contractbestand → contract testtaak [P]
   - Elk endpoint → implementatietaak
   
2. **Van Datamodel**:
   - Elke entiteit → modelcreatietaak [P]
   - Relaties → service laag taken
   
3. **Van Gebruikersverhalen**:
   - Elk verhaal → integratietest [P]
   - Quickstart scenario's → validatietaken

4. **Volgorde**:
   - Setup → Tests → Modellen → Services → Endpoints → Polish
   - Afhankelijkheden blokkeren parallelle uitvoering

## Validatiechecklist
*POORT: Gecontroleerd door main() voor retourneren*

- [ ] Alle contracten hebben bijbehorende tests
- [ ] Alle entiteiten hebben modeltaken
- [ ] Alle tests komen voor implementatie
- [ ] Parallelle taken zijn werkelijk onafhankelijk
- [ ] Elke taak specificeert exact bestandspad
- [ ] Geen taak wijzigt hetzelfde bestand als een andere [P] taak