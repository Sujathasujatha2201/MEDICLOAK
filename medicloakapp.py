import streamlit as st
import re

st.set_page_config(page_title="MediCloak", page_icon="🛡")

st.title("🛡 MediCloak - AI Privacy Protector")
st.markdown(
    """
    MediCloak detects and hides private details in medical text.  
    Paste some notes below, and it will redact sensitive info like *names, phone numbers, emails, IDs, dates, and addresses*.  
    """
)

# Input text box
text = st.text_area("📑 Paste medical text here:", height=200)

# --- Regex redaction for structured PII ---
def redact(t: str) -> str:
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
    # Dates (dd/mm/yyyy or yyyy-mm-dd etc.)
    t = re.sub(r'\b\d{1,2}[-/]\d{1,2}[-/]\d{2,4}\b', "[REDACTED DATE]", t)
    t = re.sub(r'\b\d{4}[-/]\d{1,2}[-/]\d{1,2}\b', "[REDACTED DATE]", t)
    return t

# --- Button Action ---
if st.button("🔍 Redact Now"):
    if not text.strip():
        st.warning("⚠ Please enter some text before redacting.")
    else:
        st.subheader("🔹 Original Text")
        st.write(text)

        st.subheader("🔹 Redacted Text")
        st.success(redact(text))

# Footer
st.markdown("---")
st.caption("Made with ❤ by Team MediCloak | Hackathon Prototype")