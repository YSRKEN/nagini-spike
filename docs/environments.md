# Naginiを動かす環境

[READMEに戻る](../README.md)。検証の意味は[仕様と検証](proofs.md)、
Pythonの機能ごとの確認範囲は[Pythonの機能](language.md)を参照してください。

## 確認した環境

2026-10-10に、次の組み合わせでリポジトリの検査を実行しました。
動作を確認した組み合わせの記録であり、ほかの版で動かないという意味ではありません。

| 項目 | 確認した構成 |
|---|---|
| 実行環境 | Windowsネイティブ |
| Python | 3.13.5 |
| Java | 17 |
| Nagini | 1.3.1 |
| Z3 | Naginiの依存として導入された4.8.7 |
| 依存の管理 | uv、版を固定した`uv.lock` |

Linux・macOSでの動作は未確認です。環境の導入を試す前に、
[公式の依存説明](https://github.com/marcoeilers/nagini#dependencies-windows)も確認してください。

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

## 検査結果の読み方

最後に「すべての検査に成功しました。」と出て終了コードが0になれば、
通常の検査、正しい実装の検証、狙った理由での誤実装の拒否が揃っています。
途中に`Verification failed`が出るのは、わざと壊した実装の検証では期待した結果です。
その文字列だけで検査全体の成功・失敗を判断しないでください。

`results/tests.log`には、契約付きの例を検証するテストも含めたpytestの結果が入ります。
`results/summary.json`は検査の開始時に`running`へ戻し、全検査の成功後に書き直します。
現在のJSONに個別結果として載るのは、通常のassertを使う絶対値とその誤実装だけです。
契約付きの例の個別結果をすべて列挙する形式ではありません。

## 開発時のGit設定

clone後にコミットの規約を有効にする場合は、次を設定します。

```powershell
git config core.hooksPath .githooks
git config branch.main.mergeoptions --no-ff
git config pull.ff only
```

## 依存とライセンス

Naginiの配布物と公式ソースのライセンスは[MPL-2.0](https://github.com/marcoeilers/nagini/blob/master/LICENSE.txt)。
Ruff、pytest、PyrightとそのPythonラッパーはMITです。
2026-10-10にPyPIの公開情報、公式のライセンス本文、導入した配布物の表示を確認しました。
このリポジトリは各ツールを依存として利用し、処理系のバイナリや改変したソースを同梱しません。
将来それらを再配布する場合は、同梱する各配布物のライセンス条件を別途確認してください。
