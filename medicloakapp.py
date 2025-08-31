import streamlit as st
from PIL import Image
import pytesseract
import pdfplumber
import re

st.set_page_config(page_title="MedicLoak - Medical Data Cloaking", layout="wide")
st.title("🩺 MedicLoak - Hide Sensitive Medical Data")

st.write("Upload *PDF or Image*. The app will automatically redact sensitive info like names, phone numbers, emails, IDs, and any extra words you specify.")

# File uploader
uploaded_file = st.file_uploader("Upload PDF or Image", type=["pdf", "png", "jpg", "jpeg"])

# Extra keywords
extra_keywords = st.text_area("Extra words to redact (comma separated):", "")

# Function to auto-detect sensitive info
def auto_redact(text):
    patterns = {
        "phone": r"\b\d{10}\b",  # 10-digit numbers
        "email": r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+",
        "date": r"\b\d{2}/\d{2}/\d{4}\b|\b\d{4}-\d{2}-\d{2}\b",  # DD/MM/YYYY or YYYY-MM-DD
        "id": r"\bID[:\s]?\d+\b"
    }
    for label, pattern in patterns.items():
        text = re.sub(pattern, "████", text)
    return text

if uploaded_file is not None:
    extracted_text = ""

    if uploaded_file.type == "application/pdf":
        with pdfplumber.open(uploaded_file) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    extracted_text += page_text + "\n"
    else:
        image = Image.open(uploaded_file)
        extracted_text = pytesseract.image_to_string(image)

    st.subheader("Extracted Text:")
    st.text_area("Original Text", extracted_text, height=300)

    if st.button("Redact Information"):
        redacted_text = auto_redact(extracted_text)

        if extra_keywords.strip():
            keywords = [kw.strip() for kw in extra_keywords.split(",") if kw.strip()]
            for kw in keywords:
                redacted_text = redacted_text.replace(kw, "████")

        st.subheader("Redacted Text:")
        st.text_area("Redacted Output", redacted_text, height=300)

        st.download_button(
            label="Download Redacted Text",
            data=redacted_text,
            file_name="redacted_text.txt",
            mime="text/plain"
        )