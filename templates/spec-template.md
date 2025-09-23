# Functiespecificatie: [FEATURE NAME]

**Functie Branch**: `[###-feature-name]`  
**Aangemaakt**: [DATE]  
**Status**: Concept  
**Invoer**: Gebruikersbeschrijving: "$ARGUMENTS"

## Uitvoeringsstroom (hoofdfunctie)
```
1. Parseer gebruikersbeschrijving van Invoer
   → Indien leeg: FOUT "Geen functiebeschrijving opgegeven"
2. Haal kernconcepten uit beschrijving
   → Identificeer: actoren, acties, gegevens, beperkingen
3. Voor elk onduidelijk aspect:
   → Markeer met [VERDUIDELIJKING NODIG: specifieke vraag]
4. Vul Gebruikersscenario's & Testen sectie in
   → Indien geen duidelijke gebruikersstroom: FOUT "Kan gebruikersscenario's niet bepalen"
5. Genereer Functionele Vereisten
   → Elke vereiste moet testbaar zijn
   → Markeer dubbelzinnige vereisten
6. Identificeer Kernentiteiten (indien gegevens betrokken)
7. Voer Beoordelingschecklist uit
   → Indien [VERDUIDELIJKING NODIG]: WAARSCHUWING "Spec heeft onzekerheden"
   → Indien implementatiedetails gevonden: FOUT "Verwijder technische details"
8. Retourneer: SUCCES (spec klaar voor planning)
```

---

## ⚡ Snelle Richtlijnen
- ✅ Focus op WAT gebruikers nodig hebben en WAAROM
- ❌ Vermijd HOE te implementeren (geen tech stack, API's, codestructuur)
- 👥 Geschreven voor bedrijfsstakeholders, niet ontwikkelaars

### Sectievereisten
- **Verplichte secties**: Moeten worden voltooid voor elke functie
- **Optionele secties**: Alleen opnemen wanneer relevant voor de functie
- Wanneer een sectie niet van toepassing is, verwijder deze volledig (laat niet staan als "N.v.t.")

### Voor AI Generatie
Bij het maken van deze spec vanuit een gebruikersprompt:
1. **Markeer alle dubbelzinnigheden**: Gebruik [VERDUIDELIJKING NODIG: specifieke vraag] voor elke aanname die je zou moeten maken
2. **Gok niet**: Als de prompt iets niet specificeert (bijv. "inlogsysteem" zonder auth methode), markeer het
3. **Denk als een tester**: Elke vage vereiste zou moeten falen op het "testbaar en ondubbelzinnig" checklist item
4. **Veelvoorkomende ondergespecificeerde gebieden**:
   - Gebruikerstypes en machtigingen
   - Gegevensbehoud/verwijderingsbeleid  
   - Prestatiedoelen en schaal
   - Foutafhandelingsgedrag
   - Integratievereisten
   - Beveiliging/compliance behoeften

---

## Gebruikersscenario's & Testen *(verplicht)*

### Primair Gebruikersverhaal
[Beschrijf de hoofdgebruikersreis in gewone taal]

### Acceptatiescenario's
1. **Gegeven** [beginstaat], **Wanneer** [actie], **Dan** [verwachte uitkomst]
2. **Gegeven** [beginstaat], **Wanneer** [actie], **Dan** [verwachte uitkomst]

### Randgevallen
- Wat gebeurt er wanneer [grensvoorwaarde]?
- Hoe gaat het systeem om met [foutscenario]?

## Vereisten *(verplicht)*

### Functionele Vereisten
- **FV-001**: Systeem MOET [specifieke mogelijkheid, bijv. "gebruikers toestaan accounts aan te maken"]
- **FV-002**: Systeem MOET [specifieke mogelijkheid, bijv. "e-mailadressen valideren"]  
- **FV-003**: Gebruikers MOETEN [kerninteractie, bijv. "hun wachtwoord kunnen resetten"]
- **FV-004**: Systeem MOET [gegevensvereiste, bijv. "gebruikersvoorkeuren bewaren"]
- **FV-005**: Systeem MOET [gedrag, bijv. "alle beveiligingsgebeurtenissen loggen"]

*Voorbeeld van markeren onduidelijke vereisten:*
- **FV-006**: Systeem MOET gebruikers authenticeren via [VERDUIDELIJKING NODIG: auth methode niet gespecificeerd - email/wachtwoord, SSO, OAuth?]
- **FV-007**: Systeem MOET gebruikersgegevens bewaren voor [VERDUIDELIJKING NODIG: bewaringsperiode niet gespecificeerd]

### Kernentiteiten *(opnemen indien functie gegevens behelst)*
- **[Entiteit 1]**: [Wat het vertegenwoordigt, kernattributen zonder implementatie]
- **[Entiteit 2]**: [Wat het vertegenwoordigt, relaties tot andere entiteiten]

---

## Beoordeling & Acceptatiechecklist
*POORT: Geautomatiseerde controles uitgevoerd tijdens main() uitvoering*

### Contentkwaliteit
- [ ] Geen implementatiedetails (talen, frameworks, API's)
- [ ] Gericht op gebruikerswaarde en bedrijfsbehoeften
- [ ] Geschreven voor niet-technische stakeholders
- [ ] Alle verplichte secties voltooid

### Vereistenvolledigheid
- [ ] Geen [VERDUIDELIJKING NODIG] markeringen over
- [ ] Vereisten zijn testbaar en ondubbelzinnig  
- [ ] Succescriteria zijn meetbaar
- [ ] Scope is duidelijk afgebakend
- [ ] Afhankelijkheden en aannames geïdentificeerd

---

## Uitvoeringsstatus
*Bijgewerkt door main() tijdens verwerking*

- [ ] Gebruikersbeschrijving geparseerd
- [ ] Kernconcepten geëxtraheerd
- [ ] Dubbelzinnigheden gemarkeerd
- [ ] Gebruikersscenario's gedefinieerd
- [ ] Vereisten gegenereerd
- [ ] Entiteiten geïdentificeerd
- [ ] Beoordelingschecklist geslaagd

---
