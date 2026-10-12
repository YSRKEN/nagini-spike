"""一括実行の計画・判定・結果表を、Nagini を起動せずに確かめる。"""

from pathlib import Path

import pytest

from scripts.verification_plan import (
    Check,
    CheckResult,
    classify,
    first_error,
    plan,
    render_table,
    replace_section,
)

VERIFIED = "Verification successful\nVerification took 2.31 seconds.\n"
FAILED = (
    "Verification failed\nErrors:\n"
    "Postcondition of wrong_absolute might not hold. Assertion Result() >= 0 might not hold. "
    "(absolute.py@13.12--13.25)\nVerification took 1.90 seconds.\n"
)
UNSUPPORTED = (
    "Translation failed\nNot supported: Unsupported function or method __getitem__ in type str "
    "(str_index.py@2.11)\n"
)


def test_classify_reads_each_kind_of_response() -> None:
    """成功・失敗・非対応・それ以外を見分ける。"""
    assert classify(VERIFIED) == "verified"
    assert classify(FAILED) == "rejected"
    assert classify(UNSUPPORTED) == "unsupported"
    assert classify("Translation failed\nType error: dead.code\n") == "error"


def test_first_error_returns_the_first_reported_error_without_location() -> None:
    """失敗の最初の1件を、位置の括弧を除いて返す。"""
    assert first_error(FAILED) == (
        "Postcondition of wrong_absolute might not hold. Assertion Result() >= 0 might not hold."
    )
    assert first_error(UNSUPPORTED) == (
        "Not supported: Unsupported function or method __getitem__ in type str"
    )
    assert first_error(VERIFIED) == ""


SOURCE = '''"""絶対値。"""


def absolute(x: int) -> int:
    return x


def caller(x: int) -> None:
    absolute(x)


def wrong_absolute(x: int) -> int:
    return x


class Base:
    pass


class WrongChild(Base):
    pass
'''


def test_plan_verifies_correct_names_together_and_each_wrong_name_alone() -> None:
    """正実装はまとめて成功を、誤実装は1つずつ拒否を期待する。"""
    assert plan(Path("features/control/absolute.py"), SOURCE) == [
        Check("正実装", "absolute,caller,Base", "verified"),
        Check("wrong_absolute", "wrong_absolute", "rejected"),
        Check("WrongChild", "WrongChild", "rejected"),
    ]


def test_plan_expects_unsupported_for_files_in_unsupported_directory() -> None:
    """非対応の題材はファイル全体で非対応を期待する。"""
    source = "def head(s: str) -> str:\n    return s[0]\n"
    assert plan(Path("features/unsupported/str_index.py"), source) == [
        Check("非対応", None, "unsupported"),
    ]


@pytest.mark.parametrize(
    "source",
    [
        "def wrong_only(x: int) -> int:\n    return x\n",
        "def right_only(x: int) -> int:\n    return x\n",
    ],
)
def test_plan_requires_both_correct_and_wrong_implementations(source: str) -> None:
    """正実装か誤実装の片方しかない題材は計画できない。"""
    with pytest.raises(ValueError):
        plan(Path("features/control/one_sided.py"), source)


def test_check_result_passes_only_when_outcome_matches_expectation() -> None:
    """期待と結果が一致したときだけ合格にする。"""
    check = Check("wrong_absolute", "wrong_absolute", "rejected")
    assert CheckResult(check, "rejected", 1.9, "").passed
    assert not CheckResult(check, "verified", 1.9, "").passed
    assert not CheckResult(check, "timeout", 120.0, "").passed


def test_render_table_summarizes_each_file_in_one_row() -> None:
    """題材ごとに、正実装の成否・拒否の数・時間・落ちた契約を1行にまとめる。"""
    correct = Check("正実装", "absolute", "verified")
    wrong = Check("wrong_absolute", "wrong_absolute", "rejected")
    unsupported = Check("非対応", None, "unsupported")
    rows = {
        Path("features/control/absolute.py"): [
            CheckResult(correct, "verified", 2.31, ""),
            CheckResult(wrong, "rejected", 1.9, "Assertion Result() >= 0 might not hold."),
        ],
        Path("features/unsupported/str_index.py"): [
            CheckResult(unsupported, "unsupported", 0.48, "Not supported: str"),
        ],
    }
    assert render_table(rows).splitlines() == [
        "| 分野 | 題材 | 正実装 | 誤実装の拒否 | 時間（秒） | 誤実装・非対応で報告された内容 |",
        "| --- | --- | --- | --- | --- | --- |",
        "| 型と制御構造 | [absolute](features/control/absolute.py) | 成功 | 1/1 | 4.2 "
        "| Assertion Result() >= 0 might not hold. |",
        "| 非対応 | [str_index](features/unsupported/str_index.py) | — | — | 0.5 "
        "| Not supported: str |",
    ]


def test_render_table_marks_unexpected_outcomes() -> None:
    """期待と違う結果は、その結果の名前で表に出す。"""
    correct = Check("正実装", "absolute", "verified")
    wrong = Check("wrong_absolute", "wrong_absolute", "rejected")
    rows = {
        Path("features/control/absolute.py"): [
            CheckResult(correct, "timeout", 120.0, ""),
            CheckResult(wrong, "verified", 1.9, ""),
        ],
    }
    row = render_table(rows).splitlines()[2]
    assert "| 時間切れ | 0/1 |" in row


def test_replace_section_swaps_only_the_marked_block() -> None:
    """README の印の間だけを差し替える。"""
    readme = "前\n<!-- results:start -->\n古い表\n<!-- results:end -->\n後\n"
    assert replace_section(readme, "新しい表\n") == (
        "前\n<!-- results:start -->\n新しい表\n<!-- results:end -->\n後\n"
    )
    with pytest.raises(ValueError):
        replace_section("印が無い\n", "表\n")
