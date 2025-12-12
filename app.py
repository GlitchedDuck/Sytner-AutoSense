import json
from pathlib import Path
import random
import string
import streamlit as st
from PIL import Image, ImageOps
import datetime
import re

# ============================================================================
# CONFIGURATION
# ============================================================================

PRIMARY = "#0b3b6f"
ACCENT = "#1e90ff"
PAGE_BG = "#e6f0fa"

PLATE_REGEX = re.compile(r"[A-Z0-9]{5,10}", re.I)

# Sales Pipeline Stages
SALES_STAGES = [
    {"name": "Deposit Taken", "icon": "💰", "color": "#4caf50"},
    {"name": "Demands & Needs", "icon": "📋", "color": "#2196f3"},
    {"name": "Sign/Ink Order", "icon": "✍️", "color": "#9c27b0"},
    {"name": "Sell Option Extras", "icon": "🎁", "color": "#ff9800"},
    {"name": "Collection Day", "icon": "🚗", "color": "#f44336"}
]

GARAGES = [
    "Sytner BMW Cardiff - 285-287 Penarth Road",
    "Sytner BMW Chigwell - Langston Road, Loughton",
    "Sytner BMW Coventry - 128 Holyhead Road",
    "Sytner BMW Harold Wood - A12 Colchester Road",
    "Sytner BMW High Wycombe - 575-647 London Road",
    "Sytner BMW Leicester - Meridian East",
    "Sytner BMW Luton - 501 Dunstable Road",
    "Sytner BMW Maidenhead - Bath Road",
    "Sytner BMW Newport - Oak Way",
    "Sytner BMW Nottingham - Lenton Lane",
    "Sytner BMW Oldbury - 919 Wolverhampton Road",
    "Sytner BMW Sheffield - Brightside Way",
    "Sytner BMW Shrewsbury - 70 Battlefield Road",
    "Sytner BMW Solihull - 520 Highlands Road",
    "Sytner BMW Stevenage - Arlington Business Park",
    "Sytner BMW Sunningdale - Station Road",
    "Sytner BMW Swansea - 375 Carmarthen Road",
    "Sytner BMW Tamworth - Winchester Rd",
    "Sytner BMW Tring - Cow Roast",
    "Sytner BMW Warwick - Fusiliers Way",
    "Sytner BMW Wolverhampton - Lever Street",
    "Sytner BMW Worcester - Knightsbridge Park"
]

# GPS coordinates for each garage
GARAGE_COORDS = {
    "Sytner BMW Cardiff": (51.4695, -3.1792),
    "Sytner BMW Chigwell": (51.6460, 0.0750),
    "Sytner BMW Coventry": (52.4162, -1.5121),
    "Sytner BMW Harold Wood": (51.6089, 0.2458),
    "Sytner BMW High Wycombe": (51.6248, -0.7489),
    "Sytner BMW Leicester": (52.6111, -1.1175),
    "Sytner BMW Luton": (51.8929, -0.4372),
    "Sytner BMW Maidenhead": (51.5225, -0.6433),
    "Sytner BMW Newport": (51.5665, -2.9871),
    "Sytner BMW Nottingham": (52.9536, -1.1358),
    "Sytner BMW Oldbury": (52.5050, -2.0150),
    "Sytner BMW Sheffield": (53.4059, -1.4016),
    "Sytner BMW Shrewsbury": (52.7280, -2.7350),
    "Sytner BMW Solihull": (52.4114, -1.7869),
    "Sytner BMW Stevenage": (51.9020, -0.2050),
    "Sytner BMW Sunningdale": (51.3989, -0.6600),
    "Sytner BMW Swansea": (51.6565, -3.9900),
    "Sytner BMW Tamworth": (52.6342, -1.6950),
    "Sytner BMW Tring": (51.7950, -0.6600),
    "Sytner BMW Warwick": (52.2819, -1.5850),
    "Sytner BMW Wolverhampton": (52.5867, -2.1280),
    "Sytner BMW Worcester": (52.1936, -2.2200)
}

TIME_SLOTS = ["09:00 AM", "11:00 AM", "02:00 PM", "04:00 PM"]

# ============================================================================
# MOCK API FUNCTIONS
# ============================================================================

def calculate_distance(lat1, lon1, lat2, lon2):
    """Calculate distance between two GPS coordinates using Haversine formula (in miles)"""
    from math import radians, sin, cos, sqrt, atan2
    
    R = 3959  # Earth's radius in miles
    
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    distance = R * c
    
    return distance

def find_nearest_garage(user_lat, user_lon):
    """Find the nearest Sytner garage based on GPS coordinates"""
    nearest_garage = None
    min_distance = float('inf')
    
    for garage_name, (lat, lon) in GARAGE_COORDS.items():
        distance = calculate_distance(user_lat, user_lon, lat, lon)
        if distance < min_distance:
            min_distance = distance
            nearest_garage = garage_name
    
    for garage in GARAGES:
        if garage.startswith(nearest_garage):
            return garage, min_distance
    
    return None, None

def lookup_vehicle_basic(reg):
    """Mock vehicle lookup"""
    reg_clean = reg.upper().replace(" ", "")
    return {
        "reg": reg_clean,
        "make": "BMW",
        "model": "3 Series",
        "year": 2018,
        "vin": "WBA8BFAKEVIN12345",
        "mileage": 54000
    }

def lookup_mot_and_tax(reg):
    """Mock MOT and tax lookup"""
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
    """Mock recall lookup"""
    return [
        {"id": "R-2023-001", "summary": "Airbag inflator recall - replace module", "open": True},
        {"id": "R-2022-012", "summary": "Steering column check", "open": False}
    ]

def get_history_flags(reg):
    """Mock history check"""
    return {
        "write_off": False,
        "theft": False,
        "mileage_anomaly": True,
        "note": "Mileage shows a 5,000 jump in 2021 record"
    }

def estimate_value(make, model, year, mileage, condition="good"):
    """Mock valuation"""
    age = datetime.date.today().year - year
    base = 25000 - (age * 2000) - (mileage / 10)
    cond_multiplier = {"excellent": 1.05, "good": 1.0, "fair": 0.9, "poor": 0.8}
    return max(100, int(base * cond_multiplier.get(condition, 1.0)))

def mock_ocr_numberplate(image):
    """Mock OCR"""
    return "KT68XYZ"

# ============================================================================
# SALES CHECK-IN DATA FUNCTIONS
# ============================================================================

def load_sales_data():
    """Load sales check-in data from JSON file"""
    try:
        sales_file = Path("data/sales_records.json")
        if sales_file.exists():
            with open(sales_file, 'r') as f:
                return json.load(f)
        return []
    except Exception as e:
        st.error(f"Error loading sales data: {e}")
        return []

def generate_tracking_id():
    """Generate unique tracking ID"""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=12))

def save_customer_journey(journey_data):
    """Save new customer journey"""
    try:
        journeys_file = Path("data/customer_journeys.json")
        journeys_file.parent.mkdir(exist_ok=True)
        
        if journeys_file.exists():
            with open(journeys_file, 'r') as f:
                journeys = json.load(f)
        else:
            journeys = []
        
        journeys.append(journey_data)
        
        with open(journeys_file, 'w') as f:
            json.dump(journeys, f, indent=2)
        
        return True
    except Exception as e:
        st.warning(f"Could not save journey: {e}")
        return False

def get_journey_by_tracking_id(tracking_id):
    """Get journey by tracking ID"""
    try:
        journeys_file = Path("data/customer_journeys.json")
        if journeys_file.exists():
            with open(journeys_file, 'r') as f:
                journeys = json.load(f)
            for journey in journeys:
                if journey.get('tracking_id') == tracking_id:
                    return journey
    except:
        pass
    return None

# ============================================================================
# VALIDATION FUNCTIONS
# ============================================================================

def validate_registration(reg):
    """Validate UK registration format"""
    if not reg:
        return False
    reg_clean = reg.upper().replace(" ", "")
    return len(reg_clean) >= 5 and re.match(r'^[A-Z0-9]+$', reg_clean)

def validate_phone(phone):
    """Basic phone validation"""
    return phone and len(phone.strip()) >= 10

# ============================================================================
# SESSION STATE MANAGEMENT
# ============================================================================

def init_session_state():
    """Initialize all session state variables"""
    defaults = {
        "reg": None,
        "image": None,
        "show_summary": False,
        "vehicle_data": None,
        "booking_forms": {},
        "create_journey_mode": False,
        "journey_data": {},
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

def reset_all_state():
    """Reset all session state to initial values"""
    st.session_state.reg = None
    st.session_state.image = None
    st.session_state.show_summary = False
    st.session_state.vehicle_data = None
    st.session_state.booking_forms = {}

# ============================================================================
# ANIMATED WHEEL TRACKER
# ============================================================================

def render_wheel_tracker(current_stage_index, stages):
    """Render an animated car wheel progress tracker"""
    
    total_stages = len(stages)
    progress_percent = ((current_stage_index + 1) / total_stages) * 100
    rotation = (progress_percent / 100) * 360
    current_stage = stages[current_stage_index]
    
    st.markdown(f"""
    <style>
    @keyframes pulse {{
        0%, 100% {{ transform: scale(1); }}
        50% {{ transform: scale(1.05); }}
    }}
    
    .wheel-container {{
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding: 40px 20px;
        background: linear-gradient(135deg, {PRIMARY} 0%, {ACCENT} 100%);
        border-radius: 20px;
        margin: 20px 0;
    }}
    
    .wheel-wrapper {{
        position: relative;
        width: 280px;
        height: 280px;
        margin-bottom: 30px;
    }}
    
    .wheel-outer {{
        position: absolute;
        width: 100%;
        height: 100%;
        border-radius: 50%;
        background: linear-gradient(135deg, #2c3e50 0%, #34495e 100%);
        box-shadow: 0 10px 40px rgba(0,0,0,0.3),
                    inset 0 0 20px rgba(255,255,255,0.1);
        transform: rotate({rotation}deg);
        transition: transform 1s ease-out;
    }}
    
    .wheel-rim {{
        position: absolute;
        width: 90%;
        height: 90%;
        top: 5%;
        left: 5%;
        border-radius: 50%;
        background: conic-gradient(
            from 0deg,
            #3498db 0deg,
            #2ecc71 {progress_percent * 3.6}deg,
            #95a5a6 {progress_percent * 3.6}deg,
            #7f8c8d 360deg
        );
        box-shadow: inset 0 0 30px rgba(0,0,0,0.4);
    }}
    
    .wheel-center {{
        position: absolute;
        width: 50%;
        height: 50%;
        top: 25%;
        left: 25%;
        border-radius: 50%;
        background: linear-gradient(135deg, #ecf0f1 0%, #bdc3c7 100%);
        box-shadow: 0 5px 15px rgba(0,0,0,0.3),
                    inset 0 0 10px rgba(255,255,255,0.5);
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 48px;
        animation: pulse 2s ease-in-out infinite;
    }}
    
    .progress-text {{
        color: white;
        text-align: center;
    }}
    
    .stage-name {{
        font-size: 24px;
        font-weight: 700;
        margin-bottom: 5px;
    }}
    
    .progress-percent {{
        font-size: 48px;
        font-weight: 900;
        margin-top: 10px;
    }}
    
    .stage-dots {{
        display: flex;
        justify-content: center;
        gap: 15px;
        margin-top: 20px;
        flex-wrap: wrap;
    }}
    
    .stage-dot {{
        width: 50px;
        height: 50px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 24px;
        transition: all 0.3s ease;
        border: 3px solid rgba(255,255,255,0.3);
    }}
    
    .stage-dot.completed {{
        background-color: #4caf50;
        border-color: #4caf50;
        box-shadow: 0 0 20px rgba(76, 175, 80, 0.5);
    }}
    
    .stage-dot.current {{
        background-color: white;
        border-color: white;
        animation: pulse 1.5s ease-in-out infinite;
        box-shadow: 0 0 30px rgba(255, 255, 255, 0.8);
    }}
    
    .stage-dot.pending {{
        background-color: rgba(255,255,255,0.2);
        border-color: rgba(255,255,255,0.3);
    }}
    </style>
    
    <div class="wheel-container">
        <div class="wheel-wrapper">
            <div class="wheel-outer">
                <div class="wheel-rim"></div>
                <div class="wheel-center">
                    {current_stage['icon']}
                </div>
            </div>
        </div>
        
        <div class="progress-text">
            <div class="stage-name">{current_stage['name']}</div>
            <div style="font-size: 16px; opacity: 0.9;">Stage {current_stage_index + 1} of {total_stages}</div>
            <div class="progress-percent">{progress_percent:.0f}%</div>
        </div>
        
        <div class="stage-dots">
    """, unsafe_allow_html=True)
    
    for idx, stage in enumerate(stages):
        if idx < current_stage_index:
            dot_class = "completed"
        elif idx == current_stage_index:
            dot_class = "current"
        else:
            dot_class = "pending"
        
        st.markdown(f"""
            <div class="stage-dot {dot_class}" title="{stage['name']}">
                {stage['icon']}
            </div>
        """, unsafe_allow_html=True)
    
    st.markdown("</div></div>", unsafe_allow_html=True)

# ============================================================================
# STYLING
# ============================================================================

def apply_custom_css():
    """Apply custom CSS styling"""
    st.markdown(f"""
    <style>
    [data-testid="stAppViewContainer"] {{
        background-color: {PAGE_BG};
    }}
    .header-card {{
        background-color: {PRIMARY};
        color: white;
        padding: 16px 24px;
        border-radius: 12px;
        font-size: 24px;
        font-weight: 700;
        text-align: center;
        margin-bottom: 24px;
    }}
    .content-card {{
        background-color: white;
        padding: 16px 20px;
        border-radius: 12px;
        box-shadow: 0 6px 18px rgba(0,0,0,0.06);
        margin-bottom: 16px;
        color: {PRIMARY};
    }}
    .stButton>button {{
        background-color: {ACCENT} !important;
        color: white !important;
        font-weight: 600;
        border-radius: 8px;
        border: none !important;
        padding: 0.5rem 1rem;
        font-size: 16px;
    }}
    .stButton>button:hover {{
        background-color: #1873cc !important;
        border: none !important;
        color: white !important;
    }}
    .stFormSubmitButton>button {{
        background-color: {ACCENT} !important;
        color: white !important;
        font-weight: 600;
        border-radius: 8px;
        border: none !important;
        padding: 0.5rem 1rem;
        font-size: 16px;
    }}
    .numberplate {{
        background-color: #FFC600;
        border: 4px solid #000000;
        border-radius: 8px;
        padding: 20px 32px;
        font-size: 48px;
        font-weight: 900;
        color: #000000;
        text-align: center;
        margin: 24px auto;
        letter-spacing: 8px;
        box-shadow: 0 6px 16px rgba(0,0,0,0.25);
        max-width: 500px;
        font-family: 'Charles Wright', Arial, sans-serif;
    }}
    .badge {{
        padding: 4px 10px;
        border-radius: 12px;
        color: white;
        margin-right: 4px;
        font-size: 12px;
        display: inline-block;
    }}
    .badge-warning {{background-color: #ff9800;}}
    .badge-error {{background-color: #f44336;}}
    .badge-success {{background-color: #4caf50;}}
    </style>
    """, unsafe_allow_html=True)

# ============================================================================
# UI COMPONENTS
# ============================================================================

def render_header():
    """Render the application header"""
    st.markdown(f"""
    <div class='header-card' style='background: linear-gradient(135deg, {PRIMARY} 0%, #1a4d7a 100%);'>
        <div style='display: flex; align-items: center; justify-content: center;'>
            <div style='text-align: center;'>
                <div style='font-size: 28px; font-weight: 700;'>Sytner TradeSnap</div>
                <div style='font-size: 14px; opacity: 0.9; font-weight: 400;'>Snap it. Value it. Done.</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def render_reset_button():
    """Render reset button when on summary page"""
    if st.session_state.show_summary:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("New Vehicle Lookup", use_container_width=True):
                reset_all_state()
                st.rerun()

# ============================================================================
# PAGE RENDERERS (Simplified versions - keeping only essentials)
# ============================================================================

def render_input_page():
    """Render the vehicle input page"""
    st.markdown("### 🚗 Vehicle Lookup")
    
    manual_reg = st.text_input("Enter Registration", placeholder="AB12 CDE")
    
    if st.button("🔍 Look Up Vehicle", type="primary"):
        if validate_registration(manual_reg):
            st.session_state.reg = manual_reg.strip().upper().replace(" ", "")
            st.session_state.show_summary = True
            st.rerun()
        else:
            st.error("❌ Please enter a valid registration")

def render_summary_page():
    """Render the vehicle summary page"""
    reg = st.session_state.reg
    
    st.markdown(f"<div class='numberplate'>{reg}</div>", unsafe_allow_html=True)
    
    try:
        vehicle = lookup_vehicle_basic(reg)
        mot_tax = lookup_mot_and_tax(reg)
    except Exception as e:
        st.error(f"⚠️ Error: {str(e)}")
        st.stop()
    
    st.markdown("### Vehicle Summary")
    col1, col2 = st.columns(2)
    with col1:
        st.write(f"**Make:** {vehicle['make']}")
        st.write(f"**Model:** {vehicle['model']}")
    with col2:
        st.write(f"**Year:** {vehicle['year']}")
        st.write(f"**Mileage:** {vehicle['mileage']:,}")
    
    # Customer Journey Creation Section
    st.markdown("---")
    st.markdown("### ✨ Create Customer Journey")
    
    if st.button("🚀 Start Customer Journey", use_container_width=True, type="primary"):
        st.session_state.create_journey_mode = True
        st.rerun()
    
    if st.session_state.get('create_journey_mode', False):
        with st.form("journey_creation_form"):
            st.markdown("#### Customer Details")
            
            col1, col2 = st.columns(2)
            with col1:
                customer_name = st.text_input("Name *")
                customer_email = st.text_input("Email *")
            with col2:
                customer_phone = st.text_input("Phone *")
                deposit_amount = st.number_input("Deposit (£)", min_value=0, value=1000)
            
            garage = st.selectbox("Garage", GARAGES)
            collection_date = st.date_input("Collection Date", 
                value=datetime.date.today() + datetime.timedelta(days=30))
            
            col_a, col_b = st.columns(2)
            with col_a:
                submitted = st.form_submit_button("✅ Create", type="primary")
            with col_b:
                cancelled = st.form_submit_button("❌ Cancel")
            
            if submitted and customer_name and customer_email and customer_phone:
                tracking_id = generate_tracking_id()
                
                journey = {
                    "tracking_id": tracking_id,
                    "created_date": datetime.datetime.now().isoformat(),
                    "customer": {"name": customer_name, "email": customer_email, "phone": customer_phone},
                    "vehicle": vehicle,
                    "financial": {"deposit": deposit_amount},
                    "garage": garage,
                    "collection_date": collection_date.isoformat(),
                    "current_stage": 0
                }
                
                save_customer_journey(journey)
                st.success(f"✅ Journey Created! Tracking ID: {tracking_id}")
                st.balloons()
                st.session_state.create_journey_mode = False
            
            if cancelled:
                st.session_state.create_journey_mode = False
                st.rerun()

# ============================================================================
# SALES PIPELINE PAGE
# ============================================================================

def render_sales_pipeline_page():
    """Render sales pipeline dashboard"""
    st.markdown("### 📊 Sales Pipeline Dashboard")
    
    sales_data = load_sales_data()
    
    if sales_data:
        st.metric("Total Active Sales", len(sales_data))
        
        for sale in sales_data[:10]:
            with st.expander(f"{sale['customer']['first_name']} {sale['customer']['last_name']}"):
                st.write(f"**Sale ID:** {sale['sale_id']}")
                st.write(f"**Stage:** {sale['pipeline']['current_stage']}")
                progress = sale['pipeline']['progress_percentage'] / 100
                st.progress(progress)
    else:
        st.info("📋 No sales data. Create journeys from TradeSnap!")

# ============================================================================
# CUSTOMER TRACKER PAGE
# ============================================================================

def render_customer_tracker_page():
    """Customer-facing tracking page"""
    st.markdown("### 🔍 Track Your Vehicle")
    
    tracking_id = st.text_input("Enter Tracking ID", placeholder="ABC123XYZ456")
    
    if tracking_id:
        journey = get_journey_by_tracking_id(tracking_id.upper())
        
        if journey:
            render_wheel_tracker(journey.get('current_stage', 0), SALES_STAGES)
            
            st.markdown("### Your Details")
            st.write(f"**Name:** {journey['customer']['name']}")
            st.write(f"**Vehicle:** {journey['vehicle']['year']} {journey['vehicle']['make']}")
        else:
            st.error("❌ Tracking ID not found")

# ============================================================================
# MAIN APPLICATION
# ============================================================================

def main():
    """Main application entry point"""
    st.set_page_config(
        page_title="Sytner Complete Journey",
        page_icon="🚗",
        layout="centered"
    )
    
    init_session_state()
    apply_custom_css()
    
    # Sidebar navigation
    with st.sidebar:
        st.markdown("### 🎯 Navigation")
        page = st.radio(
            "Select Feature",
            ["🚗 TradeSnap", "📊 Sales Pipeline", "🔍 Customer Tracker"],
            label_visibility="collapsed"
        )
    
    render_header()
    
    # Route to pages
    if "TradeSnap" in page:
        render_reset_button()
        if st.session_state.show_summary and st.session_state.reg:
            render_summary_page()
        else:
            render_input_page()
    elif "Sales Pipeline" in page:
        render_sales_pipeline_page()
    else:
        render_customer_tracker_page()

if __name__ == "__main__":
    main()
