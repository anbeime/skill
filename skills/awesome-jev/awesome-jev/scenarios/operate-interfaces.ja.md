<!-- Generated from data/scenarios.json + data/projects.json. -->
[← 検索入口に戻る](../README.ja.md#discovery)

# ブラウザ・デスクトップの操作

現在の画面から次の操作を選び、実行はコードが担います。

**JEV が担当する段階**

画面の観察と操作候補 → JEV が対象・操作を選択 → 実行器が操作

## 参考プロジェクト

### [Jev Ultrafast](https://github.com/browser-use/jev-ultrafast)

JEV を使用してアクションと一致する DOM 要素を選択し、入力テキストが必要な場合にのみテキスト モデルを呼び出すブラウザ エージェント。

**参考にする部分:** 操作と DOM 対象の同時選択、文章生成との役割分担。

[根拠](https://github.com/browser-use/jev-ultrafast/blob/1231850a0bf1a0c0341fe408ef1668dbbfdfac46/jev_ultrafast/model.py)

### [Cua · JEV Use](https://github.com/trycua/cua)

Cua Driver の観察と実行を、制限された JEV の選択肢と組み合わせたコンピューター使用例。

**参考にする部分:** 画面の観察結果を有限の操作 ID 選択につなぐ方法。

[根拠](https://github.com/trycua/cua/blob/83f142c4290a0f7d9ed545ae8532858c6e4f8145/libs/cua-driver/examples/jev-use/python/jev_adapter.py#L11)

### [Agent Desktop · JEV Skill](https://github.com/lahfir/agent-desktop)

アクセシビリティ データからネイティブ デスクトップ コントロールとアクションを選択するオプションの JEV スキル。

**参考にする部分:** アクセシビリティ情報からネイティブの操作対象を選ぶ方法。

[根拠](https://github.com/lahfir/agent-desktop/blob/7a8e4a10281c7319733aa200fd79501f34529716/scripts/jev/act.mjs)

各プロジェクトはこのパターンの一部を示すもので、単一の完成アプリではありません。ソース確認は、動作・性能・BeatAPI 互換性の検証を意味しません。

[無料 JEV API を試す](https://docs.beatapi.io/decisions#free-calls) · [Agent で検索](../docs/agent-search.ja.md)
