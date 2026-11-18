---

## Phase de clôture Ekologgia *(obligatoire)*

> Section ajoutée par le preset `ekologgia`. Ces tâches sont **toujours**
> générées, en dernière phase, et ne sont jamais marquées optionnelles.

Une feature n'est pas terminée quand le code marche : elle est terminée quand la
documentation reflète le code. Ces tâches ferment cet écart.

### Vérification

- [ ] `T[N]` Exécuter `pnpm lint` sur les workspaces touchés — zéro erreur
- [ ] `T[N]` Exécuter `pnpm check-types` sur les workspaces touchés — zéro erreur
- [ ] `T[N]` Exécuter les tests des workspaces touchés et reporter le résultat réel
      (si aucun test n'existe pour la zone modifiée, l'écrire explicitement dans
      le rapport de complétion plutôt que de passer la tâche sous silence)

### Documentation (français — source canonique)

Générer une tâche par fichier réellement impacté, en s'appuyant sur la section
« Impact documentaire » de `spec.md`. Ne pas générer de tâche pour un fichier non
impacté.

- [ ] `T[N]` Mettre à jour `docs/architecture.md` — [composant, flux ou choix
      technique introduit, avec sa justification]
- [ ] `T[N]` Mettre à jour `docs/workflows.md` — [workflow métier ou technique
      modifié]
- [ ] `T[N]` Rédiger `docs/decisions/AAAA-MM-JJ-titre-court.md` — [une tâche par
      ADR identifié dans le plan : contexte, décision, alternatives écartées,
      conséquences]
- [ ] `T[N]` Mettre à jour `docs/setup.md` — [nouvelles variables
      d'environnement, prérequis ou commandes]
- [ ] `T[N]` Ajouter une entrée datée à `docs/changelog.md` — 2 à 3 lignes,
      factuelles

### Miroir anglais

- [ ] `T[N]` Régénérer les fichiers correspondants dans `docs/en/` depuis leur
      version française. Le miroir est **régénéré**, jamais édité à la main : ne
      régénérer que les fichiers dont la version FR a changé dans cette feature.

### Cohérence doc ↔ code

- [ ] `T[N]` Relire les fichiers `docs/` touchés à la recherche d'un écart avec le
      code réel. Corriger la documentation et signaler l'écart dans le rapport de
      complétion — un écart découvert est une information, pas une nuisance.
