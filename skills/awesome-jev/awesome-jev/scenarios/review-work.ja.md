<!-- Generated from data/scenarios.json + data/projects.json. -->
[← 検索入口に戻る](../README.ja.md#discovery)

# コード・出力のレビュー

結果を採用・通過させる前に、明確な条件で確認します。

**JEV が担当する段階**

出力候補と基準 → JEV が判定 → コードが報告・停止・再確認

## 参考プロジェクト

### [Jev Review](https://github.com/devagrawal09/jev-review)

Git diff またはコードベースを段階的にレビューし、ローカル ダッシュボードにレビュー リードを表示します。

**参考にする部分:** 証拠・問題の仕組み・重大度を段階的に判定する方法。

[根拠](https://github.com/devagrawal09/jev-review/blob/31f89602797fb7bea007f8a480bf368bf564954e/src/review/judgments.ts#L38)

### [Supercov](https://github.com/supercorp-ai/supercov)

JEV で限定的な品質チェックを行うコード品質・カバレッジツール。

**参考にする部分:** 生成テストとカバレッジの変化を品質基準で確認する方法。

[根拠](https://github.com/supercorp-ai/supercov/blob/55f5ce93a239829c224b89e6749991310be91ea4/crates/supercov-cli/src/quality.rs)

### [Agentgateway · JEV Guardrail](https://github.com/agentgateway/agentgateway)

モデルのリクエストとレスポンスを検査するための JEV Webhook ガードレールの例。

**参考にする部分:** リクエスト・レスポンスのリスク採点とゲートウェイ方針の連携。

[根拠](https://github.com/agentgateway/agentgateway/blob/6b0270efd25b5255932943e48b5ca47583d3ad28/examples/llm-guardrail-jev/guardrail.ts)

各プロジェクトはこのパターンの一部を示すもので、単一の完成アプリではありません。ソース確認は、動作・性能・BeatAPI 互換性の検証を意味しません。

[無料 JEV API を試す](https://docs.beatapi.io/decisions#free-calls) · [Agent で検索](../docs/agent-search.ja.md)
