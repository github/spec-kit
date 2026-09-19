<div align="center">
    <img src="https://raw.githubusercontent.com/github/spec-kit/main/media/logo_large.webp" alt="Spec Kitロゴ" width="200" height="200"/>
    <h1>🌱 Spec Kit</h1>
    <h3><em>仕様で作る、バグを直す、アイデアを見極める ―― あなたのコーディングエージェントと共に。</em></h3>
</div>

<p align="center">
    <a href="https://github.com/github/spec-kit/releases/latest"><img src="https://img.shields.io/github/v/release/github/spec-kit" alt="最新リリース"/></a>
    <a href="https://github.com/github/spec-kit/stargazers"><img src="https://img.shields.io/github/stars/github/spec-kit?style=social" alt="GitHub stars"/></a>
    <a href="https://github.com/github/spec-kit/blob/main/LICENSE"><img src="https://img.shields.io/github/license/github/spec-kit" alt="ライセンス"/></a>
    <a href="https://github.github.io/spec-kit/"><img src="https://img.shields.io/badge/docs-GitHub_Pages-blue" alt="ドキュメント"/></a>
</p>

<p align="center">
    <a href="./README.md">English</a> ·
    <a href="./README.zh-CN.md">简体中文</a> ·
    <strong>日本語</strong>
</p>

Spec Kitは、AIコーディングエージェントに構造化されたプロセス、再利用可能なテンプレート、記録に残る成果をもたらすオープンソースのツールキットです。以下の3つのプロセスのいずれかから始め、必要に応じてカスタマイズしたり、自分自身のプロセスを持ち込んだりすることもできます。

## 利用するプロセスを選択する

| やりたいこと | プロセス | 成果 |
| --- | --- | --- |
| 機能やアプリケーションを構築する | [仕様駆動開発](#仕様駆動開発) | 計画・実装・収束を経て完成した仕様 |
| 不具合のある動作を診断し、修正する | [バグ修正](#バグ修正) | 評価された原因、範囲を絞った修正、記録された検証 |
| アイデアに投資する価値があるか判断する | [アイデア評価](#アイデア評価) | 根拠に基づく、進める(go)・要確認・中止のいずれかの決定 |

これらは**独立したエントリーポイント**であり、必ず順番に実施する3段階のフェーズではありません。SDDはコアに同梱されています。バグ修正とアイデア評価は、必要なときにインストールするバンドル拡張機能です。

<a id="-はじめる"></a>
<a id="-前提条件"></a>

## はじめる

Linux、macOS、またはWindows上で、**Python 3.11以降**、**[uv](https://github.github.io/spec-kit/install/uv.html)**、および対応するAIコーディングエージェントが必要です。
**CLIのみのセットアップ**を行う場合は、ターミナルで以下のコマンドを実行してSpec Kitをインストールし、プロジェクトを作成してください。

```bash
uv tool install specify-cli
specify init my-project --integration copilot
cd my-project
```

<a id="-対応しているaiコーディングエージェント"></a>

この例では **GitHub Copilotのデフォルトのスキルモード** を使用しています。他の対応エージェントを使う場合は、`copilot` をお使いのエージェントの[エージェント識別子](https://github.github.io/spec-kit/reference/integrations.html)に置き換えてください。

すでにコードがありますか？[既存プロジェクト向けガイド](https://github.github.io/spec-kit/guides/existing-projects.html)を参照してください。バージョン固定でのインストール、その他のインストーラー、CI、トラブルシューティングについては[インストールガイド](https://github.github.io/spec-kit/installation.html)を、既存のインストールを更新する場合は[アップグレードガイド](https://github.github.io/spec-kit/upgrade.html)を参照してください。

ここから**プロジェクトディレクトリでコーディングエージェントを起動し**、下記のいずれかのプロセスを選んでください。各 `/speckit-*` **スキルはエージェントのチャット内で**、1つずつ呼び出し、結果を確認してから次に進んでください。これらはターミナルコマンドではなく、エージェントのスキルです。エージェントやモードによっては、[異なる呼び出し方](https://github.github.io/spec-kit/reference/integrations.html#command-invocation)を使う場合があります。

<a id="-仕様駆動開発とは"></a>
<a id="sdd-クイックスタート"></a>

## 仕様駆動開発

作る **方法(how)** を決める前に、 **何を(what)・なぜ(why)** を定義します。SDDは要件を仕様・技術計画・実行可能なタスクへと変換し、それらの成果物に沿って実装を導きます。

**プロジェクトごとに一度だけ全体ルール(constitution)を定め、機能ごとに 仕様化(specify) → 計画(plan) → タスク化(tasks) → 実装(implement) → 収束(converge) を行います。**

エージェントのチャットで、以下のスキルを呼び出します:

```text
/speckit-constitution Create principles focused on code quality, testing, and maintainability.
/speckit-specify Build a photo organizer with albums grouped by date and a tile preview of each album.
/speckit-plan Use Vite with vanilla JavaScript. Keep images local and store metadata in SQLite.
/speckit-tasks
/speckit-implement
/speckit-converge
```

収束結果が **Converged** と報告されるまで、**implement → converge** を繰り返します。追加の品質ゲートが必要な場合は、明確化・チェックリスト・一貫性分析を加えてください。

[SDD実践ガイド](https://github.github.io/spec-kit/quickstart.html) ·
[コマンドリファレンス](https://github.github.io/spec-kit/reference/agentic-sdd.html)

<a id="-spec-kitを利用したバグ修正"></a>
<a id="バグ修正-クイックスタート"></a>

## バグ修正

診断・修復・検証を分けておくことで、エージェントが評価済みの原因を修正し、元の症状が解消されたかを確認できるようにします。事前にSDDの機能開発ワークフローを行う必要はありません。

**CLIセットアップ(ターミナル):** プロジェクトディレクトリでオプトイン方式の拡張機能をインストールします:

```bash
specify extension add bug
```

次に、エージェントのチャットで **評価(assess) → 修正(fix) → テスト(test)** のスキルを呼び出します:

```text
/speckit-bug-assess "Submitting an empty password crashes the login form." slug=login-crash
/speckit-bug-fix slug=login-crash
/speckit-bug-test slug=login-crash
```

レポートは `.specify/bugs/login-crash/` に保存されます。最終的な判定を確認してください。
`verified`(検証済み)、`partial`(部分的)、`failed`(失敗)のいずれかです。検証がないものは修正が成功したとは言えません。

[バグ修正実践ガイド](https://github.github.io/spec-kit/guides/bugfix.html) ·
[コマンドリファレンス](https://github.github.io/spec-kit/reference/agentic-bugfix.html)

<a id="-spec-kitを利用したアイデアの評価"></a>
<a id="アイデア評価-クイックスタート"></a>

## アイデア評価

そのアイデアがソフトウェアになるかどうかにかかわらず、アイデアにコミットする前に根拠を集めます。この独立したプロセスは、ソースコードが存在しないプロジェクトでも機能します。

**CLIセットアップ(ターミナル):** プロジェクトディレクトリでオプトイン方式の拡張機能をインストールします:

```bash
specify extension add assess
```

次に、エージェントのチャットで **受付(intake) → 調査(research) → 定義(define) → 具体化(shape) → 決定(decide)** のスキルを呼び出します:

```text
/speckit-assess-intake "Let users work offline and sync when they reconnect." slug=offline-mode
/speckit-assess-research slug=offline-mode
/speckit-assess-define slug=offline-mode
/speckit-assess-shape slug=offline-mode
/speckit-assess-decide slug=offline-mode
```

成果物は `.specify/assessments/offline-mode/` に保存され、最終的に
**進める(go)・要確認(needs-clarification)・中止(kill)** の3択で結論が出ます。不明点を解消するには、ステージ全体を再生成するのではなく、既存のMarkdown成果物を直接、またはエージェントと一緒に修正してください。`go` の決定が出て実際に開発する場合は `/speckit-specify` に引き継げます。理由を明記した上で停止することも、有用な結果の一つです。

[アイデア評価実践ガイド](https://github.github.io/spec-kit/guides/assessment.html) ·
[コマンドリファレンス](https://github.github.io/spec-kit/reference/agentic-assessment.html)

<a id="-spec-kitを自分仕様にカスタマイズする-拡張機能とプリセット"></a>
<a id="-バンドルbundles-ロールベースのセットアップ"></a>
<a id="-コミュニティ"></a>

## プロセスをカスタマイズする、または自分自身のプロセスを持ち込む

**拡張機能**は新しい機能を追加し、**プリセット**は既存の挙動を調整し、**ワークフロー**は手順を自動化し、**バンドル**はロールベースのセットアップをパッケージ化します。単発のテンプレート変更にはプロジェクトローカルなオーバーライドを使用してください。

[カスタマイズガイド](https://github.github.io/spec-kit/guides/customization.html) ·
[コミュニティの拡張機能・プリセット・バンドル・ウォークスルー](https://github.github.io/spec-kit/community/overview.html)

<a id="-specify-cli-リファレンス"></a>
<a id="利用可能なスラッシュコマンド"></a>
<a id="-詳しく学ぶ"></a>
<a id="-基本理念"></a>
<a id="-開発フェーズ"></a>
<a id="-実験的な目標"></a>
<a id="️-紹介動画"></a>
<a id="-spec-kitはspec-kit自身を使っているのか"></a>

## ドキュメント

- [CLIリファレンス](https://github.github.io/spec-kit/reference/overview.html) と [プロセスコマンド](https://github.github.io/spec-kit/reference/agentic-sdd.html#command-overview)
- [SDDの理念](https://github.github.io/spec-kit/concepts/sdd.html)、[完全な方法論](./spec-driven.md)、[既存の仕様の進化](https://github.github.io/spec-kit/guides/evolving-specs.html)
- [紹介動画](https://github.github.io/spec-kit/quickstart.html#video-overview) と [プロジェクトの歴史](https://github.github.io/spec-kit/history.html)
- [Spec KitはSpec Kit自身をどう使っているか](./CONTRIBUTING.md#does-spec-kit-use-spec-kit)

<a id="-サポート"></a>

## サポートと貢献

[バグを報告する、または機能をリクエストする](https://github.com/github/spec-kit/issues/new) ·
[コントリビューションガイド](./CONTRIBUTING.md) · [行動規範](./CODE_OF_CONDUCT.md)

<a id="-ライセンス"></a>

Spec Kitは[MITライセンス](./LICENSE)の下で提供されています。
