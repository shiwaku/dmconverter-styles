# dmconverter-styles

[MIERUNE/dmconverter](https://github.com/MIERUNE/dmconverter)（DMファイルを GeoPackage に変換する QGIS プラグイン）に指定する**スタイルフォルダ（QML）**です。地図記号のアイコンと、線・面の描き分けを補います。

dmconverter はスタイルフォルダを指定しないと、点はすべて同じマーカー、線・面はランダムな色で描かれます。このリポジトリの `styles/` を指定すると、次のように描かれます。

| 対象 | 表示 |
|---|---|
| 点（E5 記号・E6 方向） | [dm-sprite](https://github.com/shiwaku/dm-sprite) の地図記号（公共測量標準図式）を分類コードで切り替えて表示。E6 は方向角で回転。1:10,000 より小縮尺では非表示 |
| 線（E2） | 黒線を基本に、境界・道路・鉄道・建物・水部・地類界・等高線を線幅と線種で描き分け（下表） |
| 面（E1） | 塗りなし＋黒の輪郭（線と重ねる前提） |

分類コードは公共測量標準図式のものを使うので、データの提供元や地図情報レベルによらず使えます。標準図式に無い独自コードも、灰色の丸（点）や黒の実線（線）で必ず表示されます。

### 線の描き分け

| 分類 | 分類コード | 表示 |
|---|---|---|
| 境界 | 1101〜1110（都府県界〜所属界） | 黒 0.25mm 一点鎖線 |
| 地下・トンネル・建設中 | 2107, 2109, 2212, 2309, 2311〜2315, 5107 | 黒 0.2mm 点線 |
| 歩道・徒歩道 | 2103, 2213 | 黒 0.2mm 破線 |
| 鉄道 | 2301〜2305 | 黒 0.5mm |
| 建物 | 3000〜3004 | 黒 0.26mm |
| 水部 | 5101〜5106, 5111（河川・水涯線・湖池・海岸線など） | 青 0.2mm |
| 地類界 | 6201, 6301〜6303（区域界・植生界・耕地界） | 黒 0.15mm 点線 |
| 等高線（計曲線） | 7101, 7105 | 黒 0.25mm |
| 等高線（主曲線） | 7102, 7106 | 黒 0.15mm |
| 等高線（補助曲線） | 7103, 7104, 7107, 7108 | 黒 0.15mm 破線 |
| その他 | 上記以外（道路縁・独自コードなど） | 黒 0.2mm |

## 使い方

1. [Releases](https://github.com/shiwaku/dmconverter-styles/releases) から `dmconverter-styles-<版>.zip` をダウンロードして展開する（このリポジトリを clone してもよい）
2. QGIS のプロセッシングツールボックスで **DM Converter** のアルゴリズムを開き、**「入力：スタイルフォルダ（QML）」に `styles/` フォルダ**を指定する
   - **DMファイルをGeoPackageに変換**: 変換と同時にスタイルが当たる
   - **スタイルを適用してQLRを出力**: 変換済みの GeoPackage にスタイルを当て、QLR（レイヤ定義ファイル）を書き出す
3. 書き出した QLR は、QGIS にドラッグ＆ドロップするか「レイヤ」→「レイヤ定義ファイルから追加…」で開く

dmconverter が対応する QGIS 3.40〜4.x で使えます（QML は QGIS 3.34 で生成し、3.34 と 4.0 で読み込めることを確認しています）。地図記号の SVG は QML に base64 で埋め込んであるので、SVG ファイルの場所を設定する必要はありません。出力した QLR も単体で記号が表示されます。

E6 の回転（`0 - "方向角"`）と、間断区分（`"間断区分" = 0`）による非表示は dmconverter が付けるので、QML には含めていません。

## 収録内容

```
styles/                 ← dmconverter に指定するフォルダ（QML 以外は置かない）
  dm_point.qml          点（E5・E6）
  dm_line.qml           線（E2）
  dm_polygon.qml        面（E1）
.github/workflows/      v* タグの push で styles/ の ZIP をリリースに添付
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
- 1:10,000 より小縮尺（広域表示）では記号が重なって読めなくなるため描きません。dmconverter は QML のレンダラーだけを使い、レイヤの縮尺表示設定は引き継がないので、記号の「有効」をデータ定義の式（`@map_scale`）で切り替えています

## 作り直す

アイコンの更新、表示サイズや記号を隠す縮尺の変更、線の描き分けの変更（スクリプト内の `LINE_GROUPS`）は、QGIS 同梱の Python で生成スクリプトを実行します。QGIS 3.34 以降で動きます。

```bat
rem Windows（<版> は入っている QGIS のフォルダ名。LTR 版は python-qgis-ltr.bat）
"C:\Program Files\QGIS <版>\bin\python-qgis.bat" scripts\gen_dm_styles.py --icon-size 9 --point-max-scale 10000
```

```sh
# macOS / Linux（qgis.core を import できる QGIS の Python で）
python3 scripts/gen_dm_styles.py --icon-size 9 --point-max-scale 10000
```

| オプション | 既定 | 内容 |
|---|---|---|
| `--icon-size` | 9 | 地図記号の SVG キャンバスの表示サイズ（mm） |
| `--point-max-scale` | 10000 | この縮尺の分母より大縮尺のときだけ地図記号を描く。0 で常に描く |
| `--out` | `styles/` | QML の出力先フォルダ |

なるべく多くの版で読めるように、配布する QML は古い版の QGIS で生成してください（新しい版は古い版の QML を読めますが、逆は保証されません）。

## リリース

`v*` のタグを push すると、GitHub Actions が `styles/`・README・ライセンスをまとめた ZIP を添付したリリースを作ります。

```sh
git tag v1.0.0
git push origin v1.0.0
```

アイコンを dm-sprite の最新に更新するときは、`icons/` と `data/icons.csv` を差し替えてから実行してください。

## 注記について

注記（E7）のレイヤには dmconverter が自前でラベル（文字サイズ・回転・縦書き）を設定し、QML を当てないため、このリポジトリでは扱いません。

## dmconverter の仕様に合わせている点

- QML はカテゴリ分類（`categorizedSymbol`）でないと読み込まれないため、すべてカテゴリ分類で作っています
- dmconverter は、間断区分のフィルタを付けるときに「その他すべて（ELSE）」カテゴリを `(ELSE) AND "間断区分" = 0` という不正な式に変えてしまいます。そのため分類コードごとのカテゴリや ELSE カテゴリは使わず、次のようにしています
  - 点: カテゴリは1つにまとめ、SVG をデータ定義の式（分類コード → SVG の対応表）で切り替える
  - 線: `CASE` 式で分類コードを 11 のカテゴリ（上の表）にまとめる
  - 面: カテゴリは1つ
- dmconverter は全レイヤに同じスタイルを複製するため、カテゴリを分類コードの数だけ作ると QLR が肥大します（動作確認に使った地図情報レベル2500の GeoPackage 約 875MB では、全コードのカテゴリにすると QLR が約 250MB になりました）。上の構成では約 25MB です

## ライセンス

- このリポジトリのスタイル・スクリプト: [MIT License](LICENSE)
- `icons/` の SVG と `data/` の対応表: [dm-sprite](https://github.com/shiwaku/dm-sprite)（MIT License, Copyright (c) 2024 Geolonia, Inc.）。[icons/LICENSE](icons/LICENSE) を参照
