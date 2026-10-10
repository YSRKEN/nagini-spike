"""辞書更新の成功期待を実在する未実装stubへ先に固定する。"""

from pathlib import Path

import pytest

import scripts.check as check
from scripts.verification_cases import (
    ExpectedVerification,
    Specification,
    VerificationCase,
    verify_case,
)

SOURCE = Path(__file__).resolve().parents[1] / "examples" / "dict_update.py"
SPECIFICATION = Specification(
    "任意整数辞書の対象値・全旧他キー値・余分キーなし・既存新規の長さ分岐と全権限返却",
    "既存キー・新規キー・空・負整数・巨大整数・長い辞書を有限通常実行で別照合",
)


def test_general_update(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """一般保存契約を満たす正実装の証明成功を期待する。"""
    monkeypatch.setattr(check, "RESULTS", tmp_path)
    verify_case(
        VerificationCase("dict_update", SPECIFICATION, ExpectedVerification("verified")), SOURCE
    )
