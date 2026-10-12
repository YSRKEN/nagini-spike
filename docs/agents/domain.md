# Domain Docs

engineering 系のスキルがコードベースを調べるときに、このリポジトリのドメイン文書をどう読むかの決まり。

## 調べる前に読むもの

- リポジトリのルートの **`CONTEXT.md`**、または
- ルートに **`CONTEXT-MAP.md`** があればそれ。文脈ごとの `CONTEXT.md` を指しているので、話題に関わるものを読む
- **`docs/adr/`**: これから手を入れる範囲に関わる ADR を読む。multi-context のリポジトリでは、文脈ごとの決定を置く `src/<context>/docs/adr/` も見る

どれかが無くても、**黙って進む**。無いことを指摘しない。先回りして作ることも勧めない。用語や決定が実際に固まった時点で、`/domain-modeling` スキル（`/grill-with-docs` と `/improve-codebase-architecture` から呼ばれる）が必要に応じて作る。

## ファイルの構成

このリポジトリは single-context:

```
/
├── CONTEXT.md
├── docs/adr/
│   ├── 0001-event-sourced-orders.md
│   └── 0002-postgres-for-write-model.md
└── src/
```

multi-context のリポジトリ（ルートに `CONTEXT-MAP.md` がある）:

```
/
├── CONTEXT-MAP.md
├── docs/adr/                          ← システム全体の決定
└── src/
    ├── ordering/
    │   ├── CONTEXT.md
    │   └── docs/adr/                  ← 文脈ごとの決定
    └── billing/
        ├── CONTEXT.md
        └── docs/adr/
```

## 用語集の語を使う

出力でドメインの概念に名前を付けるとき（issue の題、リファクタの提案、仮説、テスト名）は、`CONTEXT.md` の定義どおりの語を使う。用語集が避けると明記している類義語へずらさない。

必要な概念が用語集にまだ無いなら、それ自体が手がかりになる。プロジェクトが使わない言葉を作っている（考え直す）か、本当に抜けている（`/domain-modeling` 向けに書き留める）かのどちらかである。

## ADR との矛盾を明示する

出力が既存の ADR と食い違うなら、黙って上書きせず、はっきり示す:

> _ADR-0007（event-sourced orders）と矛盾するが、次の理由で見直す価値がある…_
