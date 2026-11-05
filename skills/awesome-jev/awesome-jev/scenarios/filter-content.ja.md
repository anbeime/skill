<!-- Generated from data/scenarios.json + data/projects.json. -->
[← 検索入口に戻る](../README.ja.md#discovery)

# ニュース・コンテンツの選別

情報の流れから必要な内容を残し、不要なものを除きます。

**JEV が担当する段階**

取得済みの内容 → JEV が関連性・分類を判定 → アプリが選別・振り分け

## 参考プロジェクト

### [NewsJack](https://github.com/elvisun/newsjack)

ライブ ニュース フィードをスクリーニングしてタイムリーなブランド チャンスを見つけるオープンソースの PR ワークフロー。

**参考にする部分:** 見出しの選別から PR 候補の検討につなぐ流れ。

[根拠](https://github.com/elvisun/newsjack/tree/092d882fc69912622f620c50eb493afe625f99dc/demos/news-desk-dealer)

### [Bluenoise](https://github.com/rokcso/bluenoise)

デフォルトでローカル ルールを使用する X/Twitter フィルタリング拡張機能。オプションで JEV が一致しない返信をチェックします。

**参考にする部分:** 返信のルール判定後に JEV を補助的に使う分担。

[根拠](https://github.com/rokcso/bluenoise/blob/ef81ea7a7c3677501d6de8f9235a4d6a866b573a/entrypoints/background.ts)

### [Youtube Sponsor Detection](https://github.com/trungdq88/youtube-sponsor-detection)

YouTube 拡張機能は、JEV を使用してライブ音声とトランスクリプトからスポンサー付きセグメントを検出し、プロモーション ブロックを自動的にスキップします。

**参考にする部分:** 字幕区間の分類と広告スキップ操作の連携。

[根拠](https://github.com/trungdq88/youtube-sponsor-detection/blob/de01f0568d043035889a296a61ce21e0accc8b16/extension/lib/jev.js#L1-L541)

各プロジェクトはこのパターンの一部を示すもので、単一の完成アプリではありません。ソース確認は、動作・性能・BeatAPI 互換性の検証を意味しません。

[無料 JEV API を試す](https://docs.beatapi.io/decisions#free-calls) · [Agent で検索](../docs/agent-search.ja.md)
