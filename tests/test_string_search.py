"""部分文字列in演算の一般成功期待を共通形式に固定する。"""

from pathlib import Path

import pytest

import scripts.check as check
from scripts.verification_cases import (
    ExpectedVerification,
    Specification,
    VerificationCase,
    verify_case,
)

SOURCE = Path(__file__).resolve().parents[1] / "examples" / "string_search.py"
SPECIFICATION = Specification(
    "任意str text,needleでResult()==(needle in text)、前提で空文字を排除しない",
    "有限通常実行を位置とスライスに基づく存在仕様と別照合する",
)


def test_general_membership(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """組込みinに相対的な一般契約の成功を期待する。"""
    monkeypatch.setattr(check, "RESULTS", tmp_path)
    verify_case(
        VerificationCase("string_search", SPECIFICATION, ExpectedVerification("verified")),
        SOURCE,
    )
