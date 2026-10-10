"""題材ごとの仕様、変更、期待診断を同じ契約で検査する。"""

from dataclasses import dataclass
from pathlib import Path
from typing import Literal


@dataclass(frozen=True)
class Specification:
    """静的に証明する条件と、別途通常実行で照合する条件を示す。"""

    static: str
    runtime: str

    def __post_init__(self) -> None:
        """仕様の説明を省略したケースを拒否する。"""
        if not self.static.strip() or not self.runtime.strip():
            raise ValueError("静的仕様と通常実行の仕様が必要です。")


@dataclass(frozen=True)
class Mutation:
    """既知の一箇所だけを変更する誤例または証明情報不足の例。"""

    original: str
    replacement: str

    def apply(self, source: str) -> str:
        """置換対象が一箇所で、実際に変更することを確かめる。"""
        if (
            not self.original
            or self.original == self.replacement
            or source.count(self.original) != 1
        ):
            raise ValueError("変更対象は異なる内容に置換する一箇所でなければなりません。")
        return source.replace(self.original, self.replacement)


@dataclass(frozen=True)
class ExpectedVerification:
    """成功か、全必須診断を伴う証明失敗かを期待値として固定する。"""

    category: Literal["verified", "proof_failure"]
    required_diagnostics: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        """失敗の原因が未指定、または期待値が矛盾していれば拒否する。"""
        if self.category not in ("verified", "proof_failure"):
            raise ValueError("未対応の期待種別です。")
        if self.category == "proof_failure" and (
            not self.required_diagnostics
            or any(not text.strip() for text in self.required_diagnostics)
        ):
            raise ValueError("証明失敗には全ての必須診断を指定してください。")
        if self.category == "verified" and self.required_diagnostics:
            raise ValueError("成功の期待値に失敗診断を指定できません。")

    def matches(self, returncode: int, output: str) -> bool:
        """起動や変換の失敗を、狙った証明失敗と取り違えずに判定する。"""
        if self.category == "verified":
            return (
                returncode == 0
                and "Verification successful" in output
                and "Verification failed" not in output
            )
        return (
            returncode == 1
            and "Verification failed" in output
            and "Verification successful" not in output
            and all(text in output for text in self.required_diagnostics)
        )


@dataclass(frozen=True)
class VerificationCase:
    """仕様・正例または変更例・期待結果を関連付ける。"""

    name: str
    specification: Specification
    expected: ExpectedVerification
    mutation: Mutation | None = None


def verify_case(case: VerificationCase, source_path: Path) -> None:
    """既存の起動条件で検証し、ケース固有の全期待診断を照合する。"""
    from scripts import check

    code, output = check.run(["-m", "nagini_translation.main", str(source_path)], case.name)
    assert case.expected.matches(code, output), (
        f"{case.name}: {case.specification.static}\n"
        f"期待: {case.expected.category} {case.expected.required_diagnostics}\n{output}"
    )
