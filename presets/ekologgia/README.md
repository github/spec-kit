# Ekologgia Engineering Standards

Preset Spec Kit encodant les standards d'ingénierie Ekologgia, dérivés des
conventions réelles du monorepo NotaImmo/Notamap (`notaimmo-backend`).

## Ce que le preset impose

| Règle | Où elle s'applique |
| --- | --- |
| Documentation FR canonique, miroir EN régénéré | `spec`, `tasks`, `implement` |
| ADR daté pour toute décision technique non triviale | `plan`, `tasks`, `implement` |
| Intégrations externes fail-closed — aucune donnée inventée | `spec`, `plan`, `implement` |
| Périmètre monorepo explicite (workspaces touchés, contrat entre eux) | `spec` |
| Modèle de données partagé dans `packages/core`, jamais dupliqué | `spec`, `plan`, `implement` |
| Guard et rôles déclarés pour chaque route | `plan` |
| Vérification explicite (lint, types, tests) — la CI ne teste pas | `plan`, `tasks`, `implement` |

## Composition

Le preset n'écrase aucun template du coeur. Il utilise la stratégie `append` sur
quatre points d'extension, ce qui le rend cumulable avec d'autres presets :

| Cible | Fichier | Stratégie |
| --- | --- | --- |
| `spec-template` | `templates/spec-addendum.md` | `append` |
| `plan-template` | `templates/plan-addendum.md` | `append` |
| `tasks-template` | `templates/tasks-addendum.md` | `append` |
| `speckit.implement` | `commands/implement-addendum.md` | `append` |

## Installation

Depuis une copie locale du dépôt `spec-kit` :

```bash
specify preset add --dev /chemin/vers/spec-kit/presets/ekologgia
```

Vérifier l'installation :

```bash
specify preset list
```

## Adapter à un autre projet Ekologgia

Les sections « Workspaces touchés » (`spec-addendum.md`) et « Modèle de données
partagé » (`plan-addendum.md`) nomment explicitement les workspaces de
`notaimmo-backend`. Pour un autre dépôt, ajuster ces deux listes ; le reste des
règles est indépendant du projet.

## Origine des règles

Les règles proviennent de sources vérifiables du dépôt `notaimmo-backend` :

- `CLAUDE.md` — obligation documentaire, format ADR, français canonique, miroir EN
- `docs/architecture.md` — rôle de `packages/core` comme modèle unique, pattern
  adaptateur fournisseurs
- `docs/workflows.md` — politique fail-closed sur Property Intelligence, guards
  et rôles, absence de tests en CI
- `docs/decisions/2026-07-10-property-intelligence-stub-fail-closed.md` — la
  règle fail-closed déjà formalisée en ADR

## Licence

MIT.
