"""文字列の内容と長さの一般契約を実検証する。"""

from pathlib import Path

import pytest

import scripts.check as check
from scripts.verification_cases import (
    ExpectedVerification,
    Specification,
    VerificationCase,
    verify_case,
)

SOURCE = Path(__file__).resolve().parents[1] / "examples" / "string_length.py"
SPECIFICATION = Specification(
    "任意str a,bについてResult()==a+bかつlen(Result())==len(a)+len(b)",
    "空文字・ASCII・Unicodeの有限例を一般静的証明とは別に照合する",
)


def test_general_concatenation(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """契約を持つ実在stubが成功することを期待し、先に赤を確認する。"""
    monkeypatch.setattr(check, "RESULTS", tmp_path)
    verify_case(
        VerificationCase("string_length", SPECIFICATION, ExpectedVerification("verified")),
        SOURCE,
    )
