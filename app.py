import os
import io
import streamlit as st
from google.cloud import texttospeech

# ==============================
# 認証
# ==============================
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "./secret.json"

# ==============================
# クライアント生成
# ==============================
client = texttospeech.TextToSpeechClient()

# ==============================
# 音声合成関数
# ==============================
def synthesize_speech(text: str, lang_code: str, voice_name: str):
    response = client.synthesize_speech(
        input=texttospeech.SynthesisInput(text=text),
        voice=texttospeech.VoiceSelectionParams(
            language_code=lang_code,
            name=voice_name
        ),
        audio_config=texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.LINEAR16
        )
    )
    return response
    
# ==============================
# 音声一覧取得（キャッシュ）
# ==============================
@st.cache_data
def get_voices(lang_code: str):
    return client.list_voices(language_code=lang_code)
    
# ==============================
# UI
# ==============================
st.title("Google Cloud Text-to-Speech Demo")
st.page_icon="🎙",
st.markdown(
    "GCP Text-to-Speech API を使用して、テキストを音声に変換します。"
)

# ---------- サイドバー ----------
st.sidebar.header("⚙ パラメータ設定")

lang_map = {
    '日本語': 'ja-JP',
    '英語': 'en-US',
}
lang_label = st.sidebar.selectbox("言語", list(lang_map.keys()))
lang_code = lang_map[lang_label]

# 音声タイプ
voice_type = st.sidebar.selectbox(
    "音声タイプ",
    ("すべて", "Chirp3", "Neural2", "Standard")
)
# 性別（※ フィルタ専用。TTS指定には使用しない）
gender_label = st.sidebar.selectbox(
    '話者の性別',
    ('すべて', 'MALE', 'FEMALE', 'NEUTRAL', 'UNSPECIFIED')
)

# ---------- 音声一覧 ----------
voices = get_voices(lang_code)

filtered_voices = [
    v for v in voices.voices
    if (
        voice_type == "すべて"
        or voice_type in v.name
    )
    and (
        gender_label == 'すべて'
        or v.ssml_gender.name == gender_label
    )
]

if not filtered_voices:
    st.sidebar.warning("条件に合う音声がありません")
    st.warning("音声タイプまたは性別を変更してください")
    st.info("左側のサイドバーで設定できます")
    st.stop()

st.sidebar.markdown("### 利用可能な音声一覧")

voice_options = {
    v.name: {
        "gender": v.ssml_gender.name,
        "rate": v.natural_sample_rate_hertz,
        "languages": v.language_codes,
    }
    for v in filtered_voices
}

selected_voice = st.sidebar.selectbox(
    "音声の選択",
    options=list(voice_options.keys())
)

info = voice_options[selected_voice]

st.sidebar.caption(
    f"""
性別: {info['gender']}  
サンプルレート: {info['rate']} Hz
"""
)

# 言語と音声の整合性チェック
# if lang_code not in info["languages"]:
#     st.sidebar.error("選択した音声はこの言語に対応していません")
#     st.stop()

# ---------- 入力 ----------
st.header("📝 入力")

input_option = st.radio(
    '入力方法',
    ('直接入力', 'テキストファイル'),
    horizontal=True
)

input_data = None

if input_option == '直接入力':
    input_data = st.text_area(
        'テキストを入力してください。', 
        'Cloud Text-to-Speech用のサンプルです。',
        height=200
    )   
else:
    uploaded_file = st.file_uploader(
        'テキストファイルをアップロード', type=['txt']
    )    
    if uploaded_file is not None:
        input_data = uploaded_file.read().decode('utf-8')

# ---------- 実行 ----------
if input_data is not None:
    if input_option == 'テキストファイル':
        with st.expander("📄 入力テキストを表示", expanded=False):
            st.write(input_data)    
        
    st.caption(f"文字数: {len(input_data)}")
    if len(input_data) > 5000:
        st.warning("文字数が多いため、料金が高くなる可能性があります")
        
    st.divider()

    run = st.button("🎧 音声合成を実行")
    status = st.empty()
    if run:
        status.write('音声合成中...')
        
        response = synthesize_speech(input_data, lang_code, selected_voice)
        
        audio_bytes = io.BytesIO(response.audio_content).read()
        st.audio(audio_bytes, format='audio/wav')
        
        status.write('完了しました！')
                
        st.download_button(
            label="音声ファイルをダウンロード",
            data=audio_bytes,
            file_name="output.wav",
            mime="audio/wav"
        )