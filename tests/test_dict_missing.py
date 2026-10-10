"""不在キーの一般契約と安全な呼び出し側を検査する。"""

from pathlib import Path

import pytest

import scripts.check as check
from scripts.verification_cases import (
    ExpectedVerification,
    Specification,
    VerificationCase,
    verify_case,
)

SOURCE = Path(__file__).resolve().parents[1] / "examples" / "dict_missing.py"
SPECIFICATION = Specification(
    "任意整数辞書とキー、None iff 不在、存在値一致、全内容長さ権限保存、caller辞書読取",
    "空辞書・不在・存在零負正の有限通常実行を一般証明と別に照合",
)


def test_correct_dict_missing(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """一般契約と呼び出し側の成功を要求する。"""
    monkeypatch.setattr(check, "RESULTS", tmp_path)
    verify_case(
        VerificationCase("dict_missing", SPECIFICATION, ExpectedVerification("verified")),
        SOURCE,
    )
