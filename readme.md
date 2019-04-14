# これは何？

キーボード入力を可視化し、gifファイルを出力するpythonスクリプト。


## 使い方

`python3`、および、`pillow`が必要です。

```sh
$ pip install Pillow
```

`input.txt`に可視化したいデータを登録し、`keyboard.py`を実行。
`output.gif`という名前で、640x360のサイズで出力されます。

入力ファイル名、出力ファイル名、サイズ等は設定で変更可能です。


## ファイル

- `setting.txt`::設定ファイル
- `keytable.txt`::キーボードレイアウトの定義ファイル。変更可能です
