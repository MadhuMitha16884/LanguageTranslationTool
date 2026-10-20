"""
CodeAlpha AI Internship - Task 1: Language Translation Tool
Stack: Streamlit (UI) + deep-translator (Google Translate) + gTTS (text-to-speech)
Run:   streamlit run app.py
"""

import json
import re
import time
from io import BytesIO

import streamlit as st
import streamlit.components.v1 as components
from deep_translator import GoogleTranslator, MyMemoryTranslator
from deep_translator.exceptions import (
    NotValidPayload,
    RequestError,
    TooManyRequests,
    TranslationNotFound,
)
from gtts import gTTS
from gtts.lang import tts_langs
from langdetect import detect

MAX_CHARS = 5000  # Google Translate limit per request in deep-translator

st.set_page_config(page_title="Language Translation Tool", page_icon="🌐", layout="centered")


# ----------------------------- Helpers ----------------------------- #
@st.cache_data(show_spinner=False)
def get_languages() -> dict:
    """Return {language name (Title Case): language code}."""
    langs = GoogleTranslator().get_supported_languages(as_dict=True)
    return {name.title(): code for name, code in sorted(langs.items())}


@st.cache_data(show_spinner=False)
def get_tts_languages() -> set:
    """Language codes supported by gTTS."""
    return set(tts_langs().keys())


@st.cache_data(show_spinner=False)
def _mymemory_codes() -> dict:
    return MyMemoryTranslator(source="en-GB", target="te-IN").get_supported_languages(as_dict=True)


def _chunks(text: str, limit: int = 450) -> list:
    """Split text into <=limit char pieces on sentence boundaries (MyMemory limit is 500)."""
    parts, current = [], ""
    for sent in re.split(r"(?<=[.!?\n])\s+", text):
        while len(sent) > limit:
            if current:
                parts.append(current)
                current = ""
            parts.append(sent[:limit])
            sent = sent[limit:]
        if len(current) + len(sent) + 1 > limit:
            parts.append(current)
            current = sent
        else:
            current = f"{current} {sent}".strip()
    if current:
        parts.append(current)
    return parts


def _fallback_translate(text: str, source: str, target: str) -> str:
    """MyMemory fallback. Needs a concrete source, so auto-detect with langdetect."""
    code_to_name = {v.lower(): k for k, v in GoogleTranslator().get_supported_languages(as_dict=True).items()}
    mm = _mymemory_codes()

    def to_mm(code: str) -> str:
        code = code.lower()
        name = code_to_name.get(code) or code_to_name.get(code.split("-")[0])
        if not name or name not in mm:
            raise ValueError(f"Fallback engine doesn't support '{code}'")
        return mm[name]

    if source == "auto":
        source = detect(text)
    src_mm, tgt_mm = to_mm(source), to_mm(target)
    return " ".join(
        MyMemoryTranslator(source=src_mm, target=tgt_mm).translate(c) for c in _chunks(text)
    )


def translate_text(text: str, source: str, target: str):
    """Try Google (with retries), then fall back to MyMemory. Returns (translation, engine)."""
    google_error = None
    for attempt in range(3):
        try:
            return GoogleTranslator(source=source, target=target).translate(text), "Google Translate"
        except TooManyRequests as e:
            google_error = e
            time.sleep(1.5 * (attempt + 1))
        except (RequestError, ConnectionError) as e:
            google_error = e
            break
    try:
        return _fallback_translate(text, source, target), "MyMemory (fallback)"
    except Exception:  # noqa: BLE001
        raise google_error


@st.cache_data(show_spinner=False)
def text_to_speech(text: str, lang: str) -> bytes:
    buf = BytesIO()
    gTTS(text=text, lang=lang).write_to_fp(buf)
    return buf.getvalue()


def copy_button(text: str) -> None:
    """Clipboard button (JS). Falls back to execCommand inside Streamlit's iframe."""
    payload = json.dumps(text)
    components.html(
        f"""
        <button id="copy-btn" style="
            padding:8px 16px;border:1px solid #d0d0d0;border-radius:8px;
            background:#ffffff;cursor:pointer;font-size:14px;font-family:sans-serif;">
            📋 Copy to Clipboard
        </button>
        <script>
        const text = {payload};
        const btn = document.getElementById("copy-btn");
        function fallbackCopy() {{
            const ta = document.createElement("textarea");
            ta.value = text;
            document.body.appendChild(ta);
            ta.select();
            document.execCommand("copy");
            document.body.removeChild(ta);
        }}
        btn.addEventListener("click", async () => {{
            try {{ await navigator.clipboard.writeText(text); }}
            catch (e) {{ fallbackCopy(); }}
            btn.innerText = "✅ Copied!";
            setTimeout(() => btn.innerText = "📋 Copy to Clipboard", 1800);
        }});
        </script>
        """,
        height=50,
    )


def swap_languages() -> None:
    """Swap source/target (and move the translation into the input box)."""
    if st.session_state.src_lang == "Auto Detect":
        st.session_state.swap_warning = True
        return
    st.session_state.src_lang, st.session_state.tgt_lang = (
        st.session_state.tgt_lang,
        st.session_state.src_lang,
    )
    if st.session_state.get("result"):
        st.session_state.input_text = st.session_state.result["translated"]


def clear_all() -> None:
    st.session_state.input_text = ""
    st.session_state.result = None


# ----------------------------- State ------------------------------- #
languages = get_languages()
tts_supported = get_tts_languages()
source_options = ["Auto Detect"] + list(languages.keys())
target_options = list(languages.keys())

st.session_state.setdefault("src_lang", "Auto Detect")
st.session_state.setdefault("tgt_lang", "Telugu" if "Telugu" in languages else target_options[0])
st.session_state.setdefault("input_text", "")
st.session_state.setdefault("result", None)
st.session_state.setdefault("history", [])
st.session_state.setdefault("swap_warning", False)

# ------------------------------- UI -------------------------------- #
st.title("🌐 Language Translation Tool")
st.caption("Translate text between 100+ languages • Copy result • Listen to the translation")

col_src, col_swap, col_tgt = st.columns([5, 1, 5])
with col_src:
    st.selectbox("From", source_options, key="src_lang")
with col_swap:
    st.write("")
    st.write("")
    st.button("⇄", on_click=swap_languages, help="Swap languages", use_container_width=True)
with col_tgt:
    st.selectbox("To", target_options, key="tgt_lang")

if st.session_state.swap_warning:
    st.warning("Can't swap while source is 'Auto Detect'. Pick a source language first.")
    st.session_state.swap_warning = False

st.text_area(
    "Enter text",
    key="input_text",
    height=170,
    max_chars=MAX_CHARS,
    placeholder="Type or paste the text you want to translate...",
)
st.caption(f"{len(st.session_state.input_text)} / {MAX_CHARS} characters")

btn_col1, btn_col2, _ = st.columns([2, 1, 4])
translate_clicked = btn_col1.button("Translate", type="primary", use_container_width=True)
btn_col2.button("Clear", on_click=clear_all, use_container_width=True)

# ---------------------------- Translate ---------------------------- #
if translate_clicked:
    text = st.session_state.input_text.strip()
    src_name, tgt_name = st.session_state.src_lang, st.session_state.tgt_lang

    if not text:
        st.warning("Please enter some text to translate.")
    elif src_name != "Auto Detect" and src_name == tgt_name:
        st.info("Source and target languages are the same. Choose a different target language.")
    else:
        src_code = "auto" if src_name == "Auto Detect" else languages[src_name]
        tgt_code = languages[tgt_name]
        try:
            with st.spinner("Translating..."):
                translated, engine = translate_text(text, src_code, tgt_code)
            if not translated:
                st.error("No translation returned. Try rephrasing the text.")
            else:
                st.session_state.result = {
                    "original": text,
                    "translated": translated,
                    "src_name": src_name,
                    "tgt_name": tgt_name,
                    "tgt_code": tgt_code,
                    "engine": engine,
                }
                st.session_state.history.insert(
                    0, {"from": src_name, "to": tgt_name, "original": text, "translated": translated}
                )
                st.session_state.history = st.session_state.history[:10]
        except TooManyRequests:
            st.error("Google blocked requests from your network (rate limit) and the fallback failed too. "
                     "Wait a few minutes, or switch network (e.g. mobile hotspot) and retry.")
        except (RequestError, ConnectionError):
            st.error("Network/API error. Check your internet connection and try again.")
        except (NotValidPayload, TranslationNotFound) as e:
            st.error(f"Could not translate this text: {e}")
        except Exception as e:  # noqa: BLE001
            st.error(f"Unexpected error: {e}")

# ----------------------------- Output ------------------------------ #
result = st.session_state.result
if result:
    st.subheader(f"Translation ({result['tgt_name']})")
    st.success(result["translated"])
    st.caption(f"Engine: {result.get('engine', 'Google Translate')}")

    act_col1, act_col2 = st.columns([1, 1])
    with act_col1:
        copy_button(result["translated"])
    with act_col2:
        listen = st.button("🔊 Listen")

    if listen:
        # gTTS uses a few different codes than Google Translate
        tts_code = {"iw": "iw", "zh-CN": "zh-CN", "zh-TW": "zh-TW"}.get(result["tgt_code"], result["tgt_code"])
        if tts_code not in tts_supported and tts_code.split("-")[0] in tts_supported:
            tts_code = tts_code.split("-")[0]
        if tts_code not in tts_supported:
            st.warning(f"Text-to-speech isn't available for {result['tgt_name']}.")
        else:
            try:
                with st.spinner("Generating audio..."):
                    audio = text_to_speech(result["translated"], tts_code)
                st.audio(audio, format="audio/mp3", autoplay=True)
            except Exception as e:  # noqa: BLE001
                st.error(f"Text-to-speech failed: {e}")

# ----------------------------- History ----------------------------- #
if st.session_state.history:
    with st.expander("🕘 Recent translations"):
        for item in st.session_state.history:
            st.markdown(f"**{item['from']} → {item['to']}**")
            st.text(f"{item['original']}\n→ {item['translated']}")
            st.divider()

st.markdown("---")
st.caption("Language Translation Tool")
