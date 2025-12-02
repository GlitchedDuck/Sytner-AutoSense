# Sytner AutoSense - Professional POC
import streamlit as st
from PIL import Image, ImageOps
import io, datetime, json, re

# -------------------------
# OCR Libraries
# -------------------------
EASYOCR_AVAILABLE = False
PYTESSERACT_AVAILABLE = False
try:
    import easyocr
    EASYOCR_AVAILABLE = True
except Exception:
    EASYOCR_AVAILABLE = False

try:
    import pytesseract
    PYTESSERACT_AVAILABLE = True
except Exception:
    PYTESSERACT_AVAILABLE = False

# -------------------------
# Mock / Placeholder Helpers
# -------------------------
def lookup_vehicle_basic(reg):
    reg = reg.upper().replace(" ", "")
    return {
        "reg": reg,
        "make": "BMW",
        "model": "3 Series",
        "year": 2018,
        "vin": "WBA8BFAKEVIN12345",
        "mileage": 54000
    }

def lookup_mot_and_tax(reg):
    today = datetime.date.today()
    return {
        "mot_next_due": (today + datetime.timedelta(days=120)).isoformat(),
        "mot_history": [
            {"date": "2024-08-17", "result": "Pass", "mileage": 52000},
            {"date": "2023-08-10", "result": "Advisory", "mileage": 48000},
        ],
        "tax_expiry": (today + datetime.timedelta(days=30)).isoformat(),
    }

def lookup_recalls(reg_or_vin):
    return [{"id": "R-2023-001", "summary": "Airbag inflator recall - replace module", "open": True}]

def lookup_history_flags(reg):
    return {"write_off": False, "theft": False, "mileage_anomaly": True, "note": "Mileage shows a 5,000 jump in 2021 record"}

def estimate_value(make, model, year, mileage, condition="good"):
    age = datetime.date.today().year - year
    base = 25000 - (age * 2000) - (mileage / 10)
    cond_multiplier = {"excellent": 1.05, "good": 1.0, "fair": 0.9, "poor": 0.8}
    return max(100, int(base * cond_multiplier.get(condition, 1.0)))

# Plate regex - permissive for UK plates and VIN-ish strings
PLATE_REGEX = re.compile(r"[A-Z0-9]{5,10}", re.I)

# -------------------------
# OCR Helper
# -------------------------
def run_easyocr(pil_image):
    reader = easyocr.Reader(["en"], gpu=False)
    with io.BytesIO() as buf:
        pil_image.save(buf, format="JPEG")
        data = buf.getvalue()
    results = reader.readtext(data)
    texts = [t[1] for t in results if len(t[1]) >= 3]
    return texts

def run_pytesseract(pil_image):
    gray = ImageOps.grayscale(pil_image)
    gray = ImageOps.autocontrast(gray)
    try:
        txt = pytesseract.image_to_string(gray, config="--psm 6")
    except Exception:
        txt = ""
    return [l.strip() for l in txt.splitlines() if l.strip()]

def run_ocr(pil_image, prefer_easyocr=True):
    if EASYOCR_AVAILABLE and prefer_easyocr:
        return run_easyocr(pil_image)
    elif PYTESSERACT_AVAILABLE:
        return run_pytesseract(pil_image)
    elif EASYOCR_AVAILABLE:
        return run_easyocr(pil_image)
    return []

# -------------------------
# Streamlit UI Config
# -------------------------
st.set_page_config(page_title="Sytner AutoSense", page_icon="🚗", layout="centered")
PRIMARY = "#0b3b6f"
ACCENT = "#1e90ff"

# Header
st.markdown(f"""
<div style="display:flex;align-items:center;gap:12px">
  <div style="background:{PRIMARY};padding:10px 14px;border-radius:8px;color:white;font-weight:700;">Sytner</div>
  <div style="font-size:22px;font-weight:700;color:{PRIMARY};">AutoSense — POC</div>
</div>
""", unsafe_allow_html=True)

st.write("POC with OCR (EasyOCR preferred, falls back to pytesseract). Mocked API adapters for vehicle, MOT, recalls, valuation.")

# Sidebar controls
with st.sidebar:
    st.header("POC Controls")
    prefer_easyocr = st.checkbox("Prefer EasyOCR (if installed)", value=True)
    enable_ocr = st.checkbox("Enable OCR", value=(EASYOCR_AVAILABLE or PYTESSERACT_AVAILABLE))
    st.markdown("---")
    st.write("OCR libraries available:")
    st.write(f"- EasyOCR: {'✅' if EASYOCR_AVAILABLE else '❌'}")
    st.write(f"- pytesseract: {'✅' if PYTESSERACT_AVAILABLE else '❌'}")
    st.markdown("---")
    st.write("Developer notes:")
    st.write("- Replace lookup_* functions with real API adapters for DVLA, MOT, HPI/CAP etc.")
    st.write("- Add GDPR consent before live lookups.")

# -------------------------
# 1) Capture / Input Registration
# -------------------------
st.markdown("## 1) Capture or enter registration / VIN")
col1, col2 = st.columns([2,1])
with col1:
    camera_img = st.camera_input("Use camera (mobile recommended) or upload photo")
    uploaded = st.file_uploader("Upload image", type=["png","jpg","jpeg"])
with col2:
    manual_reg = st.text_input("Or type registration / VIN manually", placeholder="KT68XYZ or VIN...")

image = None
if camera_img: image = Image.open(camera_img)
elif uploaded: image = Image.open(uploaded)

detected_candidates = []
ocr_raw_text = ""

if image and enable_ocr:
    st.markdown("**Image preview**")
    st.image(ImageOps.exif_transpose(image), width=320)
    with st.spinner("Running OCR..."):
        try:
            ocr_texts = run_ocr(image, prefer_easyocr)
            ocr_raw_text = "\n".join(ocr_texts)
            st.text_area("Raw OCR output", value=ocr_raw_text, height=140)
            # Filter plausible plate/VIN candidates
            for t in ocr_texts:
                candidate = re.sub(r'[^A-Z0-9]', '', t.upper())
                if PLATE_REGEX.match(candidate):
                    detected_candidates.append(candidate)
            seen = set()
            detected_candidates = [x for x in detected_candidates if not (x in seen or seen.add(x))]
        except Exception as e:
            st.error(f"OCR failed: {e}")
elif image and not enable_ocr:
    st.image(ImageOps.exif_transpose(image), width=320)
    st.info("OCR disabled - enable in sidebar to extract plate text.")

# User selects OCR candidate or manual input
choice = None
if detected_candidates:
    st.markdown("**OCR candidates**")
    pick = st.selectbox("Choose OCR candidate", options=["-- pick --"] + detected_candidates)
    if pick != "-- pick --": choice = pick
if manual_reg: choice = manual_reg.strip().upper().replace(" ", "")

if not choice:
    st.info("Provide a registration (camera/upload or manual) to proceed.")
    st.stop()

reg = choice
st.success(f"Using registration: **{reg}**")
st.markdown("---")

# -------------------------
# 2) Fetch Mocked Data
# -------------------------
vehicle = lookup_vehicle_basic(reg)
mot_tax = lookup_mot_and_tax(reg)
recalls = lookup_recalls(reg)
history_flags = lookup_history_flags(reg)
condition = st.radio("Condition for valuation", ["excellent", "good", "fair", "poor"], index=1, horizontal=True)
value = estimate_value(vehicle["make"], vehicle["model"], vehicle["year"], vehicle["mileage"], condition)

# -------------------------
# 3) Vehicle Summary (Card Metrics)
# -------------------------
st.markdown("## 2) Vehicle Summary")
col1, col2, col3 = st.columns(3)
col1.metric("Estimated Value", f"£{value:,}", condition.capitalize())
col2.metric("Next MOT", mot_tax['mot_next_due'])
col3.metric("Open Recalls", sum(1 for r in recalls if r['open']))

st.markdown("### Vehicle Details")
st.write(f"- **Make/Model:** {vehicle['make']} {vehicle['model']}")
st.write(f"- **Year / VIN:** {vehicle['year']} / {vehicle['vin']}")
st.write(f"- **Mileage:** {vehicle['mileage']} miles")
if history_flags.get('write_off'): st.error("⚠ This vehicle has a previous write-off record")
if history_flags.get('theft'): st.error("⚠ This vehicle has a theft record")
if history_flags.get('mileage_anomaly'): st.warning(f"⚠ {history_flags.get('note','Mileage anomaly detected')}")

# -------------------------
# 4) Expanders for Details
# -------------------------
with st.expander("MOT History"):
    for t in mot_tax['mot_history']:
        st.write(f"- {t['date']}: **{t['result']}** — {t['mileage']} miles")

with st.expander("Recalls"):
    if any(r['open'] for r in recalls):
        for r in recalls:
            if r['open']:
                st.warning(f"Open recall: {r['summary']} — ID: {r['id']}")
    else:
        st.success("No open recalls found")

with st.expander("Insurance (mock)"):
    st.info("Insurance quotes are mocked. Integrate aggregator APIs for live quotes.")
    if st.button('Get a mock insurance quote'):
        st.success('Sample quote: £320/year (3rd party, excess £250)')

# -------------------------
# 5) Snapshot Download
# -------------------------
st.markdown('---')
snapshot = {
    'vehicle': vehicle,
    'mot_tax': mot_tax,
    'recalls': recalls,
    'history_flags': history_flags,
    'valuation': {'value': value, 'condition': condition},
    'queried_at': datetime.datetime.utcnow().isoformat()
}
st.download_button('Download JSON snapshot', data=json.dumps(snapshot, indent=2),
                   file_name=f"{reg}_snapshot.json", mime='application/json')

st.markdown('## Notes / Next Steps')
st.write("""
- Enable EasyOCR: `pip install easyocr` (requires PyTorch).
- Enable pytesseract: `pip install pytesseract` and install Tesseract-OCR binary.
- Replace lookup_* functions with real API adapters for DVLA, MOT, HPI/CAP etc.
- Add explicit consent (GDPR) before calling live APIs.
""")
