<!-- Generated from data/scenarios.json + data/projects.json. -->
[← 検索入口に戻る](../README.ja.md#discovery)

# 関連文書・記憶の検索

検索済みの候補から Agent に渡す情報を絞ります。

**JEV が担当する段階**

候補を検索 → JEV が関連性を採点 → ローカルで再順位付け・フォールバック

## 参考プロジェクト

### [OpenViking · JEV Rerank](https://github.com/volcengine/OpenViking)

OpenViking は JEV を使い、Agent の記憶・コンテキスト検索結果を較正して再順位付けできます。

**参考にする部分:** 文書ごとの関連性判定とベクトルスコアへのフォールバック。

[根拠](https://github.com/volcengine/OpenViking/blob/b8bed5a1ad3a1c524b5e1fd0fa591df51ca9b7cc/openviking/models/rerank/jev_rerank.py)

### [Hindsight · TypeSafe Rerank](https://github.com/vectorize-io/hindsight)

Agent メモリに TypeSafe リランカーを追加し、無関係な検索候補を除外できます。

**参考にする部分:** 記憶検索における関連性採点と候補削減。

[根拠](https://github.com/vectorize-io/hindsight/blob/680406b3dd9cca2108c7f0e204820a09b4e30906/hindsight-api-slim/hindsight_api/engine/cross_encoder.py)

### [Hippo Memory · JEV Reranker](https://github.com/kitfunso/hippo-memory)

ローカル優先の Agent メモリライブラリで、任意で JEV リランカーを利用できます。

**参考にする部分:** 記憶の一括判定とローカル順位へのフォールバック。

[根拠](https://github.com/kitfunso/hippo-memory/blob/c9eb2c31cd307cdae78c05e1fcb3e6d062efd5c0/src/rerankers/jev.ts)

各プロジェクトはこのパターンの一部を示すもので、単一の完成アプリではありません。ソース確認は、動作・性能・BeatAPI 互換性の検証を意味しません。

[無料 JEV API を試す](https://docs.beatapi.io/decisions#free-calls) · [Agent で検索](../docs/agent-search.ja.md)
