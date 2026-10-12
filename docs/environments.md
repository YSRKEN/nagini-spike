# Nagini を動かす環境

[README に戻る](../README.md)

## 確かめた環境

2026-10-12 に、次の組み合わせで `scripts/check.py` を通した。ほかの版で動かないという意味ではない。

| 項目 | 確かめた構成 |
|---|---|
| OS | Windows 10（ネイティブ） |
| Python | 3.13 |
| Java | 17 |
| Nagini | 1.3.1 |
| Z3 | Nagini の依存として入る 4.8.7 |
| 依存の管理 | uv。版は `uv.lock` に固定 |

Linux・macOS では試していない。依存の入れ方は
[Nagini の公式の説明](https://github.com/marcoeilers/nagini#dependencies-windows)にある。

## 動かし方

uv、Python 3.13、Java 17 が使える環境で、リポジトリのルートから実行する。

```powershell
uv sync --locked --python 3.13
uv run --locked python scripts/check.py
```

`check.py` は ruff の lint と整形の確認、pyright の strict の型検査、一括実行の部品のテスト、
全題材の検証を順に流し、どれかが落ちたらそこで止める。README の結果表は書き換えない。
表を測り直すときは次を実行する。

```powershell
uv run --locked python scripts/verify_all.py --write-readme
```

題材を指定すれば、その題材だけを検証する（例: `scripts/verify_all.py features/control/if_branch.py`）。

## 一括実行の仕組み

`scripts/verify_all.py` は Nagini を `--server` モードで1つ起動したまま、題材を1件ずつ送る。
毎回起動すると Java の起動と Viper の標準ライブラリの読み込みで1件10秒前後かかるが、
起動したままなら2件目以降は2〜3秒で済む。計測の詳細は
[検証時間の調査](research/verification-time.md)にある。

1つの題材ファイルに対して、次の検証を行う。

- 名前が `wrong_` か `Wrong` で始まらない関数・クラスを、まとめて検証する。期待は検証成功
- `wrong_` か `Wrong` で始まる関数・クラスを、1つずつ検証する。期待は `Verification failed`（拒否）
- `features/unsupported/` の題材は、ファイル全体を検証する。期待は `Not supported` の報告か、変換中の異常終了

サーバは要求を1つずつ順に処理するので、クライアントが待つのをやめても検証は止まらない。
そこで1回の検証が120秒を超えたら、サーバを子孫プロセス（Z3）ごと止めて起動し直し、
結果を「時間切れ」とする。Nagini は変換中の Python の例外を捕まえずにサーバごと終わるので、
待つあいだにサーバが終わったら、すぐ「異常終了」として起動し直す。

Windows では、子孫ごと止めるのに Job オブジェクトを使う（`scripts/windows_job.py`）。
また、仮想環境の外の Python からサーバを起動すると Nagini が Z3 を見つけられないので、
仮想環境に同梱された Z3 を環境変数 `Z3_EXE` で渡している。Nagini のファイルは変えていない。

## 結果の読み方

最後に「すべて期待どおり。」と出て終了コードが0なら、全題材が期待どおりだった。
途中に出る `Verification failed` は、誤実装が拒否された印で、失敗ではない。
期待と違った検証は、行の頭が `NG` になり、終了コードが1になる。

## 型注釈の事情

`nagini_contracts` の型注釈は、`Acc` の割合（権限の分数）を `int` と宣言している。
Nagini は `1 / 2` のような分数を受け付けて検証も通るが、pyright の strict はこれを拒否する。
そこで分数を使う題材だけ、ファイルの先頭で `reportArgumentType` を外している。
`Acc` の import の行には、引数の型が不明だという指摘を外す注記を付けている。

## 開発時の Git の設定

clone したあとでコミットの規約を有効にするなら、次を設定する。

```powershell
git config core.hooksPath .githooks
git config branch.main.mergeoptions --no-ff
git config pull.ff only
```

## 依存とライセンス

2026-10-10 と 2026-10-12 に、PyPI の公開情報と公式のライセンス本文を確かめた。

| 依存 | ライセンス |
|---|---|
| Nagini | [MPL-2.0](https://github.com/marcoeilers/nagini/blob/master/LICENSE.txt) |
| pyzmq | BSD-3-Clause（同梱の libzmq は MPL-2.0） |
| Ruff・pytest・Pyright | MIT |

このリポジトリは各ツールを依存として使うだけで、バイナリや改変したソースを同梱しない。
再配布するときは、同梱する配布物のライセンスを別に確かめる。
