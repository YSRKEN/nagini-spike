# Issue tracker: Local Markdown

このリポジトリの issue と仕様は、`.scratch/` の下に markdown ファイルとして置く。作業の記録なので公開せず、`.gitignore` で Git の追跡から外している。

## 決まり

- 1つの機能に1つのディレクトリ: `.scratch/<feature-slug>/`
- 仕様は `.scratch/<feature-slug>/spec.md`
- 実装の issue は1チケット1ファイルで `.scratch/<feature-slug>/issues/<NN>-<slug>.md` に置く。番号は `01` から振る。チケットを1つのファイルにまとめない
- triage の状態は、各 issue ファイルの先頭近くの `Status:` 行に書く（役割の文字列は `triage-labels.md` を参照）
- コメントとやりとりの履歴は、ファイル末尾の `## Comments` 見出しの下に追記する

## スキルが「issue tracker に公開する」と言ったとき

`.scratch/<feature-slug>/` の下に新しいファイルを作る（ディレクトリが無ければ作る）。

## スキルが「該当チケットを取ってくる」と言ったとき

指定されたパスのファイルを読む。ふつうは利用者がパスか issue 番号を直接渡す。

## Wayfinding の操作

`/wayfinder` が使う。**map** は1つのファイルで、チケットごとに **child** のファイルを持つ。

- **Map**: `.scratch/<effort>/map.md`（Notes / Decisions-so-far / Fog の本文）
- **Child ticket**: `.scratch/<effort>/issues/NN-<slug>.md`。番号は `01` から振り、本文に問いを書く。`Type:` 行にチケットの種類（`research`/`prototype`/`grilling`/`task`）、`Status:` 行に `claimed`/`resolved` を書く
- **Blocking**: 先頭近くに `Blocked by: NN, NN` 行を書く。挙げたファイルがすべて `resolved` になれば、そのチケットは blocked でなくなる
- **Frontier**: `.scratch/<effort>/issues/` から、未完了で blocked でなく、まだ誰も claim していないファイルを探す。番号の小さいものから取る
- **Claim**: 作業の前に `Status: claimed` にして保存する
- **Resolve**: `## Answer` 見出しの下に答えを追記し、`Status: resolved` にしてから、`map.md` の Decisions-so-far に要旨とリンクを追記する
