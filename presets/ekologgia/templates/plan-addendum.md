---

## Revue Ekologgia *(obligatoire)*

> Section ajoutée par le preset `ekologgia`. À remplir avant de générer les tâches.

### Décisions d'architecture (ADR)

Liste chaque décision technique non triviale prise dans ce plan : choix de
bibliothèque, pattern, compromis de performance ou de sécurité, ajout d'une
dépendance, changement de schéma de données, nouvelle intégration externe.

| Décision | Non triviale ? | ADR |
| --- | --- | --- |
| [Décision] | [Oui/Non] | [`docs/decisions/AAAA-MM-JJ-titre-court.md` ou « sans objet »] |

Chaque ADR suit le format maison : **contexte**, **décision**,
**alternatives écartées**, **conséquences**. Le nom de fichier est daté
(`AAAA-MM-JJ-titre-court.md`). Écrire l'ADR fait partie du plan, pas de la
relecture : la tâche correspondante doit apparaître dans `tasks.md`.

Si aucune décision non triviale n'est prise, l'écrire explicitement — un plan
sans ADR est un signal, pas un oubli toléré par défaut.

### Modèle de données partagé

- Les entités Mongoose et schémas Zod vivent dans `packages/core` et sont
  consommés par `apps/api`, `apps/cli` et les scripts de seed via `workspace:*`.
- **Vérification** : ce plan introduit-il une définition de type ou de schéma
  qui existe déjà, ou qui devrait vivre dans `packages/core` ?
  [Réponse — si oui, corriger le plan avant de continuer.]
- Un changement de `packages/core` impacte **tous** ses consommateurs. Lister
  ceux qui devront être rebuild ou adaptés : [liste ou « aucun »]

### Intégrations externes et fail-closed

Pour chaque appel sortant introduit ou modifié :

- **Service** : [nom]
- **Configuration** : [variables d'environnement requises]
- **Chemin nominal** : [comportement quand le service répond]
- **Chemin dégradé** : [stub explicite activé par variable d'environnement, avec
  `disclaimer` dans la réponse — ou échec explicite]
- **Production sans configuration** : doit échouer explicitement. Aucune valeur
  plausible inventée. [Confirmer que le plan respecte ce point.]

### Sécurité et autorisations

Pour chaque route ou commande ajoutée :

| Route / commande | Guard | Rôles autorisés |
| --- | --- | --- |
| [`METHOD /chemin`] | [`JwtAuthGuard` / public / …] | [`@Roles(...)` ou « public »] |

`RolesGuard` s'applique **après** `JwtAuthGuard`. Une route sans ligne dans ce
tableau est une route non revue, pas une route publique.

- **Secrets** : ce plan introduit-il une nouvelle variable d'environnement
  sensible ? [Oui/Non — si oui, elle est documentée dans `docs/setup.md` et
  jamais commitée.]
- **Données personnelles** : cette feature manipule-t-elle des données de
  vendeurs, acheteurs ou notaires ? [Oui/Non — si oui, préciser la rétention et
  qui y accède.]

### Vérification

Le dépôt n'exécute **pas** les tests en CI aujourd'hui (les workflows GitHub
Actions ne couvrent que le déploiement). La vérification est donc à la charge du
plan, explicitement.

- **Commandes de vérification** : [`pnpm lint`, `pnpm check-types`, et les tests
  du ou des workspaces touchés — préciser les commandes exactes]
- **Couverture de test attendue** : [quels comportements sont couverts par un
  test automatisé, et lesquels sont vérifiés manuellement et pourquoi]
- **Vérification manuelle** : [étapes reproductibles, ou `scripts/demo-local.sh`
  si le flux complet est concerné]
