<!-- Generated from data/scenarios.json + data/projects.json. -->
[← 検索入口に戻る](../README.ja.md#discovery)

# モデル・ツール・Agent の選択

既知の候補からタスクの実行先を選びます。

**JEV が担当する段階**

タスクと候補 → JEV が分類 → ローカル方針で実行先を選択

## 参考プロジェクト

### [LiteLLM · JEV Router](https://github.com/BerriAI/litellm)

LiteLLM は、複雑さベースのモデル ルーター内で JEV を使用できます。

**参考にする部分:** リクエストの複雑さを分類してからモデルに振り分ける方法。

[根拠](https://github.com/BerriAI/litellm/blob/56116079c8022da0e8f7ff9ccb017ad5aca5aed2/litellm/router_strategy/complexity_router/jev_classifier.py#L70)

### [Jev Model Router](https://github.com/davila7/claude-code-templates)

サブエージェント モデルと推論強度の必要性を分類する Claude Code mod。

**参考にする部分:** タスク分類を Claude Code のモデル・推論設定に対応させる方法。

[根拠](https://github.com/davila7/claude-code-templates/blob/61bfcd1586bf1076f6d3cfa0436317c912811e6c/cli-tool/components/mods/productivity/jev-model-router/hooks/jev-model-router.ts)

### [JevRouter](https://github.com/BillionsBobby/JevRouter)

モデル、ツール、サブ Agent 向けの軽量 JEV ルーター。

**参考にする部分:** モデル・ツール・サブ Agent の候補から選択する方法。

[根拠](https://github.com/BillionsBobby/JevRouter/blob/715970774ae8070e958e83ac9b1a780b32a9184c/src/provider.ts)

各プロジェクトはこのパターンの一部を示すもので、単一の完成アプリではありません。ソース確認は、動作・性能・BeatAPI 互換性の検証を意味しません。

[無料 JEV API を試す](https://docs.beatapi.io/decisions#free-calls) · [Agent で検索](../docs/agent-search.ja.md)
