# 🛡 MediCloak - AI Privacy Protector

MediCloak is an AI tool that detects and hides private details in medical records so hospitals can use data safely without risking patient privacy.

---

## 🚨 Problem Statement
Medical documents often contain sensitive information.  
When processed by AI models, these details may get exposed or misused.  
Hospitals need a way to use AI safely *without leaking confidential data*.

---

## ✅ Our Solution
MediCloak detects and redacts private data like:
- Patient Names
- Phone Numbers
- IDs (e.g., Aadhaar)
- Dates & Addresses

### 🔑 Features
- Easy-to-use web app (Streamlit)
- Regex-based redaction prototype
- Extensible for NLP / OCR integration
- Ensures *AI + Privacy go hand-in-hand*

---

## 🔮 Future Enhancements
- OCR integration to process scanned medical documents
- NLP models for multilingual redaction
- Secure audit logs
- Cloud integration with EHR systems

---

## 🏃 How to Run Locally
```bash
pip install -r requirements.txt
streamlit run app.py
