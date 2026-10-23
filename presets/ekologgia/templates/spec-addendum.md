---

## Périmètre Ekologgia *(obligatoire)*

> Section ajoutée par le preset `ekologgia`. Rédigée en français — le français est
> la langue canonique des artefacts projet.

### Workspaces touchés

Coche les workspaces du monorepo que cette feature modifie. Une feature qui
touche plusieurs workspaces doit expliciter le contrat entre eux.

- [ ] `apps/api` — API HTTP (NestJS + Mongoose)
- [ ] `apps/web` — front public et espaces notaire/négociateur/staff (Next.js)
- [ ] `apps/backoffice` — back-office interne (Vite + React-admin)
- [ ] `apps/cli` — synchronisation nocturne (AWS Batch)
- [ ] `apps/cdk` — infrastructure (AWS CDK)
- [ ] `packages/core` — entités Mongoose, schémas Zod, services partagés
- [ ] Autre : [PRÉCISER]

**Contrat inter-workspaces** : [Si plusieurs workspaces sont cochés, décrire ce
qui circule entre eux — endpoint, type partagé, événement. Sinon : « sans objet ».]

### Modèle de données

- **Entités touchées** : [`listing`, `contact`, `estimation`, … ou « aucune »]
- **Nouveau champ / nouvelle entité ?** [Oui/Non — si oui, il est défini dans
  `packages/core` et **jamais** dupliqué dans un app. Voir la règle de modèle
  unique dans la constitution.]
- **Migration nécessaire ?** [Oui/Non — si oui, décrire l'état des documents
  existants et la stratégie de rétrocompatibilité.]

### Intégrations externes

Pour chaque service tiers appelé (Property Intelligence, PERVAL, SendGrid,
OpenAI, ADNOV, Noty Broadcast, BAN/adresse.data.gouv.fr, Stripe…) :

| Service | Usage | Comportement si indisponible ou non configuré |
| --- | --- | --- |
| [Nom] | [Ce qu'on lui demande] | [Fail-closed attendu — voir ci-dessous] |

**Règle fail-closed** : aucune donnée métier ne doit être inventée quand un
service externe est absent. Soit un stub explicite activé par variable
d'environnement et porteur d'un `disclaimer`, soit un échec explicite. Un
comportement dégradé silencieux est un défaut de spécification, pas un choix
d'implémentation.

### Impact documentaire

Cette feature imposera une mise à jour de (cocher ce qui s'applique) :

- [ ] `docs/architecture.md` — nouveau composant, flux, ou choix technique
- [ ] `docs/workflows.md` — workflow métier ou technique modifié
- [ ] `docs/decisions/` — ADR requis (décision technique non triviale)
- [ ] `docs/setup.md` — nouvelle variable d'environnement ou commande
- [ ] `docs/changelog.md` — toujours coché pour une feature livrée

> Le miroir anglais `docs/en/` est **régénéré** depuis le français, jamais édité
> à la main. Il n'a donc pas à être listé ici.
