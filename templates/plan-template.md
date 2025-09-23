---
description: "Implementatieplan sjabloon voor functie-ontwikkeling"
scripts:
  sh: scripts/bash/update-agent-context.sh __AGENT__
  ps: scripts/powershell/update-agent-context.ps1 -AgentType __AGENT__
---

# Implementatieplan: [FEATURE]

**Branch**: `[###-feature-name]` | **Datum**: [DATE] | **Spec**: [link]
**Invoer**: Functiespecificatie van `/specs/[###-feature-name]/spec.md`

## Uitvoeringsstroom (/plan commando bereik)
```
1. Laad functiespec van Invoerpad
   → Indien niet gevonden: FOUT "Geen functiespec op {pad}"
2. Vul Technische Context in (scan voor VERDUIDELIJKING NODIG)
   → Detecteer Projecttype uit context (web=frontend+backend, mobiel=app+api)
   → Stel Structuurbeslissing in gebaseerd op projecttype
3. Vul de Grondwetcontrole sectie in gebaseerd op de inhoud van het grondwetdocument.
4. Evalueer Grondwetcontrole sectie hieronder
   → Indien overtredingen bestaan: Documenteer in Complexiteitsvolging
   → Indien geen rechtvaardiging mogelijk: FOUT "Vereenvoudig aanpak eerst"
   → Update Voortgangsvolging: Initiële Grondwetcontrole
5. Voer Fase 0 uit → research.md
   → Indien VERDUIDELIJKING NODIG blijft: FOUT "Los onbekenden op"
6. Voer Fase 1 uit → contracten, data-model.md, quickstart.md, agent-specifiek sjabloonbestand (bijv. `CLAUDE.md` voor Claude Code, `.github/copilot-instructions.md` voor GitHub Copilot, `GEMINI.md` voor Gemini CLI, `QWEN.md` voor Qwen Code of `AGENTS.md` voor opencode).
7. Her-evalueer Grondwetcontrole sectie
   → Indien nieuwe overtredingen: Refactor ontwerp, keer terug naar Fase 1
   → Update Voortgangsvolging: Post-Ontwerp Grondwetcontrole
8. Plan Fase 2 → Beschrijf taakgeneratie aanpak (MAAK GEEN tasks.md)
9. STOP - Klaar voor /tasks commando
```

**BELANGRIJK**: Het /plan commando STOPT bij stap 7. Fasen 2-4 worden uitgevoerd door andere commando's:
- Fase 2: /tasks commando maakt tasks.md
- Fase 3-4: Implementatie-uitvoering (handmatig of via tools)

## Samenvatting
[Extraheer uit functiespec: primaire vereiste + technische aanpak uit onderzoek]

## Technische Context
**Taal/Versie**: [bijv. Python 3.11, Swift 5.9, Rust 1.75 of VERDUIDELIJKING NODIG]  
**Primaire Afhankelijkheden**: [bijv. FastAPI, UIKit, LLVM of VERDUIDELIJKING NODIG]  
**Opslag**: [indien van toepassing, bijv. PostgreSQL, CoreData, bestanden of N.v.t.]  
**Testen**: [bijv. pytest, XCTest, cargo test of VERDUIDELIJKING NODIG]  
**Doelplatform**: [bijv. Linux server, iOS 15+, WASM of VERDUIDELIJKING NODIG]
**Projecttype**: [enkel/web/mobiel - bepaalt bronstructuur]  
**Prestatiedoelen**: [domeinspecifiek, bijv. 1000 req/s, 10k regels/sec, 60 fps of VERDUIDELIJKING NODIG]  
**Beperkingen**: [domeinspecifiek, bijv. <200ms p95, <100MB geheugen, offline-capabel of VERDUIDELIJKING NODIG]  
**Schaal/Bereik**: [domeinspecifiek, bijv. 10k gebruikers, 1M LOC, 50 schermen of VERDUIDELIJKING NODIG]

## Grondwetcontrole
*POORT: Moet slagen voor Fase 0 onderzoek. Hercontrole na Fase 1 ontwerp.*

[Poorten bepaald op basis van grondwetbestand]

## Projectstructuur

### Documentatie (deze functie)
```
specs/[###-feature]/
├── plan.md              # Dit bestand (/plan commando uitvoer)
├── research.md          # Fase 0 uitvoer (/plan commando)
├── data-model.md        # Fase 1 uitvoer (/plan commando)
├── quickstart.md        # Fase 1 uitvoer (/plan commando)
├── contracts/           # Fase 1 uitvoer (/plan commando)
└── tasks.md             # Fase 2 uitvoer (/tasks commando - NIET gemaakt door /plan)
```

### Broncode (repository root)
```
# Optie 1: Enkel project (STANDAARD)
src/
├── models/
├── services/
├── cli/
└── lib/

tests/
├── contract/
├── integration/
└── unit/

# Optie 2: Webapplicatie (wanneer "frontend" + "backend" gedetecteerd)
backend/
├── src/
│   ├── models/
│   ├── services/
│   └── api/
└── tests/

frontend/
├── src/
│   ├── components/
│   ├── pages/
│   └── services/
└── tests/

# Optie 3: Mobiel + API (wanneer "iOS/Android" gedetecteerd)
api/
└── [hetzelfde als backend hierboven]

ios/ of android/
└── [platform-specifieke structuur]
```

**Structuurbeslissing**: [STANDAARD naar Optie 1 tenzij Technische Context web/mobiele app aangeeft]

## Fase 0: Overzicht & Onderzoek
1. **Extraheer onbekenden uit Technische Context** hierboven:
   - Voor elke VERDUIDELIJKING NODIG → onderzoekstaak
   - Voor elke afhankelijkheid → best practices taak
   - Voor elke integratie → patronen taak

2. **Genereer en verstuur onderzoeksagenten**:
   ```
   Voor elke onbekende in Technische Context:
     Taak: "Onderzoek {onbekende} voor {functie context}"
   Voor elke technologie keuze:
     Taak: "Vind best practices voor {tech} in {domein}"
   ```

3. **Consolideer bevindingen** in `research.md` met formaat:
   - Beslissing: [wat gekozen werd]
   - Rationale: [waarom gekozen]
   - Alternatieven overwogen: [wat anders geëvalueerd]

**Uitvoer**: research.md met alle VERDUIDELIJKING NODIG opgelost

## Fase 1: Ontwerp & Contracten
*Vereisten: research.md voltooid*

1. **Extraheer entiteiten uit functie spec** → `data-model.md`:
   - Entiteitnaam, velden, relaties
   - Validatieregels uit vereisten
   - Staat transities indien van toepassing

2. **Genereer API contracten** uit functionele vereisten:
   - Voor elke gebruikersactie → endpoint
   - Gebruik standaard REST/GraphQL patronen
   - Uitvoer OpenAPI/GraphQL schema naar `/contracts/`

3. **Genereer contract tests** uit contracten:
   - Een testbestand per endpoint
   - Bevestig request/response schema's
   - Tests moeten falen (nog geen implementatie)

4. **Extraheer test scenario's** uit gebruikersverhalen:
   - Elk verhaal → integratietest scenario
   - Quickstart test = verhaal validatie stappen

5. **Update agent bestand incrementeel** (O(1) operatie):
   - Voer `{SCRIPT}` uit
     **BELANGRIJK**: Voer het precies uit zoals hierboven gespecificeerd. Voeg geen argumenten toe of verwijder ze.
   - Indien bestaat: Voeg alleen NIEUWE tech toe uit huidig plan
   - Behoud handmatige toevoegingen tussen markeringen
   - Update recente wijzigingen (behoud laatste 3)
   - Houd onder 150 regels voor token efficiëntie
   - Uitvoer naar repository root

**Uitvoer**: data-model.md, /contracts/*, falende tests, quickstart.md, agent-specifiek bestand

## Fase 2: Taakplanning Aanpak
*Deze sectie beschrijft wat het /tasks commando zal doen - VOER NIET UIT tijdens /plan*

**Taakgeneratie Strategie**:
- Laad `.specify/templates/tasks-template.md` als basis
- Genereer taken uit Fase 1 ontwerp docs (contracten, data model, quickstart)
- Elk contract → contract test taak [P]
- Elke entiteit → model creatie taak [P] 
- Elk gebruikersverhaal → integratietest taak
- Implementatie taken om tests te laten slagen

**Volgorde Strategie**:
- TDD volgorde: Tests voor implementatie 
- Afhankelijkheidsvolgorde: Modellen voor services voor UI
- Markeer [P] voor parallelle uitvoering (onafhankelijke bestanden)

**Geschatte Uitvoer**: 25-30 genummerde, geordende taken in tasks.md

**BELANGRIJK**: Deze fase wordt uitgevoerd door het /tasks commando, NIET door /plan

## Fase 3+: Toekomstige Implementatie
*Deze fasen zijn buiten het bereik van het /plan commando*

**Fase 3**: Taakuitvoering (/tasks commando maakt tasks.md)  
**Fase 4**: Implementatie (voer tasks.md uit volgens grondwettelijke principes)  
**Fase 5**: Validatie (voer tests uit, voer quickstart.md uit, prestatie validatie)

## Complexiteitsvolging
*Vul ALLEEN in als Grondwetcontrole overtredingen heeft die gerechtvaardigd moeten worden*

| Overtreding | Waarom Nodig | Eenvoudiger Alternatief Afgewezen Omdat |
|-------------|--------------|----------------------------------------|
| [bijv. 4e project] | [huidige behoefte] | [waarom 3 projecten onvoldoende] |
| [bijv. Repository patroon] | [specifiek probleem] | [waarom directe DB toegang onvoldoende] |


## Voortgangsvolging
*Deze checklist wordt bijgewerkt tijdens uitvoeringsstroom*

**Fase Status**:
- [ ] Fase 0: Onderzoek voltooid (/plan commando)
- [ ] Fase 1: Ontwerp voltooid (/plan commando)
- [ ] Fase 2: Taakplanning voltooid (/plan commando - beschrijf alleen aanpak)
- [ ] Fase 3: Taken gegenereerd (/tasks commando)
- [ ] Fase 4: Implementatie voltooid
- [ ] Fase 5: Validatie geslaagd

**Poort Status**:
- [ ] Initiële Grondwetcontrole: GESLAAGD
- [ ] Post-Ontwerp Grondwetcontrole: GESLAAGD
- [ ] Alle VERDUIDELIJKING NODIG opgelost
- [ ] Complexiteitsafwijkingen gedocumenteerd

---
*Gebaseerd op Grondwet v2.1.1 - Zie `/memory/constitution.md`*
