"""調査台帳から進捗一覧を生成し、更新漏れを検出する。"""

import argparse
import json
import sys
from pathlib import Path
from typing import cast

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.check_investigation import Json, validate

LABELS = {
    "verified": "done（証明成功）",
    "unconfirmed": "未確認",
    "unsupported": "done（非対応確認）",
    "translation_failed": "done（変換失敗確認）",
    "rejected_incorrect": "done（誤実装拒否）",
    "insufficient_specification": "done（仕様不足確認）",
}


def cell(value: str) -> str:
    """改行と区切り文字でMarkdownの表が崩れることを防ぐ。"""
    return " ".join(value.splitlines()).replace("|", "\\|")


def render(items: list[dict[str, Json]]) -> str:
    """全問いを台帳の順序で表示し、調査済みと証明成功を分ける。"""
    pending = sum(item["status"] == "unconfirmed" for item in items)
    proven = sum(item["status"] == "verified" for item in items)
    lines = [
        "# 調査の進捗",
        "",
        "<!-- scripts/render_progress.py が investigation.json から生成。直接編集しない。 -->",
        "",
        f"全{len(items)}件：調査済み{len(items) - pending}件（証明成功{proven}件）、"
        f"未確認{pending}件。",
        "",
        "doneは各行の問いについて記録した条件で調査・分類済みという意味です。",
        "非対応・変換失敗・仕様不足も区別して表示し、Python全体の対応や実運用の安全性は保証しません。",
        "未確認には未着手だけでなく証明未達も含まれます。入力域・制約・再現方法は",
        "[台帳](investigation.json)、判定の読み方は[調査方法](investigation.md)を参照してください。",
        "台帳以前の基礎実験は[題材一覧](examples.md)にあり、この進捗の件数には含めません。",
        "",
        "| ID | 調べる問い | 状態 | 証拠 |",
        "| --- | --- | --- | --- |",
    ]
    for item in items:
        identifier = cell(cast(str, item["id"]))
        question = cell(cast(str, item["question"]))
        label = LABELS[cast(str, item["status"])]
        references = cast(list[str], item["evidence"])
        example = next((ref for ref in references if ref.endswith(".py")), None)
        log = next((ref for ref in references if ref.endswith(".log")), None)
        links: list[str] = []
        if example:
            links.append(f"[コード](../{example})")
        if log:
            links.append(f"[診断](../{log})")
        evidence = " / ".join(links) or "—"
        lines.append(f"| `{identifier}` | {question} | {label} | {evidence} |")
    return "\n".join(lines) + "\n"


def synchronize(target: Path, expected: str, *, check: bool) -> int:
    """検査では書き換えず、生成時だけ表を更新する。"""
    if check:
        return 0 if target.is_file() and target.read_text(encoding="utf-8") == expected else 1
    target.write_text(expected, encoding="utf-8", newline="\n")
    return 0


def main() -> int:
    """通常の台帳整合性を確認し、進捗表を生成または照合する。"""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="表を変更せず台帳との一致を確認")
    arguments = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    ledger = root / "docs/investigation.json"
    errors = validate(ledger, root)
    if errors:
        print("\n".join(errors))
        return 1
    data = cast(dict[str, Json], json.loads(ledger.read_text(encoding="utf-8-sig")))
    items = cast(list[dict[str, Json]], data["items"])
    result = synchronize(root / "docs/progress.md", render(items), check=arguments.check)
    if result:
        print("進捗表が台帳と一致しません。python scripts/render_progress.pyで更新してください。")
    else:
        print("進捗表と台帳が一致" if arguments.check else "進捗表を更新")
    return result


if __name__ == "__main__":
    raise SystemExit(main())
