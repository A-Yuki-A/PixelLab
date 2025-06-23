import streamlit as st
from pydub import AudioSegment
import numpy as np
import matplotlib.pyplot as plt
import librosa
import tempfile
import soundfile as sf

# ── ffmpeg/ffprobe のパス指定 ──
AudioSegment.converter = "/usr/bin/ffmpeg"
AudioSegment.ffprobe   = "/usr/bin/ffprobe"

# ── 音声ロード関数 ──
def load_mp3(uploaded_file):
    """
    MP3を一時ファイル経由で読み込み、
    正規化したNumPy配列とサンプリングレートを返す
    """
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
        tmp.write(uploaded_file.read())
        tmp_path = tmp.name
    audio = AudioSegment.from_file(tmp_path, format="mp3")
    sr = audio.frame_rate
    data = np.array(audio.get_array_of_samples(), dtype=np.float32)
    if audio.channels == 2:
        data = data.reshape((-1, 2)).mean(axis=1)
    data /= np.abs(data).max()
    return data, sr

# ── ページ設定 ──
st.set_page_config(
    page_title="WaveForge",
    layout="centered"
)

# ── アプリ本体 ──
st.title("WaveForge")  # おすすめタイトル

# ファイルアップロード
df = st.file_uploader("MP3ファイルをアップロード", type="mp3")
if not df:
    st.info("MP3ファイルをアップロードしてください。")
    st.stop()

# 音声読み込み
data, orig_sr = load_mp3(df)
duration = len(data) / orig_sr

# ── 設定変更 ──
st.write("### 設定変更")
# 指示文
st.markdown(
    f"KB＝{kb_size:,.2f}"
)
st.markdown(
    f"MB＝{mb_size:,.2f}"
)
# チャンネル説明を追加
st.write("- ステレオ(2ch): 左右2つの音声信号を同時に再生します。音に広がりがあります。")
st.write("- モノラル(1ch): 1つの音声信号で再生します。音の定位は中央になります。")
st.markdown(
    f"MB＝{mb_size:,.2f}"
)
