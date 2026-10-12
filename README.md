# Nagini 検証

Python の基本機能を [Nagini](https://github.com/marcoeilers/nagini) で証明できるかを、短いコードで確かめるリポジトリ。
関数ごとに「満たすべき条件」（契約）を書き、Nagini がその条件をどの入力でも満たすと示せるかを見る。
21 の題材のうち 18 では、契約を満たす実装（正実装）の証明が通り、わざと間違えた実装（誤実装）は拒否された。
残りの 3 題材は、Nagini が扱えない機能の例である。

## Nagini は条件を書くだけで、すべての入力について証明する

Nagini は ETH Zürich が作った Python の静的検証器である。関数に事前条件（`Requires`、呼ぶ側が守る条件）・
事後条件（`Ensures`、返すときに成り立つ条件）・ループ不変条件（`Invariant`、ループの各回で成り立つ条件）を書く。
Nagini はそれを Viper という検証用の中間言語に変換し、論理式を自動で解く道具（SMT ソルバの Z3）に渡す。
テストのように具体例を試すのではなく、「条件が破れる入力は1つも無い」ことを示す。

人が書くのは契約だけで、証明の道筋はソルバが探す。そのかわり対象は型注釈付きの Python の一部に限られる。
また、リストや辞書を引数に取る関数には、その関数が中身を読んでよいか・書き換えてよいかを
権限として書く必要がある（`Acc(list_pred(values))` など）。

検証が通ったというのは、書いた契約が成り立つという意味で、契約が十分かまでは保証しない。
たとえば「返り値は0以上」としか書かなければ、常に0を返す実装も通る。
そこで各題材に誤実装を1つ置き、それが拒否されることで、契約が実装を十分に縛っていることを確かめている。

## 18 題材で証明が通り、誤実装はすべて拒否された

2026-10-12、Windows・Nagini 1.3.1 で `scripts/verify_all.py --write-readme` を実行した結果。
「正実装」が成功で「誤実装の拒否」が 1/1 なら期待どおり。非対応の行は、Nagini が扱えないと報告したか、
変換の途中で異常終了したことを示す。右端の列は、誤実装や非対応の題材で Nagini が報告した最初の内容である。
時間は Nagini を起動したまま測った秒数で、題材の中の検証をすべて足したもの。

<!-- results:start -->
| 分野 | 題材 | 正実装 | 誤実装の拒否 | 時間（秒） | 誤実装・非対応で報告された内容 |
| --- | --- | --- | --- | --- | --- |
| 型と制御構造 | [break_search](features/control/break_search.py) | 成功 | 1/1 | 8.2 | Postcondition of wrong_find_first might not hold. Assertion Forall(int, lambda j: Implies(0 <= j and j < ResultT(int), values[j] != target)) might not hold. |
| 型と制御構造 | [for_loop](features/control/for_loop.py) | 成功 | 1/1 | 9.2 | Postcondition of wrong_maximum might not hold. Assertion Forall(ToSeq(values), lambda value: value <= Result()) might not hold. |
| 型と制御構造 | [function_call](features/control/function_call.py) | 成功 | 1/1 | 3.7 | The precondition of method clamp might not hold. Assertion low <= high might not hold. |
| 型と制御構造 | [if_branch](features/control/if_branch.py) | 成功 | 1/1 | 3.7 | Postcondition of wrong_absolute might not hold. Assertion Result() >= 0 might not hold. |
| 型と制御構造 | [recursion](features/control/recursion.py) | 成功 | 1/1 | 4.1 | Postcondition of wrong_factorial might not hold. Assertion Result() == fac(n) might not hold. |
| 型と制御構造 | [while_loop](features/control/while_loop.py) | 成功 | 1/1 | 4.1 | Postcondition of wrong_sum_below might not hold. Assertion 2 * Result() == n * (n - 1) might not hold. |
| コレクション | [dict_assign](features/collections/dict_assign.py) | 成功 | 1/1 | 14.5 | Postcondition of wrong_put might not hold. Assertion Forall(int, lambda other: Implies(Old(other in values) and other != key, other in values and values[other] == Old(values[other]))) might not hold. |
| コレクション | [dict_membership](features/collections/dict_membership.py) | 成功 | 1/1 | 3.9 | The precondition of values[key] might not hold. |
| コレクション | [list_append](features/collections/list_append.py) | 成功 | 1/1 | 5.1 | Postcondition of wrong_push might not hold. Assertion values[len(values) - 1] == value might not hold. |
| コレクション | [list_index_assign](features/collections/list_index_assign.py) | 成功 | 1/1 | 6.5 | Postcondition of wrong_set_at might not hold. Assertion Forall(int, lambda i: Implies(0 <= i and i < len(values) and (i != index), values[i] == Old(ToSeq(values))[i])) might not hold. |
| コレクション | [list_slice](features/collections/list_slice.py) | 成功 | 1/1 | 8.9 | Postcondition of wrong_window might not hold. Assertion Forall(int, lambda i: Implies(0 <= i and i < stop - start, Result()[i] == values[start + i])) might not hold. |
| コレクション | [set_add](features/collections/set_add.py) | 成功 | 1/1 | 3.6 | Postcondition of wrong_remember might not hold. Assertion value in seen might not hold. |
| コレクション | [tuple_return](features/collections/tuple_return.py) | 成功 | 1/1 | 4.5 | Postcondition of wrong_divide might not hold. Assertion Result()[0] * divisor + Result()[1] == numerator might not hold. |
| クラス | [field_update](features/classes/field_update.py) | 成功 | 1/1 | 3.7 | Postcondition of increment might not hold. Assertion self.value == Old(self.value) + 1 might not hold. |
| クラス | [inheritance](features/classes/inheritance.py) | 成功 | 1/1 | 3.7 | Postcondition of corners might not hold. Assertion Result() >= 0 might not hold. |
| クラス | [optional_value](features/classes/optional_value.py) | 成功 | 1/1 | 3.9 | Postcondition of wrong_increment_nonnegative might not hold. Assertion value >= 0 or Result() == 0 might not hold. |
| 例外 | [raise_error](features/exceptions/raise_error.py) | 成功 | 1/1 | 4.1 | Postcondition of wrong_check_age might not hold. Assertion age < 0 might not hold. |
| 例外 | [try_except](features/exceptions/try_except.py) | 成功 | 1/1 | 4.1 | Postcondition of wrong_age_or_zero might not hold. Assertion Implies(age < 0, Result() == 0) might not hold. |
| 非対応 | [builtin_exception](features/unsupported/builtin_exception.py) | — | — | 0.8 | サーバが異常終了: AttributeError: 'NoneType' object has no attribute 'name' |
| 非対応 | [higher_order](features/unsupported/higher_order.py) | — | — | 1.0 | サーバが異常終了: AssertionError |
| 非対応 | [str_index](features/unsupported/str_index.py) | — | — | 0.6 | Not supported: Unsupported function or method __getitem__ in type str |
<!-- results:end -->

## 1つのファイルに正実装と誤実装を並べる

1つの機能を1ファイルにし、正実装と、同じ契約でわざと間違えた誤実装を並べる。誤実装は名前を `wrong_`（クラスなら `Wrong`）で始める。
次の例では、`wrong_absolute` が負の入力をそのまま返すので「返り値は0以上」が破れ、Nagini に拒否される。

```python
def absolute(x: int) -> int:
    """負なら符号を反転して返す。"""
    Ensures(Result() >= 0)
    Ensures(Result() == x or Result() == -x)
    if x < 0:
        return -x
    return x


def wrong_absolute(x: int) -> int:
    """分岐を書き忘れ、負の入力をそのまま返す。"""
    Ensures(Result() >= 0)
    Ensures(Result() == x or Result() == -x)
    return x
```

題材は分野ごとに `features/control/`（型と制御構造）・`collections/`・`classes/`・`exceptions/`・`unsupported/` に置いた。

## 文字列の添字・高階関数・組み込みの例外などは扱えない

題材で確かめたもの（`features/unsupported/`）。

- `str` の添字（`text[0]`）: `Not supported` と報告される
- 高階関数（`Callable` の引数を呼ぶ）: 変換中に `AssertionError` で異常終了する
- 組み込みの例外を `Exsures` に書く（`Exsures(ValueError, …)`）: 変換中に `AttributeError` で異常終了する。`Exception` を継承した独自の例外なら書ける

作り直しの途中で手元で試したもの。

- `yield`（ジェネレータ）: `Not supported: unsupported expression statement`
- `zip`: `Not supported: Unsupported builtin function.`

公式の文書とソースから読んだもの（[対応機能の調査](docs/research/feature-support.md)）。

- `float` は既定では演算について何も証明できない
- `str` で使えるのは連結・`==`・`len`・`format` など一部だけ
- `list.pop`・`dict.items` など多くのメソッドと、`map`・`filter`・`any`・`all` などの組み込み関数は使えない
- 標準ライブラリの import（`import math` など）は変換に失敗する例がある。原因は調べていない

## 動かすには uv・Python 3.13・Java 17 が要る

Java が要るのは、Nagini が使う検証器 Viper が Java の仮想マシンの上で動くため。リポジトリのルートから実行する。Windows で確かめた。

```powershell
uv sync --locked --python 3.13
uv run --locked python scripts/check.py
```

lint・整形・strict の型検査・一括実行の部品のテスト・全題材の検証を順に流す。
途中に出る `Verification failed` は誤実装が拒否された印で、失敗ではない。最後に「すべての検査が通った。」と出れば成功。
2026-10-12 の実行では、全題材の検証が 2 分前後で終わった。

## 詳しく読む

| 知りたいこと | 文書 |
| --- | --- |
| 環境、一括実行の仕組み、結果の読み方、開発の設定 | [実行環境](docs/environments.md) |
| Nagini の検証時間の内訳と、速くする手段 | [検証時間の調査](docs/research/verification-time.md) |
| Nagini が対応・非対応としている Python の機能 | [対応機能の調査](docs/research/feature-support.md) |

構成の参考は [bend2-spike](https://github.com/YSRKEN/bend2-spike)。参考元のコードは取り込んでいない。
