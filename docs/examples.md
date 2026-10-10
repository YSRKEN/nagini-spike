# 基礎実験と題材一覧

[READMEへ戻る](../README.md) / [実用調査の進捗](progress.md)

基礎実験の確認範囲をまとめます。各行の成功はその仕様の範囲での結果です。
実用調査のdone/未確認は別の台帳で管理し、未確認の機能へ一般化しません。

## 基礎実験で分かったこと

| 問い | 結果 | 詳しく |
|---|---|---|
| 小さなPython関数を検証できるか | 絶対値の二つのassertを検証できた | [仕様と検証](proofs.md) |
| 正しい実装を通すだけでなく、誤実装を拒否するか | 負数の分岐を壊すと、非負条件の違反で拒否した | [仕様と検証](proofs.md) |
| 仕様を先に決め、TDDで実装できるか | 未完成の実装の失敗を確認し、契約を変えずに実装して成功した | [TDDの実験](proofs.md) |
| 部品の保証を呼び出し側でも使えるか | 返り値の契約で使えた。非負の保証を外すと呼び出し側が失敗した | [契約の実験](proofs.md) |
| 検証したコードを通常のPythonで実行できるか | assertだけの例は直接実行でき、契約付きの例も検証後に生成したコピーで実行できた | [実行上の制約](language.md) |
| whileループで範囲の和を検証できるか | 途中の和を表す不変条件で成功した。誤計算と不変条件不足は異なる箇所で失敗した | [ループの実験](proofs.md) |
| リストの内容を読み取れるか | 空と非空の分岐、長さ、先頭の読み取りを検証できた。添字の誤り・権限不足・読み取り専用での書き込みは拒否した | [リストの実験](proofs.md) |
| リストの内容を書き換えられるか | 書き込み権限で先頭の値と長さを検証できた。最初の例では残りの要素の不変性を実行テストだけで確認。仕様を強めた例では静的検証でも保証できた | [書き込みの実験](proofs.md) |
| 任意長リストに末尾追加して全旧要素を保てるか | 長さ1増・全旧要素保存・新末尾一致と権限返却を証明。三独立誤例を各事後条件で拒否した | [追加の実験](proofs.md) |
| リストを渡す関数の保証を呼び出し側でも使えるか | 非空リストの長さ・先頭の値・書き込み権限を事後条件で返せた。契約を弱めると呼び出し側で失敗した | [リストの契約](proofs.md) |
| リストをループで順に読めるか | 読み取り権限と途中の条件を維持して、非負整数の和の非負性を検証できた。正確な合計値は実行テストで確認 | [走査の実験](proofs.md) |
| 辞書から安全に値を読めるか | キーの有無を分けて、存在する値または0を返す仕様を検証できた。別キーの参照と権限違反を拒否した | [辞書の実験](proofs.md) |
| クラスの初期化と更新を契約で検証できるか | 整数属性の初期値と1増える更新を保証し、呼び出し側で二回の更新を検証できた | [クラスの実験](proofs.md) |
| 整数除算の境界条件を検証できるか | 正の除数で再構成の等式と余りの範囲を検証できた。商・余りの誤りとゼロ除算の危険を拒否した | [境界条件の実験](proofs.md) |
| 有限例を通る偽階乗を一般仕様で拒否できるか | 独立Pureの再帰一般定義で正実装が成功。同じ契約で偽6次多項式のHorner形を拒否し、0〜4一致・5で676対120を実測 | [一般階乗契約](proofs.md) |

## ファイルから探す

| パス | 内容 |
|---|---|
| [examples/absolute.py](../examples/absolute.py) | 通常のPythonでも実行する、assertを使う最小例 |
| [examples/absolute_contract.py](../examples/absolute_contract.py) | 返り値の契約と、その保証を使う呼び出し側。直接実行には契約の除去が必要 |
| [examples/sum_range.py](../examples/sum_range.py) | 0からn未満までを足すwhileループ。途中の条件と最後のassertを検証 |
| [examples/list_head.py](../examples/list_head.py) | 空なら0、それ以外なら先頭を返す読み取りの例 |
| [examples/list_write.py](../examples/list_write.py) | 空なら何もせず、要素があれば先頭を指定値に置き換える例 |
| [examples/list_frame.py](../examples/list_frame.py) | 変更前の値と比較して、先頭以外の全要素が変わらないことも検証する例 |
| [examples/list_contract.py](../examples/list_contract.py) | 非空リストの先頭の値と長さを保証し、書き込み権限を呼び出し側へ返す例 |
| [examples/list_append.py](../examples/list_append.py) | 任意長の末尾追加と全旧要素保存、権限返却を呼び出し側も利用する例 |
| [examples/list_scan.py](../examples/list_scan.py) | 非負整数のリストを走査し、結果が非負になることを検証する例 |
| [examples/dict_read.py](../examples/dict_read.py) | 整数の辞書でキーがあれば値、なければ0を返す例 |
| [examples/counter_contract.py](../examples/counter_contract.py) | 整数属性を初期化し、1増やすメソッドと呼び出し側を契約で検証する例 |
| [examples/division_boundaries.py](../examples/division_boundaries.py) | 正の除数で整数の商と余りを計算し、再構成と余りの範囲を検証する例 |
| [examples/factorial_general.py](../examples/factorial_general.py) | 独立Pureの一般階乗モデルと再帰正実装。偽多項式との同契約比較はテストに保持 |
| [examples/optional_narrow.py](../examples/optional_narrow.py) | Noneと任意整数を分岐し、返り値の一般契約を証明する例 |
| [tests/](../tests/) | 具体例の実行、検証成功、狙った理由での拒否を確認する検査 |
| [scripts/check.py](../scripts/check.py) | 検査一式を実行する入口 |
| [scripts/extract_absolute.py](../scripts/extract_absolute.py) | 絶対値の契約付きソースを検証し、実行用コピーを生成する実験 |
| [docs/](./) | 手順、Pythonの確認範囲、検証の仕組みと実験結果 |
