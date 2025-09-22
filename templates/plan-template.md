---
description: "Implementation plan template for feature development"
scripts:
  sh: scripts/bash/update-agent-context.sh __AGENT__
  ps: scripts/powershell/update-agent-context.ps1 -AgentType __AGENT__
---

# 実装計画: [機能名]

**ブランチ**: `[###-feature-name]` | **日付**: [DATE] | **仕様**: [link]
**入力**: `/specs/[###-feature-name]/spec.md` からの機能仕様

## 実行フロー (/plan コマンドスコープ)
```
1. 入力パスから機能仕様を読み込み
   → 見つからない場合: ERROR "No feature spec at {path}"
2. 技術コンテキストを入力 (NEEDS CLARIFICATION をスキャン)
   → コンテキストからプロジェクトタイプを検出 (web=frontend+backend, mobile=app+api)
   → プロジェクトタイプに基づいて構造決定を設定
3. 憲章文書の内容に基づいて憲章チェックセクションを入力
4. 以下の憲章チェックセクションを評価
   → 違反が存在する場合: 複雑性追跡に文書化
   → 正当化が不可能な場合: ERROR "Simplify approach first"
   → 進捗追跡を更新: 初期憲章チェック
5. フェーズ0を実行 → research.md
   → NEEDS CLARIFICATION が残る場合: ERROR "Resolve unknowns"
6. フェーズ1を実行 → contracts, data-model.md, quickstart.md, エージェント固有テンプレートファイル (例: Claude Code用 `CLAUDE.md`, GitHub Copilot用 `.github/copilot-instructions.md`, Gemini CLI用 `GEMINI.md`, Qwen Code用 `QWEN.md`, opencode用 `AGENTS.md`)
7. 憲章チェックセクションを再評価
   → 新しい違反がある場合: 設計をリファクタリング、フェーズ1に戻る
   → 進捗追跡を更新: 設計後憲章チェック
8. フェーズ2を計画 → タスク生成アプローチを記述 (tasks.mdは作成しない)
9. 停止 - /tasks コマンドの準備完了
```

**重要**: /plan コマンドはステップ7で停止します。フェーズ2-4は他のコマンドで実行されます:
- フェーズ2: /tasks コマンドが tasks.md を作成
- フェーズ3-4: 実装実行 (手動またはツール経由)

## 概要
[機能仕様から抽出: 主要要件 + 調査からの技術アプローチ]

## 技術コンテキスト
**言語/バージョン**: [例: Python 3.11, Swift 5.9, Rust 1.75 または NEEDS CLARIFICATION]
**主要依存関係**: [例: FastAPI, UIKit, LLVM または NEEDS CLARIFICATION]
**ストレージ**: [該当する場合、例: PostgreSQL, CoreData, files または N/A]
**テスト**: [例: pytest, XCTest, cargo test または NEEDS CLARIFICATION]
**ターゲットプラットフォーム**: [例: Linux server, iOS 15+, WASM または NEEDS CLARIFICATION]
**プロジェクトタイプ**: [single/web/mobile - ソース構造を決定]
**パフォーマンス目標**: [ドメイン固有、例: 1000 req/s, 10k lines/sec, 60 fps または NEEDS CLARIFICATION]
**制約**: [ドメイン固有、例: <200ms p95, <100MB memory, offline-capable または NEEDS CLARIFICATION]
**規模/スコープ**: [ドメイン固有、例: 10k users, 1M LOC, 50 screens または NEEDS CLARIFICATION]

## 憲章チェック
*ゲート: フェーズ0調査前に通過必須。フェーズ1設計後に再チェック。*

[憲章ファイルに基づいて決定されるゲート]

## プロジェクト構造

### ドキュメント (この機能)
```
specs/[###-feature]/
├── plan.md              # このファイル (/plan コマンド出力)
├── research.md          # フェーズ0出力 (/plan コマンド)
├── data-model.md        # フェーズ1出力 (/plan コマンド)
├── quickstart.md        # フェーズ1出力 (/plan コマンド)
├── contracts/           # フェーズ1出力 (/plan コマンド)
└── tasks.md             # フェーズ2出力 (/tasks コマンド - /plan では作成されない)
```

### ソースコード (リポジトリルート)
```
# オプション1: 単一プロジェクト (デフォルト)
src/
├── models/
├── services/
├── cli/
└── lib/

tests/
├── contract/
├── integration/
└── unit/

# オプション2: Webアプリケーション ("frontend" + "backend" を検出した場合)
backend/
├── src/
│   ├── models/
│   ├── services/
│   └── api/
└── tests/

frontend/
├── src/
│   ├── components/
│   ├── pages/
│   └── services/
└── tests/

# オプション3: モバイル + API ("iOS/Android" を検出した場合)
api/
└── [上記backendと同じ]

ios/ or android/
└── [プラットフォーム固有構造]
```

**構造決定**: [技術コンテキストでweb/mobileアプリが示されない限り、デフォルトでオプション1]

## フェーズ0: 概要と調査
1. **上記技術コンテキストから未知項目を抽出**:
   - 各 NEEDS CLARIFICATION → 調査タスク
   - 各依存関係 → ベストプラクティスタスク
   - 各統合 → パターンタスク

2. **調査エージェントを生成・派遣**:
   ```
   技術コンテキストの各未知項目について:
     タスク: "Research {unknown} for {feature context}"
   各技術選択について:
     タスク: "Find best practices for {tech} in {domain}"
   ```

3. **発見事項を統合** `research.md` に以下の形式で:
   - 決定: [選択されたもの]
   - 根拠: [選択理由]
   - 検討した代替案: [他に評価したもの]

**出力**: すべての NEEDS CLARIFICATION が解決された research.md

## フェーズ1: 設計とコントラクト
*前提条件: research.md 完了*

1. **機能仕様からエンティティを抽出** → `data-model.md`:
   - エンティティ名、フィールド、関係
   - 要件からの検証ルール
   - 該当する場合は状態遷移

2. **機能要件からAPIコントラクトを生成**:
   - 各ユーザーアクション → エンドポイント
   - 標準的なREST/GraphQLパターンを使用
   - OpenAPI/GraphQLスキーマを `/contracts/` に出力

3. **コントラクトからコントラクトテストを生成**:
   - エンドポイントごとに1つのテストファイル
   - リクエスト/レスポンススキーマをアサート
   - テストは失敗する必要がある (実装がまだないため)

4. **ユーザーストーリーからテストシナリオを抽出**:
   - 各ストーリー → 統合テストシナリオ
   - クイックスタートテスト = ストーリー検証ステップ

5. **エージェントファイルを段階的に更新** (O(1)操作):
   - `{SCRIPT}` を実行
     **重要**: 上記で指定された通りに正確に実行する。引数を追加・削除しない。
   - 存在する場合: 現在の計画から新しい技術のみを追加
   - マーカー間の手動追加を保持
   - 最近の変更を更新 (最新3つを保持)
   - トークン効率のため150行以下を維持
   - リポジトリルートに出力

**出力**: data-model.md, /contracts/*, 失敗するテスト, quickstart.md, エージェント固有ファイル

## フェーズ2: タスク計画アプローチ
*このセクションは /tasks コマンドが行うことを記述 - /plan 中は実行しない*

**タスク生成戦略**:
- `.specify/templates/tasks-template.md` をベースとして読み込み
- フェーズ1設計文書 (コントラクト、データモデル、クイックスタート) からタスクを生成
- 各コントラクト → コントラクトテストタスク [P]
- 各エンティティ → モデル作成タスク [P]
- 各ユーザーストーリー → 統合テストタスク
- テストを通すための実装タスク

**順序戦略**:
- TDD順序: 実装前にテスト
- 依存関係順序: モデル、サービス、UIの順
- 並列実行用に [P] をマーク (独立ファイル)

**推定出力**: tasks.md に25-30の番号付き、順序付きタスク

**重要**: このフェーズは /tasks コマンドで実行され、/plan では実行されない

## フェーズ3以降: 将来の実装
*これらのフェーズは /plan コマンドのスコープ外*

**フェーズ3**: タスク実行 (/tasks コマンドが tasks.md を作成)
**フェーズ4**: 実装 (憲章原則に従って tasks.md を実行)
**フェーズ5**: 検証 (テスト実行、quickstart.md 実行、パフォーマンス検証)

## 複雑性追跡
*憲章チェックで正当化が必要な違反がある場合のみ入力*

| 違反 | 必要な理由 | 却下されたより簡単な代替案とその理由 |
|-----------|------------|-------------------------------------|
| [例: 4つ目のプロジェクト] | [現在のニーズ] | [3つのプロジェクトでは不十分な理由] |
| [例: Repositoryパターン] | [具体的な問題] | [直接DB接続では不十分な理由] |


## 進捗追跡
*このチェックリストは実行フロー中に更新される*

**フェーズステータス**:
- [ ] フェーズ0: 調査完了 (/plan コマンド)
- [ ] フェーズ1: 設計完了 (/plan コマンド)
- [ ] フェーズ2: タスク計画完了 (/plan コマンド - アプローチのみ記述)
- [ ] フェーズ3: タスク生成完了 (/tasks コマンド)
- [ ] フェーズ4: 実装完了
- [ ] フェーズ5: 検証通過

**ゲートステータス**:
- [ ] 初期憲章チェック: 合格
- [ ] 設計後憲章チェック: 合格
- [ ] すべての NEEDS CLARIFICATION 解決済み
- [ ] 複雑性逸脱を文書化済み

---
*憲章 v2.1.1 に基づく - `/memory/constitution.md` を参照*
