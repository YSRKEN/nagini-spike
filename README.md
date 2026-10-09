# Nagini検証

[Nagini](https://github.com/marcoeilers/nagini)で、小さなPythonコードの正しさを検証する実験です。
Pythonのどんな機能を検証材料にできるかと、与えられた仕様を変えずに
TDD（先に検査の失敗を確認し、実装して成功させる進め方）でコードを書けるかを調べます。

[bend2-spike](https://github.com/YSRKEN/bend2-spike)を参考に、問いと結果を入口にまとめ、
手順・検証の仕組み・確認範囲を詳細文書に分けています。参考元のコードは取り込んでいません。

## 試したこと

2026-10-10に、Windowsネイティブ、Python 3.13.5、Java 17、Nagini 1.3.1、Z3 4.8.7で確認しました。
題材は整数の絶対値、範囲の和のwhileループ、整数リストの先頭の読み取り・書き換えと、リストの走査です。確認した範囲は[Pythonの機能](docs/language.md)を参照してください。

| 問い | 結果 | 詳しく |
|---|---|---|
| 小さなPython関数を検証できるか | 絶対値の二つのassertを検証できた | [仕様と検証](docs/proofs.md) |
| 正しい実装を通すだけでなく、誤実装を拒否するか | 負数の分岐を壊すと、非負条件の違反で拒否した | [仕様と検証](docs/proofs.md) |
| 仕様を先に決め、TDDで実装できるか | 未完成の実装の失敗を確認し、契約を変えずに実装して成功した | [TDDの実験](docs/proofs.md) |
| 部品の保証を呼び出し側でも使えるか | 返り値の契約で使えた。非負の保証を外すと呼び出し側が失敗した | [契約の実験](docs/proofs.md) |
| 検証したコードを通常のPythonで実行できるか | assertだけの例は直接実行でき、契約付きの例も検証後に生成したコピーで実行できた | [実行上の制約](docs/language.md) |
| whileループで範囲の和を検証できるか | 途中の和を表す不変条件で成功した。誤計算と不変条件不足は異なる箇所で失敗した | [ループの実験](docs/proofs.md) |
| リストの内容を読み取れるか | 空と非空の分岐、長さ、先頭の読み取りを検証できた。添字の誤り・権限不足・読み取り専用での書き込みは拒否した | [リストの実験](docs/proofs.md) |
| リストの内容を書き換えられるか | 書き込み権限で先頭の値と長さを検証できた。最初の例では残りの要素の不変性を実行テストだけで確認。仕様を強めた例では静的検証でも保証できた | [書き込みの実験](docs/proofs.md) |
| リストを渡す関数の保証を呼び出し側でも使えるか | 非空リストの長さ・先頭の値・書き込み権限を事後条件で返せた。契約を弱めると呼び出し側で失敗した | [リストの契約](docs/proofs.md) |
| リストをループで順に読めるか | 読み取り権限と途中の条件を維持して、非負整数の和の非負性を検証できた。正確な合計値は実行テストで確認 | [走査の実験](docs/proofs.md) |

## 動かし方

uv、Python 3.13、Java 17が使える環境で、リポジトリのルートから実行します。
依存の版は`uv.lock`に固定しています。

```powershell
uv sync --locked --python 3.13
uv run --locked python scripts/check.py
```

この手順はWindowsで実行して確認しました。Linux・macOSでは未確認です。
lint・整形・型検査・81件のテストと、正しい実装の検証・誤実装の拒否が通っています。
誤実装の検証では意図的に`Verification failed`が出ます。
検査全体の成功は最後のメッセージと終了コードで確認します。
環境の条件、結果の読み方、開発時の設定は[環境](docs/environments.md)を参照してください。

## 構成

| パス | 内容 |
|---|---|
| [examples/absolute.py](examples/absolute.py) | 通常のPythonでも実行する、assertを使う最小例 |
| [examples/absolute_contract.py](examples/absolute_contract.py) | 返り値の契約と、その保証を使う呼び出し側。直接実行には契約の除去が必要 |
| [examples/sum_range.py](examples/sum_range.py) | 0からn未満までを足すwhileループ。途中の条件と最後のassertを検証 |
| [examples/list_head.py](examples/list_head.py) | 空なら0、それ以外なら先頭を返す読み取りの例 |
| [examples/list_write.py](examples/list_write.py) | 空なら何もせず、要素があれば先頭を指定値に置き換える例 |
| [examples/list_frame.py](examples/list_frame.py) | 変更前の値と比較して、先頭以外の全要素が変わらないことも検証する例 |
| [examples/list_contract.py](examples/list_contract.py) | 非空リストの先頭の値と長さを保証し、書き込み権限を呼び出し側へ返す例 |
| [examples/list_scan.py](examples/list_scan.py) | 非負整数のリストを走査し、結果が非負になることを検証する例 |
| [tests/](tests/) | 具体例の実行、検証成功、狙った理由での拒否を確認する検査 |
| [scripts/check.py](scripts/check.py) | 検査一式を実行する入口 |
| [scripts/extract_absolute.py](scripts/extract_absolute.py) | 絶対値の契約付きソースを検証し、実行用コピーを生成する実験 |
| [docs/](docs/) | 手順、Pythonの確認範囲、検証の仕組みと実験結果 |

## もっと知るには

| 文書 | 読む人と内容 |
|---|---|
| [docs/environments.md](docs/environments.md) | 動かしたい人へ。確認した環境、実行手順、診断とログ、Git設定、依存のライセンス |
| [docs/language.md](docs/language.md) | Pythonで書きたい人へ。機能ごとの確認範囲、必要な記法、実行時の制約 |
| [docs/proofs.md](docs/proofs.md) | 検証を理解したい人へ。テストとの違い、契約、TDDの実験、信頼する処理系と保証の限界 |

検証成功は、書いた条件がNaginiのモデル上で成立したという結果です。
仕様が十分であることや、未確認のPython機能まで正しいことは保証しません。
