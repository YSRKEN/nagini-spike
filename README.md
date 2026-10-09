# Nagini 検証

[Nagini](https://github.com/marcoeilers/nagini)で、小さなPython関数の条件を検証する実験です。
[bend2-spike](https://github.com/YSRKEN/bend2-spike)の「正しい実装を通すだけでなく、
条件を変えずに実装を壊して拒否を確認する」という検証方針を参考にしています。
参考リポジトリのコードは取り込んでいません。

最初の題材は整数の絶対値だけです。ループ、可変オブジェクト、外部ライブラリ、
ネットワークやファイルの入出力は扱っていません。

## 確認したこと

2026-10-10にWindowsネイティブで、Python 3.13.5、Java 17、Nagini 1.3.1、
同梱のZ3 4.8.7を使って確認しました。

| 検査 | 結果 |
|---|---|
| 絶対値の実装 | `Verification successful`、終了コード0 |
| 負数の分岐だけを壊したコピー | `Verification failed`、終了コード1。非負条件の違反を報告 |
| 実行・診断判定・契約の検証テスト | 17件が成功 |
| Ruffのlint・整形、Pyrightのstrict型検査 | 成功 |

`absolute(x)`の結果について、通常の`assert`で次の両方を要求します。

- 結果が0以上である。
- 結果が`x`または`-x`である。

Naginiは対応するPythonのモデル上で、これらのassertが常に成立することを検証します。
pytestは選んだ入力について、組み込みの`abs`と結果を照合します。
両者の保証範囲は異なります。

## 仕様を先に決める最小実験

`examples/absolute_contract.py`では、`Ensures`で「正常に返ったときに満たす条件」を
関数の先頭に宣言します。`ResultT(int)`は、その返り値を検証上で参照する記法です。
条件は、返り値が非負であり、入力かその符号を反転した値に等しいことです。

Naginiは通常、呼び出し側を検証するときに呼び出した関数の実装を展開せず、
その契約を使います。`caller`内のassertは、この保証が呼び出し側に届くことを調べます。
詳しくは[公式の契約説明](https://github.com/marcoeilers/nagini/wiki#general-contracts)を参照してください。

2026-10-10に次の順序を実際に試しました。

1. 契約と検査を先に書き、入力をそのまま返す未完成の実装で検査を実行する。
   `Postcondition of absolute might not hold`となり、非負条件の違反で失敗した。
2. 契約を変えずに、負数のときに符号を反転する分岐を実装する。
   関数自身と呼び出し側の検証が成功した。
3. 一時コピーで負数の分岐を壊す。同じ返り値の条件で失敗した。
4. 別の一時コピーで、非負の返り値を保証する宣言だけを外す。
   実装は正しいままでも、呼び出し側の`assert result >= 0`が検証に失敗した。

3と4は毎回の検査にも含めています。宣言の削除は検証の仕組みを調べるための実験で、
実装を完成させる際の回避策ではありません。今回、1から2の間で仕様は変えていませんが、
将来の編集で仕様の変更を禁止する仕組みまでは導入していません。

**この契約付きの例は、現段階では検証用です。** 導入した版で`absolute(1)`を通常の
Pythonから直接呼ぶと、`ResultT(int)`が`None`となり比較で`TypeError`になります。
契約を除去して同じ実装を実行する手順は未確認です。
通常のPythonで実行する絶対値の例は、引き続き`examples/absolute.py`です。

実験では処理速度よりも、Pythonの各機能を検証できる条件と、仕様を先に固定して
実装を完成させる手順を重視します。各題材で、対象の機能、仕様、必要な注釈、
検証成功、狙った理由での失敗、実行テスト、保証の範囲を記録します。
確認できた範囲を越えて、一般的な対応可否を結論付けません。

## 動かし方

uv、Python 3.13、Java 17が使える環境で、リポジトリのルートから実行します。
依存の版は`uv.lock`に固定しています。

```powershell
uv sync --locked --python 3.13
uv run --locked python scripts/check.py
```

この手順はWindowsで実行して確認しました。Linux・macOSでは未確認です。
Javaが見つからない場合は、公式の[導入説明](https://github.com/marcoeilers/nagini#dependencies-windows)
を参照してください。

`check.py`は作業場所をリポジトリのルートに固定し、lint、整形、型検査、テスト、
正常な実装の検証、誤実装の拒否を順に確認します。各処理には90秒の制限があります。
起動失敗や構文エラーを、誤実装の拒否成功とは扱いません。

Windowsでは`python -m nagini_translation.main`の起動方法だとZ3の自動探索に失敗しました。
確認スクリプトは仮想環境の`bin`に同梱されたZ3を明示し、外部PATHに依存しないようにします。
Nagini自体のファイルは変更していません。

実行ログ、壊したコピー、結果のJSONは`results/`に生成します。
環境固有のパスを含み得るため、Gitの追跡対象には含めません。

## 構成

| パス | 内容 |
|---|---|
| `examples/absolute.py` | 最小の実装と、検証するassert |
| `examples/absolute_contract.py` | 返り値の契約と、その保証を利用する呼び出し側（検証用） |
| `tests/test_absolute_contract.py` | 契約の成功、誤実装の拒否、保証不足の拒否 |
| `tests/test_absolute.py` | 組み込みのabsとの照合 |
| `tests/test_check.py` | 成功・拒否と環境故障を区別する判定のテスト |
| `scripts/check.py` | 検査一式と、条件を維持した誤実装の生成 |

clone後にコミットの規約を有効にする場合は、次を設定します。

```powershell
git config core.hooksPath .githooks
git config branch.main.mergeoptions --no-ff
git config pull.ff only
```

## 証明の範囲と依存

この実験はNaginiの健全性を証明するものではありません。
PythonからViperへの変換、Viper、Z3、PythonとJavaの処理系を信頼しています。
今回の成功を、任意のPythonプログラムやその外部ライブラリの正しさに一般化はできません。
また、assertを消す、成立しない前提を加えるなどの検証逃れは、今回の実験対象外です。

Naginiの配布物と公式ソースのライセンスは[MPL-2.0](https://github.com/marcoeilers/nagini/blob/master/LICENSE.txt)。
Ruff、pytest、PyrightとそのPythonラッパーはMITです。
2026-10-10にPyPIの公開情報、公式のライセンス本文、導入した配布物の表示を確認しました。
このリポジトリは各ツールを依存として利用し、処理系のバイナリや改変したソースを同梱しません。
将来それらを再配布する場合は、同梱する各配布物のライセンス条件を別途確認してください。
