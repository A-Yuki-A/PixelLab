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

    # オリジナルと調整後
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
    ch_cols[0].image(Image.merge("RGB", (r, Image.new("L", img.size), Image.new("L", img.size))), caption="R (赤)")
    ch_cols[1].image(Image.merge("RGB", (Image.new("L", img.size), g, Image.new("L", img.size))), caption="G (緑)")
    ch_cols[2].image(Image.merge("RGB", (Image.new("L", img.size), Image.new("L", img.size), b)), caption="B (青)")

    # ディスプレイ解像度のシミュレーション
    st.subheader("ディスプレイ解像度のシミュレーション")
    st.write("1インチ（2.54cm）あたりのピクセル数(PPI)が異なると、同じ表示サイズでも見え方が変わります。")
    ppi_values = [10, 50, 200]
    ppi_labels = ["低解像度 (10 PPI)", "中解像度 (50 PPI)", "高解像度 (200 PPI)"]
    ppi_cols = st.columns(3)
    display_cm = 10  # 表示幅10cm
    inch = display_cm / 2.54
    for col, ppi, label in zip(ppi_cols, ppi_values, ppi_labels):
        w_ppi = int(ppi * inch)
        h_ppi = int(w_ppi * orig_h / orig_w)
        small = img.resize((w_ppi, h_ppi), Image.BILINEAR)
        restored = small.resize((orig_w, orig_h), Image.NEAREST)
        col.image(restored, caption=label, use_container_width=True)

    # 階調（量子化ビット数）
    st.subheader("階調（量子化ビット数）")
    st.write(
        "RGBの各色を何ビットで表現するかを示します。ビット数を減らすと、色の滑らかさが変化します。通常の画像は各色8ビットの合計24ビット（フルカラー）で表示されます。"
    )
    depth_cols = st.columns(3)
    for col, bits in zip(depth_cols, [5, 3, 2]):
        def q(x, b=bits): return ((x >> (8-b)) << (8-b))
        r_q = r.point(lambda px: q(px))
        g_q = g.point(lambda px: q(px))
        b_q = b.point(lambda px: q(px))
        col.image(Image.merge("RGB", (r_q, g_q, b_q)), caption=f"{bits*3}ビット（各色{bits}bit）")

    # ファイル形式の特徴
    st.subheader("ファイル形式の特徴")
    df_f = pd.DataFrame([
        {"拡張子": "JPG", "用途": "写真", "特徴": "非可逆圧縮で自然画像に最適"},
        {"拡張子": "PNG", "用途": "イラスト・透過画像", "特徴": "可逆圧縮で透過対応"},
        {"拡張子": "GIF", "用途": "アニメーション", "特徴": "可逆圧縮で256色まで"},
        {"拡張子": "BMP", "用途": "非圧縮保存", "特徴": "シンプルな非圧縮フォーマット"},
    ])
    st.table(df_f.set_index("拡張子"))

    # JPGとのデータ量比較
    st.subheader("JPGとのデータ量比較")
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded.name)[1]) as tmp:
        img.save(tmp, format=img.format)
        in_p = tmp.name
    orig_s = os.path.getsize(in_p)
    sizes = {"JPG": orig_s}
    for ext, fmt in [("PNG","PNG"),("GIF","GIF"),("BMP","BMP")]:
        buf = io.BytesIO(); img.save(buf, format=fmt)
        sizes[ext] = len(buf.getvalue())
    comp = {"JPG":"非可逆","PNG":"可逆","GIF":"可逆","BMP":"非圧縮"}
    rows = []
    for e, s in sizes.items(): rows.append({"形式":e,"方式":comp[e],"サイズ(KB)":f"{s/1024:.2f}"})
    st.table(pd.DataFrame(rows).set_index("形式"))

    # 確認問題（動的出題）
    st.subheader("確認問題")
    # 問1
    w,h = random.choice([(10,20),(12,20),(15,25)])
    st.write(f"**問1:** {w}×{h} 画素の画像の総画素数は？")
    with st.expander("解答・解説1"):
        st.write(f"{w}×{h}={w*h} 画素")
    # 問2: ビット数
    c = random.choice([16,64,256,1024])
    b = c.bit_length()-1
    st.write(f"**問2:** 1画素で{c}色を表現するには何ビット必要？")
    with st.expander("解答・解説2"):
        st.write(f"2^{b}={c} より {b}ビットが必要")
    # 問3: データ量
    cols_num = random.choice([2,4,8,16,32])
    w2,h2 = random.choice([(50,50),(80,80),(100,60)])
    bits2 = cols_num.bit_length()-1
    kb = w2*h2*bits2/8/1024
    st.write(f"**問3:** {w2}×{h2}画素, {cols_num}色の画像のデータ量(KB)は？")
    with st.expander("解答・解説3"):
        st.write(f"総ビット数={w2*h2*bits2} → バイト={w2*h2*bits2/8:.2f} → KB={kb:.2f}")

    # 一時ファイル削除
    try: os.remove(in_p)
    except: pass
