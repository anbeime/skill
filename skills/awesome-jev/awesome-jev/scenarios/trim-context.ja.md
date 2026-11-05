<!-- Generated from data/scenarios.json + data/projects.json. -->
[← 検索入口に戻る](../README.ja.md#discovery)

# Agent 履歴・ツール出力の整理

限られた文脈予算の中で有用な情報を残します。

**JEV が担当する段階**

履歴・出力断片 → JEV が保持価値を判定 → コードが保持・短縮・削除

## 参考プロジェクト

### [Fast Jev Compaction](https://github.com/tamaratran/fast-jev-compaction)

保持されたテキストをそのまま保持しながら、Claude Code ツール履歴を圧縮します。

**参考にする部分:** 有用なツール履歴を原文のまま保持する方法。

[根拠](https://github.com/tamaratran/fast-jev-compaction/blob/e3f262a7f4d42bd8dd32ced30d26176f7cb545b0/src/client.ts)

### [JEV Pruner](https://github.com/tamaratran/jev-pruner)

長い Bash 出力をモデルに渡す前に TypeSafe JEV で刈り込む Claude Code プラグイン。

**参考にする部分:** モデルに渡す前に長い Bash 出力を絞る方法。

[根拠](https://github.com/tamaratran/jev-pruner/blob/47d017c34eab7690b95f075ce6f4839247c5dc0a/src/jev.ts)

### [Save Token JEV Clean](https://github.com/IAmUnbounded/save-token-jev-clean)

履歴を保持・短縮・削除するか JEV に判断させる文脈クリーナー。

**参考にする部分:** 会話項目の保持スコアを整理処理に反映する方法。

[根拠](https://github.com/IAmUnbounded/save-token-jev-clean/blob/a7007354a8d3747f06ff82130561edb2822a17df/src/client.ts)

各プロジェクトはこのパターンの一部を示すもので、単一の完成アプリではありません。ソース確認は、動作・性能・BeatAPI 互換性の検証を意味しません。

[無料 JEV API を試す](https://docs.beatapi.io/decisions#free-calls) · [Agent で検索](../docs/agent-search.ja.md)
