"""調査台帳の整合性と、根拠のある完了宣言を検査する。"""

import argparse
import json
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import TypeAlias, cast

Json: TypeAlias = str | int | float | bool | None | list["Json"] | dict[str, "Json"]
STATES = {
    "unconfirmed",
    "verified",
    "insufficient_specification",
    "rejected_incorrect",
    "translation_failed",
    "unsupported",
}
FIELDS = {
    "id",
    "question",
    "status",
    "scope",
    "reproduction",
    "expected",
    "actual",
    "diagnosis",
    "evidence",
}


def evidence_error(reference: str, root: Path) -> str | None:
    """リポジトリ内の空でない証拠ファイルだけを許可する。"""
    posix = PurePosixPath(reference)
    windows = PureWindowsPath(reference)
    if (
        not reference
        or "\\" in reference
        or posix.is_absolute()
        or windows.drive
        or ".." in posix.parts
        or ":" in reference
    ):
        return "証拠はリポジトリ内の相対パスで指定してください"
    target = (root / reference).resolve()
    if not target.is_relative_to(root.resolve()):
        return "証拠の実体がリポジトリ外にあります"
    if not target.is_file() or target.stat().st_size == 0:
        return "証拠ファイルが存在しないか空です"
    return None


def validate(path: Path, root: Path, *, require_complete: bool = False) -> list[str]:
    """台帳の型・状態・証拠と、要求された完了条件を検査する。

    Parameters
    ----------
    path : Path
        検査するJSON台帳。
    root : Path
        証拠を探索するリポジトリのルート。
    require_complete : bool
        未確認の問いを拒否するか。

    Returns
    -------
    list[str]
        問題の一覧。空なら契約を満たす。
    """
    try:
        data = cast(Json, json.loads(path.read_text(encoding="utf-8-sig")))
    except (OSError, ValueError) as error:
        return ["台帳を読み取れません: " + str(error)]
    if not isinstance(data, dict) or set(data) != {"schema_version", "items"}:
        return ["台帳のキーが不正です"]
    if type(data["schema_version"]) is not int or data["schema_version"] != 1:
        return ["schema_versionは整数1である必要があります"]
    items = data["items"]
    if not isinstance(items, list) or not items:
        return ["問いの配列が必要です。空台帳は完了できません"]
    errors: list[str] = []
    identifiers: set[str] = set()
    for index, item in enumerate(items):
        label = f"items[{index}]"
        if not isinstance(item, dict) or set(item) != FIELDS:
            errors.append(label + ": 項目のキーが不正です")
            continue
        for field in FIELDS - {"evidence"}:
            value = item[field]
            if not isinstance(value, str):
                errors.append(label + ": " + field + "は文字列が必要です")
        identifier = item["id"]
        if isinstance(identifier, str):
            if not identifier.strip() or identifier in identifiers:
                errors.append(label + ": IDが空か重複しています")
            identifiers.add(identifier)
        status = item["status"]
        if not isinstance(status, str) or status not in STATES:
            errors.append(label + ": 未知の状態です")
            continue
        if not isinstance(item["question"], str) or not item["question"].strip():
            errors.append(label + ": 問いが必要です")
        pending = status == "unconfirmed"
        if pending and require_complete:
            errors.append(label + ": 未確認の問いが残っています")
        if not pending:
            for field in ("scope", "reproduction", "expected", "actual", "diagnosis"):
                value = item[field]
                if not isinstance(value, str) or not value.strip():
                    errors.append(label + ": 確認済みには" + field + "が必要です")
        evidence = item["evidence"]
        if not isinstance(evidence, list):
            errors.append(label + ": evidenceは配列が必要です")
            continue
        if not pending and len(evidence) < 2:
            errors.append(label + ": 再現例と診断の証拠が必要です")
        references: list[str] = []
        for reference in evidence:
            if not isinstance(reference, str):
                errors.append(label + ": 証拠パスは文字列が必要です")
                continue
            references.append(reference)
            try:
                error = evidence_error(reference, root)
            except (OSError, ValueError) as exception:
                error = "証拠を確認できません: " + str(exception)
            if error:
                errors.append(label + ": " + reference + ": " + error)
        if not pending and (
            not any(ref.endswith(".py") for ref in references)
            or not any(ref.endswith((".log", ".txt", ".json")) for ref in references)
        ):
            errors.append(label + ": Python再現例と診断ログを参照してください")
    return errors


def main() -> int:
    """通常検査と完了要求を明示的に切り替える。"""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--require-complete", action="store_true")
    parser.add_argument("--ledger", type=Path, default=Path("docs/investigation.json"))
    arguments = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    errors = validate(arguments.ledger, root, require_complete=arguments.require_complete)
    for error in errors:
        print(error)
    if not errors:
        print(
            "調査台帳の完了条件に適合" if arguments.require_complete else "調査台帳の整合性に適合"
        )
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
