"""文字列inの変換失敗と有限通常実行を別々に再現する。"""

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

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "examples" / "string_search.py"
BODY_SOURCE = ROOT / "examples" / "string_membership_body.py"
SPECIFICATION = Specification(
    "任意str text,needleでResult()==(needle in text)、組込み演算相対の仕様",
    "有限通常実行を位置とスライスに基づく存在仕様と別照合する",
)
CONDITION = "    Ensures(Result() == (needle in text))\n"
BODY = "    return needle in text\n"
PAIRS = (
    ("", ""),
    ("", "a"),
    ("abc", ""),
    ("abc", "a"),
    ("abc", "bc"),
    ("abc", "abc"),
    ("abc", "abcd"),
    ("abc", "x"),
    ("ababa", "aba"),
    ("日本語", "本"),
    ("😀é", "😀"),
    ("e\u0301", "é"),
    ("a\x00b", "\x00"),
)


def runtime_function(source: str) -> Callable[[str, str], bool]:
    """照合した一Ensuresのみ除いて実際の同じ本体を通常実行する。"""
    assert source.count(CONDITION) == 1
    source = source.replace(CONDITION, "\n")
    assert "Ensures(" not in source
    namespace: dict[str, object] = {}
    exec(compile(source, "runtime_string_search.py", "exec"), namespace)
    return cast(Callable[[str, str], bool], namespace["contains_substring"])


def finite_specification(text: str, needle: str) -> bool:
    """文字位置とスライス一致を列挙し有限実行用の独立期待値を作る。"""
    return any(text[start : start + len(needle)] == needle for start in range(len(text) + 1))


@pytest.mark.parametrize(
    "name,replacement",
    (("good", BODY), ("false", "    return False\n"), ("true", "    return True\n")),
)
def test_membership_contract_translation(
    name: str, replacement: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """正例も誤例も契約の変換段階で止まり事後条件拒否ではないと確認する。"""
    source = SOURCE.read_text(encoding="utf-8-sig")
    mutation = None if name == "good" else Mutation(BODY, replacement)
    changed = source if mutation is None else mutation.apply(source)
    assert changed.split("    return ")[0] == source.split("    return ")[0]
    path = tmp_path / ("string_search_" + name + ".py")
    path.write_text(changed, encoding="utf-8")
    monkeypatch.setattr(check, "RESULTS", tmp_path)
    verify_case(
        VerificationCase(
            "string_search_" + name,
            SPECIFICATION,
            ExpectedVerification(
                "translation_failure",
                (
                    "Not supported: Unsupported function or method __contains__ in type str",
                    path.name + "@21.25",
                ),
            ),
            mutation,
        ),
        path,
    )
    calculate = runtime_function(changed)
    matches = [
        calculate(text, needle) == finite_specification(text, needle) for text, needle in PAIRS
    ]
    assert all(matches) if name == "good" else not all(matches)


def test_membership_body_translation(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """契約を除いた本体だけでも同演算の未対応で変換が止まると確認する。"""
    monkeypatch.setattr(check, "RESULTS", tmp_path)
    verify_case(
        VerificationCase(
            "string_membership_body",
            SPECIFICATION,
            ExpectedVerification(
                "translation_failure",
                (
                    "Not supported: Unsupported function or method __contains__ in type str",
                    "string_membership_body.py@19.11",
                ),
            ),
        ),
        BODY_SOURCE,
    )
