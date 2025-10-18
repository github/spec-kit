<div align="center">
    <img src="./media/logo_small.webp"/>
    <h1>🪣 Spec Kit</h1>
    <h3><em>高品質なソフトウェアをより速く構築する。</em></h3>
</div>

<p align="center">
    <strong>プロダクトのシナリオと予測可能な結果に集中できるようにし、すべてを一からビビッドコーディングする代わりになるオープンソースツールキット。</strong>
</p>

<p align="center">
    <a href="https://github.com/github/spec-kit/actions/workflows/release.yml"><img src="https://github.com/github/spec-kit/actions/workflows/release.yml/badge.svg" alt="リリース"/></a>
    <a href="https://github.com/github/spec-kit/stargazers"><img src="https://img.shields.io/github/stars/github/spec-kit?style=social" alt="GitHub スター"/></a>
    <a href="https://github.com/github/spec-kit/blob/main/LICENSE"><img src="https://img.shields.io/github/license/github/spec-kit" alt="ライセンス"/></a>
    <a href="https://github.github.io/spec-kit/"><img src="https://img.shields.io/badge/docs-GitHub_Pages-blue" alt="ドキュメント"/></a>
</p>

---

## 目次

- [🪣 スペック駆動開発とは？](#-スペック駆動開発とは)
- [✅ はじめに](#-はじめに)
- [📹 ビデオ概要](#-ビデオ概要)
- [🤖 サポートされているAIエージェント](#-サポートされているaiエージェント)
- [⚙️ Specify CLI リファレンス](#-specify-cli-リファレンス)
- [🎯 核となる哲学](#-核となる哲学)
- [🔄 開発フェーズ](#-開発フェーズ)
- [🧪 実験的目標](#-実験的目標)
- [📋 前提条件](#-前提条件)
- [📚 より詳しく](#-より詳しく)
- [📝 詳細なプロセス](#-詳細なプロセス)
- [🔧 トラブルシューティング](#-トラブルシューティング)
- [👥 メンテナー](#-メンテナー)
- [💬 サポート](#-サポート)
- [🙏 謝辞](#-謝辞)
- [📄 ライセンス](#-ライセンス)

## 🪣 スペック駆動開発とは？

スペック駆動開発は、従来のソフトウェア開発の**常識を覆す**ものです。何十年もの間、コードが王様でした —— 仕様は「本格的な作業」であるコーディングが始まる前に構築して捨て去るだけの足場に過ぎませんでした。スペック駆動開発はこれを変えるものです：**仕様が実行可能**になり、単に指導するだけでなく、直接動作する実装を生成します。

## ✅ はじめに

### 1. Specify CLI をインストール

好みのインストール方法を選択してください：

#### オプション 1: 永続的なインストール（推奨）

一度インストールしてどこでも使用：

```bash
uv tool install specify-cli --from git+https://github.com/github/spec-kit.git
```

その後、ツールを直接使用：

```bash
specify init <PROJECT_NAME>
specify check
```

specify をアップグレードするには：

```bash
uv tool install specify-cli --force --from git+https://github.com/github/spec-kit.git
```

#### オプション 2: 一度限りの使用

インストールせずに直接実行：

```bash
uvx --from git+https://github.com/github/spec-kit.git specify init <PROJECT_NAME>
```

**永続的なインストールの利点：**

- ツールはインストールされたままになり、PATH で利用可能
- シェルエイリアスを作成する必要なし
- `uv tool list`, `uv tool upgrade`, `uv tool uninstall` による優れたツール管理
- よりクリーンなシェル構成

### 2. プロジェクトの原則を確立

プロジェクトディレクトリで AI アシスタントを起動します。アシスタントでは `/speckit.*` コマンドが利用可能です。

**`/speckit.constitution`** コマンドを使用して、すべての後続開発を指導するプロジェクトの統治原則と開発ガイドラインを作成します。

```bash
/speckit.constitution コード品質、テスト基準、ユーザーエクスペリエンスの一貫性、およびパフォーマンス要件に焦点を当てた原則を作成
```

### 3. 仕様を作成

**`/speckit.specify`** コマンドを使用して、構築したいものを記述します。**何**と**なぜ**に焦点を当て、技術スタックではありません。

```bash
/speckit.specify 写真を別々のフォトアルバムに整理できるアプリケーションを構築。アルバムは日付ごとにグループ化され、メインページでドラッグアンドドロップで再編成できます。アルバムは他のネストされたアルバムに含まれることはありません。各アルバム内では、写真はタイル状のインターフェースでプレビューされます。
```

### 4. 技術的実装計画を作成

**`/speckit.plan`** コマンドを使用して、技術スタックとアーキテクチャの選択を提供します。

```bash
/speckit.plan アプリケーションはViteを使用し、最小限のライブラリを使用します。可能な限りvanilla HTML、CSS、JavaScriptを使用します。画像はどこにもアップロードされず、メタデータはローカルSQLiteデータベースに保存されます。
```

### 5. タスクに分解

**`/speckit.tasks`** を使用して、実装計画から実行可能なタスクリストを作成します。

```bash
/speckit.tasks
```

### 6. 実装を実行

**`/speckit.implement`** を使用してすべてのタスクを実行し、計画に従って機能を構築します。

```bash
/speckit.implement
```

詳細なステップバイステップの説明については、[包括的なガイド](./spec-driven.md)を参照してください。

## 📹 ビデオ概要

Spec Kit の実際の動作を見たいですか？[ビデオ概要](https://www.youtube.com/watch?v=a9eR1xsfvHg&pp=0gcJCckJAYcqIYzv)をご覧ください！

[![Spec Kit ビデオヘッダー](/media/spec-kit-video-header.jpg)](https://www.youtube.com/watch?v=a9eR1xsfvHg&pp=0gcJCckJAYcqIYzv)

## 🤖 サポートされているAIエージェント

| エージェント | サポート | 備考 |
|-----------------------------------------------------------|---------|---------------------------------------------------|
| [Claude Code](https://www.anthropic.com/claude-code) | ✅ | |
| [GitHub Copilot](https://code.visualstudio.com/) | ✅ | |
| [Gemini CLI](https://github.com/google-gemini/gemini-cli) | ✅ | |
| [Cursor](https://cursor.sh/) | ✅ | |
| [Qwen Code](https://github.com/QwenLM/qwen-code) | ✅ | |
| [opencode](https://opencode.ai/) | ✅ | |
| [Windsurf](https://windsurf.com/) | ✅ | |
| [Kilo Code](https://github.com/Kilo-Org/kilocode) | ✅ | |
| [Auggie CLI](https://docs.augmentcode.com/cli/overview) | ✅ | |
| [CodeBuddy CLI](https://www.codebuddy.ai/cli) | ✅ | |
| [Roo Code](https://roocode.com/) | ✅ | |
| [Codex CLI](https://github.com/openai/codex) | ✅ | |
| [Amazon Q Developer CLI](https://aws.amazon.com/developer/learning/q-developer-cli/) | ❌⚠️ | Amazon Q Developer CLI はスラッシュコマンドのカスタム引数を[サポートしていません](https://github.com/aws/amazon-q-developer-cli/issues/3064)。 |

## ⚙️ Specify CLI リファレンス

`specify` コマンドは以下のオプションをサポートしています：

### コマンド

| コマンド | 説明 |
|-------------|----------------------------------------------------------------|
| `init` | 最新のテンプレートから新しい Specify プロジェクトを初期化 |
| `check` | インストールされたツールをチェック (`git`, `claude`, `gemini`, `code`/`code-insiders`, `cursor-agent`, `windsurf`, `qwen`, `opencode`, `codex`) |

### `specify init` 引数とオプション

| 引数/オプション | タイプ | 説明 |
|------------------------|----------|------------------------------------------------------------------------------|
| `<project-name>` | 引数 | 新しいプロジェクトディレクトリの名前（`--here` を使用する場合はオプション、または `.` で現在のディレクトリを使用） |
| `--ai` | オプション | 使用する AI アシスタント：`claude`, `gemini`, `copilot`, `cursor-agent`, `qwen`, `opencode`, `codex`, `windsurf`, `kilocode`, `auggie`, `roo`, `codebuddy`, または `q` |
| `--script` | オプション | 使用するスクリプトバリアント：`sh` (bash/zsh) または `ps` (PowerShell) |
| `--ignore-agent-tools` | フラグ | Claude Code のような AI エージェントツールのチェックをスキップ |
| `--no-git` | フラグ | git リポジトリの初期化をスキップ |
| `--here` | フラグ | 新しいディレクトリを作成する代わりに現在のディレクトリでプロジェクトを初期化 |
| `--force` | フラグ | 現在のディレクトリで初期化する際にマージ/上書きを強制（確認をスキップ） |
| `--skip-tls` | フラグ | SSL/TLS 検証をスキップ（推奨されません） |
| `--debug` | フラグ | トラブルシューティングのための詳細なデバッグ出力を有効化 |
| `--github-token` | オプション | API リクエストのための GitHub トークン（または GH_TOKEN/GITHUB_TOKEN 環境変数を設定） |

### 例

```bash
# 基本的なプロジェクト初期化
specify init my-project

# 特定の AI アシスタントで初期化
specify init my-project --ai claude

# Cursor サポートで初期化
specify init my-project --ai cursor-agent

# Windsurf サポートで初期化
specify init my-project --ai windsurf

# PowerShell スクリプトで初期化（Windows/クロスプラットフォーム）
specify init my-project --ai copilot --script ps

# 現在のディレクトリで初期化
specify init . --ai copilot
# または --here フラグを使用
specify init --here --ai copilot

# 確認なしで現在の（空でない）ディレクトリに強制的にマージ
specify init . --force --ai copilot
# または
specify init --here --force --ai copilot

# git 初期化をスキップ
specify init my-project --ai gemini --no-git

# トラブルシューティングのためのデバッグ出力を有効化
specify init my-project --ai claude --debug

# API リクエストに GitHub トークンを使用（企業環境に便利）
specify init my-project --ai claude --github-token ghp_your_token_here

# システム要件をチェック
specify check
```

### 利用可能なスラッシュコマンド

`specify init` を実行後、AI コーディングエージェントは構造化開発のためのこれらのスラッシュコマンドにアクセスできます：

#### コアコマンド

スペック駆動開発ワークフローの基本的なコマンド：

| コマンド | 説明 |
|--------------------------|-----------------------------------------------------------------------|
| `/speckit.constitution` | プロジェクトの統治原則と開発ガイドラインを作成または更新 |
| `/speckit.specify` | 構築したいものを定義（要件とユーザーストーリー） |
| `/speckit.plan` | 選択した技術スタックで技術的実装計画を作成 |
| `/speckit.tasks` | 実装のための実行可能なタスクリストを生成 |
| `/speckit.implement` | すべてのタスクを実行して計画に従って機能を構築 |

#### オプションコマンド

品質と検証を強化するための追加コマンド：

| コマンド | 説明 |
|----------------------|-----------------------------------------------------------------------|
| `/speckit.clarify` | 不十分に仕様化された領域を明確化（`/speckit.plan` の前に推奨；以前は `/quizme`） |
| `/speckit.analyze` | 複数アーティファクト間の一貫性とカバレッジ分析（`/speckit.tasks` の後、`/speckit.implement` の前で実行） |
| `/speckit.checklist` | 要件の完全性、明確性、一貫性を検証するカスタム品質チェックリストを生成（「英語のユニットテスト」のような） |

### 環境変数

| 変数 | 説明 |
|------------------|------------------------------------------------------------------------------------------------|
| `SPECIFY_FEATURE` | 非 Git リポジトリの機能検出を上書きします。機能ディレクトリ名（例：`001-photo-albums`）を設定して、Git ブランチを使用しない場合に特定の機能で作業します。<br/>**`/speckit.plan` または後続コマンドを使用する前に、作業しているエージェントのコンテキストで設定する必要があります。 |

## 🎯 核となる哲学

スペック駆動開発は以下のことを強調する構造化プロセスです：

- **意図駆動開発**：仕様が「_何_」を「_どうやって_」の前に定義する
- **豊富な仕様作成**：ガードレールと組織的原則を使用
- **複数ステップの精巧化**：プロンプトからのワンショットコード生成ではなく
- **高度な AI モデル能力**の仕様解釈への**多大な依存**

## 🔄 開発フェーズ

| フェーズ | 焦点 | 主な活動 |
|-------|-------|----------------|
| **0から1の開発**（"グリーンフィールド"） | 一から生成 | <ul><li>高レベルの要件から始める</li><li>仕様を生成</li><li>実装ステップを計画</li><li>プロダクションレディなアプリケーションを構築</li></ul> |
| **クリエイティブ探索** | 並列実装 | <ul><li>多様なソリューションを探索</li><li>複数の技術スタックとアーキテクチャをサポート</li><li>UXパターンを実験</li></ul> |
| **反復的強化**（"ブラウンフィールド"） | ブラウンフィールドのモダナイゼーション | <ul><li>機能を反復的に追加</li><li>レガシーシステムのモダナイゼーション</li><li>プロセスを適応</li></ul> |

## 🧪 実験的目标

私たちの研究と実験は以下に焦点を当てています：

### 技術的独立性

- 異なる技術スタックを使用してアプリケーションを作成
- スペック駆動開発が特定の技術、プログラミング言語、またはフレームワークに結びついていないプロセスであるという仮説を検証

### エンタープライズ制約

- ミッションクリティカルなアプリケーション開発を実証
- 組織的制約（クラウドプロバイダ、技術スタック、エンジニアリングプラクティス）を組み込み
- エンタープライズデザインシステムとコンプライアンス要件をサポート

### ユーザーセンタード開発

- 異なるユーザーコホートと嗜好のためにアプリケーションを構築
- 様々な開発アプローチ（ビビッドコーディングからAIネイティブ開発まで）をサポート

### クリエイティブおよび反復的プロセス

- 並列実装探索の概念を検証
- 堅牢な反復的機能開発ワークフローを提供
- アップグレードとモダナイゼーションタスクを処理するようにプロセスを拡張

## 📋 前提条件

- **Linux/macOS/Windows**
- [サポートされている](#-サポートされているaiエージェント) AI コーディングエージェント。
- パッケージ管理のための [uv](https://docs.astral.sh/uv/)
- [Python 3.11+](https://www.python.org/downloads/)
- [Git](https://git-scm.com/downloads)

エージェントで問題が発生した場合は、統合を洗練させるために問題を報告してください。

## 📚 より詳しく

- **[完全なスペック駆動開発メソドロジー](./spec-driven.md)** - 完全プロセスの詳細
- **[詳細なウォークスルー](#-詳細なプロセス)** - ステップバイステップの実装ガイド

---

## 📝 詳細なプロセス

<details>
<summary>クリックして詳細なステップバイステップのウォークスルーを展開</summary>

Specify CLI を使用してプロジェクトをブートストラップできます。これにより、必要なアーティファクトが環境に導入されます。実行：

```bash
specify init <project_name>
```

または現在のディレクトリで初期化：

```bash
specify init .
# または --here フラグを使用
specify init --here
# ディレクトリに既にファイルがある場合に確認をスキップ
specify init . --force
# または
specify init --here --force
```

![Specify CLI が端末で新しいプロジェクトをブートストラップ](./media/specify_cli.gif)

使用している AI エージェントを選択するように求められます。端末で積極的に指定することもできます：

```bash
specify init <project_name> --ai claude
specify init <project_name> --ai gemini
specify init <project_name> --ai copilot

# または現在のディレクトリで：
specify init . --ai claude
specify init . --ai codex

# または --here フラグを使用
specify init --here --ai claude
specify init --here --ai codex

# 空でない現在のディレクトリに強制的にマージ
specify init . --force --ai claude

# または
specify init --here --force --ai claude
```

CLI は Claude Code、Gemini CLI、Cursor CLI、Qwen CLI、opencode、Codex CLI、または Amazon Q Developer CLI がインストールされているかを確認します。インストールされていない場合、または正しいツールのチェックなしでテンプレートを取得したい場合は、コマンドで `--ignore-agent-tools` を使用します：

```bash
specify init <project_name> --ai claude --ignore-agent-tools
```

### **ステップ 1：** プロジェクトの原則を確立

プロジェクトフォルダに移動し、AI エージェントを実行します。私たちの例では `claude` を使用します。

![Claude Code 環境のブートストラップ](./media/bootstrap-claude-code.gif)

`/speckit.constitution`、`/speckit.specify`、`/speckit.plan`、`/speckit.tasks`、および `/speckit.implement` コマンドが利用可能であることを確認できれば、正しく構成されています。

最初のステップは `/speckit.constitution` コマンドを使用してプロジェクトの統治原則を確立することです。これにより、すべての後続開発フェーズで一貫した意思決定が保証されます：

```text
/speckit.constitution コード品質、テスト基準、ユーザーエクスペリエンスの一貫性、およびパフォーマンス要件に焦点を当てた原則を作成。これらの原則が技術的決定と実装の選択を指導する方法に関するガバナンスを含める。
```

このステップでは、AI エージェントが仕様、計画、および実装フェーズ中に参照するプロジェクトの基本ガイドラインを `.specify/memory/constitution.md` ファイルに作成または更新します。

### **ステップ 2：** プロジェクト仕様を作成

プロジェクトの原則が確立されたので、機能仕様を作成できます。`/speckit.specify` コマンドを使用し、開発したいプロジェクトの具体的な要件を提供します。

>[!IMPORTANT]
>構築しようとしている_何_と_なぜ_についてできるだけ明確にしてください。**この時点では技術スタックに焦点を当てないでください**。

例のプロンプト：

```text
Taskify、チーム生産性プラットフォームを開発してください。ユーザーがプロジェクトを作成し、チームメンバーを追加し、
タスクを割り当て、コメントし、カンバンスタイルのボード間でタスクを移動できるようにする必要があります。この機能の初期段階では、
これを「Create Taskify」と呼びましょう。複数のユーザーをあらかじめ宣言し、事前定義します。
私は5人のユーザーを2つの異なるカテゴリに分けたい、1人のプロダクトマネージャーと4人のエンジニアです。3つの
異なるサンプルプロジェクトを作成しましょう。各タスクのステータスの標準的なカンバン列を作成しましょう、「To Do」、
「In Progress」、「In Review」、および「Done」。このアプリケーションにはログイン機能はなく、これは基本的な機能が
設定されていることを確認するための最初のテストにすぎません。UIの各タスクカードでは、
カンバン作業ボードの異なる列の間でタスクの現在のステータスを変更できる必要があります。
特定のカードに無制限の数のコメントを残すことができます。そのタスク
カードから、有効なユーザーの1人を割り当てることができます。Taskifyを最初に起動すると、5人のユーザーのリストが
表示され、そこから選択できます。パスワードは必要ありません。ユーザーをクリックすると、
プロジェクトのリストを表示するメインビューに入ります。プロジェクトをクリックすると、そのプロジェクトの
カンバンボードが開きます。列が表示されます。
異なる列の間でカードをドラッグアンドドロップできます。あなたに
割り当てられている任意のカードは、現在ログインしているユーザーとして、他のすべてのカードとは異なる色で表示され、
迅速に自分のカードを確認できます。あなたが作成したコメントはすべて編集できますが、他の人が作成したコメントは編集できません。あなたは
自分が作成したコメントはすべて削除できますが、他の誰かが作成したコメントは削除できません。
```

このプロンプトが入力されると、Claude Code が計画と仕様作成プロセスを開始するはずです。Claude Code は、組み込みスクリプトをいくつか起動してリポジトリのセットアップも行います。

このステップが完了すると、新しいブランチが作成され（例：`001-create-taskify`）、`specs/001-create-taskify` ディレクトリに新しい仕様が作成されます。

生成された仕様には、テンプレートで定義されたユーザーストーリーと機能要件のセットが含まれます。

この段階で、プロジェクトフォルダの内容は以下のようになります：

```text
├── .specify
    ├── memory
    │    ├── constitution.md
    ├── scripts
    │    ├── check-prerequisites.sh
    │    ├── common.sh
    │    ├── create-new-feature.sh
    │    ├── setup-plan.sh
    │    └── update-claude-md.sh
    ├── specs
    │    ├── 001-create-taskify
    │        ├── spec.md
    └── templates
        ├── plan-template.md
        ├── spec-template.md
        └── tasks-template.md
```

### **ステップ 3：** 機能仕様の明確化（計画前必須）

ベースライン仕様が作成されたので、最初の試行で正しくキャプチャされなかった要件を明確化できます。

下流での再作業を減らすために、**技術計画を作成する前に**構造化された明確化ワークフローを実行する必要があります。

推奨順序：
1. `/speckit.clarify`（構造化）— 明確化セクションに回答を記録する順次、カバレッジベースの質問。
2. 必要に応じて、自由形式の精錬を後続で行う。

意図的に明確化をスキップしたい場合（例：スパイクまたは探索的プロトタイプ）、明確に述べてエージェントが不足している明確化でブロックしないようにしてください。

例の自由形式の精錬プロンプト（`/speckit.clarify` の後が必要な場合）：

```text
作成する各サンプルプロジェクトまたはプロジェクトには、5〜15の間の
タスクがあり、それぞれが異なる完了状態にランダムに分布するようにしてください。
各完了段階に少なくとも1つのタスクがあることを確認してください。
```

Claude Code に**レビューおよび承認チェックリスト**を検証するように指示する必要もあります。要件を満たす項目をチェックし、満たさない項目は空のままにしてください。以下のプロンプトを使用できます：

```text
レビューおよび承認チェックリストを読み、機能仕様が基準を満たす場合はチェックリストの各項目をチェックしてください。満たさない場合は空のままにしてください。
```

Claude Code とのインタラクションを仕様に関する明確化と質問の機会として活用することが重要です — **最初の試みを最終的なものとして扱わないでください**。

### **ステップ 4：** 計画を生成

これで、技術スタックやその他の技術要件について具体的に指定できます。プロジェクトテンプレートに組み込まれた `/speckit.plan` コマンドを使用し、以下のようなプロンプトを使用します：

```text
.NET Aspire を使用してこれを生成します。データベースにはPostgresを使用します。フロントエンドは
Blazor サーバーとドラッグアンドドロップのタスクボード、リアルタイム更新を使用します。プロジェクトAPI、
タスクAPI、および通知APIを持つREST APIを作成する必要があります。
```

このステップの出力には多くの実装詳細ドキュメントが含まれ、ディレクトリツリーは以下のようになります：

```text
.
├── CLAUDE.md
├── memory
│    ├── constitution.md
├── scripts
│    ├── check-prerequisites.sh
│    ├── common.sh
│    ├── create-new-feature.sh
│    ├── setup-plan.sh
│    └── update-claude-md.sh
├── specs
│    ├── 001-create-taskify
│        ├── contracts
│        │    ├── api-spec.json
│        │    └── signalr-spec.md
│        ├── data-model.md
│        ├── plan.md
│        ├── quickstart.md
│        ├── research.md
│        └── spec.md
└── templates
    ├── CLAUDE-template.md
    ├── plan-template.md
    ├── spec-template.md
    └── tasks-template.md
```

指示に基づいて正しい技術スタックが使用されていることを確認するために `research.md` ドキュメントを確認してください。コンポーネントが目立つ場合は Claude Code に精錬を依頼するか、使用したいプラットフォーム/フレームワーク（例：.NET）のローカルインストールバージョンを確認するように依頼することもできます。

さらに、選択した技術スタックが急速に変化している場合（例：.NET Aspire、JSフレームワーク）、以下のようなプロンプトで Claude Code に詳細を調査するように依頼することもできます：

```text
実装計画と実装詳細を通過して、.NET Aspire が急速に変化するライブラリであるため、
追加の研究が役立つ可能性のある領域を探してください。特定の識別された領域について
追加研究が必要な場合は、Taskify アプリケーションで使用する特定のバージョンに関する
追加の詳細で研究ドキュメントを更新し、Webからの研究を使用して詳細を明確化する
並列研究タスクを生成してください。
```

このプロセス中に、Claude Code が間違ったことを研究して詰まってしまうことがあります - 以下のようなプロンプトで正しい方向に導くことができます：

```text
これを一連のステップに分解する必要があります。まず、実装中に
実行する必要があるタスクのリストを特定してください
不確かなもの、またはさらなる研究が役立つものです。それらのタスクのリストを書いてください。そして、
これらのタスクのそれぞれについて、個別の研究タスクを開始して、
すべての非常に特定のタスクを並列で研究していることです。あなたがやっているように見えたのは、
.NET Aspire 全般を研究していたようで、この場合、あまり役に立たないと思います。
これはターゲットが広すぎる研究です。研究は特定のターゲットのある質問を解決するのに役立つ必要があります。
```

>[!NOTE]
>Claude Code は過度に積極的で、要求していないコンポーネントを追加するかもしれません。変更の理由と出所を明確化するように依頼してください。

### **ステップ 5：** Claude Code に計画を検証させる

計画が策定されたので、Claude Code にそれを通読させて、抜けがないか確認する必要があります。以下のようなプロンプトを使用できます：

```text
今、実装計画と実装詳細ファイルを検査してください。
読む際に、読んだ結果から明らかになる必要があるタスクのシーケンスが
あるかどうかを判断してください。なぜなら、十分にあるかどうか分からないからです。例えば、
コア実装を見ると、各ステップを通過する際に実装詳細の適切な場所を参照することが
役立つかもしれません。
```

これにより、実装計画が洗練され、Claude Code が計画サイクルで見逃した潜在的な盲点を回避できます。初期の精錬パスが完了したら、実装に進む前に Claude Code にもう一度チェックリストを通過させます。

[GitHub CLI](https://docs.github.com/en/github-cli/github-cli) をインストールしている場合は、Claude Code に現在のブランチから `main` へのプルリクエストを詳細な説明で作成するように依頼することもできます。これにより、作業が適切に追跡されます。

>[!NOTE]
>エージェントに実装させる前に、オーバーエンジニアリングされた部分がないか Claude Code にプロンプトしてクロスチェックすることも価値があります（覚えておいてください - 過度に積極的です）。オーバーエンジニアリングされたコンポーネントや決定が存在する場合は、Claude Code に解決を依頼できます。Claude Code が計画を確立する際に遵守しなければならない基本的な部分として、[constitution](base/memory/constitution.md) に従うことを確認してください。

### **ステップ 6：** /speckit.tasks でタスク分解を生成

実装計画が検証されたので、計画を正しい順序で実行可能な具体的なタスクに分解できます。`/speckit.tasks` コマンドを使用して、実装計画から詳細なタスク分解を自動生成します：

```text
/speckit.tasks
```

このステップでは、機能仕様ディレクトリに `tasks.md` ファイルを作成し、以下を含みます：

- **ユーザーストーリーごとに整理されたタスク分解** - 各ユーザーストーリーは独自のタスクセットを持つ独立した実装フェーズになります
- **依存関係管理** - タスクはコンポーネント間の依存関係を尊重するように順序付けされます（例：モデルの前にサービス、サービスの前にエンドポイント）
- **並列実行マーカー** - 並列で実行できるタスクは `[P]` でマークされ、開発ワークフローを最適化します
- **ファイルパス指定** - 各タスクには実装が発生する正確なファイルパスが含まれます
- **テスト駆動開発構造** - テストが要求された場合、テストタスクが含まれ、実装の前に書かれるように順序付けされます
- **チェックポイント検証** - 各ユーザーストーリーフェーズには、独立した機能を検証するためのチェックポイントが含まれます

生成された tasks.md は `/speckit.implement` コマンドの明確なロードマップを提供し、コード品質を維持し、ユーザーストーリーのインクリメンタルデリバリーを可能にする体系的な実装を保証します。

### **ステップ 7：** 実装

準備ができたら、`/speckit.implement` コマンドを使用して実装計画を実行します：

```text
/speckit.implement
```

`/speckit.implement` コマンドは以下を実行します：
- すべての前提条件が整っていることを検証します（constitution、spec、plan、および tasks）
- `tasks.md` からタスク分解を解析します
- 依存関係と並列実行マーカーを尊重して正しい順序でタスクを実行します
- タスク計画で定義された TDD アプローチに従います
- 進行状況の更新を提供し、エラーを適切に処理します

>[!IMPORTANT]
>AI エージェントはローカル CLI コマンド（`dotnet`、`npm` など）を実行します - 必要なツールがマシンにインストールされていることを確認してください。

実装が完了したら、アプリケーションをテストし、CLI ログでは見えない可能性のある実行時エラーを解決します（例：ブラウザコンソールエラー）。そのようなエラーを AI エージェントにコピー＆ペーストして解決できます。

</details>

---

## 🔧 トラブルシューティング

### Linux での Git Credential Manager

Linux で Git 認証の問題が発生している場合は、Git Credential Manager をインストールできます：

```bash
#!/usr/bin/env bash
set -e
echo "Git Credential Manager v2.6.1 をダウンロード中..."
wget https://github.com/git-ecosystem/git-credential-manager/releases/download/v2.6.1/gcm-linux_amd64.2.6.1.deb
echo "Git Credential Manager をインストール中..."
sudo dpkg -i gcm-linux_amd64.2.6.1.deb
echo "Git を GCM を使用するように構成..."
git config --global credential.helper manager
echo "クリーンアップ..."
rm gcm-linux_amd64.2.6.1.deb
```

## 👥 メンテナー

- Den Delimarsky ([@localden](https://github.com/localden))
- John Lam ([@jflam](https://github.com/jflam))

## 💬 サポート

サポートについては、[GitHub issue](https://github.com/github/spec-kit/issues/new) を開いてください。バグ報告、機能リクエスト、およびスペック駆動開発に関する質問を歓迎します。

## 🙏 謝辞

このプロジェクトは [John Lam](https://github.com/jflam) の作業と研究に大きく影響を受けており、その基礎上に成り立っています。

## 📄 ライセンス

このプロジェクトは MIT オープンソースライセンスの条件に基づいてライセンスされています。完全な条項については [LICENSE](./LICENSE) ファイルを参照してください。