import streamlit as st
import re

# Try to import spaCy (optional). If not available, app still works using regex.
try:
    import spacy
    try:
        nlp = spacy.load("en_core_web_sm")
    except Exception:
        # Model not available; set nlp to None (we won't crash)
        nlp = None
except Exception:
    nlp = None

st.set_page_config(page_title="MediCloak", page_icon="🛡")
st.title("🛡 MediCloak - AI Privacy Protector")
st.markdown(
    """
    Paste medical notes below. MediCloak redacts common PII (names, phones, emails, dates, Aadhaar, PAN, PIN, simple addresses).
    If spaCy model en_core_web_sm is available, NER will be used to help redact names/locations.
    """
)

text = st.text_area("📑 Paste medical text here:", height=250)

# --- Regex-based redaction (fast, works without extra libs) ---
def regex_redact(t: str) -> str:
    if not t:
        return ""

    # Emails
    t = re.sub(r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}', "[REDACTED EMAIL]", t)

    # Phone numbers (simple patterns including optional +91)
    t = re.sub(r'\b(?:\+91[-\s]?|0)?\d{10}\b', "[REDACTED PHONE]", t)
    t = re.sub(r'\b\d{3}[-.\s]\d{3}[-.\s]\d{4}\b', "[REDACTED PHONE]", t)

    # Aadhaar (12 digits, allow spaces)
    t = re.sub(r'\b\d{4}\s?\d{4}\s?\d{4}\b', "[REDACTED AADHAAR]", t)

    # PAN (India) e.g., ABCDE1234F
    t = re.sub(r'\b[A-Z]{5}\d{4}[A-Z]\b', "[REDACTED PAN]", t)

    # PIN code (6 digits - India)
    t = re.sub(r'\b\d{6}\b', "[REDACTED PIN]", t)

    # Dates dd/mm/yyyy or dd-mm-yyyy or yyyy-mm-dd
    t = re.sub(r'\b\d{1,2}[-/]\d{1,2}[-/]\d{2,4}\b', "[REDACTED DATE]", t)
    t = re.sub(r'\b\d{4}[-/]\d{1,2}[-/]\d{1,2}\b', "[REDACTED DATE]", t)

    # Simple addresses (street/road/avenue/nagar/colony etc.)
    t = re.sub(
        r'\b\d{1,4}\s+[A-Za-z0-9\.,\s]{1,80}\b(?:Street|St|Road|Rd|Avenue|Ave|Nagar|Colony|Lane|Ln|Block|Sector|City|Town)\b',
        "[REDACTED ADDRESS]", t, flags=re.IGNORECASE
    )

    # Names (basic: Two capitalized words). This is simple — NER is better.
    t = re.sub(r'\b[A-Z][a-z]{2,}\s[A-Z][a-z]{2,}\b', "[REDACTED NAME]", t)

    return t

# --- spaCy-based NER redaction (optional, better accuracy for names/locations) ---
def spacy_redact(t: str) -> str:
    if not nlp:
        return t
    doc = nlp(t)
    redacted = t
    # iterate reversed so indices don't shift for remaining ents
    for ent in reversed(doc.ents):
        label = ent.label_
        if label in ("PERSON", "GPE", "LOC", "ORG", "DATE", "TIME", "MONEY", "FAC"):
            start, end = ent.start_char, ent.end_char
            redacted = redacted[:start] + f"[REDACTED_{label}]" + redacted[end:]
    return redacted

# Option to enable spaCy NER if available
use_spacy = st.checkbox("Use spaCy NER if available (may slow load)", value=False)

if st.button("🔍 Redact Now"):
    if not text:
        st.warning("Please paste some medical text to redact.")
    else:
        st.subheader("🔹 Original Text")
        st.write(text)

        # First apply spaCy (if requested and available), then regex to catch structured PII
        if use_spacy and nlp is not None:
            out = spacy_redact(text)
            out = regex_redact(out)
        else:
            out = regex_redact(text)

        st.subheader("🔹 Redacted Text")
        st.success(out)

st.markdown("---")
if nlp is None:
    st.info("spaCy model not loaded. For better name/location detection, install spaCy and the 'en_core_web_sm' model.")
st.caption("Made with ❤ by Team MediCloak | Hackathon Prototype")