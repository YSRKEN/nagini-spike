"""任意有効添字更新の一般契約を共通ケースで照合する。"""

from pathlib import Path

import pytest

import scripts.check as check
from scripts.verification_cases import ExpectedVerification, Specification, VerificationCase, verify_case

SOURCE = Path(__file__).resolve().parents[1] / "examples" / "list_update.py"
SPECIFICATION = Specification(
    "任意整数リストの有効添字更新で対象値・長さ不変・全他要素保存・全権限返却",
    "単一・先頭・末尾・負整数・巨大整数・長い列の有限通常実行を別照合",
)


def test_general_update(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """入力域を有限に狭めず一般保存契約の証明成功を要求する。"""
    monkeypatch.setattr(check, "RESULTS", tmp_path)
    verify_case(
        VerificationCase("list_update", SPECIFICATION, ExpectedVerification("verified")), SOURCE
    )
