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
正常な実装の検証、誤実装の拒否を順に確認します。個々の処理には90秒の制限を設け、
複数のNagini検証をまとめるpytestの一式だけ240秒にしています。
起動失敗や構文エラーを、誤実装の拒否成功とは扱いません。

Windowsでは`python -m nagini_translation.main`の起動方法だとZ3の自動探索に失敗しました。
確認スクリプトは仮想環境の`bin`に同梱されたZ3を明示し、外部PATHに依存しないようにします。
Nagini自体のファイルは変更していません。

実行ログ、壊したコピー、結果のJSONは`results/`に生成します。
環境固有のパスを含み得るため、Gitの追跡対象には含めません。

## 契約付きの絶対値を実行する

通常のPythonで契約付きのファイルを直接呼ぶと、検証用の`ResultT`の評価で失敗します。
この例では、次のコマンドで元のコードをNaginiで検証してから、実行用コピーを生成します。

```powershell
uv run --locked python -m scripts.extract_absolute
uv run --locked python -c "import runpy; m = runpy.run_path('results/absolute_runtime.py'); print(m['absolute'](-17)); m['caller'](-17)"
```

2026-10-10に実行し、検証成功後にコピーが生成され、二つ目のコマンドが`17`を表示して
正常終了することを確認しました。`runpy.run_path`は、指定したPythonファイルを読み込んで
関数などを取り出す標準ライブラリの機能です。

生成される`results/absolute_runtime.py`はGitで追跡しません。
生成開始時には実行を拒否する内容で出力先を上書きし、検証が失敗した場合に
前回の成功コピーを今回の結果として誤用できないようにしています。
検証前後で元のソースが変わっていないことも確認してから保存します。
検査一式では、テスト用の一時ディレクトリで同じ生成と実行の流れを確認します。

このスクリプトは今回の絶対値の例専用です。
[公式WikiのGhost code説明](https://github.com/marcoeilers/nagini/wiki#ghost-code)には
`--extraction`の記載がありますが、導入済みのNagini 1.3.1ではCLIのヘルプとソースに
そのオプションがありませんでした。Wikiの機能をこの版で利用できるとは扱わず、版も変更していません。

## 検査結果の読み方

最後に「すべての検査に成功しました。」と出て終了コードが0になれば、
通常の検査、正しい実装の検証、狙った理由での誤実装の拒否が揃っています。
途中に`Verification failed`が出るのは、わざと壊した実装の検証では期待した結果です。
その文字列だけで検査全体の成功・失敗を判断しないでください。

`results/tests.log`には、契約付きの例を検証するテストも含めたpytestの結果が入ります。
`results/summary.json`は検査の開始時に`running`へ戻し、全検査の成功後に書き直します。
現在のJSONに個別結果として載るのは、通常のassertを使う絶対値とその誤実装だけです。
契約付きの例の個別結果をすべて列挙する形式ではありません。

## 配布物の型注釈に対する局所的な扱い

リストの読み取り例で使う`Acc`には、配布物の引数`field`と`ratio`の型注釈がありません。
Pyrightは`field`をUnknown、既定値が1の`ratio`をintと推論し、
公式に説明される分数の権限指定`1 / 2`を拒否しました。
導入済みNagini 1.3.1では、この分数の指定で検証が成功しています。

[list_head.py](../examples/list_head.py)では、`Acc`のimportに対する未知の型の診断と、
分数の引数に対する診断の二か所だけを`pyright: ignore`で指定しています。
プロジェクト全体のstrict設定やほかの診断は変更していません。
[書き込み例](../examples/list_write.py)でも同じ`Acc`を使い、importの未知の型だけを
局所的に指定しています。分数を渡さないので、引数の診断の例外は必要ありません。
型検査の例外が不要な形で配布物の注釈が整備されたかは、今後の版で別途確認する事項です。

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
