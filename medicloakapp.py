import streamlit as st
import re
from PIL import Image
import pytesseract

st.set_page_config(page_title="MediCloak", page_icon="🛡")

st.title("🛡 MediCloak - AI Privacy Protector")
st.markdown(
    """
    MediCloak detects and hides private details in medical text.  

    You can either:
    - 📑 *Paste text* directly  
    - 📂 *Upload a medical file (image/PDF)* to extract and redact sensitive info.  
    """
)

# --- Extra keywords for address & names ---
ADDRESS_KEYWORDS = [
    "street", "road", "nagar", "colony", "hospital", 
    "clinic", "avenue", "lane", "block", "chennai", "delhi", "bangalore", "mumbai"
]

NAME_KEYWORDS = [
    "ramesh", "kumar", "sujatha", "raj", "anita", "arun"
]

# --- Dictionary-based redaction ---
def dictionary_redact(t: str) -> str:
    for word in ADDRESS_KEYWORDS:
        t = re.sub(rf"\b{word}\b", "[REDACTED ADDRESS]", t, flags=re.IGNORECASE)
    for word in NAME_KEYWORDS:
        t = re.sub(rf"\b{word}\b", "[REDACTED NAME]", t, flags=re.IGNORECASE)
    return t

# --- Regex redaction for structured PII ---
def regex_redact(t: str) -> str:
    if not t:
        return t

    # Emails
    t = re.sub(r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}', "[REDACTED EMAIL]", t)

    # Phone numbers
    t = re.sub(r'\b(?:\+91[-\s]?|0)?\d{10}\b', "[REDACTED PHONE]", t)
    t = re.sub(r'\b\d{3}[-.\s]\d{3}[-.\s]\d{4}\b', "[REDACTED PHONE]", t)

    # Aadhaar, PAN, PIN
    t = re.sub(r'\b\d{4}\s?\d{4}\s?\d{4}\b', "[REDACTED AADHAAR]", t)
    t = re.sub(r'\b[A-Z]{5}\d{4}[A-Z]\b', "[REDACTED PAN]", t)
    t = re.sub(r'\b\d{6}\b', "[REDACTED PIN]", t)

    # Dates
    t = re.sub(r'\b\d{1,2}[-/]\d{1,2}[-/]\d{2,4}\b', "[REDACTED DATE]", t)
    t = re.sub(r'\b\d{4}[-/]\d{1,2}[-/]\d{1,2}\b', "[REDACTED DATE]", t)

    # Emergency Contact (any extra phone-like number 5–10 digits)
    t = re.sub(r'\b(?:\+91[-\s]?|0)?\d{5,10}\b', "[REDACTED PHONE]", t)

    # Insurance ID (e.g., INS12345)
    t = re.sub(r'\bINS\d+\b', "[REDACTED INSURANCE ID]", t, flags=re.IGNORECASE)

    # Medical Record Number (e.g., MRN-12345 or MRN12345)
    t = re.sub(r'\bMRN[-]?\d+\b', "[REDACTED MRN]", t, flags=re.IGNORECASE)

    return t

# --- Final combined redaction ---
def redact(t: str) -> str:
    t = regex_redact(t)        # Redact structured PII
    t = dictionary_redact(t)   # Redact names & addresses
    return t

# --- Input Section ---
st.subheader("📥 Enter Medical Data")

option = st.radio("Choose input method:", ["Paste Text", "Upload File"])

text = ""

if option == "Paste Text":
    text = st.text_area("📑 Paste medical text here:", height=200)

elif option == "Upload File":
    uploaded_file = st.file_uploader("📂 Upload an image (JPG/PNG) or PDF", type=["png", "jpg", "jpeg", "pdf"])
    if uploaded_file:
        if uploaded_file.type == "application/pdf":
            st.warning("⚠ PDF support not added yet. Please upload an image for demo.")
        else:
            image = Image.open(uploaded_file)
            st.image(image, caption="Uploaded File", use_container_width=True)
            text = pytesseract.image_to_string(image)

# --- Button Action ---
if st.button("🔍 Redact Now"):
    if not text.strip():
        st.warning("⚠ Please provide some input before redacting.")
    else:
        st.subheader("🔹 Original Text")
        st.write(text)

        st.subheader("🔹 Redacted Text")
        st.success(redact(text))

# Footer
st.markdown("---")
st.caption("Made with ❤ by Team MediCloak | Hackathon Prototype")