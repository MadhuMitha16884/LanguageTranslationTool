# CodeAlpha_LanguageTranslationTool

AI Internship (CodeAlpha) - Task 1: Language Translation Tool

Streamlit web app that translates text between 100+ languages using `deep-translator` (Google Translate), with copy-to-clipboard and text-to-speech (gTTS).

## Features
- Text input with source (incl. Auto Detect) and target language selection
- Swap languages button
- Clear translated output
- Copy to Clipboard button
- Listen (text-to-speech) for the translated text
- Recent translation history (last 10, per session)
- Error handling for empty input, network issues, rate limits

## Setup

Requires Python 3.9+ and an internet connection.

```bash
# 1. (Optional) create a virtual environment
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the app
streamlit run app.py
```

The app opens at http://localhost:8501

## Project structure
```
CodeAlpha_LanguageTranslationTool/
├── app.py
├── requirements.txt
└── README.md
```

## Notes
- Max 5000 characters per translation (Google Translate limit).
- Text-to-speech depends on gTTS language support; unsupported languages show a warning.
- Uses the free Google Translate endpoint via deep-translator; if Google rate-limits your IP (429), the app retries and then falls back to MyMemory automatically.
