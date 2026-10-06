# dmconverter-styles

[MIERUNE/dmconverter](https://github.com/MIERUNE/dmconverter)（DMファイルを GeoPackage に変換する QGIS プラグイン）に指定する**スタイルフォルダ（QML）**です。地図記号のアイコンと、線・面の描き分けを補います。

dmconverter はスタイルフォルダを指定しないと、点はすべて同じマーカー、線・面はランダムな色で描かれます。このリポジトリの `styles/` を指定すると、次のように描かれます。

| 対象 | 表示 |
|---|---|
| 点（E5 記号・E6 方向） | [dm-sprite](https://github.com/shiwaku/dm-sprite) の地図記号（公共測量標準図式）を分類コードで切り替えて表示。E6 は方向角で回転 |
| 線（E2） | 黒線。歩道は破線、等高線・凹地は細線、建物は太線 |
| 面（E1） | 塗りなし＋黒の輪郭（線と重ねる前提） |

見た目は [shiwaku/dm-converter](https://github.com/shiwaku/dm-converter) の QGIS スタイルに合わせています。

## 使い方

1. このリポジトリをダウンロード（または clone）する
2. QGIS のプロセッシングツールボックスで **DM Converter** のアルゴリズムを開き、**「入力：スタイルフォルダ（QML）」に `styles/` フォルダ**を指定する
   - **DMファイルをGeoPackageに変換**: 変換と同時にスタイルが当たる
   - **スタイルを適用してQLRを出力**: 変換済みの GeoPackage にスタイルを当て、QLR（レイヤ定義ファイル）を書き出す
3. 書き出した QLR は、QGIS にドラッグ＆ドロップするか「レイヤ」→「レイヤ定義ファイルから追加…」で開く

地図記号の SVG は QML に base64 で埋め込んであるので、SVG ファイルの場所を設定する必要はありません。出力した QLR も単体で記号が表示されます。

E6 の回転（`0 - "方向角"`）と、間断区分（`"間断区分" = 0`）による非表示は dmconverter が付けるので、QML には含めていません。

## 収録内容

```
styles/                 ← dmconverter に指定するフォルダ（QML 以外は置かない）
  dm_point.qml          点（E5・E6）
  dm_line.qml           線（E2）
  dm_polygon.qml        面（E1）
icons/                  dm-sprite の SVG（QML の生成元）。SOURCE.json に取得元コミット
data/
  icons.csv             アイコンの名称表（dm-sprite）
  standard-codes.csv    公共測量標準図式の全分類コード（dm-sprite）
scripts/
  gen_dm_styles.py      styles/*.qml の生成スクリプト
```

## 地図記号について

- 標準図式のアイコン 176 コードを、分類コード（`HCODE2` の頭4桁）で切り替えて表示します
- **アイコンの無いコードは灰色の丸**で表示します。標準図式で点記号を持たないコード（例: 6110 被覆。図式では線記号）や、自治体・ベンダ独自の拡張 DM コードが該当します
- 拡張 DM 向けのアイコン（`dm-<提供元>-<コード>.svg`）は、同じコードでも提供元ごとに意味が異なるため使っていません
- 表示サイズの既定は 9mm です。SVG は 64×64 のキャンバスに対して絵が3割ほどなので、見た目は 3mm 前後になります

## 作り直す

アイコンの更新や表示サイズの変更は、QGIS 同梱の Python で生成スクリプトを実行します。

```bat
"C:\Program Files\QGIS 4.0.0\bin\python-qgis.bat" scripts\gen_dm_styles.py --icon-size 9
```

アイコンを dm-sprite の最新に更新するときは、`icons/` と `data/icons.csv` を差し替えてから実行してください。

## 注記について

注記（E7）のレイヤには dmconverter が自前でラベル（文字サイズ・回転・縦書き）を設定し、QML を当てないため、このリポジトリでは扱いません。

## dmconverter の仕様に合わせている点

- QML はカテゴリ分類（`categorizedSymbol`）でないと読み込まれないため、すべてカテゴリ分類で作っています
- dmconverter は、間断区分のフィルタを付けるときに「その他すべて（ELSE）」カテゴリを `(ELSE) AND "間断区分" = 0` という不正な式に変えてしまいます。そのため分類コードごとのカテゴリや ELSE カテゴリは使わず、次のようにしています
  - 点: カテゴリは1つにまとめ、SVG をデータ定義の式（分類コード → SVG の対応表）で切り替える
  - 線: `CASE` 式で「歩道・等高線・建物・その他」の4カテゴリにまとめる
  - 面: カテゴリは1つ
- dmconverter は全レイヤに同じスタイルを複製するため、カテゴリを分類コードの数だけ作ると QLR が肥大します（動作確認に使った地図情報レベル2500の GeoPackage 約 875MB では、全コードのカテゴリにすると QLR が約 250MB になりました）。上の構成では約 25MB です

## ライセンス

- このリポジトリのスタイル・スクリプト: [MIT License](LICENSE)
- `icons/` の SVG と `data/` の対応表: [dm-sprite](https://github.com/shiwaku/dm-sprite)（MIT License, Copyright (c) 2024 Geolonia, Inc.）。[icons/LICENSE](icons/LICENSE) を参照
