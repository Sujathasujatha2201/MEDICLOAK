import streamlit as st
import re
import spacy

# ---------------------------
# MediCloak Prototype App
# ---------------------------

st.set_page_config(page_title="MediCloak", page_icon="🛡")

st.title("🛡 MediCloak - AI Privacy Protector")
st.markdown(
    """
    MediCloak is an AI-based tool that detects and hides private details in medical text.  
    Paste some medical notes below, and MediCloak will *redact sensitive info* like **names, phone numbers, emails, IDs, dates, and addresses**.  
    """
)

# Input text box
text = st.text_area("📑 Paste medical text here:", height=200)

# --- Load spaCy model ---
nlp = spacy.load("en_core_web_sm")

# --- Regex redaction for structured PII ---
def regex_redact(t: str) -> str:
    if not t:
        return t
    # Emails
    t = re.sub(r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}', "[REDACTED EMAIL]", t)
    # Phone numbers (+91, 10-digits, 3-3-4 format)
    t = re.sub(r'\b(?:\+91[-\s]?|0)?\d{10}\b', "[REDACTED PHONE]", t)
    t = re.sub(r'\b\d{3}[-.\s]\d{3}[-.\s]\d{4}\b', "[REDACTED PHONE]", t)
    # Aadhaar (12 digits)
    t = re.sub(r'\b\d{4}\s?\d{4}\s?\d{4}\b', "[REDACTED AADHAAR]", t)
    # PAN (ABCDE1234F format)
    t = re.sub(r'\b[A-Z]{5}\d{4}[A-Z]\b', "[REDACTED PAN]", t)
    # PIN code (6 digits)
    t = re.sub(r'\b\d{6}\b', "[REDACTED PIN]", t)
    # Dates (dd/mm/yyyy, dd-mm-yyyy, yyyy-mm-dd)
    t = re.sub(r'\b\d{1,2}[-/]\d{1,2}[-/]\d{2,4}\b', "[REDACTED DATE]", t)
    t = re.sub(r'\b\d{4}[-/]\d{1,2}[-/]\d{1,2}\b', "[REDACTED DATE]", t)
    return t

# --- Combined redaction (regex + spaCy NER) ---
def redact(t: str) -> str:
    if not t:
        return ""
    # Apply regex first
    t = regex_redact(t)
    # Apply spaCy NER for names, addresses, orgs, cities, dates
    doc = nlp(t)
    redacted = t
    for ent in reversed(doc.ents):
        if ent.label_ in ["PERSON", "GPE", "LOC", "ORG", "DATE"]:
            redacted = redacted[:ent.start_char] + f"[REDACTED {ent.label_}]" + redacted[ent.end_char:]
    return redacted

# --- Button Action ---
if st.button("🔍 Redact Now"):
    if not text.strip():
        st.warning("⚠️ Please enter some text before redacting.")
    else:
        st.subheader("🔹 Original Text")
        st.write(text)

        st.subheader("🔹 Redacted Text")
        st.success(redact(text))

# Footer
st.markdown("---")
st.caption("Made with ❤ by Team MediCloak | Hackathon Prototype")
