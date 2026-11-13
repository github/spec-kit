---

## Définition de terminé — Ekologgia

> Section ajoutée par le preset `ekologgia`. Elle complète la section
> « Done When » du coeur : les deux s'appliquent.

Ces conditions ne sont pas des suggestions de fin de course. Une tâche
d'implémentation qui modifie le comportement du système n'est pas terminée tant
que la documentation correspondante n'est pas à jour.

### Règles d'exécution

1. **Documentation avant clôture.** Après toute modification significative —
   nouvelle feature, refacto, changement d'architecture, nouvelle dépendance,
   nouvel endpoint, changement de schéma de données — mettre à jour les fichiers
   concernés dans `docs/` **avant** de considérer la tâche terminée.

2. **ADR pour les décisions non triviales.** Si l'implémentation impose une
   décision technique qui n'était pas dans le plan (choix de bibliothèque,
   pattern, compromis de performance ou de sécurité), rédiger un ADR daté dans
   `docs/decisions/` au format contexte / décision / alternatives écartées /
   conséquences. Ne pas attendre la relecture.

3. **Français canonique, anglais régénéré.** Écrire la documentation en français,
   de façon concise et factuelle. Régénérer ensuite les fichiers correspondants
   dans `docs/en/` — ne jamais éditer le miroir anglais directement.

4. **Documenter le pourquoi, pas la ligne.** Le code documente le détail. `docs/`
   documente le pourquoi et le comment global. Quelqu'un qui rejoint le projet
   doit comprendre le système en quinze minutes de lecture.

5. **Signaler les écarts.** En cas de divergence entre la documentation existante
   et le code réel, corriger la documentation et le signaler explicitement dans
   le rapport de complétion.

6. **Fail-closed.** Ne jamais livrer un chemin de code qui invente une donnée
   métier quand un service externe est absent. Stub explicite activé par variable
   d'environnement et porteur d'un `disclaimer`, ou échec explicite — rien d'autre.

7. **Modèle unique.** Les entités Mongoose et schémas Zod partagés vivent dans
   `packages/core`. Ne pas dupliquer une définition de type dans un app parce que
   c'était plus rapide.

8. **Rapporter la vérification honnêtement.** Exécuter `pnpm lint`,
   `pnpm check-types` et les tests des workspaces touchés. Reporter le résultat
   réel, y compris les échecs et les zones sans couverture de test. Le dépôt
   n'exécute pas les tests en CI : ce rapport est la seule vérification.

### Done When — Ekologgia

- [ ] `docs/architecture.md` et `docs/workflows.md` reflètent le code livré
- [ ] Un ADR daté existe pour chaque décision technique non triviale
- [ ] `docs/setup.md` liste toute nouvelle variable d'environnement ou commande
- [ ] `docs/changelog.md` porte une entrée datée de 2 à 3 lignes
- [ ] Les fichiers modifiés de `docs/` ont leur miroir régénéré dans `docs/en/`
- [ ] `pnpm lint` et `pnpm check-types` passent sur les workspaces touchés
- [ ] Le résultat réel des tests est reporté, échecs et lacunes compris
- [ ] Tout écart doc ↔ code découvert en chemin est corrigé et signalé
