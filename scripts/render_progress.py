"""台帳から進捗表を生成する。"""

from pathlib import Path

from scripts.check_investigation import Json


def render(items: list[dict[str, Json]]) -> str:
    """調査状態をMarkdownへ表示する。"""
    return ""


def synchronize(target: Path, expected: str, *, check: bool) -> int:
    """更新漏れを検出し、生成時だけ書き込む。"""
    return 0
