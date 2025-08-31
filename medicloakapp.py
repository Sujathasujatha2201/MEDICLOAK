import streamlit as st
import pdfplumber
from PIL import Image
import io

st.title("🔒 Medical Report Redactor")
st.write("Upload your medical reports (PDF or Image) and redact sensitive info.")

# File upload
uploaded_file = st.file_uploader("Upload a file", type=["pdf", "jpg", "jpeg", "png"])

if uploaded_file:
    if uploaded_file.type == "application/pdf":
        st.subheader("PDF Uploaded")
        text_content = ""
        with pdfplumber.open(uploaded_file) as pdf:
            for page in pdf.pages:
                text_content += page.extract_text() + "\n"

        st.text_area("Extracted Text", text_content, height=300)

        # Redaction input
        sensitive_text = st.text_area("Enter words to redact (comma-separated):")
        if st.button("Redact PDF"):
            if sensitive_text:
                words_to_redact = [w.strip() for w in sensitive_text.split(",")]
                redacted_text = text_content
                for word in words_to_redact:
                    redacted_text = redacted_text.replace(word, "[REDACTED]")
                st.text_area("Redacted Text", redacted_text, height=300)
            else:
                st.warning("Please enter at least one word to redact.")

    else:
        st.subheader("Image Uploaded")
        image = Image.open(uploaded_file)
        st.image(image, caption="Original Image", use_column_width=True)
        st.write("Currently, image redaction is manual. (Coming soon: automatic text detection!)")