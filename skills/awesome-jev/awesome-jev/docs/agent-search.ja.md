[← Awesome JEV](../README.ja.md#discovery)

# Agent でプロジェクトを検索

やりたいことを伝えると、Agent が同じカタログと用途索引から参考実装を選びます。検索には BeatAPI アカウントも API キーも不要です。

## インストール

```bash
npx skills add BeatAPI/awesome-jev
```

スキルを使いたいプロジェクトで実行し、インストーラーで Agent を選びます。Node.js/npm が必要です。対応ホストはインストーラーで確認してください。

[Skill source](../skills/awesome-jev/SKILL.md) · [Installer documentation](https://skills.sh/docs/cli)

## 質問例

- ブランドに関係するニュースを選別したい。参考になる JEV プロジェクトと、各実装の参考箇所を教えて。
- Agent の記憶を再順位付けする Python プロジェクトを探して。直接使える部分と改修が必要な部分を分けて。
- コーディング Agent 向けの JEV モデルルーティングを比較し、実装の根拠も示して。

## 得られる結果

GitHub リンク、適合する理由、参考箇所、確認状態を添えた少数の候補。Agent は公開カタログの最新版を読みます。取得できない場合は、その制約を報告します。

## 手動インストール

`skills/awesome-jev` フォルダーをホストのスキルディレクトリにコピーします。Codex なら `~/.codex/skills/awesome-jev` に配置し、新しいセッションを開始します。候補プロジェクトのインストールや実行は行いません。

## メンテナー向けローカル確認

マージ前はチェックアウト内で `npx skills add . --list` を実行し、`npx skills add .` でローカルからインストールできます。上のリモートコマンドはデフォルトブランチへの反映後に利用可能です。
