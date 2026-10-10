# Optional整数の戻り契約

任意整数valueから負ならNone、非負ならvalueを返す。二つのEnsuresで
None iff value<0と非None時の入力一致を固定する。呼び出し側はその契約で
None分岐後に安全に加算し、負なら0・非負ならvalue+1を一般証明する。
Requires・Assume・Trustedは使わず、入力域を有限化しない。

成功期待テストをreturn Noneのstubで先に実行して赤を確認する。
同契約で負側整数返却・非負側None・非負側value+1の独立誤例を実行し、
事後条件診断全文・位置・終了コードを確認する。通常実行の有限例は別証拠。
これは検索結果と不在条件の対応を検証していないため、元optional-returnは未確認を維持する。

正例と呼出側は一般証明に成功した。負側で整数を返す誤例と非負側でNoneを返す誤例は
None iff負の事後条件@21.12--21.45、値に1を加える誤例は値一致@22.12--22.49で
それぞれ終了1、対応する事後条件一つだけが失敗した。変換・型エラーではない。
診断位置は保存した実診断を照合し、テストが全文条件・位置・単独失敗を再検査する。
赤stubは成功期待pytestが1 failed in 11.43sとなった。通常実行7具体例は別JSON。

元の検索問いを置換せず、台帳にoptional-return-intを追加した。
一般Optional入力を整数へ変換する既存optional-narrowとも別の契約である。
全体完了候補ではなく、実台帳の完了ゲートは実行していない。

呼出側の非負加算は本体のインライン展開による成功とは区別する。
導入済みcall.pyのtranslate_normal_callは単純なグローバル関数呼出を受け付け、
PureでもInlineでもない場合は_translate_method_callへ進む。
_only_translate_method_callはcreate_method_call_nodeを生成する。
今回の関数にPure/Inline指定はなく、この契約付きメソッド呼出の経路に当たる。
観測したソースの狭い抜粋はoptional-return-call-model.jsonへ保存した。

最終scripts/check.pyは終了0。台帳整合性・進捗一致・lint・51ファイル整形・strict型検査、
全pytest 214件（773.99秒）、最後のNagini正例と狙ったAssert拒否がすべて成功した。
外側全体は798.95秒。pytest制限1200秒と個別90秒、外側1500秒で完走した。
保存証拠はdocs/evidence/optional-return-final-check.log。
