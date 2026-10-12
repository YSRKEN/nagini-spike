"""単一継承: 子クラスの上書きが、親の契約を守る。"""

from nagini_contracts.contracts import Ensures, Result


class Shape:
    """角の数を持つ図形。"""

    def corners(self) -> int:
        """角の数を返す。どの図形でも負にはならない。"""
        Ensures(Result() >= 0)
        return 0


class Square(Shape):
    """正方形。"""

    def corners(self) -> int:
        """角の数は4。親の「負にならない」より強い約束なので守れている。"""
        Ensures(Result() == 4)
        return 4


class WrongShape(Shape):
    """親の契約を破る図形。"""

    def corners(self) -> int:
        """角の数を -1 と約束してしまい、親の「負にならない」を破る。"""
        Ensures(Result() == -1)
        return -1
