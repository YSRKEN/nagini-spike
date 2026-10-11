"""空非空の一般結果契約と呼び出し側を検査する。"""

from pathlib import Path

import pytest

import scripts.check as check
from scripts.verification_cases import (
    ExpectedVerification,
    Specification,
    VerificationCase,
    verify_case,
)

SOURCE = Path(__file__).resolve().parents[1] / "examples" / "list_empty.py"
SPECIFICATION = Specification(
    "任意整数リストの空非空bool同値、全権限・長さ・内容保存、caller実先頭読取",
    "空・単一・複数の負零正整数と任意defaultの有限通常実行を別照合",
)


def test_correct_list_empty(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """一般結果契約と先頭を実読取するcallerの証明成功を要求する。"""
    monkeypatch.setattr(check, "RESULTS", tmp_path)
    verify_case(
        VerificationCase("list_empty", SPECIFICATION, ExpectedVerification("verified")), SOURCE
    )
