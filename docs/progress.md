# 調査の進捗

<!-- scripts/render_progress.py が investigation.json から生成。直接編集しない。 -->

全28件：調査済み10件（証明成功9件）、未確認18件。

doneは各行の問いについて記録した条件で調査・分類済みという意味です。
非対応・変換失敗・仕様不足も区別して表示し、Python全体の対応や実運用の安全性は保証しません。
未確認には未着手だけでなく証明未達も含まれます。入力域・制約・再現方法は
[台帳](investigation.json)、判定の読み方は[調査方法](investigation.md)を参照してください。
台帳以前の基礎実験は[題材一覧](examples.md)にあり、この進捗の件数には含めません。

| ID | 調べる問い | 状態 | 証拠 |
| --- | --- | --- | --- |
| `factorial-general` | 0〜4の有限例を通る偽多項式を独立した一般階乗契約で拒否し、正実装を証明できるか | done（証明成功） | [コード](../examples/factorial_general.py) / [診断](../docs/evidence/factorial-general.log) |
| `list-exact-sum` | 任意長の整数リストの合計を要素列の数学的総和と一致する契約で証明できるか | 未確認 | — |
| `list-append` | append後の長さと既存要素の保存、新しい末尾を証明できるか | done（証明成功） | [コード](../examples/list_append.py) / [診断](../docs/evidence/list_append.log) |
| `list-update` | 指定添字の更新で他の全要素が変わらないことを証明できるか | done（証明成功） | [コード](../examples/list_update.py) / [診断](../docs/evidence/list_update.log) |
| `list-empty` | 空/非空の結果契約を呼び出し側へ返し、その契約だけで先頭取得の安全性を証明できるか | done（証明成功） | [コード](../examples/list_empty.py) / [診断](../docs/evidence/list-empty-red.log) |
| `dict-update` | 既存キーと新規キーへの代入で他のキーの値を保存できるか | done（証明成功） | [コード](../examples/dict_update.py) / [診断](../docs/evidence/dict_update.log) |
| `dict-delete` | キー削除後の不在と他のキーの保存を証明できるか | 未確認 | — |
| `dict-missing` | キー不在の結果契約を呼び出し側へ返し、その契約だけで辞書アクセスの安全性を証明できるか | done（証明成功） | [コード](../examples/dict_missing.py) / [診断](../docs/evidence/dict-missing-red.log) |
| `string-length` | 文字列の連結と長さの関係を契約で扱えるか | done（証明成功） | [コード](../examples/string_length.py) / [診断](../docs/evidence/string_length.log) |
| `string-search` | 文字列の添字と部分文字列検索の実用的な条件を扱えるか | 未確認 | — |
| `optional-narrow` | Optional値をNone分岐で絞り込み安全に利用できるか | done（証明成功） | [コード](../examples/optional_narrow.py) / [診断](../docs/evidence/optional-red.log) |
| `optional-return` | 検索結果のOptional戻り値と見つからない条件を対応付けられるか | 未確認 | — |
| `for-invariant` | forで整数列を走査し不変条件から合計の正確性を証明できるか | 未確認 | — |
| `for-break` | breakする検索ループで見つかった位置と終了条件を証明できるか | 未確認 | — |
| `slicing-copy` | リストのスライスの範囲とコピー後の変更独立性を証明できるか | 未確認 | — |
| `alias-permission` | 同一リストへの二つの参照に対する更新権限と観測を扱えるか | 未確認 | — |
| `exception-raise` | 不正入力の例外送出と正常戻りの事後条件を区別できるか | 未確認 | — |
| `exception-catch` | 例外を捕捉して代替値を返す条件と状態保存を証明できるか | 未確認 | — |
| `inheritance-contract` | 継承したメソッドの事前・事後条件と動的呼び出しを証明できるか | 未確認 | — |
| `third-party-boundary` | 第三者ライブラリの未検証呼び出しに必要な契約境界を特定できるか | 未確認 | — |
| `io-boundary` | ファイルや外部IOの結果を純粋な検証対象へ渡す境界を記述できるか | 未確認 | — |
| `inventory-combination` | 辞書・クラス状態・分岐を組み合わせ在庫更新の保存則を証明できるか | 未確認 | — |
| `filter-combination` | Optionalとリスト走査を組み合わせ条件に合う要素だけを抽出できるか | 未確認 | — |
| `division-combination` | 整数除算とループを組み合わせ分配の総量保存を証明できるか | 未確認 | — |
| `state-machine-combination` | 継承・状態遷移・例外を組み合わせ不正な遷移の拒否を証明できるか | 未確認 | — |
| `factorial-loop-model` | 独立Pure再帰モデルと一致するwhile実装を、Assume/Trustedなしで証明できるか | 未確認 | — |
| `string-membership` | 任意str textとneedleのinによる部分文字列存在判定と契約を変換できるか | done（非対応確認） | [コード](../examples/string_search.py) / [診断](../docs/evidence/string-search-good.log) |
| `optional-return-int` | 任意整数からOptional[int]へ返すNone/値契約と呼出側の安全利用を証明できるか | done（証明成功） | [コード](../examples/optional_return.py) / [診断](../docs/evidence/optional-return-red.log) |
