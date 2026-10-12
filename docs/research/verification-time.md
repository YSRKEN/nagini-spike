# Nagini の検証時間は何に食われているか

調査日: 2026-10-12。環境: Windows 10、Python 3.13.5、Java 17（Temurin）、Nagini 1.3.1、論理12コア。
計測中、同じ機械で別のセッションが動いており、同じコマンドでも10〜60%ぶれた（後述）。
数値はすべて「その回の実測」で、分布を示すために回数を書いた。

札: 【実測】この調査で計った / 【ソース】導入済み Nagini 1.3.1 のソースを読んだ / 【文書】公式文書 / 【推定】計算や推測。

## 結論の要点

1. 1ファイル約12秒のうち、軽い題材ではおよそ8〜9秒が「ファイルの中身に関係なく毎回かかる固定費」である【実測】。
   最大の項目は、Nagini 同梱の Viper ライブラリ（`all.sil`）を JVM で構文解析する4.6〜5.0秒【実測】。
2. 題材が1ファイル内の数十行で、ループや量化子を含んでも、軽いうちは時間がほとんど伸びない【実測】。
   Z3 が本当に効いてくるのは重い題材（`dict_missing.py`）だけで、そこでは Z3 の CPU 時間が検証の大半になる【実測】。
3. JVM を残して使い回すと、2ファイル目以降は約2.4〜3.2秒になる【実測】。
   Nagini 自身の `--server` モードは、この使い回しを行うためのもの【ソース】【文書】。
4. 別プロセスを並列に走らせると、4〜8本で約2倍の短縮にとどまった【実測】。

## 1. 12秒の内訳

### 1.1 計測方法

`Verification took N seconds` は、型検査・翻訳・検証を測るが、Python の起動と import、JVM 起動は含まない【ソース: `nagini_translation/main.py` の `translate_and_verify`、`start = time.time()` はその関数の先頭】。
プロセス全体の壁時間は、これより1.2〜2.5秒長かった【実測】。

段階別の時間は、`nagini_translation.main` の関数を差し替えて計時する `docs/research/verification-time/phase_profile.py` で測った。
Z3 の CPU 時間は、Z3 の子プロセスの CPU 時間を Windows の `GetProcessTimes` で読んで足した近似値で、読む処理自体が全体を伸ばすため、段階別の時間は `NOPOLL=1`（読まない設定）で別に測った。

### 1.2 軽い題材の内訳

`sum_range.py`（ループあり。34行）と `list_contract.py`（量化子の契約あり。47行）を、`NOPOLL=1` で各1回、プロセス全体の経過時間で測った。
他の負荷が小さかった回の値である。

| 段階 | `sum_range.py` | `list_contract.py` | 備考 |
| --- | --- | --- | --- |
| Python 起動と Nagini の import | 1.01秒 | 0.96秒 | |
| JVM 起動（`jpype.startJVM`） | 0.47秒 | 0.46秒 | |
| 型検査（mypy） | 0.44秒 | 0.43秒 | |
| 構文の解析と解析器（Analyzer） | 0.55秒 | 0.56秒 | |
| Viper ライブラリ `all.sil` の読み込み | 4.63秒 | 4.85秒 | JVM 内の Viper 構文解析器で毎回解析される |
| Viper プログラムへの変換 | 0.52秒 | 0.55秒 | |
| `translate` 全体 | 6.66秒 | 6.90秒 | 上の項目に、Viper AST の組み立てなどを足したもの |
| Silicon の初期化 | 0.65秒 | 0.67秒 | |
| Silicon の検証 | 3.18秒 | 3.45秒 | Z3 の探索を含む |
| プロセス全体 | 11.98秒 | 12.45秒 | `Verification took` は10.50秒と11.03秒 |

コマンド: `NOPOLL=1 .venv/Scripts/python.exe docs/research/verification-time/phase_profile.py examples/<ファイル>.py`

`examples/absolute.py`（23行）を同じスクリプトで3回測ると、`all.sil` の読み込みは5.31、6.98、7.76秒、`Verification took` は11.88、15.05、17.21秒だった。
同じ題材で5割以上ぶれており、上の表は「機械が空いていた回」に近い値と読むべきである。

### 1.3 Z3 の割合

- 軽い題材（`absolute.py`）: Silicon が起こした Z3 子プロセスの CPU 時間の合計は 1.27秒と1.23秒（2回）。Silicon の検証3.9〜5.6秒の一部にすぎない【実測】。
  残りは JVM 上での Silicon 本体の処理と、クラス読み込みや JIT 前の遅さと考えられる【推定】。
- 重い題材（`dict_missing.py`、81行）: Silicon の検証が40.28秒、Z3 の CPU 時間の合計が42.98秒（Z3 のプロセスは13個、並列で動く）【実測、1回】。
  この題材では Z3 の探索が検証時間の大半を占める【実測】。
- 結論: 12秒の内訳は、題材によらない固定費（import、JVM、`all.sil` の読み込み、Silicon の初期化）が大半で、Z3 は軽い題材では1割程度、重い題材では支配的になる。

### 1.4 固定費の下限

構文解析が通らない題材（`string_membership_body.py`、`string_search.py`。`Translation failed` で終わる）でも壁時間が7.8秒かかる【実測、各1回】。
検証に入る前の段階だけで8秒近くかかる、という上の内訳と合う。

## 2. 題材の規模による伸び

`examples/` の全22ファイルを、別プロセスで1回ずつ検証した（`docs/research/verification-time/cold_all.py`、結果は `docs/research/verification-time/cold_all_result.txt`）。

- 成功した20ファイルのうち、`dict_missing.py` と最初の4ファイルを除く15ファイルの `Verification took` は 10.05〜12.86秒だった。行数は19〜60行、`while` ループ、量化子の契約、`list`、`dict`、`Optional` を含むが、時間の差はほとんど無い【実測、各1回】。
  除いた最初の4ファイル（`absolute.py` 19.09秒、`absolute_contract.py` 14.81秒、`counter_contract.py` 19.40秒、`dict_update.py` 16.84秒）は他の負荷が重い時間帯で、同じ題材でも遅く出ている【推定: 機械の負荷。同じ `absolute.py` は別の回に10.6〜13.1秒】。
- 外れ値は `dict_missing.py`（81行、関数2つ）で、58.59秒（上の一括計測）、48.06秒（段階別計測）、37.69秒（同じ JVM で暖機済みの状態の6本目）と、条件で大きくぶれた【実測】。
  `--select lookup` で `lookup` だけ検証すると 18.51秒、`--select read_or_default` だけだと 41.12秒で、重いのは `read_or_default` の側【実測、各1回】。
- 関数の数や行数では伸びず、特定の証明の重さ（Z3 の探索）で急に伸びる、という形である【実測からの読み取り】。
  ループや量化子があっても、`sum_range.py` と `list_contract.py` は固定費の上に3秒程度を足しただけだった。

`scripts/check.py` の13〜19分の見立て【推定】: `tests/` と `scripts/` には Nagini を起動するケースが約43〜46か所ある（`grep -rn "VerificationCase(" tests` で43件）。
1回あたりの壁時間が12〜20秒なら、43ケースで約9〜15分になり、検査全体の13〜19分のかなりの部分を説明できる。他の部分（lint、型検査、pytest 本体）の内訳は測っていない。

## 3. 公式の短縮手段と、その効果

### 3.1 JVM とビルトインを使い回す（`--server`、実測は同じ方式の自作ループ）

- Nagini は `--server` を持つ。起動時に JVM と `all.sil` を1回だけ読み込み、ZeroMQ（`tcp://127.0.0.1:5555`）で要求を受けるたびに `translate_and_verify` を呼ぶ【ソース: `main.py` の `if args.server:`】。
  公式 README にも "Server Mode / Faster Verification Mode" という節がある。起動時の作業と JVM 起動の費用を省く説明で、`nagini --server <otherArgs> dummyFile.py` で起動し、`nagini_client path/to/file.py` で呼ぶ【文書: https://github.com/marcoeilers/nagini/blob/master/README.rst 、WebFetch の要約で確認】。
- 必要な `pyzmq` は Nagini の `server` extra（`pyzmq==27.1.0`）で、この環境の `uv.lock` には入っていない【ソース: `nagini-1.3.1.dist-info/METADATA`、`.venv` に zmq が無いことを確認】。
  依存を足すと `pyproject.toml` / `uv.lock` の変更になるため、この調査では入れていない。ZeroMQ の通信そのものは未検証。
- 代わりに、サーバーの本体と同じ「JVM と `all.sil` を1度だけ読み、`translate_and_verify` を繰り返す」処理を `docs/research/verification-time/persistent.py` で再現して測った。通信の費用は含まない。

同一プロセスで続けて検証した結果（1本の実行内、1回）:

| 順番 | ファイル | 時間 |
| --- | --- | --- |
| 1 | `absolute.py` | 10.64秒（import と JVM の1.46秒は別） |
| 2 | `sum_range.py` | 2.97秒 |
| 3 | `list_contract.py` | 3.18秒 |
| 4 | `list_empty.py` | 3.09秒 |
| 5 | `absolute.py`（2回目） | 2.42秒 |
| 6 | `dict_missing.py` | 37.69秒 |

コマンド: `.venv/Scripts/python.exe docs/research/verification-time/persistent.py examples/absolute.py examples/sum_range.py examples/list_contract.py examples/list_empty.py examples/absolute.py examples/dict_missing.py`

- 2本目以降は約2.4〜3.2秒で、別プロセスでの約11〜12秒の約4分の1。固定費のうち `all.sil` の読み込み（2本目以降は読み込み済みのグローバルを再利用【ソース: `translate` の `'sil_programs' not in globals()`】）と、JVM の暖機（JIT、クラス読み込み）が消えている【実測からの読み取り】。
- `python -m nagini_translation.main --benchmark 5 examples/absolute.py`（ソースにある測定用オプションで、README には無い。毎回翻訳と検証をやり直す）でも、同じ JVM 内で 7.96、4.23、4.04、3.56、2.59秒と下がった【実測、1回】。
- 重い題材（`dict_missing.py`）は使い回しても37.69秒で、短くならない【実測】。

### 3.2 ViperServer とキャッシュ（`--viper-server`）

- 1.3.1 のソースにある。`--viper-server` を付けると、Viper 付属の ViperServer（同一プロセス内）で検証し、同じプログラムの結果をキャッシュする。サーバーモードで使うと、キャッシュは要求をまたいで残る【ソース: `main.py` の `--viper-server` の説明、`viper_server.py` の `ViperServerManager`】。
  README には、`--viper-server` という名前のオプションは出てこず、MCP サーバーが既定でこの方式を使うという記述だけだった【文書: 上の README、WebFetch の要約。ソースの方が詳しい】。
- 単発の起動での効果は無い: `absolute.py` を3回測って、`Verification took` は 11.57、11.64、10.99秒（付けない場合の10.6〜13.1秒と同程度）【実測】。
- JVM を使い回すループの中で効く: `dict_missing.py` を2回続けて検証すると、1回目45.84秒、同じ内容の2回目6.47秒【実測、1回】。キャッシュが当たったとみられる【推定: 当たった印は確認していない】。
  内容を変えた場合にどこまで効くかは測っていない（ViperServer のキャッシュの粒度は未確認）。
  軽い題材（`absolute.py` と `sum_range.py` を各2回）では、2回目も 2.5〜2.7秒で、キャッシュの有無で目立つ差は出なかった【実測】。

### 3.3 `--select`（検証対象の絞り込み）

`--select` は、関数・メソッド・クラスを名前で絞って検証する【ソース: `main.py` の引数の説明。README の "Command Line Usage" にも同旨の記述あり】。
1節に書いたとおり、`dict_missing.py` では `--select lookup` で18.51秒、`--select read_or_default` で41.12秒。全体は48〜58秒。軽い題材では固定費が残るため絞っても大差ない。

### 3.4 バックエンドの選択（Silicon か Carbon）

- `--verifier silicon`（既定）と `carbon` を選べる。Carbon は Boogie 2.15.9 が別に要る【文書: README の "Dependencies"、"Command Line Usage"】。
- この環境には Boogie が無い（`which boogie` に出ない）ため、Carbon は試していない。**未計測**。

### 3.5 並列実行

README に、並列検証の仕組みの記述は見つからなかった【文書: README の WebFetch 要約】。
OS の別プロセスを同時に走らせて測った（`docs/research/verification-time/parallel.py`）:

| 同時に走らせた数 | 全体の壁時間 | 逐次の見込み（約12秒×本数） |
| --- | --- | --- |
| 4本 | 23.0秒 | 約48秒 |
| 8本 | 48.5秒 | 約96秒 |

【実測、各1回】。約2倍の短縮にとどまり、本数に比例した短縮にはならなかった。
Silicon は1プロセスで複数の Z3 を並列に起こす（Z3 のプロセスが13個見えた）ため、プロセスを増やすと12コアを取り合うと考えられる【推定】。
JVM 使い回しの逐次実行は、8本なら約 10.6 + 7×3 = 32秒の見込み【推定: 上の使い回しの表からの計算】で、並列プロセス8本の48.5秒より短い。

### 3.6 試したが効かなかったもの

- Silicon の並列検証器の数を1にする（`--viper-arg=--numberOfParallelVerifiers,1`）: `absolute.py` で 10.57、9.76、9.76秒。付けない回（10.6〜13.1秒）との差は機械のぶれの範囲に近い【実測、各3回】。
- JVM に `-XX:TieredStopAtLevel=1`（JIT をC1だけにする。環境変数 `JAVA_TOOL_OPTIONS` で渡す）: `absolute.py` で 12.16、12.49、12.90秒。短くならなかった【実測、3回。公式の手段ではない】。

## 4. 確かめていないこと

- ZeroMQ の `--server` / `nagini_client` の実際の往復（`pyzmq` を入れていない）。
- Carbon バックエンド。
- `--viper-server` のキャッシュが、ファイルを少し書き換えたときにどこまで当たるか。
- `scripts/check.py` 全体の実行。13〜19分という数字は、利用者から伝えられた値で、この調査では測っていない。
- 同じ条件の繰り返し回数が少ない（多くは1〜3回）。機械の負荷でぶれるので、1秒未満の差は意味を持たない。

## 5. 再現手順

```powershell
uv sync --locked --python 3.13
# 段階別（Z3 の CPU 時間の読み取りは NOPOLL=1 で止める）
$env:NOPOLL = "1"; .venv\Scripts\python.exe docs\research\verification-time\phase_profile.py examples\sum_range.py
# 全 examples を別プロセスで1回ずつ
.venv\Scripts\python.exe docs\research\verification-time\cold_all.py
# JVM を使い回す
.venv\Scripts\python.exe docs\research\verification-time\persistent.py examples\absolute.py examples\sum_range.py
# 別プロセスの並列
.venv\Scripts\python.exe docs\research\verification-time\parallel.py examples\absolute.py examples\sum_range.py
```

`Z3_EXE` は各スクリプトが `.venv\bin\z3.exe` を自動で指す（`docs/environments.md` と同じ理由）。
