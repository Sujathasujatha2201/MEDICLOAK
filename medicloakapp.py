# medicloakapp.py
import streamlit as st
from PIL import Image, ImageDraw
import pytesseract
import fitz  # PyMuPDF
import io
import re
import tempfile
import base64
import os

st.set_page_config(page_title="MediCloak - Auto OCR Redactor", layout="wide", page_icon="🛡")
st.title("🛡 MediCloak — Automatic Redaction for Medical Scans")
st.write(
    "Upload images or scanned PDFs. MediCloak will extract text, automatically redact common PII (phones, emails, dates, IDs), "
    "and optionally redact values after labels like Name: or Address:. You can also provide manual keywords."
)

# ---------------------------
# Utility: regex detectors
# ---------------------------
PHONE_RE = re.compile(r'(\+?\d{1,3}[-\s]?)?(?:\d{10}|\d{5}[-\s]\d{5}|\d{3}[-.\s]\d{3}[-.\s]\d{4})')
EMAIL_RE = re.compile(r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}')
DATE_RE = re.compile(r'\b\d{1,2}[-/]\d{1,2}[-/]\d{2,4}\b')
AADHAAR_RE = re.compile(r'\b\d{4}\s?\d{4}\s?\d{4}\b')
PAN_RE = re.compile(r'\b[A-Z]{5}\d{4}[A-Z]\b', re.IGNORECASE)
MRN_RE = re.compile(r'\bMRN[-]?\d+\b', re.IGNORECASE)
INS_RE = re.compile(r'\bINS[-_ ]?\d+\b', re.IGNORECASE)
PINCODE_RE = re.compile(r'\b\d{6}\b')

# labels to detect values after them
LABELS = [
    r'patient name', r'patient', r'name', r'phone', r'mobile', r'mobile no', r'contact',
    r'email', r'address', r'addr', r'age', r'dob'
]
LABEL_RE = re.compile(r'(' + r'|'.join(LABELS) + r')\s*[:\-]?\s*', re.IGNORECASE)

# ---------------------------
# Helpers
# ---------------------------
def find_sensitive_values(text):
    """
    Return set/list of substrings in text that should be redacted.
    Uses regex detectors and label-based heuristics.
    """
    found = set()

    # regex-based matches
    for rx in [EMAIL_RE, PHONE_RE, DATE_RE, AADHAAR_RE, PAN_RE, MRN_RE, INS_RE, PINCODE_RE]:
        for m in rx.finditer(text):
            # add the exact matched substring
            found.add(m.group().strip())

    # label-based heuristics: find 'Name: X', 'Address: X' and add the X portion (until newline)
    for m in re.finditer(r'(?P<label>' + r'|'.join(LABELS) + r')\s*[:\-]?\s*(?P<val>.+)', text, re.IGNORECASE):
        val = m.group('val').strip()
        # only take up to end of line or next period if large
        val_line = val.splitlines()[0].split('  ')[0]
        # trim long trailing context (like 'Diagnosis:')
        val_line = re.split(r'\s{2,}|\t|\r|\n', val_line)[0]
        # sometimes there's "Name: John Doe Age: 45" — stop at 'Age' label
        val_line = re.split(r'\b(Age|DOB|Diagnosis|Phone|Contact|Address|Email|MRN|ID)\b', val_line, flags=re.IGNORECASE)[0].strip()
        if val_line:
            # split into words and add different granular substrings
            words = val_line.split()
            # add full and partial phrases
            found.add(val_line)
            if len(words) <= 4:
                # also add each word (useful for visual token matching)
                for w in words:
                    found.add(w.strip().strip(':,'))
            else:
                # add first two words (common for names)
                found.add(' '.join(words[:2]))

    # Clean small tokens
    found_clean = {s for s in found if len(s) >= 2}
    return found_clean

def redact_text_only(text, manual_keywords=None):
    """
    Return redacted text (string) and set/list of detected sensitive substrings.
    Manual keywords (comma-separated list) are also removed.
    """
    manual_keywords = manual_keywords or []
    sensitive = find_sensitive_values(text)
    redacted = text

    # Replace regex matches first with █████
    for rx in [EMAIL_RE, PHONE_RE, DATE_RE, AADHAAR_RE, PAN_RE, MRN_RE, INS_RE, PINCODE_RE]:
        redacted = rx.sub("████", redacted)

    # Replace label-value heuristics: e.g., "Name: John Doe" => "Name: ████"
    def _label_replacer(match):
        label = match.group(0)
        # replace the value portion after label with ███ up to newline
        # use a simple approach: find the label and then mask until newline
        return re.sub(r'(?P<label>' + r'|'.join(LABELS) + r')\s*[:\-]?\s*(?P<val>.+)', lambda mm: mm.group(0).split(':')[0] + ': ████', match.group(0), flags=re.IGNORECASE)

    # Simpler manual approach: mask values after common label occurrences line-by-line
    lines = redacted.splitlines()
    new_lines = []
    for ln in lines:
        ln_stripped = ln.strip()
        # if line has label at start, mask the part after colon
        label_match = re.match(r'^\s*(' + r'|'.join(LABELS) + r')\s*[:\-]\s*(.+)$', ln, re.IGNORECASE)
        if label_match:
            lbl = label_match.group(1)
            new_lines.append(f"{lbl}: ████")
        else:
            # also mask "Name John Doe" patterns
            inline_match = re.search(r'\b(' + r'|'.join(LABELS) + r')\b\s*(?:[:\-]?\s*)([A-Za-z0-9 ,.-]+)', ln, re.IGNORECASE)
            if inline_match:
                lbl = inline_match.group(1)
                new_lines.append(re.sub(r'(' + re.escape(inline_match.group(2)) + r')', '████', ln, flags=re.IGNORECASE))
            else:
                new_lines.append(ln)
    redacted = "\n".join(new_lines)

    # Finally, apply manual keyword redaction
    for kw in manual_keywords:
        kw = kw.strip()
        if not kw:
            continue
        redacted = re.sub(re.escape(kw), "████", redacted, flags=re.IGNORECASE)

    # Also ensure regex patterns covered everything
    for rx in [EMAIL_RE, PHONE_RE, DATE_RE, AADHAAR_RE, PAN_RE, MRN_RE, INS_RE, PINCODE_RE]:
        redacted = rx.sub("████", redacted)

    # Recompute sensitive substrings from original text for visual redaction guidance
    sensitive_substrings = find_sensitive_values(text)
    # add manual keywords themselves
    for kw in manual_keywords:
        if kw.strip():
            sensitive_substrings.add(kw.strip())

    return redacted, sensitive_substrings

# ---------------------------
# Image visual redaction
# ---------------------------
def redact_image_visual(pil_img, sensitive_substrings):
    """
    Given a PIL image and set of sensitive substrings, runs OCR with bounding boxes
    and draws black rectangles over tokens that match sensitive substrings or follow
    label tokens like 'Name' -> next tokens.
    Returns redacted PIL image and a list of redacted bbox info.
    """
    img_rgb = pil_img.convert("RGB")
    draw = ImageDraw.Draw(img_rgb)
    # get detailed OCR data
    data = pytesseract.image_to_data(img_rgb, output_type=pytesseract.Output.DICT)
    n_boxes = len(data['level'])
    redacted_boxes = []

    # Build lowercase sensitive set for matching
    sens_lower = {s.lower() for s in sensitive_substrings}

    # iterate tokens
    prev_word = ""
    for i in range(n_boxes):
        word = data['text'][i].strip()
        if not word:
            prev_word = ""
            continue
        word_low = word.lower()

        left = data['left'][i]
        top = data['top'][i]
        width = data['width'][i]
        height = data['height'][i]
        right = left + width
        bottom = top + height

        should_mask = False

        # direct match (token contained in any sensitive substring)
        if word_low in sens_lower:
            should_mask = True

        # partial: if any sensitive substring contains this token
        for s in sens_lower:
            if word_low and word_low in s and len(word_low) >= 2:
                should_mask = True
                break

        # regex detectors on token
        if PHONE_RE.search(word) or EMAIL_RE.search(word) or AADHAAR_RE.search(word) or PAN_RE.search(word) or MRN_RE.search(word) or INS_RE.search(word) or DATE_RE.search(word) or PINCODE_RE.search(word):
            should_mask = True

        # label-following heuristic: if previous token is a label, mask this token
        if prev_word and re.match(r'(' + r'|'.join(LABELS) + r')', prev_word, re.IGNORECASE):
            should_mask = True

        if should_mask:
            # draw filled rectangle (black)
            draw.rectangle(((left, top), (right, bottom)), fill="black")
            redacted_boxes.append(((left, top, right, bottom), word))
        prev_word = word

    return img_rgb, redacted_boxes

# ---------------------------
# PDF helpers: extract text & render pages to PIL images
# ---------------------------
def extract_text_from_pdf_bytes(pdf_bytes):
    text = ""
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    for page in doc:
        try:
            page_text = page.get_text("text")
            if page_text:
                text += page_text + "\n"
        except Exception:
            pass
    doc.close()
    return text

def render_pdf_pages_to_images(pdf_bytes, zoom=2):
    """Return list of PIL Images (one per page) rendered from PDF using PyMuPDF."""
    imgs = []
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    for page in doc:
        mat = fitz.Matrix(zoom, zoom)  # zoom for higher resolution
        pix = page.get_pixmap(matrix=mat, alpha=False)
        img_data = pix.tobytes("png")
        pil_img = Image.open(io.BytesIO(img_data)).convert("RGB")
        imgs.append(pil_img)
    doc.close()
    return imgs

# ---------------------------
# Copy to clipboard helper (Streamlit component)
# ---------------------------
import streamlit.components.v1 as components
def copy_button(text, button_text="Copy to clipboard"):
    """
    Renders a small HTML button that copies text to the clipboard.
    """
    text_b64 = base64.b64encode(text.encode()).decode()
    component = f"""
    <button id="copybtn">{button_text}</button>
    <script>
    const b=document.getElementById("copybtn");
    b.addEventListener("click",async ()=>{{
      const text = atob("{text_b64}");
      await navigator.clipboard.writeText(text);
      b.innerText = "Copied!";
      setTimeout(()=>{{b.innerText = "{button_text}";}},2000);
    }});
    </script>
    <style>
      #copybtn {{ background:#4CAF50; color:white; padding:6px 10px; border-radius:6px; border:none; cursor:pointer; }}
      #copybtn:active {{ transform: translateY(1px); }}
    </style>
    """
    components.html(component, height=40)

# ---------------------------
# Streamlit UI & main flow
# ---------------------------
st.sidebar.header("Options")
manual_kw_input = st.sidebar.text_area("Manual keywords to redact (comma separated):", value="")
auto_visual = st.sidebar.checkbox("Enable visual redaction on images / scanned PDF pages", value=True)
download_pdf_images = st.sidebar.checkbox("Return a redacted PDF (for scanned PDFs)", value=True)

uploaded = st.file_uploader("Upload a scanned PDF or image (PNG/JPG).", type=["pdf", "png", "jpg", "jpeg"])

if uploaded is None:
    st.info("Upload an image or scanned PDF to begin. You can also paste text in the 'Paste text' panel below.")
# Also allow manual text paste (user may paste text with PHI)
paste_text = st.text_area("Or paste text here (optional):", height=120)

if uploaded is not None or paste_text.strip():
    extracted_text = ""
    page_images = []

    if uploaded is not None:
        bytes_data = uploaded.read()
        if uploaded.type == "application/pdf":
            # Extract text from PDF and render pages (for visual redaction)
            try:
                extracted_text = extract_text_from_pdf_bytes(bytes_data)
            except Exception as e:
                st.warning("Could not extract text from PDF using PyMuPDF. Falling back to page rendering + OCR.")
                extracted_text = ""
            # Render pages to images if visual redaction or if no text extracted
            try:
                page_images = render_pdf_pages_to_images(bytes_data, zoom=2)
            except Exception as e:
                st.error(f"Error rendering PDF pages: {e}")
        else:
            # Image: open as PIL
            try:
                pil = Image.open(io.BytesIO(bytes_data)).convert("RGB")
                page_images = [pil]
                # OCR to extract text
                extracted_text = pytesseract.image_to_string(pil)
            except Exception as e:
                st.error(f"Could not open image: {e}")

    # If user pasted text, prefer that appended to extracted_text
    if paste_text and paste_text.strip():
        # Append user-provided text (so they can paste and redact without uploading)
        extracted_text = (extracted_text + "\n" + paste_text).strip()

    st.subheader("Extracted Text")
    st.text_area("Extracted (editable):", extracted_text, height=240, key="extracted_area")

    # Redaction action
    if st.button("🔍 Redact Automatically"):
        manual_keywords = [k.strip() for k in manual_kw_input.split(",") if k.strip()]
        redacted_text, sensitive_substrings = redact_text_only(extracted_text, manual_keywords)

        st.subheader("Redacted Text")
        st.text_area("Redacted", redacted_text, height=240, key="redacted_area")

        # copy buttons
        st.write("Copy / Download:")
        copy_button(redacted_text, button_text="Copy Redacted Text")
        st.download_button("⬇ Download Redacted Text", redacted_text, file_name="redacted_text.txt", mime="text/plain")

        # Visual redaction for images / PDF pages
        if auto_visual and page_images:
            st.subheader("Visual Redaction — redacted images")
            redacted_page_imgs = []
            for idx, pil_img in enumerate(page_images):
                pil_redacted, boxes = redact_image_visual(pil_img, sensitive_substrings)
                st.image(pil_redacted, caption=f"Page {idx+1} — visually redacted", use_column_width=True)
                redacted_page_imgs.append(pil_redacted)

            # If user wants a redacted PDF and there are images to combine
            if download_pdf_images and redacted_page_imgs:
                # Save images into a single PDF in memory
                with io.BytesIO() as pdf_buf:
                    # PIL save requires all images in RGB and first.save(..., save_all=True, append_images=[...])
                    first, rest = redacted_page_imgs[0], redacted_page_imgs[1:]
                    first.save(pdf_buf, format="PDF", save_all=True, append_images=rest)
                    pdf_bytes = pdf_buf.getvalue()
                    st.download_button("⬇ Download Redacted PDF (scanned)", pdf_bytes, file_name="redacted_scanned.pdf", mime="application/pdf")

        st.success("Redaction completed. Review text and images above.")
        st.info("Note: visual redaction masks tokens detected by OCR. Very small or handwritten text may not be detected accurately.")