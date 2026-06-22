import streamlit as st
import json
import urllib.parse
from google import genai
from google.genai import types

# 1. PAGE CONFIGURATION
st.set_page_config(
    page_title="AI Director & Storyboarder Pro",
    page_icon="🎬",
    layout="wide"
)

# CUSTOM CSS (Dark Modern Cinema Theme)
st.markdown("""
<style>
    .main { background-color: #0f172a; color: #f8fafc; }
    .storyboard-card {
        background-color: #1e293b;
        border-radius: 12px;
        padding: 18px;
        margin-bottom: 25px;
        border: 1px solid #334155;
    }
    .scene-header {
        background: linear-gradient(90deg, #38bdf8, #0369a1);
        padding: 12px 20px;
        border-radius: 8px;
        color: white;
        font-weight: bold;
        margin-top: 30px;
        margin-bottom: 15px;
        font-size: 18px;
    }
    .shot-title {
        color: #38bdf8;
        font-weight: bold;
        font-size: 16px;
        margin-bottom: 10px;
    }
    .audio-box {
        background-color: #0f172a;
        border-left: 3px solid #e2e8f0;
        padding: 8px 12px;
        border-radius: 4px;
        margin-top: 10px;
        font-size: 14px;
    }
</style>
""", unsafe_allow_html=True)

# 2. API INITIALIZATION
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
except:
    API_KEY = ""

if not API_KEY:
    st.sidebar.warning("⚠️ API Key လိုအပ်နေပါသည်။")
    API_KEY = st.sidebar.text_input("Enter Gemini API Key:", type="password")

# 3. SIDEBAR CONTROLS (ပြန်လည်ဖြည့်စွက်ထားသော Panel)
st.sidebar.title("🎬 Director's Control Panel")
st.sidebar.markdown("---")

lang = st.sidebar.selectbox("Language (ဘာသာစကား)", ["မြန်မာစာ (Burmese)", "English"])

# Genre ရွေးချယ်မှုစနစ် (Drama, Funny, Sci-Fi, Horror, Action)
genre = st.sidebar.selectbox("Story Genre (ဇာတ်လမ်းအမျိုးအစား)", [
    "Drama (ရသစုံ ဒရမ်မာ)", 
    "Comedy/Funny (ဟာသ)", 
    "Horror/Thriller (သည်းထိတ်ရင်ဖို)", 
    "Action/Adventure (အက်ရှင်)", 
    "Sci-Fi/Fantasy (သိပ္ပံနှင့် စိတ်ကူးယဉ်)"
])

# မိနစ် နှင့် စက္ကန့် ခွဲခြားရွေးချယ်ခွင့်
st.sidebar.markdown("**Video Duration (ဗီဒီယိုကြာချိန်)**")
col_min, col_sec = st.sidebar.columns(2)
with col_min:
    duration_min = st.number_input("မိနစ် (Min)", min_value=0, max_value=60, value=0)
with col_sec:
    duration_sec = st.number_input("စက္ကန့် (Sec)", min_value=0, max_value=59, value=30)

total_seconds = (duration_min * 60) + duration_sec

scene_breakdown = st.sidebar.toggle("Scene Breakdown ခွဲမည်", value=True)
show_storyboard = st.sidebar.toggle("Storyboard ပုံများ ထုတ်မည် (Free API)", value=True)

visual_style = st.sidebar.selectbox("Visual Art Style", [
    "3D Disney Cartoon Style", 
    "Japanese Anime Style", 
    "Cinematic Live-Action", 
    "Cyberpunk Digital Art"
])

character_desc = st.sidebar.text_area("Character Consistency (ဇာတ်ကောင်ပုံစံ)", 
    placeholder="ဥပမာ- မောင်မောင်: အသက် ၁၅ နှစ်၊ မျက်မှန်တပ်ထားသည်၊ အပြာရောင်ဂျာကင်ဝတ်ဆင်သည်။")

# 4. MAIN INTERFACE
st.title("🎬 AI Director Workspace")
st.caption("From Concept to Visual Storyboard - Powered by Gemini 2.5 Flash")
st.markdown("---")

user_story = st.text_area("✍️ ဇာတ်လမ်းအကျဉ်း သို့မဟုတ် ခေါင်းစဉ်ကို ရိုက်ထည့်ပါ (ဗလာထားပါက AI မှ Random ဖန်တီးပေးမည်) :", height=100)

# SYSTEM INSTRUCTION
system_prompt = f"""
မင်းက ကမ္ဘာကျော် ရုပ်ရှင်ဒါရိုက်တာနဲ့ ဇာတ်ညွှန်းရေးဆရာ၊ Storyboard Artist ဖြစ်တယ်။ ငါပေးတဲ့ အိုင်ဒီယာအပေါ် အခြေခံပြီး JSON format နဲ့သာ ပြန်ပေးပါ။

သတ်မှတ်ချက်များ:
၁။ ဇာတ်လမ်းပုံစံ: {genre} အမျိုးအစားဖြစ်ပြီး စာရေးဆရာစတိုင် စွဲဆောင်မှုရှိရမည်။ ဒါရိုက်တာတွေ ကြိုက်မယ့် Strong Conflict ပါရမည်။
၂။ ဘာသာစကား: {lang} ဖြင့် ဇာတ်လမ်း၊ ဇာတ်ညွှန်းနှင့် Shot Action များကို ရေးသားပါ။
