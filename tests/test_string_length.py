"""文字列の内容と長さの一般契約を実検証する。"""

from pathlib import Path
from typing import Callable, cast

import pytest

import scripts.check as check
from scripts.verification_cases import (
    ExpectedVerification,
    Mutation,
    Specification,
    VerificationCase,
    verify_case,
)

SOURCE = Path(__file__).resolve().parents[1] / "examples" / "string_length.py"
SPECIFICATION = Specification(
    "任意str a,bについてResult()==a+bかつlen(Result())==len(a)+len(b)",
    "空文字・ASCII・Unicodeの有限例を一般静的証明とは別に照合する",
)
CONDITIONS = (
    "    Ensures(Result() == a + b)\n",
    "    Ensures(len(Result()) == len(a) + len(b))\n",
)
PAIRS = (("", ""), ("", "abc"), ("abc", ""), ("a", "bc"), ("日本", "語"), ("😀", "é"))


def runtime_function(source: str) -> Callable[[str, str], str]:
    """照合済みの二つの契約だけを除き、同じ本体を通常実行する。"""
    for condition in CONDITIONS:
        assert source.count(condition) == 1
        source = source.replace(condition, "\n")
    assert "Ensures(" not in source
    namespace: dict[str, object] = {}
    exec(compile(source, "runtime_string_length.py", "exec"), namespace)
    return cast(Callable[[str, str], str], namespace["concatenate"])


def test_general_concatenation(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """任意文字列の証明成功と有限例の通常実行を分けて確認する。"""
    monkeypatch.setattr(check, "RESULTS", tmp_path)
    verify_case(
        VerificationCase("string_length", SPECIFICATION, ExpectedVerification("verified")),
        SOURCE,
    )
    calculate = runtime_function(SOURCE.read_text(encoding="utf-8-sig"))
    for a, b in PAIRS:
        result = calculate(a, b)
        assert result == a + b
        assert len(result) == len(a) + len(b)


@pytest.mark.parametrize(
    ("name", "replacement", "condition"),
    (
        ("wrong_content", "    return b + a\n", "Result() == a + b"),
        (
            "wrong_length",
            '    return a + b + "x"\n',
            "len(Result()) == len(a) + len(b)",
        ),
    ),
)
def test_independent_mutations(
    name: str,
    replacement: str,
    condition: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """同じ二契約を維持して内容と長さの誤例を対応する事後条件で拒否する。"""
    source = SOURCE.read_text(encoding="utf-8-sig")
    mutation = Mutation("    return a + b\n", replacement)
    changed = mutation.apply(source)
    assert source.split("    return ")[0] == changed.split("    return ")[0]
    path = tmp_path / ("string_" + name + ".py")
    path.write_text(changed, encoding="utf-8")
    monkeypatch.setattr(check, "RESULTS", tmp_path)
    verify_case(
        VerificationCase(
            "string_" + name,
            SPECIFICATION,
            ExpectedVerification(
                "proof_failure",
                (
                    "Postcondition of concatenate might not hold.",
                    "Assertion " + condition + " might not hold.",
                    (
                        "string_wrong_content.py@22.12--22.29"
                        if name == "wrong_content"
                        else "string_wrong_length.py@21.12--21.44"
                    ),
                ),
            ),
            mutation,
        ),
        path,
    )
    calculate = runtime_function(changed)
    result = calculate("a", "bc")
    assert result != "abc"
    assert (len(result) == 3) == (name == "wrong_content")
