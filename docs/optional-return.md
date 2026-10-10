# Optional整数の戻り契約

任意整数valueから負ならNone、非負ならvalueを返す。二つのEnsuresで
None iff value<0と非None時の入力一致を固定する。呼び出し側はその契約で
None分岐後に安全に加算し、負なら0・非負ならvalue+1を一般証明する。
Requires・Assume・Trustedは使わず、入力域を有限化しない。

成功期待テストをreturn Noneのstubで先に実行して赤を確認する。
同契約で負側整数返却・非負側None・非負側value+1の独立誤例を実行し、
事後条件診断全文・位置・終了コードを確認する。通常実行の有限例は別証拠。
これは検索結果と不在条件の対応を検証していないため、元optional-returnは未確認を維持する。
