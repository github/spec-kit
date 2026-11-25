<div align="center">
    <img src="https://raw.githubusercontent.com/github/spec-kit/main/media/logo_large.webp" alt="Logo de Spec Kit" width="200" height="200"/>
    <h1>🌱 Spec Kit</h1>
    <h3><em>Développez à partir d'une spécification, corrigez un bug ou évaluez une idée, avec votre agent de codage.</em></h3>
</div>

<p align="center">
    <a href="https://github.com/github/spec-kit/releases/latest"><img src="https://img.shields.io/github/v/release/github/spec-kit" alt="Dernière version"/></a>
    <a href="https://github.com/github/spec-kit/stargazers"><img src="https://img.shields.io/github/stars/github/spec-kit?style=social" alt="Étoiles GitHub"/></a>
    <a href="https://github.com/github/spec-kit/blob/main/LICENSE"><img src="https://img.shields.io/github/license/github/spec-kit" alt="Licence"/></a>
    <a href="https://github.github.io/spec-kit/"><img src="https://img.shields.io/badge/docs-GitHub_Pages-blue" alt="Documentation"/></a>
</p>

<p align="center">
    <a href="./README.md">English</a> ·
    <a href="./README.zh-CN.md">简体中文</a> ·
    <a href="./README.ja.md">日本語</a> ·
    <a href="./README.ko.md">한국어</a> ·
    <strong>Français</strong>
</p>

Spec Kit est une boîte à outils open source qui apporte aux agents de codage IA
des processus structurés, des modèles réutilisables et des résultats documentés.
Partez d'un processus prêt à l'emploi, adaptez-le ou apportez le vôtre.

## Choisir son processus

| Votre besoin | Processus | Résultat |
| --- | --- | --- |
| Construire une fonctionnalité ou une application | [Développement piloté par les spécifications](#développement-piloté-par-les-spécifications) | Une spécification menée jusqu'au plan, à l'implémentation et à la convergence |
| Diagnostiquer et réparer un comportement défaillant | [Correction de bugs](#correction-de-bugs) | Une cause évaluée, un correctif au périmètre défini et une vérification consignée |
| Décider si une idée mérite qu'on y investisse | [Évaluation d'idées](#évaluation-didées) | Une décision étayée : poursuivre, clarifier ou arrêter |
| Adopter ou créer un autre processus | [Votre propre processus](#fonctionnalités) | Un processus adapté ou assemblé à partir de briques réutilisables |

Ce sont des points d'entrée indépendants, pas des étapes obligatoires. Le SDD est
inclus dans le cœur ; la correction de bugs et l'évaluation sont des extensions
fournies avec Spec Kit, à installer au besoin, et les briques ci-dessous
permettent d'adopter ou de créer d'autres processus.

## Fonctionnalités

Spec Kit associe des processus prêts à l'emploi à des mécanismes combinables :

| Fonctionnalité | Mécanisme de Spec Kit |
| --- | --- |
| Se connecter à des agents de codage ou passer de l'un à l'autre | [Intégration](https://github.github.io/spec-kit/integrations/index.html) |
| Ajouter une commande, un point de contrôle qualité ou un processus complet | [Extension](https://github.github.io/spec-kit/reference/extensions.html) |
| Relier un processus à un outil ou à un service externe | [Extension](https://github.github.io/spec-kit/reference/extensions.html) |
| Réagir aux événements du cycle de vie de l'agent de codage | [Événement d'exécution d'extension](https://github.github.io/spec-kit/reference/extensions.html#extension-runtime-events) |
| Lancer des commandes d'extension avant ou après les commandes de Spec Kit | [Hook d'extension](https://github.github.io/spec-kit/reference/extensions.html#project-extension-and-hook-configuration) |
| Adapter les modèles, les commandes, la terminologie ou la méthode | [Preset](https://github.github.io/spec-kit/reference/presets.html) |
| Faire respecter des normes internes ou réglementaires | [Preset](https://github.github.io/spec-kit/reference/presets.html) |
| Remplacer un modèle pour un seul projet | [Surcharge locale au projet](https://github.github.io/spec-kit/guides/customization.html#project-local-overrides-and-resolution) |
| Automatiser des prompts, des commandes, des contrôles et des tâches shell | [Workflow](https://github.github.io/spec-kit/reference/workflows.html) |
| Modifier un workflow installé sans le forker | [Surcouche de workflow](https://github.github.io/spec-kit/reference/workflows.html#workflow-overlays) |
| Ajouter aux workflows un comportement exécutable réutilisable | [Étape de workflow](https://github.github.io/spec-kit/reference/workflows.html#custom-step-packages) |
| Installer une configuration soigneusement composée pour un rôle ou une équipe | [Bundle](https://github.github.io/spec-kit/reference/bundles.html) |
| Découvrir les composants de la communauté | [Catalogue](https://github.github.io/spec-kit/reference/catalogs.html) |
| Héberger un catalogue privé de composants approuvés | [Catalogue](https://github.github.io/spec-kit/reference/catalogs.html) |
| Accéder aux catalogues privés et aux téléchargements de composants | [Authentification](https://github.github.io/spec-kit/reference/authentication.html) |
| Travailler hors ligne ou derrière un pare-feu | [Sources locales et catalogues auto-hébergés](https://github.github.io/spec-kit/install/air-gapped.html) |
| Voir quelle couche fournit une commande, un modèle ou un script | [Inventaire des artefacts](https://github.github.io/spec-kit/reference/artifacts.html) |

Cherchez dans les catalogues actifs avec des commandes comme `specify extension search`,
`specify preset search`, `specify workflow search` et `specify bundle search`.
Spec Kit inclut des catalogues de la communauté, et les organisations peuvent
ajouter leurs propres sources sélectionnées. Figurer dans un catalogue n'est ni un
audit ni une recommandation : relisez le code source des composants de la
communauté avant de les installer ou de les exécuter.

<a id="-get-started"></a>
<a id="-prerequisites"></a>

## Démarrer

Il vous faut Python 3.11+, [uv](https://github.github.io/spec-kit/install/uv.html)
et un agent de codage IA pris en charge, sous Linux, macOS ou Windows.

Lancez ces commandes dans votre terminal pour installer Spec Kit et créer un projet.
Cet exemple utilise GitHub Copilot.

```bash
uv tool install specify-cli
specify init my-project --integration copilot
cd my-project
```

<a id="-supported-ai-coding-agent-integrations"></a>

Une fois le CLI Specify installé et le projet créé, lancez votre agent de codage
dans le dossier du projet, puis choisissez un processus ci-dessous.

Pour d'autres configurations :

- [Installation](https://github.github.io/spec-kit/installation.html) : versions figées, autres installateurs, CI et dépannage.
- [Projets existants](https://github.github.io/spec-kit/guides/existing-projects.html) : démarrer avec du code que vous avez déjà.
- [Autres agents](https://github.github.io/spec-kit/integrations/index.html) : clés d'intégration et [syntaxe d'appel](https://github.github.io/spec-kit/integrations/cli.html#command-invocation).
- [Mise à jour](https://github.github.io/spec-kit/upgrade.html) : mettre à jour une installation existante.

<a id="-what-is-spec-driven-development"></a>
<a id="sdd-quickstart"></a>

## Développement piloté par les spécifications

Définissez quoi construire et pourquoi, puis transformez la spécification en plan,
en tâches et en code qui fonctionne.

Le parcours minimal figure ci-dessous. Créez une constitution une fois par projet,
puis répétez les autres étapes pour chaque fonctionnalité. Lancez ces skills dans
le chat de votre agent, pas dans votre terminal, une à une, en relisant chaque
résultat avant de continuer.

Cet exemple utilise la syntaxe de skills par défaut de GitHub Copilot. Pour un autre
agent, utilisez sa [syntaxe d'appel équivalente](https://github.github.io/spec-kit/integrations/cli.html#command-invocation).

```text
/speckit-constitution Create principles focused on code quality, testing, and maintainability.
/speckit-specify Build a photo organizer with albums grouped by date and a tile preview of each album.
/speckit-plan Use Vite with vanilla JavaScript. Keep images local and store metadata in SQLite.
/speckit-tasks
/speckit-implement
/speckit-converge
```

Répétez implement et converge jusqu'à ce que la convergence indique `Converged`.
Pour la clarification, les checklists et l'analyse de cohérence, consultez le
guide pas à pas du SDD.

[Guide pas à pas du SDD](https://github.github.io/spec-kit/quickstart.html) ·
[Référence des commandes](https://github.github.io/spec-kit/reference/agentic-sdd.html)

<a id="-bug-fixing-with-spec-kit"></a>
<a id="bug-fix-quickstart"></a>

## Correction de bugs

Évaluez la cause, corrigez le bug et vérifiez que le symptôme d'origine a disparu.
Aucun workflow de fonctionnalité SDD n'est nécessaire au préalable.

Installez l'extension de correction de bugs dans votre terminal, depuis le dossier
du projet :

```bash
specify extension add bug
```

Lancez ces skills dans le chat de votre agent, pas dans votre terminal, une à une,
en relisant chaque résultat avant de continuer.

Cet exemple utilise la syntaxe de skills par défaut de GitHub Copilot. Pour un autre
agent, utilisez sa [syntaxe d'appel équivalente](https://github.github.io/spec-kit/integrations/cli.html#command-invocation).

```text
/speckit-bug-assess "Submitting an empty password crashes the login form." slug=login-crash
/speckit-bug-fix slug=login-crash
/speckit-bug-test slug=login-crash
```

Relisez les rapports dans `.specify/bugs/login-crash/`. Le verdict final est
`verified`, `partial` ou `failed` ; seul `verified` confirme que la correction a réussi.

[Guide pas à pas de la correction de bugs](https://github.github.io/spec-kit/guides/bugfix.html) ·
[Référence des commandes](https://github.github.io/spec-kit/reference/agentic-bugfix.html)

<a id="-assessing-ideas-with-spec-kit"></a>
<a id="idea-assessment-quickstart"></a>

## Évaluation d'idées

Rassemblez des éléments concrets pour décider si une idée vaut la peine d'être menée.
Ni code source ni workflow de fonctionnalité SDD ne sont nécessaires.

Installez l'extension d'évaluation dans votre terminal, depuis le dossier du projet :

```bash
specify extension add assess
```

Lancez ces skills dans le chat de votre agent, pas dans votre terminal, une à une,
en relisant chaque résultat avant de continuer.

Cet exemple utilise la syntaxe de skills par défaut de GitHub Copilot. Pour un autre
agent, utilisez sa [syntaxe d'appel équivalente](https://github.github.io/spec-kit/integrations/cli.html#command-invocation).

```text
/speckit-assess-intake "Let users work offline and sync when they reconnect." slug=offline-mode
/speckit-assess-research slug=offline-mode
/speckit-assess-define slug=offline-mode
/speckit-assess-shape slug=offline-mode
/speckit-assess-decide slug=offline-mode
```

Relisez les artefacts dans `.specify/assessments/offline-mode/` et la décision
finale : `go`, `needs-clarification` ou `kill`. Levez les inconnues en modifiant
les artefacts Markdown existants, vous-même ou avec votre agent, plutôt qu'en
relançant des étapes entières. Si vous décidez de construire une idée logicielle
qui a reçu un `go`, établissez une constitution de projet si besoin, puis passez
le résumé de passation de `decision.md` à `/speckit-specify`. S'arrêter avec une
raison documentée est aussi un résultat utile.

[Guide pas à pas de l'évaluation](https://github.github.io/spec-kit/guides/assessment.html) ·
[Référence des commandes](https://github.github.io/spec-kit/reference/agentic-assessment.html)

<a id="-making-spec-kit-your-own-extensions--presets"></a>
<a id="-bundles-role-based-setups"></a>
<a id="-community"></a>

## Adapter un processus ou apporter le vôtre

Adaptez le développement piloté par les spécifications, la correction de bugs ou
l'évaluation d'idées aux standards de votre équipe. Ou apportez votre propre
processus sans adopter aucun d'eux. Combinez les [fonctionnalités ci-dessus](#fonctionnalités)
selon votre objectif :

- Adaptez un processus existant avec un preset, par exemple pour exiger la traçabilité réglementaire dans les plans. Utilisez une surcharge locale au projet pour modifier ponctuellement un modèle.
- Apportez votre propre processus en ajoutant ses commandes par une extension et en les rendant accessibles à votre agent de codage par une intégration.
- Automatisez des commandes et des contrôles dans un workflow. Utilisez des surcouches pour adapter un workflow installé sans le forker, ou ajoutez des étapes de workflow personnalisées quand les types intégrés ne suffisent pas.
- Partagez une configuration réutilisable en regroupant ses extensions, presets, workflows et étapes de workflow dans un bundle.

Commencez par le plus petit changement qui répond à votre besoin : vous n'avez pas
à remplacer tout le processus.

[Guide de personnalisation](https://github.github.io/spec-kit/guides/customization.html) ·
[Composants et guides de la communauté](https://github.github.io/spec-kit/community/overview.html)

<a id="-specify-cli-reference"></a>
<a id="available-slash-commands"></a>
<a id="-learn-more"></a>
<a id="-core-philosophy"></a>
<a id="-development-phases"></a>
<a id="-experimental-goals"></a>
<a id="-does-spec-kit-use-spec-kit"></a>

## Documentation

- [Référence du CLI](https://github.github.io/spec-kit/reference/overview.html) et [commandes des processus](https://github.github.io/spec-kit/reference/agentic-sdd.html#command-overview)
- [Philosophie du SDD](https://github.github.io/spec-kit/concepts/sdd.html), [méthode complète](./spec-driven.md) et [faire évoluer des spécifications existantes](https://github.github.io/spec-kit/guides/evolving-specs.html)
- [Historique du projet](https://github.github.io/spec-kit/history.html)
- [Comment Spec Kit utilise Spec Kit](./CONTRIBUTING.md#does-spec-kit-use-spec-kit)

## Dans les médias

- [Open Source Friday: Spec Kit Part 2](https://www.youtube.com/watch?v=8hHCpNVLhmI) (16 octobre 2026) — Manfred Riem et Nicole Haugen présentent Spec Kit 1.0 et la boîte à outils étendue (en anglais).
- [Open Source Friday with Spec Kit](https://www.youtube.com/watch?v=2IArMAhkJcE) (8 mai 2026) — Introduction et démonstration du SDD avec Manfred Riem (en anglais).

## Historique des étoiles

<p align="center">
    <a href="https://www.star-history.com/#github/spec-kit&Date">
        <picture>
            <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/svg?repos=github%2Fspec-kit&type=Date&theme=dark"/>
            <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/svg?repos=github%2Fspec-kit&type=Date"/>
            <img src="https://api.star-history.com/svg?repos=github%2Fspec-kit&type=Date" alt="Graphique de l'historique des étoiles de Spec Kit"/>
        </picture>
    </a>
</p>

<p align="center">
    <em>Merci à toutes celles et ceux qui font briller Spec Kit.</em>
</p>

<a id="-support"></a>

## Assistance et contribution

[Signaler un bug ou demander une fonctionnalité](https://github.com/github/spec-kit/issues/new) ·
[Guide de contribution](./CONTRIBUTING.md) · [Code de conduite](./CODE_OF_CONDUCT.md)

<a id="-license"></a>

Spec Kit est distribué sous [licence MIT](./LICENSE).
