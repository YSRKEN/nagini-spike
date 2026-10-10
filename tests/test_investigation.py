"""調査完了の主張を証拠の契約と照合する。"""

import json
from pathlib import Path
from typing import cast

import pytest

from scripts.check_investigation import validate


def ledger(root: Path, status: str = "verified") -> dict[str, object]:
    """再現例と診断を持つ最小の調査を作る。"""
    (root / "case.py").write_text("pass\n", encoding="utf-8")
    (root / "diagnostic.log").write_text("Verification successful\n", encoding="utf-8")
    return {
        "schema_version": 1,
        "items": [
            {
                "id": "case",
                "question": "限定した入力で契約を証明できるか",
                "status": status,
                "scope": "Nagini 1.3.1; 非負整数",
                "reproduction": "python -m pytest tests/test_case.py",
                "expected": "契約の検証成功",
                "actual": "契約の検証成功",
                "diagnosis": "終了コード0と検証成功診断を観測",
                "evidence": ["case.py", "diagnostic.log"],
            }
        ],
    }


def check(root: Path, data: dict[str, object], complete: bool = True) -> list[str]:
    """JSONを経由して外部入力として検査する。"""
    path = root / "ledger.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return validate(path, root, require_complete=complete)


def test_valid_resolved_ledger(tmp_path: Path) -> None:
    """限定条件と再現証拠が揃う解決済み台帳を受理する。"""
    assert check(tmp_path, ledger(tmp_path)) == []


def test_pending_is_consistent_but_not_complete(tmp_path: Path) -> None:
    """候補の整合性検査と調査完了を区別する。"""
    data = ledger(tmp_path, "unconfirmed")
    assert check(tmp_path, data, False) == []
    assert check(tmp_path, data)


@pytest.mark.parametrize(
    "field,value",
    [
        ("status", "invented"),
        ("scope", ""),
        ("reproduction", ""),
        ("expected", ""),
        ("actual", ""),
        ("diagnosis", ""),
        ("evidence", []),
        ("evidence", ["missing.log"]),
        ("evidence", ["../outside.log"]),
        ("evidence", ["/absolute.log"]),
        ("evidence", ["C:\\private.log"]),
        ("evidence", ["case.py", 1]),
    ],
)
def test_rejects_unsupported_claims(tmp_path: Path, field: str, value: object) -> None:
    """状態の捏造・根拠欠落・外部パスを拒否する。"""
    data = ledger(tmp_path)
    items = cast(list[dict[str, object]], data["items"])
    items[0][field] = value
    assert check(tmp_path, data)


@pytest.mark.parametrize(
    "data",
    [
        {"schema_version": 1, "items": []},
        {"schema_version": True, "items": []},
        {"schema_version": 1, "items": "bad"},
    ],
)
def test_rejects_empty_or_malformed_ledger(tmp_path: Path, data: dict[str, object]) -> None:
    """空集合や型の取り違えを完了としない。"""
    assert check(tmp_path, data)


def test_duplicate_identifiers(tmp_path: Path) -> None:
    """同一問いの重複を拒否する。"""
    data = ledger(tmp_path)
    items = cast(list[dict[str, object]], data["items"])
    items.append(items[0])
    assert check(tmp_path, data)


@pytest.mark.parametrize(
    "status",
    [
        "verified",
        "insufficient_specification",
        "rejected_incorrect",
        "translation_failed",
        "unsupported",
    ],
)
def test_each_resolved_state_needs_evidence(tmp_path: Path, status: str) -> None:
    """異なる分類でも証拠の契約を省略できない。"""
    data = ledger(tmp_path, status)
    assert check(tmp_path, data) == []
    items = cast(list[dict[str, object]], data["items"])
    items[0]["diagnosis"] = ""
    assert check(tmp_path, data)


def test_invalid_json_and_empty_evidence(tmp_path: Path) -> None:
    """壊れたJSONと空のログから完了を認めない。"""
    path = tmp_path / "bad.json"
    path.write_text("{", encoding="utf-8")
    assert validate(path, tmp_path, require_complete=True)
    data = ledger(tmp_path)
    (tmp_path / "diagnostic.log").write_text("", encoding="utf-8")
    assert check(tmp_path, data)


def test_symlink_escape(tmp_path: Path) -> None:
    """相対パスでも実体が外部なら証拠として許可しない。"""
    root = tmp_path / "repo"
    root.mkdir()
    data = ledger(root)
    outside = tmp_path / "outside.log"
    outside.write_text("outside", encoding="utf-8")
    try:
        (root / "link.log").symlink_to(outside)
    except OSError:
        pytest.skip("この環境ではシンボリックリンクの作成権限がありません")
    items = cast(list[dict[str, object]], data["items"])
    items[0]["evidence"] = ["case.py", "link.log"]
    assert check(root, data)
