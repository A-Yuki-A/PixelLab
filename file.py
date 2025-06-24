import streamlit as st
from PIL import Image, ImageEnhance
# Disable DecompressionBombError for large zoom previews
Image.MAX_IMAGE_PIXELS = None
import io
import os
import tempfile
import pandas as pd
import random  # for dynamic questions

# --- ページ設定とカスタムCSS ---
st.set_page_config(page_title="PixelLab", layout="centered")
st.markdown(
    """
   <style>
   /* アプリ背景 */
   [data-testid="stAppViewContainer"] { background-color: #f5f5f5; }
   /* コンテナ背景 */
   div.block-container { background-color: #fcfcfc; padding: 1.5rem; border-radius: 10px; }
   /* 大見出し */
   h1 { color: #333333; }
   /* セクション見出し */
   h2 { background-color: #f0f0f0; padding: 0.4rem; border-left: 4px solid #cccccc; border-radius: 4px; }
   /* サブ見出し */
   h3 { background-color: #f0f0f0; padding: 0.3rem; border-left: 4px solid #cccccc; border-radius: 4px; }
   /* Expanderヘッダー */
   .stExpanderHeader { background-color: #eeeeee !important; border-radius: 4px; }
   /* ボタン */
   button[data-baseweb="button"] { background-color: #e0f7fa !important; color: #000; border: 1px solid #b2ebf2 !important; border-radius: 5px; padding: 0.5rem 1rem; }
   </style>
    """,
    unsafe_allow_html=True
)

st.title("PixelLab")
st.write("JPEG ファイルをアップロードして、各種画像データをチェックできます。")

# --- 画像アップロード ---
uploaded = st.file_uploader("JPEG をアップロード", type=["jpg", "jpeg"])
if uploaded:
    # 画像読み込み
    orig_img = Image.open(io.BytesIO(uploaded.read()))
    orig_w, orig_h = orig_img.size

    # 明るさ／コントラスト調整
    st.subheader("画像調整")
    st.write("明るさやコントラストを変えて、画像の変化を見てみよう")
    col1, col2 = st.columns(2)
    brightness = col1.slider("明るさ", 0.5, 2.0, 1.0)
    contrast = col2.slider("コントラスト", 0.5, 2.0, 1.0)

    img = orig_img.copy()
    img = ImageEnhance.Brightness(img).enhance(brightness)
    img = ImageEnhance.Contrast(img).enhance(contrast)

    # 比較表示
    st.subheader("オリジナル と 調整後 の比較")
    img_col1, img_col2 = st.columns(2)
    img_col1.image(orig_img, caption="Uploaded JPEG")
    img_col2.image(img, caption="Adjusted Image")
    st.markdown(
        f"<p style='font-size:18px;'>元画像サイズ: {orig_w}×{orig_h} 画素 = {orig_w*orig_h:,} 総画素数</p>",
        unsafe_allow_html=True
    )

    # RGBチャンネル分解
    st.subheader("RGBチャンネル分解")
    st.write("RGBの画像を合成して、カラー画像が表示されます。")
    r, g, b = img.split()
    ch_cols = st.columns(3)
    red_img = Image.merge("RGB", (r, Image.new("L", img.size), Image.new("L", img.size)))
    green_img = Image.merge("RGB", (Image.new("L", img.size), g, Image.new("L", img.size)))
    blue_img = Image.merge("RGB", (Image.new("L", img.size), Image.new("L", img.size), b))
    ch_cols[0].image(red_img, caption="R (赤)")
    ch_cols[1].image(green_img, caption="G (緑)")
    ch_cols[2].image(blue_img, caption="B (青)")

    # 解像度比較
    st.subheader("解像度")
    st.write("解像度とは1インチ（2.54cm）にいくつの画素が並んでいるかをdpiで表します。")
    res_cols = st.columns(3)
    for col, size in zip(res_cols, [128, 64, 16]):
        low = img.resize((size, size), Image.BILINEAR)
        restored = low.resize((orig_w, orig_h), Image.NEAREST)
        col.image(restored, caption=f"{size}画素 → {orig_w}画素")

    # 階調（量子化ビット数）
    st.subheader("階調（量子化ビット数）")
    st.write(
        "階調（量子化ビット数）はRGBそれぞれを何ビットで表現するかを表しています。"
        "ビット数が減ると、画像がどのように変化しているか確認してください。"
        "※通常は赤・緑・青それぞれに8bit（256色）を割り当て、色を表現しています。"
    )
    depth_cols = st.columns(3)
    channel_bits = [5, 3, 2]
    total_bits = [15, 9, 6]
    for dcol, cb, tb in zip(depth_cols, channel_bits, total_bits):
        def quantize(x, bits=cb):
            return ((x >> (8-bits)) << (8-bits))
        rq = r.point(lambda x: quantize(x))
        gq = g.point(lambda x: quantize(x))
        bq = b.point(lambda x: quantize(x))
        img_q = Image.merge("RGB", (rq, gq, bq))
        dcol.image(img_q, caption=f"{tb}ビット（各色{cb}bit）")

    # ファイル形式の特徴
    st.subheader("ファイル形式の特徴")
    df_formats = pd.DataFrame([
        {"拡張子": "JPG", "用途": "写真", "特徴": "非可逆圧縮で自然画像に最適"},
        {"拡張子": "PNG", "用途": "イラスト、透過画像", "特徴": "可逆圧縮で透過対応"},
        {"拡張子": "GIF", "用途": "アニメーション", "特徴": "可逆圧縮で256色まで"},
        {"拡張子": "BMP", "用途": "非圧縮保存", "特徴": "シンプルな非圧縮フォーマット"},
    ])
    st.table(df_formats.set_index("拡張子"))

    # JPGとのデータ量比較
    st.subheader("JPGとのデータ量比較")
    with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=os.path.splitext(uploaded.name)[1]
        ) as tmp:
        img.save(tmp, format=img.format)
        in_path = tmp.name
    orig_size = os.path.getsize(in_path)
    sizes = {"jpg": orig_size}
    for ext, fmt in [("bmp", "BMP"), ("png", "PNG"), ("gif", "GIF")]:
        buf = io.BytesIO()
        img.save(buf, format=fmt)
        sizes[ext] = len(buf.getvalue())
    comp = {"JPG": "非可逆", "PNG": "可逆", "GIF": "可逆", "BMP": "非圧縮"}
    rows = []
    for e, s in sizes.items():
        kb = s / 1024
        dk = (s - orig_size) / 1024
        rows.append({
            "拡張子": e.upper(),
            "方式": comp[e.upper()],
            "サイズ(バイト)": f"{s:,} バイト",
            "サイズ(KB)": f"{kb:,.2f} KB",
            "差分(KB)": f"{dk:+.2f} KB"
        })
    st.table(pd.DataFrame(rows).set_index("拡張子"))
    st.write("拡張子によってファイルサイズが違うことを確認してください。")

    # 確認問題（動的出題）
    st.subheader("確認問題")

    # 問1
    w, h = random.choice([(10, 20), (12, 20), (15, 25), (20, 30), (25, 30)])
    st.write(f"**問1:** 幅が{w}画素、高さが{h}画素の画像があります。総画素数は何画素でしょうか？")
    with st.expander("解答・解説1"):
        total_px = w * h
        st.write(f"**解答：** {total_px} 画素")
        st.write(f"**解説：** {w} × {h} = {total_px} で計算します。")

    # 問2
    colors = random.choice([2, 4, 8, 16, 32, 64, 128, 256, 512, 1024])
    w2, h2 = random.choice([(50, 50), (80, 80), (100, 60), (120, 80)])
    bits = colors.bit_length() - 1
    bytes_per_pixel = bits / 8
    total_kb = w2 * h2 * bytes_per_pixel / 1024
    st.write
