import streamlit as st
import easyocr
import fitz  # PyMuPDF
from pdf2image import convert_from_path
from PIL import Image
import re
import spacy
import io

# Load NLP model
nlp = spacy.load("en_core_web_sm")

# Initialize OCR
reader = easyocr.Reader(['en'])

# --- Functions ---
def extract_text_from_image(image):
    result = reader.readtext(image, detail=0)
    return " ".join(result)

def extract_text_from_pdf(file):
    text = ""
    doc = fitz.open(stream=file.read(), filetype="pdf")
    for page in doc:
        text += page.get_text()
    return text

def redact_text(text):
    # Basic regex for common PII
    patterns = {
        "Aadhaar": r"\b\d{4}\s\d{4}\s\d{4}\b",
        "Phone": r"\b\d{10}\b",
        "Email": r"[\w\.-]+@[\w\.-]+\.\w+",
        "Date": r"\b\d{2}[-/]\d{2}[-/]\d{4}\b"
    }

    for label, pattern in patterns.items():
        text = re.sub(pattern, f"[REDACTED {label}]", text)

    # Use spaCy for names and locations
    doc = nlp(text)
    for ent in doc.ents:
        if ent.label_ in ["PERSON", "GPE", "ORG"]:
            text = text.replace(ent.text, "[REDACTED]")
    return text

def download_text_file(content, filename="redacted_report.txt"):
    return io.BytesIO(content.encode("utf-8"))

# --- Streamlit UI ---
st.title("Medical Report PII Redactor")
st.write("Upload a *medical report (PDF/Image/Text)* and redact sensitive information.")

uploaded_file = st.file_uploader("Upload File", type=["pdf", "png", "jpg", "jpeg", "txt"])

if uploaded_file:
    file_type = uploaded_file.type

    if "image" in file_type:
        image = Image.open(uploaded_file)
        st.image(image, caption="Uploaded Image", use_column_width=True)
        extracted_text = extract_text_from_image(uploaded_file)
    elif "pdf" in file_type:
        extracted_text = extract_text_from_pdf(uploaded_file)
    else:
        extracted_text = uploaded_file.read().decode("utf-8")

    st.subheader("Extracted Text")
    st.text_area("Original Text", extracted_text, height=200)

    if st.button("Redact PII"):
        redacted_text = redact_text(extracted_text)
        st.subheader("Redacted Text")
        st.text_area("Output", redacted_text, height=200)

        # Download button
        st.download_button("Download Redacted Text", download_text_file(redacted_text), file_name="redacted_report.txt")