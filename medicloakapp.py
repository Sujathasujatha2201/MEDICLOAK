import streamlit as st
import re
import fitz  # PyMuPDF
from PIL import Image
import pytesseract
import io

# --- Streamlit page config ---
st.set_page_config(page_title="MediCloak", page_icon="🛡")
st.title("🛡 MediCloak - AI Privacy Protector")
st.markdown(
    """
Upload a PDF, Image, or Text file, or paste your notes below.  
MediCloak will redact *names, phone numbers, emails, IDs, dates, addresses, insurance IDs, MRNs*, and other sensitive info.
"""
)

# --- Tesseract path (Windows only, uncomment if needed) ---
# pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# --- Keywords for dictionary-based redaction ---
ADDRESS_KEYWORDS = ["street","road","nagar","colony","hospital","clinic","avenue","lane","block","chennai","delhi","bangalore","mumbai"]
NAME_KEYWORDS = ["ramesh","kumar","sujatha","raj","anita","arun"]

# --- Redaction functions ---
def dictionary_redact(t: str) -> str:
    for word in ADDRESS_KEYWORDS:
        t = re.sub(rf"\b{word}\b", "[REDACTED ADDRESS]", t, flags=re.IGNORECASE)
    for word in NAME_KEYWORDS:
        t = re.sub(rf"\b{word}\b", "[REDACTED NAME]", t, flags=re.IGNORECASE)
    return t

def regex_redact(t: str) -> str:
    if not t: return t
    t = re.sub(r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}', "[REDACTED EMAIL]", t)
    t = re.sub(r'\b(?:\+91[-\s]?|0)?\d{10}\b', "[REDACTED PHONE]", t)
    t = re.sub(r'\b\d{3}[-.\s]\d{3}[-.\s]\d{4}\b', "[REDACTED PHONE]", t)
    t = re.sub(r'\b\d{4}\s?\d{4}\s?\d{4}\b', "[REDACTED AADHAAR]", t)
    t = re.sub(r'\b[A-Z]{5}\d{4}[A-Z]\b', "[REDACTED PAN]", t)
    t = re.sub(r'\b\d{6}\b', "[REDACTED PIN]", t)
    t = re.sub(r'\b\d{1,2}[-/]\d{1,2}[-/]\d{2,4}\b', "[REDACTED DATE]", t)
    t = re.sub(r'\b\d{4}[-/]\d{1,2}[-/]\d{1,2}\b', "[REDACTED DATE]", t)
    t = re.sub(r'\b(?:\+91[-\s]?|0)?\d{5,10}\b', "[REDACTED PHONE]", t)
    t = re.sub(r'\bINS\d+\b', "[REDACTED INSURANCE ID]", t, flags=re.IGNORECASE)
    t = re.sub(r'\bMRN[-]?\d+\b', "[REDACTED MRN]", t, flags=re.IGNORECASE)
    return t

def redact(t: str) -> str:
    t = regex_redact(t)
    t = dictionary_redact(t)
    return t

# --- File uploader & text input ---
uploaded_file = st.file_uploader("Upload PDF / Image / Text", type=["pdf","png","jpg","jpeg","txt"])
manual_text = st.text_area("Or paste your text here:")

text_to_process = ""

# --- Extract text from uploaded file ---
if uploaded_file:
    fname = uploaded_file.name.lower()
    # PDF
    if fname.endswith(".pdf"):
        try:
            doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
            pages = [page.get_text() for page in doc]
            text_to_process = "\n\n".join(pages)
        except Exception as e:
            st.error(f"Error reading PDF: {e}")
    # Image
    elif fname.endswith((".png",".jpg",".jpeg")):
        try:
            image = Image.open(uploaded_file).convert("RGB")
            text_to_process = pytesseract.image_to_string(image)
        except Exception as e:
            st.error(f"Error reading image: {e}")
    # Text file
    elif fname.endswith(".txt"):
        try:
            raw = uploaded_file.read()
            text_to_process = raw.decode("utf-8", errors="ignore")
        except Exception as e:
            st.error(f"Error reading text file: {e}")
    else:
        st.error("Unsupported file type.")

elif manual_text:
    text_to_process = manual_text

# --- Redact button ---
if st.button("🔍 Redact Now"):
    if not text_to_process.strip():
        st.warning("⚠ Please provide some text or upload a file.")
    else:
        st.subheader("🔹 Original Text")
        st.text_area("Original:", text_to_process, height=250)

        st.subheader("🔹 Redacted Text")
        redacted = redact(text_to_process)
        st.text_area("Redacted:", redacted, height=250)

        # Download redacted text
        st.download_button("⬇ Download Redacted Text", redacted, file_name="redacted.txt")

# Footer
st.markdown("---")
st.caption("Made with ❤ by Team MediCloak | Hackathon Prototype")