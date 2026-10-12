# Nagini 1.3.1 が対応する Python の機能

調査日は 2026-10-12。対象は Nagini 1.3.1（手元の `.venv` に入っている版）。
選定の結論は書かない。デモに含める機能の選定は別チケットで利用者が決める。

## 出典の種類と読み方

「根拠」列の記号は次の意味。公式の文言と、ソース・テストからの推定を分けて読むこと。

| 記号 | 意味 | 強さ |
|---|---|---|
| 公式 | README・wiki・CHANGELOG・論文に明記されている | 強い |
| ソース | `v1.3.1` タグのソースが「対応しない」と例外を出す、または対応処理を持つ | 強い |
| テスト | `tests/functional/verification/` に通る題材がある（対応の証拠。網羅性の証拠ではない） | 中 |
| 実測 | 手元の `.venv` で 1 ファイルずつ実行した結果 | 強い |
| 手元 | このリポジトリの `docs/language.md` の実測 | 強い |
| 推定 | 定義が無いこと等からの推定。実行して確かめていない | 弱い |

一次情報の所在:

- README: https://github.com/marcoeilers/nagini/blob/v1.3.1/README.rst
- wiki（仕様言語の説明）: https://github.com/marcoeilers/nagini/wiki （`Home.md`）。
  対応機能の一覧表はなく、仕様言語の説明のみ
- CHANGELOG: https://github.com/marcoeilers/nagini/blob/v1.3.1/CHANGELOG.md
- 論文: Eilers & Müller, CAV 2018（https://pm.inf.ethz.ch/publications/getpdf.php?bibname=Own&id=EilersMueller18.pdf）。
  「2 Language and Specifications」節
- ソース: https://github.com/marcoeilers/nagini/tree/v1.3.1/src/nagini_translation 。
  v1.3.1 のタグの tar と手元 `.venv/Lib/site-packages/nagini_translation` を `diff -rq` で比べ、
  差は `wp.py` が手元にだけ有ること（`__pycache__` を除く）だった。翻訳部分は同一
- 組み込み型の対応メソッドの表: `src/nagini_translation/resources/builtins.json`
- テスト題材: https://github.com/marcoeilers/nagini/tree/v1.3.1/tests/functional/verification
  （以下 `T/` と略す）

## 公式が明言している全体方針

- 入力は PEP 484 の静的な名前的型システム（mypy が通るもの）に従う。関数の引数と返り値に型注釈が要る。
  mypy の型システムのうち「段階的でない部分」は、ジェネリクスと共用体型を含め完全対応（論文 2 節）
- リフレクションと動的コード生成は非対応（論文 2 節）
- 対応外の機能に当たると、黙って通さずエラーにする（健全性の方針。論文 2 節）。
  実際には `UnsupportedException`（「Not supported: …」）。一部は内部のアサーション失敗になる（実測の高階関数）
- 検証は関数単位。呼び出し先は本体でなく契約だけを見る。純粋関数（`@Pure`）と `@Inline` は例外
  （wiki General contracts）
- Python は 3.12〜3.14、Java 11 以上（README）
- 浮動小数点は既定で「抽象値と未解釈関数」で、実質的に何も証明できない。`--float-encoding=real` か `ieee32` で変えられる（README）。
  ビット演算は `--int-bitops-size`（既定 8）の範囲内と証明できる整数だけ（README）

## 機能別の一覧

判定の凡例: 対応 = 検証できる。制限 = 条件付き。非対応 = エラーになる。

### 基本型

| 機能 | 判定 | 必要な注釈・制限 | 根拠 |
|---|---|---|---|
| `int`（`+ - * // % **`、比較、`abs/min/max`、`bit_length`） | 対応 | 追加の注釈は不要。整数は無制限。`/` は `float` を返す | ソース: builtins.json の int。テスト: `T/test_builtin_functions.py`, `T/test_operators.py`。手元: 絶対値・除算 |
| `int` のビット演算（and・or・xor・not・シフト） | 制限 | `--int-bitops-size`（既定 8 ビット）の範囲内と証明できる値のみ | 公式: README、CHANGELOG v1.3.0（シフト）。テスト: `T/test_bitwise_op.py` |
| `bool` | 対応 | `bool` は `int` の部分型（`Forall(int, …)` は `True/False` も含む） | 公式: wiki「Common pitfalls」。ソース: builtins.json |
| `float` | 制限 | 既定では演算結果について何も証明できない。`--float-encoding=real` なら実数として扱う。`ieee32` は時間切れしやすい | 公式: README。テスト: `T/test_float.py`, `T/float_real/`, `T/float_ieee32/` |
| `str` | 制限 | 使えるのはリテラル、`==`、`+`、`len`、`%`、`join`、`format`、`split`、f 文字列のみ。添字・スライス・`in`・`upper` などは非対応。文字列の内容に関する性質はほぼ証明できない | ソース: builtins.json の str（`__add__ __eq__ __len__ __mod__ join format split`）。テスト: `T/test_string.py`（リテラルの比較・連結・`len`・format）。実測: `s[0]` と `s.upper()` は非対応。手元: 文字列の `in` 非対応 |
| `bytes` / `bytearray` | 対応 | 添字、スライス、`+`、`len`、`append/extend/reverse`。契約用の `PByteSeq` もある | 公式: CHANGELOG v1.3.0。テスト: `T/test_bytes.py`, `T/test_bytearray.py`, `T/test_pbyteseq.py` |
| `None` | 対応 | `is None` / `is not None` で分岐 | テスト: `T/test_optional_types.py` |

### コレクション

| 機能 | 判定 | 必要な注釈・制限 | 根拠 |
|---|---|---|---|
| `list[T]` の読み取り（`[]`、`len`、`in`、負の添字、`+`、`*`） | 対応 | 引数・フィールドの `list` に触る関数は、契約に `Acc(list_pred(l))`（読むだけなら `1/2` など分数）が要る。リテラルで作ったローカルリストは不要 | 公式: wiki「Permissions to built-in predicates」。ソース: builtins.json の list。テスト: `T/test_lists.py`, `T/test_list_pred.py`。手元: `list_head.py`, `list_scan.py` |
| `list` の書き込み（`l[i] = v`、`append`、`extend`、`reverse`） | 対応 | 全権限 `Acc(list_pred(l))` が要る。他の要素の保存は `ToSeq` と `Forall` で表す | ソース: builtins.json。手元: `list_write.py`, `list_frame.py`, `list_append.py` |
| `list` の他のメソッド（`pop`、`insert`、`remove`、`sort`、`index`、`count`、`copy` など） | 非対応 | builtins.json に定義が無く、呼ぶと「Unsupported function or method」になる。組み込み関数 `sorted(l)` は対応 | ソース: `translators/common.py:564`、builtins.json の list。テスト: `T/test_sum_sorted.py`（`sorted`）。推定（メソッドごとの実測はしていない） |
| スライス `a[i:j]`、`a[:]`（list・tuple・bytes） | 対応 | 結果は新しいコピー | テスト: `T/test_slicing.py` |
| スライスの刻み `a[::2]` | 非対応 | `slice step` | ソース: `translators/expression.py:772` |
| スライスへの代入 `a[1:3] = …` | 非対応 | `assignment to slice` | ソース: `translators/statement.py:1456` |
| `dict[K, V]` の読み取り（`[]`、`in`、`get`、`len`） | 対応 | `Acc(dict_pred(d))` が要る | 公式: wiki。テスト: `T/test_dicts.py`, `T/test_dict_pred.py`。手元: `dict_read.py` |
| `dict` の書き込み（`d[k] = v`） | 対応 | 全権限 | ソース: builtins.json（`__setitem__`）。テスト: `T/test_dicts.py` |
| `dict` の `keys()` / `values()` / 反復 | 対応 | | ソース: builtins.json。テスト: `T/test_iterator_dict.py` |
| `dict` の `items()`、`pop`、`update`、`setdefault`、`del d[k]` | 非対応 | `del` はオブジェクトのフィールドにしか使えない。他は定義が無い | ソース: `translators/statement.py:390`、builtins.json。推定（実測なし） |
| `set[T]`（`{…}`、`set(l)`、`in`、`len`、`add`、`remove`、`clear`、反復） | 対応 | `Acc(set_pred(s))` が要る | ソース: builtins.json の set。テスト: `T/test_set.py`, `T/test_set_pred.py`, `T/test_iterator_set.py` |
| 集合演算（和・積・差、`discard`） | 非対応 | builtins.json の set に演算子が無い。契約用の `PSet` には和と差がある | ソース: builtins.json。wiki「Datatypes」。推定（実測なし） |
| `tuple`（固定長 `Tuple[int, str]`、可変長 `Tuple[int, ...]`、添字、`len`、アンパック、スライス） | 対応 | 10 要素以上のタプルは非対応。定数でない添字は型がそろっている場合だけ | ソース: `translators/expression.py:735`, `lib/resolver.py:596`。テスト: `T/test_tuples.py`, `T/test_slicing.py`。手元: 除算の `(商, 余り)` |
| `range`（`range(n)`、`range(a, b)`、`range(a, b, step)`）と `enumerate` | 対応 | step と `enumerate(xs, start)` は v1.3.1 の新機能 | 公式: CHANGELOG v1.3.1。テスト: `T/test_range.py`, `T/test_range_step.py`, `T/test_enumerate.py` |
| `sum`、`sorted`、`min`、`max`、`abs`、`len`、`print`、`hash`、`isinstance`、`type`、`cast` | 対応 | 引数は対応する型に限る | ソース: builtins.json の global と `translators/call.py:640` 付近の組み込み関数の分岐。テスト: `T/test_sum_sorted.py`, `T/test_builtin_functions.py`, `T/test_print.py` |
| `zip`、`map`、`filter`、`any`、`all`、`reversed`、`open` などの他の組み込み関数 | 非対応 | `unsupported built-in function` | ソース: `translators/call.py:661`（分岐に無い）。推定（実測なし） |

### 内包表記

| 機能 | 判定 | 必要な注釈・制限 | 根拠 |
|---|---|---|---|
| リスト内包表記（`[f(x) for x in xs if c]`） | 制限 | 生成器（for 節）は 1 つだけ。結果はローカル変数へ直接代入し、型を注釈する（`res = […]  # type: List[int]`）。入力リストに `list_pred` が要る | ソース: `translators/expression.py:168`（複数生成器は非対応）、`lib/resolver.py:402`（直接代入の制約）。テスト: `T/test_list_comprehension.py`, `T/test_list_comprehension_filter.py` |
| 集合・辞書の内包表記 | 制限（同上） | CHANGELOG v1.3.1 は複数の生成器にも対応と書くが、v1.3.1 のソースは複数なら例外を出す。公式の記述とソースが食い違う（後述） | 公式: CHANGELOG v1.3.1。ソース: `translators/expression.py:334`, `:353`。テスト: `T/test_set_comprehension.py`, `T/test_dict_comprehension.py` |
| ジェネレータ式・`yield`・`async/await` | 非対応 | 対応する変換処理が無く `unsupported Python construct` になる | ソース: `translators/common.py:82`（`GeneratorExp`・`Yield`の処理が無い）。推定（実測なし） |

### 制御構造

| 機能 | 判定 | 必要な注釈・制限 | 根拠 |
|---|---|---|---|
| `if` / `elif` / `else`、条件式、`and/or/not`、連鎖比較（`a < b < c`） | 対応 | | 公式: CHANGELOG v1.3.1（連鎖比較）。テスト: `T/test_boolop.py`, `T/test_chained_comparison.py` |
| `while`、`break`、`continue` | 対応 | ループ内で変数や権限を使うなら `Invariant(...)` が要る。停止性は義務の契約（`MustTerminate`）で別に扱う | 公式: wiki「Loop invariants」「Obligation contracts」。テスト: `T/test_while.py`, `T/test_loop_break.py`, `T/test_loop_continue.py`。手元: `sum_range.py` |
| `for x in <list/set/dict/range/bytes/bytearray>` | 対応 | ループ中に触る権限は不変条件に書く。走査中のコレクションを変更しない権限が要る。`Previous(x)` で過去の要素を参照できる | 公式: wiki「Contract expressions」。ソース: `translators/statement.py:495`。テスト: `T/test_iterator_list.py`, `T/test_iterator_set.py`, `T/test_iterator_dict.py`, `T/test_range.py` |
| `for` で文字列・タプルを走査 | 非対応 | 上記の対応する型に `str` と `tuple` が無い（`unsupported iterable type`） | ソース: `translators/statement.py:501`, `:731`。推定（実測なし） |
| `match` / `case` | 制限 | 値・OR・ワイルドカード・キャプチャ・クラス（キーワード引数）は対応。位置引数のクラスパターン、シーケンスパターン、マッピングパターンは非対応 | 公式: CHANGELOG v1.3.0（キーワード付きのクラスパターンは非対応と明記）。ソース: `translators/statement.py:1181`, `:1221`, `:1224`。テスト: `T/test_match.py`, `T/test_match_pure.py` |
| 代入・拡張代入（`+=`）・多重代入・アンパック | 対応 | | テスト: `T/test_assign.py`。手元: `sum_range.py` |
| `assert` | 対応 | 通常の `assert` は真偽式のみ。権限を含む式は `Assert(...)` | 公式: wiki「Checking assertions」 |
| グローバル変数 | 制限 | 定数なら自由。複数箇所で代入するなら `Acc(g)` の権限が要る | 公式: wiki「Permissions to mutable global variables」。テスト: `T/test_global_mutable_1.py` ほか |
| ネストした関数（関数内の `def`） | 非対応 | `nested.function.declaration` | ソース: `analyzer.py:718` |
| クラス内のクラス | 非対応 | `nested.class.declaration` | ソース: `analyzer.py:543` |
| `nonlocal` | 非対応 | | ソース: `analyzer.py:1467` |

### 関数・高階関数・ラムダ

| 機能 | 判定 | 必要な注釈・制限 | 根拠 |
|---|---|---|---|
| 関数・メソッドの呼び出し、既定値、名前付き引数、`*args`、`**kwargs` | 対応 | 呼び出し先の契約（`Requires`/`Ensures`）だけで推論する。契約が無いと返り値の性質が証明できない | 公式: wiki「General contracts」。テスト: `T/test_named_args.py`, `T/test_varargs.py`, `T/test_funcs_and_methods.py`, `T/test_starred.py` |
| 純粋関数 `@Pure`、再帰、`@Opaque`、`Decreases` | 対応 | 本体は 1 つの式、または代入・return・条件分岐だけ。ループ不可 | 公式: wiki「Pure functions」。手元: 階乗の再帰モデル |
| `@Inline`（呼び出し時に展開） | 対応 | コンストラクタには使えない | 公式: wiki。ソース: `analyzer.py:773` |
| `lambda` | 契約内のみ | `Forall`・`Exists`・`Let`・`Ensures(type, lambda r: …)` の中では使える。実行されるコードで作って渡す使い方は、実測で失敗した | 公式: wiki「Other assertion functions」。テスト: `T/test_post_lambda.py`（契約内のみ。契約の外で`lambda`を使う題材は`T/`に無い）。実測: 下の「実測」節 |
| 高階関数（`Callable[[int], int]` の引数を呼ぶ） | 非対応 | `Callable` の型名は builtins.json にあるが、呼び出しの変換が失敗する | 実測: 下の「実測」節（`AssertionError`）。`T/` に該当の題材が無い |
| デコレータ | 制限 | Nagini 自身の `@Pure` `@Predicate` `@Inline` `@Opaque` `@ContractOnly`、`@property`、`@staticmethod`、`@classmethod`、`@dataclass` などだけ。任意のデコレータは扱えない | 公式: 論文 2 節（頻出のデコレータとメタクラスを直接サポート）。ソース: `analyzer.py:776`, `:1900` |

### クラス・継承・ジェネリクス

| 機能 | 判定 | 必要な注釈・制限 | 根拠 |
|---|---|---|---|
| クラスとフィールド | 対応 | `__init__` の事後条件に `Ensures(Acc(self.f))` を書く。フィールドの権限が検証の単位（`# type: ignore` が要る） | 公式: 論文 2 節。テスト: `T/test_fields.py`。手元: `counter_contract.py` |
| 単一継承 | 対応 | サブクラスのメソッドは振る舞い的部分型（親の契約を満たすこと）を検査される。述語は継承の族として合成される | 公式: wiki「Predicates」。テスト: `T/test_behavioural_subtyping.py`, `T/test_super.py`, `T/test_predicate_families.py` |
| 多重継承 | 非対応 | `multiple inheritance` | ソース: `analyzer.py:580` |
| 組み込み型の継承（`class A(list)` など） | 非対応（`int`・`Exception`・`IntEnum` は例外） | `Subclassing builtin type is currently not supported` | 公式: CHANGELOG v1.3.0（`int` のみ対応）。ソース: `analyzer.py:578` |
| `@property` と setter | 対応 | getter/setter に契約が要る | テスト: `T/test_property.py`, `T/test_property_inherited.py` |
| `@staticmethod` / `@classmethod`、クラス変数 | 対応 | | テスト: `T/test_classmethod.py`, `T/test_static_calls.py`, `T/test_static_class_members.py` |
| 演算子の多重定義と比較メソッド | 対応 | | 論文 2 節の評価対象の機能。テスト: `T/test_operator_overloading.py`, `T/test_magic_methods.py` |
| 抽象クラス（`ABC`） | 対応 | | テスト: `T/test_abc.py` |
| `dataclass`、`IntEnum` | 対応 | `frozen`・既定値・継承の上書きの題材がある。`Enum` 一般ではなく `IntEnum` | 公式: CHANGELOG v1.3.0（`IntEnum`）。テスト: `T/test_dataclass*.py`, `T/test_enum_int.py` |
| メタクラス | 非対応（既知のもの以外） | `Unsupported metaclass` | ソース: `analyzer.py:598` |
| 動的なフィールド追加・削除 | 対応 | `MayCreate`/`MaySet` の権限で扱う | 公式: wiki「Permissions for field creation」。テスト: `T/test_dynamic_field_creation.py`, `T/test_field_deletion.py` |
| ジェネリックなクラス・メソッド（`Generic[T]`、`TypeVar`、上限 `bound=`） | 対応 | | 公式: 論文 2 節。テスト: `T/test_generic_classes.py`, `T/test_generic_methods.py` |
| `Optional[T]`、`Union[A, B]`、型エイリアス、`isinstance` による絞り込み | 対応 | `Optional` は `is None` で分岐。フィールドを読むには非 `None` と権限が要る | 公式: 論文 2 節。テスト: `T/test_optional_types.py`, `T/test_union_types.py`, `T/test_type_aliases.py`, `T/test_union_contracts.py`。手元: `optional-return.md` |
| `typing.Protocol`（構造的部分型） | 非対応（推定） | 論文は回避策として共用体型への書き換えを挙げる | 公式: 論文 2 節（回避策の記述）。推定（実測なし） |

### 例外

| 機能 | 判定 | 必要な注釈・制限 | 根拠 |
|---|---|---|---|
| `raise`、`try` / `except` / `finally`、独自の例外クラス | 対応 | 投げる例外は `Exsures(ExcType, 条件)` で宣言する。宣言の無い例外が漏れる経路はエラー。`RaisedException()` を事後条件・不変条件で参照できる | 公式: 論文 2 節（`Exsures`、未宣言の例外を検出）。ソース: `translators/statement.py:916`（try の処理に finally を含む）。テスト: `T/test_exception.py`, `T/test_exception_loop.py`, `T/test_raised_exception.py` |
| `with`（`__enter__` / `__exit__`） | 対応 | 両メソッドに契約が要る | テスト: `T/test_with.py` |
| 組み込みの失敗（ゼロ除算、範囲外の添字など） | 対応 | 事前条件として `Requires(divisor != 0)` などを書く。Nagini は検証エラーとして報告する | 論文: 実行時エラーを起こさないことを検証。手元: `division_boundaries.py`, `list_head.py` |

### 並行・入出力・外部

| 機能 | 判定 | 必要な注釈・制限 | 根拠 |
|---|---|---|---|
| スレッド・ロック | 対応 | 専用の契約が要る | 公式: wiki「Finite blocking contracts」。テスト: `T/test_thread_*.py`, `T/test_lock.py` |
| 入出力（ファイル・ネットワーク）の振る舞い | 制限 | `nagini_contracts.io_builtins` の専用の IO 操作と IO 契約で表す。通常の `open` などは使えない | 公式: wiki「Input/Output contracts」。手元: 未確認 |
| 外部ライブラリ・標準ライブラリの呼び出し（`import math` など） | 非対応に近い | Nagini は import 先のソースも解析対象にする。標準ライブラリを import しただけで変換が失敗する例を実測した。外部関数を使うには、契約だけを書いたラッパー（`@ContractOnly` など）を自前で用意する形になると推定 | ソース: `analyzer.py:160-200`（import した各モジュールを解析）、`lib/constants.py` の `IGNORED_IMPORTS`（`typing`, `abc`, `dataclasses`, `enum`, `sys`, `types`, `builtins`, `nagini_contracts` 系のみ読み飛ばす）。実測: `import math`。`@ContractOnly` は `nagini_contracts/contracts.py:563` にあるが、使い方の説明は wiki に無い |
| 相対 import | 対応 | | 公式: CHANGELOG v1.3.0 |
| 秘密情報の流れ（`Low`、`Declassify`） | 対応（別オプション） | `--sif` で有効化。通常の検証とは別 | 公式: README、wiki「Secure Information Flow」 |

### 仕様言語（注釈の一覧）

| 注釈 | 用途 | 根拠 |
|---|---|---|
| `Requires` / `Ensures` / `Exsures` / `Invariant` | 事前条件・事後条件・例外時の事後条件・ループ不変条件 | 公式: wiki「Contract declarations」 |
| `Acc(x.f, 分数)` | フィールドの権限。分数の省略は全権限、`1/2` などは読み取り専用 | 公式: wiki「Permission assertions」 |
| `list_pred(l)` / `dict_pred(d)` / `set_pred(s)` | コレクション内容の権限。fold/unfold は不要 | 公式: wiki「Permissions to built-in predicates」 |
| `Result()` / `ResultT(T)` / `Old(e)` / `Previous(x)` / `ToSeq(c)` / `Let` / `Unfolding` | 契約式 | 公式: wiki「Contract expressions」 |
| `Forall` / `Exists` / `Implies` / `Forall2..6` | 量化。型への量化は部分型も含み、`Forall(int, …)` は `bool` も含む。トリガーを書ける | 公式: wiki「Other assertion functions」「Common pitfalls」 |
| `@Pure` / `@Opaque` / `@Predicate` / `@Inline` / `Fold` / `Unfold` / `Reveal` | 純粋関数・述語 | 公式: wiki「Pure functions and predicates」 |
| `PSeq` / `PSet` / `PMultiset` / `PByteSeq` | 契約用の純粋なデータ型 | 公式: wiki「Datatypes」 |
| `Assert` / `Assume` / `Refute` | 検証用のアサーション | 公式: wiki「Checking assertions」。`Refute` は `contracts.py:77` |
| `MustTerminate` ほか義務の契約、`Decreases` | 停止性（副作用のある関数は義務の契約、純粋関数は `Decreases`） | 公式: wiki「Pure functions」「Obligation contracts」 |

## 実測（手元の `.venv`、公式の記述が曖昧だった 4 点を 1 回ずつ）

全体の検査 `scripts/check.py` は回していない。リポジトリの `.venv`（Nagini 1.3.1）で、
`Z3_EXE` に `.venv/bin/z3.exe` を指定し、`python -m nagini_translation.main <ファイル>` を 1 ファイルずつ流した（各 10 秒前後）。
試したファイルはセッションの作業用フォルダに置き、リポジトリには含めない。内容は表の「試した内容」のとおり。

| 試した内容 | 結果 |
|---|---|
| `import math` して `math.sqrt(x)` を返す関数 | `Translation failed` / `Type error: dead.code (math@12.0)`。標準ライブラリの import で変換が失敗した。原因（Nagini の仕様か、このマシンの型定義の構成か）は調べていない |
| `def f(s: str) -> str: return s[0]` | `Not supported: Unsupported function or method __getitem__ in type str` |
| `def f(s: str) -> str: return s.upper()` | `Not supported: Unsupported builtin function.` |
| `apply(g: Callable[[int], int], x: int)` が `g(x)` を返し、別関数が `apply(lambda y: y + 1, 3)` を呼ぶ | 変換中に `AssertionError`（`translators/call.py:826` の `assert isinstance(called_func, PythonMethod)`）。`g(x)` の呼び出しが原因と読めるが、`lambda` の渡し方が原因かは切り分けていない |

## 公式の記述とソースの食い違い・不明点

- CHANGELOG v1.3.1 は集合・辞書の内包表記が複数の生成器にも対応と書くが、v1.3.1 のソースはリスト・集合・辞書とも
  生成器が複数なら例外を出す（`translators/expression.py:168`, `:334`, `:353`）。手元の `.venv` も同じ。実測はしていない
- CHANGELOG v1.3.0 は `match` の「ほとんどのパターン（シーケンス・マッピング含む）」に対応と読めるが、
  `translators/statement.py:1221`, `:1224` は「not yet supported」を出す。純粋関数側（`T/test_match_pure.py`）の経路が別かは調べていない
- wiki は「対応する Python の機能一覧」を持たない。対応範囲は、ソースの例外とテスト題材から読むしかない
- 外部ライブラリの扱い（契約だけのスタブの書き方）は wiki に説明が無い
- 論文（2018 年）は Python 3.5 時代の記述で、`match`・`dataclass`・内包表記の詳細などは古い。1.3.1 の判定にはソースを優先した
