<div align="center">
    <img src="https://raw.githubusercontent.com/github/spec-kit/main/media/logo_large.webp" alt="Spec Kit Logo" width="200" height="200"/>
    <h1>🌱 Spec Kit</h1>
    <h3><em>作り始める前に、何を作るかを定義する ―― どのようなAIコーディングエージェントでも</em></h3>
</div>

<p align="center">
    <strong>どんなAIコーディングエージェントとも組み合わせて高品質なソフトウェアを作れるオープンソースのツールキットです。すぐに使える仕様駆動プロセスを備えつつ(自前のプロセスへの差し替えも可能)、無限に拡張でき、コミュニティ主導で育ち、組織全体で使えるように設計されています。</strong>
</p>

<p align="center">
    <a href="https://github.com/github/spec-kit/releases/latest"><img src="https://img.shields.io/github/v/release/github/spec-kit" alt="Latest Release"/></a>
    <a href="https://github.com/github/spec-kit/stargazers"><img src="https://img.shields.io/github/stars/github/spec-kit?style=social" alt="GitHub stars"/></a>
    <a href="https://github.com/github/spec-kit/blob/main/LICENSE"><img src="https://img.shields.io/github/license/github/spec-kit" alt="License"/></a>
    <a href="https://github.github.io/spec-kit/"><img src="https://img.shields.io/badge/docs-GitHub_Pages-blue" alt="Documentation"/></a>
</p>

<p align="center">
    <a href="./README.md">English</a>·
    <a href="./README.zh-CN.md">简体中文</a>·
    <strong>日本語</strong>
</p>

> [!NOTE]
> **Spec Kit、1周年 ―― そして1.0.0へ**
>
> 最初のコミットから1年、Spec Kitは[1.0.0](https://github.com/github/spec-kit/releases/tag/v1.0.0)に到達しました。作業が完了したからでも、形が固まったからでもありません。このプロジェクトが一貫性のある、役に立つものへと育ち、それを立ち上げた人たちよりもずっと多くの人々によって形作られてきたからです。
>
> リードメンテナー本人による1周年記念の投稿、[*Spec Kit Turns One — and Ships 1.0.0*](https://www.manorrock.com/blog/2026/08/21/spec_kit_turns_one.html)では、このプロジェクトにとって1.0.0が実際に何を意味するのかが語られています ―― **それはもはや単なる番号にすぎない**、ということです。エージェントによって変化への適応コストが劇的に下がるにつれて、価値の重心は安定性から適応力へと移っていきます。
>
> Spec Kitを使ってくれた人、その前提に疑問を投げかけてくれた人、問題を報告してくれた人、コードやドキュメントで貢献してくれた人、拡張機能やプリセットを作ってくれた人、アイデアを共有してくれた人、誰かのスタートを手伝ってくれた人 ―― そのすべての方へ:**感謝します**。このマイルストーンは、プロジェクトを最初の1年間支え続け、これからの方向性を形作り続けているコミュニティのものです。

---

## 目次

- [🤔 仕様駆動開発とは?](#-仕様駆動開発とは)
- [🐞 Spec Kitを利用したバグ修正](#-spec-kitを利用したバグ修正)
- [💡 Spec Kitを利用したアイデアの評価](#-spec-kitを利用したアイデアの評価)
- [⚡ はじめる](#-はじめる)
- [📽️ 紹介動画](#️-紹介動画)
- [🌍 コミュニティ](#-コミュニティ)
- [🤖 対応しているAIコーディングエージェント](#-対応しているaiコーディングエージェント)
- [🔧 Specify CLI リファレンス](#-specify-cli-リファレンス)
- [🧩 Spec Kitを自分仕様にカスタマイズする: 拡張機能とプリセット](#-spec-kitを自分仕様にカスタマイズする-拡張機能とプリセット)
- [📦 バンドル(Bundles): ロールベースのセットアップ](#-バンドルbundles-ロールベースのセットアップ)
- [📚 基本理念](#-基本理念)
- [🪞 Spec KitはSpec Kit自身を使っているのか?](#-spec-kitはspec-kit自身を使っているのか)
- [🌟 開発フェーズ](#-開発フェーズ)
- [🎯 実験的な目標](#-実験的な目標)
- [🔧 前提条件](#-前提条件)
- [📖 詳しく学ぶ](#-詳しく学ぶ)
- [💬 サポート](#-サポート)
- [🙏 謝辞](#-謝辞)
- [📄 ライセンス](#-ライセンス)

## 🤔 仕様駆動開発とは?

仕様駆動開発(Spec Driven Development)は、従来のソフトウェア開発の常識を覆します。これまで何十年もの間、コードこそが主役であり、仕様書はコーディングという"本当の仕事"が始まれば捨てられる、単なる踏み台に過ぎませんでした。仕様駆動開発はこれを一変させます ―― 仕様書自体が実行可能になり、単に実装の指針を示すのではなく、動くソフトウェアを直接作り出すのです。

### SDD クイックスタート

`vX.Y.Z` を[最新のリリース・タグ](https://github.com/github/spec-kit/releases)に置き換えてください。その際、先頭の `v` はそのまま残してください。

```bash
uv tool install specify-cli --from git+https://github.com/github/spec-kit.git@vX.Y.Z
specify init my-project --integration copilot
cd my-project
```

プロジェクトディレクトリでコーディングエージェントを起動します。

0. **確立する(Establish)**: プロジェクトのルールを最初に一度だけ定義します。(`/speckit-constitution`)。プロジェクトごとに1回だけ行うステップです。
1. **仕様化する(Specify)**: 何を作りたいかを定義します(`/speckit-specify`)。
2. **計画する(Plan)**: どう作るかを計画します(`/speckit-plan`)。
3. **分解する(Break down)**: 計画を実行可能なタスクに分解します(`/speckit-tasks`)。
4. **実装する(Implement)**: タスクを実装します(`/speckit-implement`)。
5. **収束させる(Converge)**: 実装が仕様・計画・タスクと一致しているかを検証し、ズレを収束させます。(`/speckit-converge`)。

> [!NOTE]
> `/speckit-converge` が **Converged** と出力されるまでステップ4と5を繰り返します。

## 🐞 Spec Kitを利用したバグ修正

エージェントが診断を検証せず、また修正が本来の症状を解消したかを確認しないまま、報告からいきなり修正パッチへ飛びつくと、バグ修正はリスクを伴います。同梱されているオプトイン方式のbug拡張機能は、評価(assess) → 修正(fix) → テスト(test) という反復可能なワークフローを提供し、各修正の範囲を限定し、根拠に基づいたものにし、根本原因から検証までを文書化された状態に保ちます。

### バグ修正 クイックスタート

`vX.Y.Z` を[最新のリリース・タグ](https://github.com/github/spec-kit/releases)に置き換えてください。その際、先頭の `v` はそのまま残してください。

```bash
uv tool install specify-cli --from git+https://github.com/github/spec-kit.git@vX.Y.Z
specify init my-project --integration copilot
cd my-project
specify extension add bug
```

プロジェクトディレクトリでコーディングエージェントを起動します。

1. **評価する(Assess)**: バグを評価する(`/speckit-bug-assess "<bug report>" slug=login-crash`)。
2. **修正する(Fix)**: 評価されたバグの原因を修正する(`/speckit-bug-fix slug=login-crash`)。
3. **テストする(Test)**: 修正をテストする(`/speckit-bug-test slug=login-crash`)。

## 💡 Spec Kitを利用したアイデアの評価

良いアイデアは、それがソフトウェアになるかどうかにかかわらず、コミットする前に根拠を伴うべきです。同梱されているオプトイン方式のassess拡張機能は、独立した 受付(intake) → 調査(research) → 定義(define) → 具体化(shape) → 決定(decide) というワークフローを通じて、生のアイデアを文書化された 実行(go) / 要明確化(needs-clarification) / 却下(kill) の判断へと変えます。

### アイデア評価 クイックスタート

`vX.Y.Z` を[最新のリリース・タグ](https://github.com/github/spec-kit/releases)に置き換えてください。その際、先頭の `v` はそのまま残してください。

```bash
uv tool install specify-cli --from git+https://github.com/github/spec-kit.git@vX.Y.Z
specify init my-project --integration copilot
cd my-project
specify extension add assess
```

プロジェクトディレクトリでコーディングエージェントを起動します。

1. **受付する(Intake)**: アイデアを受け付ける(`/speckit-assess-intake "<idea>" slug=offline-mode`)。
2. **調査する(Research)**: 賛否両方の根拠を調査する(`/speckit-assess-research slug=offline-mode`)。
3. **定義する(Define)**: 問題・目標・成功指標を定義する(`/speckit-assess-define slug=offline-mode`)。
4. **具体化する(Shape)**: 考えられる解決策とそのトレードオフを具体化する(`/speckit-assess-shape slug=offline-mode`)。
5. **決定する(Decide)**: 進める・明確化する・中止する、のいずれかを決定する(`/speckit-assess-decide slug=offline-mode`)。

> [!NOTE]
> アイデア評価は独立した機能です。**go(実行)** の判断が出たアイデアを実際に作ることにした場合は、`/speckit-specify` に引き継ぐことができます。

## ⚡ はじめる

### 1. Specify CLIをインストールする

**[uv](https://docs.astral.sh/uv/)** が必要です（[uvのインストール](./docs/install/uv.md)）。`vX.Y.Z` を [Releases](https://github.com/github/spec-kit/releases) にある最新のリリース・タグに置き換えてください。その際、先頭の `v` は残したままにしてください（例: `0.12.11` ではなく `v0.12.11`）。

```bash
uv tool install specify-cli --from git+https://github.com/github/spec-kit.git@vX.Y.Z
```

PyPIからのインストールがお好みですか?specify-cli パッケージはPyPIにも公開されています。

```bash
uv tool install specify-cli
```

別のインストール方法、検証、アップグレード、トラブルシューティングについては[インストールガイド](./docs/installation.md) を参照してください。

### 2. プロジェクトを初期化する

```bash
specify init my-project --integration copilot
cd my-project
```

CI環境やAIエージェントのハーネス(キーボードがない、または矢印キーを送れないPTYの場合)では、`--non-interactive` を指定することで、initが選択肢(picker)の入力待ちでハングしないようにできます。空でないディレクトリに初期化する場合は、`--force` と組み合わせて使用してください。

```bash
specify init my-project --non-interactive --ignore-agent-tools
specify init --here --force --non-interactive --integration claude
```

更新の確認やインストール済みCLIのアップグレードには、セルフマネジメントコマンドを使用してください。詳細なシナリオやカスタマイズオプションについては、[アップグレードガイド](./docs/upgrade.md) を参照してください。

```bash
# 新しいリリースが利用可能かを確認する(読み取り専用 ―― 何も変更しません)
specify self check

# 実際にはアップグレードせず、何が実行されるかをプレビューする
specify self upgrade --dry-run

# 最新の安定版にその場でアップグレードする(uv tool か pipx かは自動判定)
specify self upgrade

# または特定のリリースタグに固定する(vX.Y.Z[suffix] を希望のタグに置き換えてください)
specify self upgrade --tag vX.Y.Z[suffix]
```

引数なしの `specify self upgrade` は即座に実行され、`pip install -U` や `npm update` のような確認プロンプトがない挙動と一致します。`uv tool` でインストールした場合は、内部で `uv tool install specify-cli --force --from <git ref>` を実行するため、dev、alpha/beta/rc、ビルドメタデータのサフィックスを含め、固定されたリリースタグでも動作します。`uvx`(一時実行)やソースからのチェックアウトは検出され、インストーラーを実行する代わりに、それぞれの方法に応じたガイダンスが表示されます。インストーラーのサブプロセスが実行できる時間の上限は `SPECIFY_UPGRADE_TIMEOUT_SECS` で設定できます(デフォルトはタイムアウトなし ―― 必要な場合は `Ctrl+C` で中断してください)。

### 3. プロジェクトルールを定義する

プロジェクトディレクトリでコーディングエージェントを起動します。ほとんどのエージェントは spec-kit を `/speckit.*` というスラッシュコマンドとして公開していますが、Codex CLI とスキルモードの Command Code は代わりに `$speckit-*` を使用します。GitHub Copilot CLI では /agents でエージェントを選択するか、プロンプト内で直接指定します。

プロジェクトの全体ルールと、今後の開発すべてを導く開発ガイドラインを作成するには、**`/speckit.constitution`** コマンドを使用してください。

```bash
/speckit.constitution Create principles focused on code quality, testing standards, user experience consistency, and performance requirements
```

### 4. 仕様を作成する

作りたいものを説明するには、**`/speckit.specify`** コマンドを使用してください。技術スタックではなく、**何を(what)・なぜ(why)** に焦点を当ててください。

```bash
/speckit.specify Build an application that can help me organize my photos in separate photo albums. Albums are grouped by date and can be re-organized by dragging and dropping on the main page. Albums are never in other nested albums. Within each album, photos are previewed in a tile-like interface.
```

### 5. 実装計画の作成

技術スタックとアーキテクチャの選定を示すには、**`/speckit.plan`** コマンドを使用してください。

```bash
/speckit.plan The application uses Vite with minimal number of libraries. Use vanilla HTML, CSS, and JavaScript as much as possible. Images are not uploaded anywhere and metadata is stored in a local SQLite database.
```

### 6.タスクに分解する

実装計画から実行可能なタスクリストを作成するには、**`/speckit.tasks`** を使用してください。

```bash
/speckit.tasks
```

### 7. 実装する

すべてのタスクを実行し、計画に沿って機能を構築するには、**`/speckit.implement`** を使用してください。

```bash
/speckit.implement
```

詳細な手順については、[包括的なガイド](./spec-driven.md)を参照してください。

## 📽️ 紹介動画

Spec Kitの動作を見てみたいですか?[紹介動画](https://www.youtube.com/watch?v=a9eR1xsfvHg&pp=0gcJCckJAYcqIYzv)をご覧ください!

[![Spec Kit video header](https://raw.githubusercontent.com/github/spec-kit/main/media/spec-kit-video-header.jpg)](https://www.youtube.com/watch?v=a9eR1xsfvHg&pp=0gcJCckJAYcqIYzv)

## 🌍 コミュニティ

[Spec Kit ドキュメントサイト](https://github.github.io/spec-kit/)で、コミュニティが提供するリソースを探索できます。

- [拡張機能(Extensions)](https://github.github.io/spec-kit/community/extensions.html) ―― コマンド、フック、各種機能
- [プリセット(Presets)](https://github.github.io/spec-kit/community/presets.html) ―― テンプレートと用語のオーバーライド
- [バンドル(Bundles)](https://github.github.io/spec-kit/community/bundles.html) ―― 既存コンポーネントを組み合わせたロール別・チーム別のスタック
- [ウォークスルー(Walkthroughs)](https://github.github.io/spec-kit/community/walkthroughs.html) ―― エンドツーエンドのSDDシナリオ
- [関連プロジェクト(Friends)](https://github.github.io/spec-kit/community/friends.html) ―― Spec Kitを拡張・活用しているプロジェクト

> [!NOTE]
> コミュニティによる貢献は、それぞれの作成者が独立して作成・保守しているものです。インストール前にソースコードを確認し、自己責任でご利用ください。

貢献したいですか?[拡張機能公開ガイド](extensions/EXTENSION-PUBLISHING-GUIDE.md)、[プリセット公開ガイド](presets/PUBLISHING.md)、または[コミュニティバンドルガイド](docs/community/bundles.md)を参照してください。

## 🤖 対応しているAIコーディングエージェント

Spec Kitは、CLIツールとIDEベースのアシスタントを含む30以上のAIコーディングエージェントに対応しています。注意点や使用方法の詳細を含む完全なリストは、[対応しているAIコーディングエージェント](https://github.github.io/spec-kit/reference/integrations.html) ガイドを参照してください。

インストール済みのバージョンで利用可能な一覧を確認するには、`specify integration list` を実行してください。

## 利用可能なスラッシュコマンド

`specify init` を実行すると、AIコーディングエージェントは構造化された開発のためにこれらのスラッシュコマンドを利用できるようになります。スキルモードに対応した統合では、`--integration <agent> --integration-options="--skills"` を指定することで、スラッシュコマンドのプロンプトファイルの代わりにエージェントスキルがインストールされます。

### 主要コマンド

仕様駆動開発ワークフローに不可欠なコマンド

| コマンド                  | エージェントスキル       | 説明                                                                  |
| ------------------------ | ---------------------- | --------------------------------------------------------------------- |
| `/speckit.constitution`  | `speckit-constitution` | プロジェクトの全体ルールと開発ガイドラインを作成または更新する                          |
| `/speckit.specify`       | `speckit-specify`      | 何を作りたいかを定義する(要件とユーザーストーリー)                          |
| `/speckit.plan`          | `speckit-plan`         | 選定した技術スタックで技術的な実装計画を作成する                             |
| `/speckit.tasks`         | `speckit-tasks`        | 実装のための実行可能なタスクリストを生成する                                |
| `/speckit.taskstoissues` | `speckit-taskstoissues`| 生成されたタスクリストを、追跡・実行用のGitHub issueに変換する                |
| `/speckit.implement`     | `speckit-implement`    | 計画に沿って機能を構築するため、すべてのタスクを実行する                       |
| `/speckit.converge`      | `speckit-converge`     | 仕様/計画/タスクに照らしてコードベースを評価し、残作業を新規タスクとして追加する      |

### オプションコマンド

品質向上と検証のための追加コマンド

| コマンド              | エージェントスキル       | 説明                                                                                                    |
| -------------------- | ---------------------- | -------------------------------------------------------------------------------------------------------- |
| `/speckit.clarify`   | `speckit-clarify`      | 仕様が不十分な箇所を明確化する(`/speckit.plan` の前に実行することを推奨。旧 `/quizme`)                          |
| `/speckit.analyze`   | `speckit-analyze`      | 成果物間の一貫性とカバレッジを分析する(`/speckit.tasks` の後、`/speckit.implement` の前に実行)                  |
| `/speckit.checklist` | `speckit-checklist`    | 要件の網羅性・明確さ・一貫性を検証するカスタム品質チェックリストを生成する(いわば「英語のためのユニットテスト」)      |

## 🔧 Specify CLI リファレンス

コマンドの詳細、オプション、使用例については、[CLIリファレンス](https://github.github.io/spec-kit/reference/overview.html) を参照してください。

## 🧩 Spec Kitを自分仕様にカスタマイズする: 拡張機能とプリセット

Spec Kitは、**拡張機能(extensions)** と **プリセット(presets)** という2つの補完的な仕組み、および単発の調整用のプロジェクトローカルなオーバーライドによって、ニーズに合わせて調整できます。

| 優先度 | コンポーネントの種類                                  | 場所                              |
| ----: | ---------------------------------------------------- | --------------------------------- |
|   ⬆ 1 | プロジェクトローカルなオーバーライド                     | `.specify/templates/overrides/`  |
|     2 | プリセット ―― コアと拡張機能をカスタマイズ                | `.specify/presets/templates/`    |
|     3 | 拡張機能 ―― 新しい機能を追加                            | `.specify/extensions/templates/` |
|   ⬇ 4 | Spec Kitコア ―― 組み込みのSDDコマンドとテンプレート        | `.specify/templates/`            |

- **テンプレート**は**実行時**に解決されます ―― Spec Kitはこのスタックを上から順にたどり、最初に一致したものを使用します。
- プロジェクトローカルなオーバーライド(`.specify/templates/overrides/`)を使えば、完全なプリセットを作らなくても、単一プロジェクトに対して一度限りの調整ができます。
- **拡張機能/プリセットのコマンド**は**インストール時**に適用されます ―― `specify extension add` や `specify preset add` を実行すると、コマンドファイルがエージェントのディレクトリ(例: `.claude/commands/`)に書き込まれます。
- 複数のプリセットや拡張機能が同じコマンドを提供している場合、最も優先度の高いバージョンが有効になります。削除すると、次に優先度の高いバージョンが自動的に復元されます。
- オーバーライドやカスタマイズが存在しない場合、Spec Kitはコアのデフォルトを使用します。

### 拡張機能(Extensions) ―― 新しい機能を追加する

Spec Kitのコアを超えた機能が必要な場合は、**拡張機能**を使用します。拡張機能は新しいコマンドやテンプレートを導入します ―― 例えば、組み込みのSDDコマンドではカバーされていないドメイン固有のワークフローを追加したり、外部ツールと統合したり、まったく新しい開発フェーズを追加したりできます。拡張機能は *Spec Kitに何ができるか* を広げるものです。

```bash
# 利用可能な拡張機能を検索する
specify extension search

# 拡張機能をインストールする
specify extension add <extension-name>
```

例えば、拡張機能によってJira連携、実装後のコードレビュー、Vモデルのテストトレーサビリティ、プロジェクトの健全性診断などを追加できます。

コマンドの完全なガイドについては、[拡張機能リファレンス](https://github.github.io/spec-kit/reference/extensions.html) を参照してください。利用可能なものについては、[コミュニティの拡張機能](https://github.github.io/spec-kit/community/extensions.html) をご覧ください。

### プリセット(Presets) ―― 既存のワークフローをカスタマイズする

新しい機能を追加せずにSpec Kitの*動作の仕方*を変えたい場合は、**プリセット**を使用します。プリセットは、コアおよびインストール済みの拡張機能に付属するテンプレートとコマンドを上書きします ―― 例えば、コンプライアンス重視の仕様フォーマットを強制したり、ドメイン固有の用語を使用したり、計画やタスクに組織の標準を適用したりできます。プリセットは、Spec Kitとその拡張機能が生成する成果物や指示をカスタマイズするものです。

```bash
# 利用可能なプリセットを検索する
specify preset search

# プリセットをインストールする
specify preset add <preset-name>
```

例えば、プリセットによって規制上のトレーサビリティを要求するように仕様テンプレートを再構成したり、使用している手法(アジャイル、カンバン、ウォーターフォール、ジョブ理論、ドメイン駆動設計など)にワークフローを適応させたり、計画に必須のセキュリティレビューゲートを追加したり、テストファーストのタスク順序を強制したり、ワークフロー全体を別の言語にローカライズしたりできます。[pirate-speak-preset-demo](https://github.com/mnriem/spec-kit-pirate-speak-preset-demo) は、カスタマイズがどこまで深くできるかを示す一例です。複数のプリセットは、優先順位を付けて重ねて適用できます。

解決順序や優先度の重ね合わせを含む、コマンドの完全なガイドについては、[プリセットリファレンス](https://github.github.io/spec-kit/reference/presets.html) を参照してください。

## 📦 バンドル(Bundles): ロールベースのセットアップ

拡張機能とプリセットは個々の構成要素です。**バンドル**は、拡張機能、プリセット、ステップ、ワークフローといった、厳選された組み合わせを1つのバージョン管理されたロール指向のセットアップにまとめたもので、これによりチーム全体のペルソナ(プロダクトマネージャー、ビジネスアナリスト、セキュリティリサーチャー、開発者、…)を1つのコマンドでプロビジョニングできます。

バンドルは手書きの `bundle.yml` マニフェストによって記述されます。各コンポーネントをバージョンに固定し、必要に応じて特定の統合先を指定できます。`integration` が指定されていないバンドルは**汎用**とみなされ、プロジェクトが既に使用している統合をそのまま引き継ぎます。

```bash
# 有効なカタログスタックの中からバンドルを探す
specify bundle search [<query>]

# バンドルが追加する正確なコンポーネント集合を確認する(installの内容と一致)
specify bundle info <bundle-id>

# バンドルのコンポーネント一式を一度の操作でインストールする
specify bundle install <bundle-id>

# インストール済みの内容を確認し、非破壊的に更新・削除する
specify bundle list
specify bundle update <bundle-id>     # または --all
specify bundle remove <bundle-id>     # このバンドルのコンポーネントのみ削除
```

バンドルは**優先順位付けされたカタログスタック**(プロジェクト > ユーザー > 組み込み)から解決されます。各ソースにはインストールポリシーが設定されており、`install-allowed` のソースからはインストールできますが、`discovery-only` のソースは `search`/`info` では表示されるもののインストールは拒否されます。このスタックは `specify bundle catalog list|add|remove` で管理します。

作成者はバンドルをローカルで検証・パッケージ化します。配布とは、ビルドした成果物をホスティングし、カタログソースを追加することを指します。コミュニティによるバンドルの提出には、必要なコンポーネントカタログとインストールの根拠をレビューできるよう、[バンドル提出](https://github.com/github/spec-kit/issues/new?template=bundle_submission.yml) issueテンプレートを使用します

```bash
specify bundle validate --path ./my-bundle      # 構造チェック + 参照チェック
specify bundle build --path ./my-bundle         # バージョン管理された .zip 成果物を生成
```

すぐに読める4つのバンドルマニフェストのサンプルが [`examples/bundles/`](examples/bundles/) にあります(プロダクトマネージャー、ビジネスアナリスト、セキュリティリサーチャー、開発者)。これらはバンドルのパッケージング例であり、生成済みの機能仕様の実例ではありません。エンドツーエンドのコミュニティ実例については、[コミュニティウォークスルー](https://github.github.io/spec-kit/community/walkthroughs.html) を参照してください。

主な保証事項: `info` は `install` が何を追加するかを正確に示します(透明性)。インストールは冪等であり、プロジェクトルート内に限定されます。`remove` は、他のインストール済みバンドルがまだ必要としているコンポーネントには決して手を加えません。そして、すべての利用・作成コマンドは、ローカルまたは固定されたソースに対して**オフライン**で動作します。

### どれを使うべきか

| 目的 | 使うもの |
| --- | --- |
| まったく新しいコマンドやワークフローを追加する | 拡張機能 |
| 仕様・計画・タスクのフォーマットをカスタマイズする | プリセット |
| 外部ツールやサービスと統合する | 拡張機能 |
| 組織や規制の標準を強制する | プリセット |
| 再利用可能なドメイン固有のテンプレートを提供する | どちらも可 ―― テンプレートの上書きにはプリセット、新しいコマンドと同梱するテンプレートには拡張機能 |
| ロールベースの完全なセットアップを1つのコマンドでプロビジョニングする | バンドル |

## 📚 基本理念

仕様駆動開発は、以下を重視する構造化されたプロセスです

- **意図駆動の開発**: 仕様書が「*どうやって(how)*」よりも先に「*何を(what)*」を定義する
- **リッチな仕様書の作成**: ガードレールと組織的な原則を用いる
- **多段階での洗練**: プロンプトからの一発生成ではなく、段階を踏んで作り込む
- **高度なAIモデルの能力への依存**: 仕様の解釈を高度なAIモデルの能力に大きく依存する

## 🪞 Spec KitはSpec Kit自身を使っているのか?

はい ―― 私たちはSpec Kitを開発する際に、特に大きな機能追加や開発ワークフローの変更について、Spec Kit自身をドッグフーディング(自社製品を自ら使うこと)しています。コントリビューターは、関連する変更を仕様駆動開発のコマンドを通じてテストするよう求められます。[機能評価ワークフロー](./.github/workflows/feature-assess.md) は、現時点で自動化されたドッグフーディングの経路です。そのセットアップでは、現在のチェックアウトのCLIを使ってCopilotを初期化し `assess` 拡張機能をインストールした上で、Copilotが生成された評価スキルに従って機能リクエストを処理します。その他のエージェント型ワークフローは、現時点ではSpecify CLIとは独立して動作しています。

とはいえ、すべての変更がこのフルワークフローを経由するわけではありません。小さな修正は、通常のissue・プルリクエスト・レビュー・テストのプロセスで対応できます。`.github/agents/`、`.github/prompts/`、`.github/copilot-instructions.md`、`.grok/`、`.specify/`、`specs/` 以下にあるドッグフーディング用のスキャフォールディングや成果物は、意図的にgitignoreされています。自動化された評価ワークフローは一時的なものであり、生成されたCopilotスキルをコミットもプッシュもしないため、その出力がリポジトリの履歴に残ることはありません。検証にあたって期待される内容については、[コントリビューター向け開発ワークフロー](./CONTRIBUTING.md#development-workflow) を参照してください。

## 🌟 開発フェーズ

| フェーズ                                        | 焦点                     | 主な活動                                                                                                                                     |
| ------------------------------------------------ | ------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------- |
| **ゼロからの開発("グリーンフィールド")**            | ゼロから生成する          | <ul><li>高レベルの要件から始める</li><li>仕様書を生成する</li><li>実装ステップを計画する</li><li>本番運用可能なアプリケーションを構築する</li></ul> |
| **創造的な探索**                                  | 並行した実装              | <ul><li>多様な解決策を探索する</li><li>複数の技術スタック・アーキテクチャに対応する</li><li>UXパターンを試す</li></ul>                             |
| **反復的な改善("ブラウンフィールド")**              | ブラウンフィールドの近代化 | <ul><li>機能を反復的に追加する</li><li>レガシーシステムを近代化する</li><li>プロセスを適応させる</li></ul>                                        |

既存のプロジェクトでは、Spec Kitツールのアップデートと機能成果物の変化を分けて管理してください。アップグレード時には管理対象のプロジェクトファイルを更新し、意図した挙動が変わった際には `specs/` 配下の成果物を更新します。[仕様の進化ガイド](./docs/guides/evolving-specs.md) では、推奨されるブラウンフィールドループについて説明しています。

## 🎯 実験的な目標

私たちの研究と実験は、以下に重点を置いています:

### 技術非依存性

- 多様な技術スタックを用いてアプリケーションを作成する
- 規範駆動開発が、特定の技術・プログラミング言語・フレームワークに縛られないプロセスであるという仮説を検証する

### エンタープライズ制約

- ミッションクリティカルなアプリケーション開発を実証する
- 組織的な制約(クラウドプロバイダー、技術スタック、エンジニアリング慣行)を取り入れる
- エンタープライズのデザインシステムとコンプライアンス要件をサポートする

### ユーザー中心の開発

- 異なるユーザー層や好みに合わせてアプリケーションを構築する
- 様々な開発アプローチ(バイブコーディングからAIネイティブな開発まで)をサポートする

### 創造的・反復的なプロセス

- 並行した実装探索という概念を検証する
- 堅牢な反復的機能開発ワークフローを提供する
- アップグレードや近代化のタスクに対応できるようプロセスを拡張する

## 🔧 前提条件

- **Linux/macOS/Windows**
- [対応している](#-対応しているaiコーディングエージェント) AIコーディングエージェント
- パッケージ管理には [uv](https://docs.astral.sh/uv/)(推奨)、または永続的インストールには [pipx](https://pipx.pypa.io/)
- [Python 3.11以上](https://www.python.org/downloads/)
- [Git](https://git-scm.com/downloads)

エージェントで問題が発生した場合は、統合を改善できるようissueを開いてください。

## 📖 詳しく学ぶ

- **[規範駆動開発の完全な方法論](./spec-driven.md)** - プロセス全体を深く掘り下げる
- **[クイックスタートガイド](https://github.github.io/spec-kit/quickstart.html)** - 段階的な実装の解説

---

## 💬 サポート

サポートが必要な場合は、[GitHub issue](https://github.com/github/spec-kit/issues/new) を開いてください。バグ報告、機能リクエスト、規範駆動開発の使い方に関する質問を歓迎します。

## 🙏 謝辞

このプロジェクトは、[John Lam](https://github.com/jflam) の研究と成果に大きく影響を受け、それを基にしています。

## 📄 ライセンス

このプロジェクトはMITオープンソースライセンスの条件の下でライセンスされています。詳細な条件については [LICENSE](./LICENSE) ファイルを参照してください。
