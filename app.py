import streamlit as st
import requests
import trafilatura
import google.generativeai as genai
from gtts import gTTS
import tempfile
import os
import uuid

# =========================================
# GEMINI API
# =========================================


GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
genai.configure(api_key=GEMINI_API_KEY)
# =========================================
# STREAMLIT AYARLARI
# =========================================

st.set_page_config(
    page_title="AI Haber Podcast",
    page_icon="🎙️",
    layout="centered"
)

st.title("🎙️ AI Haber Podcast")
st.write("Bir haber linki yapıştırın ve otomatik podcast oluşturun.")

# =========================================
# HABER METNİ ÇEKME
# =========================================

def haber_metni_cek(url):

    try:
        headers = {
            "User-Agent": "Mozilla/5.0"
        }

        response = requests.get(
            url,
            headers=headers,
            timeout=15
        )

        if response.status_code != 200:
            return None

        downloaded = trafilatura.extract(
            response.text,
            include_comments=False,
            include_tables=False
        )

        if not downloaded:
            return None

        temiz_metin = downloaded.strip()

        if len(temiz_metin) < 200:
            return None

        return temiz_metin[:5000]

    except Exception as e:
        st.error(f"Haber çekme hatası: {e}")
        return None

# =========================================
# PODCAST SENARYOSU ÜRET
# =========================================

def podcast_senaryosu_uret(haber_metni, format_secimi):

    model = genai.GenerativeModel("gemini-1.5-flash")

    if format_secimi == "Tek Sunucu":

        prompt = f"""
        Sen profesyonel bir podcast sunucususun.

        Aşağıdaki haberi:
        - doğal
        - akıcı
        - samimi
        - podcast tarzında

        anlat.

        Çok uzun olmasın.
        Gereksiz tekrar yapma.
        Sadece podcast metni üret.

        Haber:
        {haber_metni}
        """

    else:

        prompt = f"""
        Sen profesyonel bir haber podcasti yazarıısın.

        Aşağıdaki haberi
        Emel ve Ahmet isimli iki sunucunun sohbet ettiği doğal bir podcast formatına dönüştür.

        Kurallar:
        - Doğal konuşsunlar
        - Haber spikeri gibi olmasın
        - Kısa tut
        - Samimi olsun

        Format:

        Emel: ...
        Ahmet: ...

        Haber:
        {haber_metni}
        """

    response = model.generate_content(prompt)

    return response.text

# =========================================
# SES OLUŞTUR
# =========================================

def podcast_sesi_olustur(metin):

    try:

        dosya_adi = f"{uuid.uuid4()}.mp3"

        temp_dir = tempfile.gettempdir()

        dosya_yolu = os.path.join(temp_dir, dosya_adi)

        tts = gTTS(
            text=metin,
            lang="tr",
            slow=False
        )

        tts.save(dosya_yolu)

        return dosya_yolu

    except Exception as e:
        st.error(f"Ses oluşturma hatası: {e}")
        return None

# =========================================
# KULLANICI ARAYÜZÜ
# =========================================

url_input = st.text_input(
    "📰 Haber URL'si"
)

format_secimi = st.selectbox(
    "🎧 Podcast Formatı",
    [
        "Tek Sunucu",
        "Çift Sunucu"
    ]
)

# =========================================
# PODCAST OLUŞTUR
# =========================================

if st.button("🎙️ Podcast Oluştur"):

    if not url_input:

        st.warning("Lütfen haber linki girin.")

    else:

        with st.spinner("Haber çekiliyor..."):

            haber_metni = haber_metni_cek(url_input)

        if not haber_metni:

            st.error("Haber metni alınamadı.")

        else:

            st.success("Haber başarıyla çekildi.")

            with st.spinner("Podcast senaryosu yazılıyor..."):

                podcast_metni = podcast_senaryosu_uret(
                    haber_metni,
                    format_secimi
                )

            st.subheader("📝 Podcast Metni")

            st.write(podcast_metni)

            with st.spinner("Podcast sesi oluşturuluyor..."):

                ses_dosyasi = podcast_sesi_olustur(
                    podcast_metni
                )

            if ses_dosyasi:

                st.success("🎉 Podcast hazır!")

                st.audio(ses_dosyasi)

                with open(ses_dosyasi, "rb") as file:

                    st.download_button(
                        label="⬇️ Podcast İndir",
                        data=file,
                        file_name="podcast.mp3",
                        mime="audio/mp3"
                    )