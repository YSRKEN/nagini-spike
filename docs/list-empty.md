# 空非空の結果契約と先頭アクセス

Nagini 1.3.1で、空を含む任意長の整数リストと任意整数defaultを対象に確認した。事前条件はリスト全権限だけ。空を除外せず、Assume/TrustedやPure/Inlineによる実装展開は使わない。

`has_head`はbool結果と非空の同値、権限返却、長さ不変、全要素列保存を一般Ensuresで返す。入場時の独立した列はOld(ToSeq(values))で参照する。`read_or_default`は結果だけで分岐し、True側で実際にvalues[0]を読む。callerの事前条件にも非空を置かず、安全な先頭読取と先頭値/defaultの結果、全内容・長さ・権限保存を証明した。

## 仕様・赤・誤例と対照

先に四Ensures、実在return False stubと成功期待pytestを固定した。赤は1 failed、17.94秒で、`Postcondition of has_head might not hold. Assertion Result() == (len(values) > 0) might not hold.`を@32.12--32.41で取得した。

正実装とcallerは終了0、Verification successful、11.61秒。空だけTrueにする誤例12.60秒と非空だけFalseにする誤例12.11秒は、同じ一般契約の同じ結果同値条件@32.12--32.41で終了1となり、各診断は一つだけである。二誤例は長さ・全内容・権限を変えない。

結果同値Ensures一つだけを除いた対照は、実装は正しいままcallerの`values[0]`前提条件を証明できない。実診断は`The precondition of values[0] might not hold.`、@58.15--58.24、found分岐@57.7--57.12。これは呼出先の契約情報不足であり、誤実装拒否とは別の結果である。最終の目的契約は弱めていない。

対象4テストは52.98秒で成功。変換失敗・タイムアウト・起動障害は観測していない。

## 通常実行と限界

固定したRequires/Ensures宣言だけを数で照合して除き、同じ実装を通常実行した。空・単一の負零正・複数・巨大整数・1024要素列と、負零正defaultを比較し、判定・返却・入力保存を別JSONへ記録した。有限例の成功は全入力の通常実行保証ではなく、Naginiの一般証明と区別する。

全書き込み権限の範囲に限定する。共有別名、分数権限、更新、負添字、例外、ループや複数機能の実用ロジックはこの題材では未確認。元list-emptyの結果契約とcaller先頭安全性の問いを満たしたが、調査全体は未完である。実台帳の完了候補ゲートは実行しない。

再現: `.venv/Scripts/python.exe -m pytest -q tests/test_list_empty.py`

元診断は[証拠一覧](progress.md)から参照できる。

## 最終全検査

通常scripts/check.pyは終了コード0。台帳整合性・進捗一致・lint・57ファイル整形・strict型0、全pytest228件1177.96秒、末尾Nagini正例10.91秒と指定Assert誤例10.43秒を確認した。最新ログはdocs/evidence/list-empty-final-check.log。pytest上限1200秒まで22.04秒と近接しているため、後続再開時はこの実測で時間枠を再評価する。個別90秒と上限は今回維持した。これは調査全体の完了ではなく、元list-empty一題の確認である。
