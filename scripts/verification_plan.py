"""題材ごとの検証の計画を立て、Nagini の応答を判定して結果表にまとめる。

ここには副作用を置かない。Nagini の起動と通信は ``scripts/nagini_server.py`` が受け持つ。
"""

import ast
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

Expectation = Literal["verified", "rejected", "unsupported"]
Outcome = Literal["verified", "rejected", "unsupported", "error", "timeout"]

AREAS = {
    "control": "型と制御構造",
    "collections": "コレクション",
    "classes": "クラス",
    "exceptions": "例外",
    "unsupported": "非対応",
}
OUTCOME_LABELS: dict[Outcome, str] = {
    "verified": "成功",
    "rejected": "拒否",
    "unsupported": "非対応",
    "error": "変換エラー",
    "timeout": "時間切れ",
}
START = "<!-- results:start -->"
END = "<!-- results:end -->"
_LOCATION = re.compile(r"\s*\([^()]*@[^()]*\)$")


@dataclass(frozen=True)
class Check:
    """1回の検証の要求と、その期待。

    Attributes
    ----------
    label : str
        結果表で使う名前。正実装は「正実装」、誤実装は関数・クラスの名前。
    select : str or None
        Nagini に渡す検証対象の名前（カンマ区切り）。None ならファイル全体。
    expected : Expectation
        期待する結果。
    """

    label: str
    select: str | None
    expected: Expectation


@dataclass(frozen=True)
class CheckResult:
    """1回の検証の結果。

    Attributes
    ----------
    check : Check
        行った検証。
    outcome : Outcome
        Nagini の応答から判定した結果。
    seconds : float
        要求から応答までの実時間。
    detail : str
        失敗・非対応のときに報告された最初の内容。
    """

    check: Check
    outcome: Outcome
    seconds: float
    detail: str

    @property
    def passed(self) -> bool:
        """結果が期待と一致したかを返す。"""
        return self.outcome == self.check.expected


def classify(response: str) -> Outcome:
    """Nagini の応答を、成功・拒否・非対応・その他に分ける。

    Parameters
    ----------
    response : str
        Nagini が返した出力。

    Returns
    -------
    Outcome
        判定した結果。時間切れはここでは返さない。
    """
    if "Verification successful" in response:
        return "verified"
    if "Verification failed" in response:
        return "rejected"
    if "Not supported" in response:
        return "unsupported"
    return "error"


def first_error(response: str) -> str:
    """応答から最初に報告された失敗・非対応の内容を、位置を除いて返す。

    Parameters
    ----------
    response : str
        Nagini が返した出力。

    Returns
    -------
    str
        最初の失敗・非対応の内容。無ければ空文字列。
    """
    lines = [line.strip() for line in response.splitlines() if line.strip()]
    for index, line in enumerate(lines):
        if line == "Errors:" and index + 1 < len(lines):
            return _LOCATION.sub("", lines[index + 1])
        if line.startswith("Not supported"):
            return _LOCATION.sub("", line)
    return ""


def _is_wrong(name: str) -> bool:
    return name.startswith("wrong_") or name.startswith("Wrong")


def plan(path: Path, source: str) -> list[Check]:
    """題材ファイルから、行う検証の一覧を作る。

    Parameters
    ----------
    path : Path
        題材ファイルのパス。親ディレクトリの名前で分野を決める。
    source : str
        題材ファイルの中身。

    Returns
    -------
    list of Check
        非対応の題材ならファイル全体の1件。それ以外は、正実装をまとめた1件と、誤実装ごとの1件。

    Raises
    ------
    ValueError
        正実装か誤実装のどちらかが無い題材。
    """
    if path.parent.name == "unsupported":
        return [Check("非対応", None, "unsupported")]
    names = [
        node.name
        for node in ast.parse(source).body
        if isinstance(node, (ast.FunctionDef, ast.ClassDef))
    ]
    correct = [name for name in names if not _is_wrong(name)]
    wrong = [name for name in names if _is_wrong(name)]
    if not correct or not wrong:
        raise ValueError(f"{path} には正実装と誤実装の両方が要る")
    return [Check("正実装", ",".join(correct), "verified")] + [
        Check(name, name, "rejected") for name in wrong
    ]


def _row(path: Path, results: Sequence[CheckResult]) -> str:
    area = AREAS.get(path.parent.name, path.parent.name)
    link = f"[{path.stem}]({path.as_posix()})"
    seconds = f"{sum(result.seconds for result in results):.1f}"
    details = " / ".join(result.detail for result in results if result.detail)
    if path.parent.name == "unsupported":
        return f"| {area} | {link} | — | — | {seconds} | {details} |"
    correct = [result for result in results if result.check.expected == "verified"]
    wrong = [result for result in results if result.check.expected == "rejected"]
    verdict = "、".join(OUTCOME_LABELS[result.outcome] for result in correct)
    rejected = f"{sum(result.passed for result in wrong)}/{len(wrong)}"
    return f"| {area} | {link} | {verdict} | {rejected} | {seconds} | {details} |"


def render_table(rows: Mapping[Path, Sequence[CheckResult]]) -> str:
    """題材ごとの結果を、README に載せる Markdown の表にする。

    Parameters
    ----------
    rows : Mapping of Path to sequence of CheckResult
        題材ファイルごとの検証結果。並び順のまま行にする。

    Returns
    -------
    str
        末尾に改行を付けた表。
    """
    lines = [
        "| 分野 | 題材 | 正実装 | 誤実装の拒否 | 時間（秒） | 誤実装・非対応で報告された内容 |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    lines += [_row(path, results) for path, results in rows.items()]
    return "\n".join(lines) + "\n"


def replace_section(readme: str, table: str) -> str:
    """README の印の間を、新しい表に差し替える。

    Parameters
    ----------
    readme : str
        README の中身。
    table : str
        差し替える表。

    Returns
    -------
    str
        差し替えた README。

    Raises
    ------
    ValueError
        印が無い、または順序が逆の README。
    """
    start = readme.find(START)
    end = readme.find(END)
    if start < 0 or end < start:
        raise ValueError("README に結果表の印が無い")
    return readme[: start + len(START)] + "\n" + table + readme[end:]
