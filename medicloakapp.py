import streamlit as st
import re

# ---------------------------
# MediCloak Prototype App
# ---------------------------

st.set_page_config(page_title="MediCloak", page_icon="🛡")

st.title("🛡 MediCloak - AI Privacy Protector")
st.markdown(
    """
    MediCloak is an AI-based tool that detects and hides private details in medical text.  
    Paste some medical notes below, and MediCloak will *redact sensitive info* like names, phone numbers, and dates.  
    """
)

# Input text
text = st.text_area("📑 Paste medical text here:")

# Redaction function
def redact(text):
    if not text:
        return ""
    # Example regex patterns (can be extended with NLP for advanced use)
    text = re.sub(r'\b[A-Z][a-z]+\s[A-Z][a-z]+\b', "[REDACTED NAME]", text)  # Names
    text = re.sub(r'\b\d{10}\b', "[REDACTED PHONE]", text)  # Phone numbers
    text = re.sub(r'\d{2}/\d{2}/\d{4}', "[REDACTED DATE]", text)  # Dates
    text = re.sub(r'\b\d{12}\b', "[REDACTED AADHAAR]", text)  # Aadhaar ID (India-specific)
    return text

# Button action
if st.button("🔍 Redact Now"):
    st.subheader("🔹 Original Text")
    st.write(text if text else "No input provided")

    st.subheader("🔹 Redacted Text")
    st.success(redact(text) if text else "No input provided")

# Footer
st.markdown("---")
st.caption("Made with ❤ by Team MediCloak | Hackathon Prototype")