# Nagini検証

[Nagini](https://github.com/marcoeilers/nagini)で、仕様に合うPythonコードを証明できるかを調べる実験です。
正実装の成功に加え、同じ仕様を満たさない誤実装が、狙った理由で拒否されることを確認します。
仕様を先に固定し、失敗する検査から実装を進めるTDDを使います。

## 進捗を見る

**[done・未確認の一覧](docs/progress.md)** で、調査中の各題材と証拠を確認できます。
進捗表は[JSON台帳](docs/investigation.json)から生成し、通常検査で更新漏れを検出します。
台帳以前の基礎実験とソースの一覧は[題材一覧](docs/examples.md)にまとめています。

検証成功は、記述した条件がNaginiのモデル上で成立するという意味です。
仕様の十分性や、未確認のPython機能まで保証するものではありません。

## 動かす

Windowsで、Python 3.13・Java 17・Nagini 1.3.1を使って確認しています。
uv、Python 3.13、Java 17が使える環境で、リポジトリのルートから実行します。
依存の版は`uv.lock`に固定しています。環境条件と診断の読み方は[実行環境](docs/environments.md)を参照してください。

```powershell
uv sync --locked --python 3.13
uv run --locked python scripts/check.py
```

検査にはlint・整形・strict型検査・通常実行・Naginiの実検証を含めます。
誤実装の拒否では意図的に`Verification failed`が出ます。検査全体の成功は最後のメッセージと終了コードで確認します。

## 詳しく読む

| 知りたいこと | 文書 |
| --- | --- |
| doneと未確認、元の証拠 | [調査の進捗](docs/progress.md) |
| 台帳の判定・更新・完了条件 | [調査方法](docs/investigation.md) |
| 試したコードを探す | [題材一覧](docs/examples.md) |
| Python機能の確認範囲と実行上の制約 | [Pythonの機能](docs/language.md) |
| テストと証明の違い、契約と誤実装の拒否 | [仕様と検証](docs/proofs.md) |
| 環境構築、ログ、開発設定 | [実行環境](docs/environments.md) |
| 時間切れ時のプロセス回収と限定範囲 | [子孫プロセスの回収](docs/timeout-process-cleanup.md) |

構成の参考は[bend2-spike](https://github.com/YSRKEN/bend2-spike)です。参考元のコードは取り込んでいません。
