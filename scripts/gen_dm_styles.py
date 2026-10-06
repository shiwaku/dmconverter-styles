"""dmconverter の「スタイルを適用してQLRを出力」用に、点・線・面の QML を生成する。

見た目は shiwaku/dm-converter の qgis/*.qml に合わせる。
- 点（E5記号・E6方向）: dm-sprite（https://github.com/shiwaku/dm-sprite）の SVG を分類コードで
  切り替える。SVG は base64 で埋め込むので、QML と出力 QLR は SVG ファイル無しで表示できる。
  アイコンの無いコード（拡張DMコードを含む）は灰色の丸で描く
- 線（E2）: 黒線。歩道は破線、等高線・凹地は細線、建物は太線
- 面（E1）: 塗りなし＋黒の輪郭（線と重ねる前提）

dmconverter の制約に合わせている点:
- QML はカテゴリ分類（categorizedSymbol）でないと読まれない
- dmconverter は全レイヤに同じレンダラーを複製し、間断区分フィルタの付与で
  「その他すべて（ELSE）」カテゴリを壊す。そのため分類コードごとのカテゴリは作らず、
  点は SVG をデータ定義の式（分類コード→SVG の対応表）で切り替え、線は CASE 式で
  まとめた少数のカテゴリにする。どの分類コードでも何かしら描かれ、QLR も肥大しない
- E6 の回転（0 - "方向角"）と間断区分フィルタは dmconverter が付けるので QML には入れない
- 注記（E7）は dmconverter がラベルを直接設定し QML を当てないため、ここでは作らない

使い方（QGIS 同梱の Python で実行）:
    python-qgis.bat scripts/gen_dm_styles.py [--icon-size 9]

    icons/（dm-*.svg）と data/icons.csv を読み、styles/ に
    dm_point.qml・dm_line.qml・dm_polygon.qml を書き出す。
"""

import argparse
import base64
import csv
import os
import sys

from qgis.core import (
    Qgis,
    QgsApplication,
    QgsCategorizedSymbolRenderer,
    QgsFillSymbol,
    QgsLineSymbol,
    QgsMarkerSymbol,
    QgsProperty,
    QgsRendererCategory,
    QgsSymbolLayer,
    QgsSvgMarkerSymbolLayer,
    QgsVectorLayer,
)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STYLES = os.path.join(ROOT, "styles")
CODE_EXPR = 'left("HCODE2", 4)'

# アイコンの無いコードに使う灰色の丸。9mm のキャンバスで直径2mm 程度
FALLBACK_SVG = (
    '<svg width="64" height="64" viewBox="0 0 64 64" xmlns="http://www.w3.org/2000/svg">'
    '<circle cx="32" cy="32" r="7" fill="#808080"/></svg>'
)

# 線の描き分け（dm-converter の 都市計画基本図_線.qml と同じ。凹地の等高線も細線にする）
LINE_GROUPS = [
    ("歩道", ["2213"], {"line_style": "dash"}),
    ("等高線", ["7101", "7102", "7103", "7104", "7105", "7106", "7107"], {"line_width": "0.15"}),
    ("建物", ["3001", "3002", "3003", "3004"], {"line_width": "0.26"}),
]
LINE_OTHER = "その他"


def b64(data: bytes) -> str:
    return "base64:" + base64.b64encode(data).decode("ascii")


def quote(s: str) -> str:
    return "'" + s.replace("'", "''") + "'"


def save_qml(renderer, geom: str, path: str) -> None:
    layer = QgsVectorLayer(f"{geom}?crs=EPSG:6676&field=HCODE2:string", "dm", "memory")
    layer.setRenderer(renderer)
    _, ok = layer.saveNamedStyle(path)
    if not ok:
        raise RuntimeError(f"QMLの保存に失敗: {path}")


def standard_icons() -> dict[str, str]:
    """標準図式のアイコン（dm-<4桁>.svg）を {分類コード: base64} で返す。

    拡張DM（dm-<提供元>-<コード>.svg）は提供元ごとに意味が異なるため使わない。
    """
    icons = {}
    with open(os.path.join(ROOT, "data", "icons.csv"), encoding="utf-8") as f:
        for row in csv.DictReader(f):
            code = row["4桁コード"]
            if row["分類"] != "標準図式" or row["ファイル名"] != f"dm-{code}.svg":
                continue
            svg = os.path.join(ROOT, "icons", row["ファイル名"])
            if os.path.exists(svg):
                with open(svg, "rb") as g:
                    icons[code] = b64(g.read())
    return icons


def point_renderer(icons: dict[str, str], icon_size: float):
    fallback = b64(FALLBACK_SVG.encode("utf-8"))
    sl = QgsSvgMarkerSymbolLayer(fallback, icon_size)
    sl.setSizeUnit(Qgis.RenderUnit.Millimeters)
    pairs = ", ".join(f"{quote(code)}, {quote(data)}" for code, data in sorted(icons.items()))
    expr = f"coalesce(map_get(map({pairs}), {CODE_EXPR}), {quote(fallback)})"
    sl.setDataDefinedProperty(QgsSymbolLayer.Property.Name, QgsProperty.fromExpression(expr))
    category = QgsRendererCategory("地図記号", QgsMarkerSymbol([sl]), "地図記号（分類コードで切替）")
    return QgsCategorizedSymbolRenderer("'地図記号'", [category])


def line_renderer():
    whens = " ".join(
        f"WHEN {CODE_EXPR} IN ({', '.join(quote(c) for c in codes)}) THEN {quote(name)}"
        for name, codes, _ in LINE_GROUPS
    )
    expr = f"CASE {whens} ELSE {quote(LINE_OTHER)} END"
    categories = []
    for name, _, override in LINE_GROUPS + [(LINE_OTHER, [], {})]:
        props = {"line_color": "0,0,0,255", "line_width": "0.2", "line_width_unit": "MM",
                 "capstyle": "square", "joinstyle": "bevel", "line_style": "solid"}
        props.update(override)
        categories.append(QgsRendererCategory(name, QgsLineSymbol.createSimple(props), name))
    return QgsCategorizedSymbolRenderer(expr, categories)


def polygon_renderer():
    sym = QgsFillSymbol.createSimple({
        "style": "no", "color": "0,0,0,0", "outline_color": "0,0,0,255",
        "outline_style": "solid", "outline_width": "0.2", "outline_width_unit": "MM",
        "joinstyle": "bevel",
    })
    return QgsCategorizedSymbolRenderer("'面'", [QgsRendererCategory("面", sym, "面（輪郭のみ）")])


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--icon-size", type=float, default=9.0,
                    help="地図記号のSVGキャンバスの表示サイズ（mm）。インクは指定値の3分の1程度")
    args = ap.parse_args()

    app = QgsApplication([], False)
    app.initQgis()
    os.makedirs(STYLES, exist_ok=True)

    icons = standard_icons()
    save_qml(point_renderer(icons, args.icon_size), "Point", os.path.join(STYLES, "dm_point.qml"))
    print(f"点: 地図記号 {len(icons)}コード（それ以外は灰色の丸）")
    save_qml(line_renderer(), "LineString", os.path.join(STYLES, "dm_line.qml"))
    print(f"線: {len(LINE_GROUPS) + 1}分類（{'・'.join(g[0] for g in LINE_GROUPS)}・{LINE_OTHER}）")
    save_qml(polygon_renderer(), "Polygon", os.path.join(STYLES, "dm_polygon.qml"))
    print("面: 1分類（輪郭のみ）")
    app.exitQgis()


if __name__ == "__main__":
    main()
