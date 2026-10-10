"""絶対値の例だけを対象に、検証後の実行用コピーを生成する。"""

import ast

from scripts.check import RESULTS, ROOT, run
from scripts.verification_cases import ExpectedVerification, Specification, VerificationCase

IMPORT = "from nagini_contracts.contracts import Ensures, ResultT"
CONTRACTS = (
    "Ensures(ResultT(int) >= 0)",
    "Ensures(ResultT(int) == x or ResultT(int) == -x)",
)


def extract(source: str) -> str:
    """既知の三行だけを除去し、残りのソースを保つ。

    Parameters
    ----------
    source : str
        契約付き絶対値のソース。

    Returns
    -------
    str
        二つの契約宣言と専用importを除いたソース。

    Raises
    ------
    ValueError
        仕様、ファイルの構成、検証用記法の使い方が想定と異なる場合。
    """
    tree = ast.parse(source)
    if len(tree.body) != 4 or not isinstance(tree.body[1], ast.ImportFrom):
        raise ValueError("絶対値の例の構成が変わっています。")
    functions = tree.body[2:]
    if not all(isinstance(node, ast.FunctionDef) for node in functions):
        raise ValueError("想定した関数ではありません。")
    absolute = functions[0]
    caller = functions[1]
    if not isinstance(absolute, ast.FunctionDef) or not isinstance(caller, ast.FunctionDef):
        raise ValueError("想定した関数ではありません。")
    if absolute.name != "absolute" or caller.name != "caller":
        raise ValueError("想定した関数名ではありません。")
    nodes = [tree.body[1], *absolute.body[1:3]]
    expected = [IMPORT, *CONTRACTS]
    if len(nodes) != len(expected):
        raise ValueError("契約の宣言が足りません。")
    lines = source.splitlines(keepends=True)
    for node, text in zip(nodes, expected, strict=True):
        if node.end_lineno != node.lineno or lines[node.lineno - 1].strip() != text:
            raise ValueError("除去する宣言が変わっています。")
        if ast.dump(node) != ast.dump(ast.parse(text).body[0]):
            raise ValueError("除去する宣言の構造が変わっています。")
        lines[node.lineno - 1] = "\n"
    extracted = "".join(lines)
    if any(
        isinstance(node, ast.Name) and node.id in {"Ensures", "ResultT"}
        for node in ast.walk(ast.parse(extracted))
    ):
        raise ValueError("実行するコードに検証用の名前が残っています。")
    return extracted


def main() -> int:
    """元のファイルの検証が成功した後にだけ実行用コピーを保存する。"""
    RESULTS.mkdir(exist_ok=True)
    source_path = ROOT / "examples" / "absolute_contract.py"
    output_path = RESULTS / "absolute_runtime.py"
    # 前回の成功したコピーを今回の結果として誤って使わせない。
    output_path.write_text(
        'raise RuntimeError("実行用コピーの生成が完了していません。")\n', encoding="utf-8"
    )
    source = source_path.read_bytes()
    extracted = extract(source.decode("utf-8"))
    case = VerificationCase(
        "absolute_contract_extract",
        Specification(
            "absoluteが非負かつxまたは-xを返し、callerへ契約が届く",
            "既知のAST宣言だけを除くコピーでabsとcallerを照合する",
        ),
        ExpectedVerification("verified"),
    )
    returncode, output = run(["-m", "nagini_translation.main", str(source_path)], case.name)
    if not case.expected.matches(returncode, output):
        print("元の契約付きコードの検証が成功していません。")
        return 1
    if source_path.read_bytes() != source:
        print("検証中に元のファイルが変わりました。")
        return 1
    output_path.write_text(extracted, encoding="utf-8", newline="\n")
    print("検証したソースからresults/absolute_runtime.pyを生成しました。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
