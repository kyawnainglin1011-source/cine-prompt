import streamlit as st
import json
from google import genai
from google.genai import types

# 1. PAGE CONFIGURATION (UI ကို လန်းဆန်းကျယ်ပြန့်စေရန်)
st.set_page_config(
    page_title="AI Director Workspace",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CUSTOM CSS (Dark Theme နှင့် UI ကို ပိုမိုလှပစေရန်)
st.markdown("""
<style>
    .main { background-color: #0f172a; color: #f8fafc; }
    .stButton>button {
        background: linear-gradient(135deg, #38bdf8 0%, #0369a1 100%);
        color: white; border: none; padding: 12px 24px;
        border-radius: 8px; font-weight: bold; width: 100%;
    }
    .stButton>button:hover { background: linear-gradient(135deg, #0284c7 0%, #075985 100%); }
    .scene-box {
        background-color: #1e293b; border-left: 5px solid #38bdf8;
        padding: 20px; border-radius: 8px; margin-bottom: 20px;
    }
    .shot-box {
        background-color: #0f172a; border: 1px solid #334155;
        padding: 15px; border-radius: 6px; margin-top: 10px;
    }
    .prompt-label { color: #38bdf8; font-weight: bold; font-size: 14px; }
</style>
""", unsafe_allow_html=True)

# 2. GEMINI API INITIALIZATION
# Streamlit secrets သို့မဟုတ် environment variable ထဲက API Key ကို ယူမည်
API_KEY = st.secrets.get("GEMINI_API_KEY", "")
if not API_KEY:
    st.sidebar.warning("⚠️ API Key လိုအပ်နေပါသည်။ Sidebar တွင် ထည့်သွင်းပေးပါ။")
    API_KEY = st.sidebar.text_input("Enter Gemini API Key:", type="password")

# 3. SIDEBAR CONTROLS (ရွေးချယ်မှုအပိုင်းများ)
st.sidebar.title("🎬 Director's Control Panel")
st.sidebar.markdown("---")

lang = st.sidebar.selectbox("Language (ဘာသာစကား)", ["မြန်မာစာ (Burmese)", "English"])
duration = st.sidebar.slider("Estimated Duration (ကြာချိန်)", min_value=15, max_value=300, value=60, step=15, format="%d စက္ကန့်")

scene_breakdown = st.sidebar.toggle("Scene Breakdown လုပ်မည်", value=True)

visual_style = st.sidebar.selectbox("Visual Art Style", [
    "3D Disney Cartoon Style",
    "Japanese Anime Style",
    "Cinematic Live-Action",
    "Cyberpunk Digital Art",
    "Pixar Animation Studio Style"
])

character_desc = st.sidebar.text_area("Character Consistency (ဇာတ်ကောင် အသွင်အပြင် သတ်မှတ်ရန်)", 
    placeholder="ဥပမာ- မောင်မောင်: အသက် ၁၅ နှစ်၊ မျက်မှန်တပ်ထားသည်၊ အပြာရောင်ဂျာကင်ဝတ်ဆင်သည်။")

# 4. MAIN INTERFACE DESIGN
st.title("🎬 AI Director Workspace")
st.caption("From Concept to Cinematic Prompts in Seconds - Powered by Gemini 2.5 Flash")
st.markdown("---")

# User Input Box
user_story = st.text_area("✍️ ဇာတ်လမ်းအကျဉ်း သို့မဟုတ် ခေါင်းစဉ်ကို ရိုက်ထည့်ပါ (ဗလာထားပါက AI မှ Random ဖန်တီးပေးမည်) :", height=120)

# SYSTEM INSTRUCTION (Gemini ကို ဒါရိုက်တာလို တွေးခေါ်စေမည့် အမိန့်စာ)
system_prompt = f"""
မင်းက ကမ္ဘာကျော် ရုပ်ရှင်ဒါရိုက်တာနဲ့ ဇာတ်ညွှန်းရေးဆရာ ဖြစ်တယ်။ ငါပေးတဲ့ အိုင်ဒီယာအပေါ် အခြေခံပြီး ဒါရိုက်တာတွေ မျက်စိကျမယ့် စိတ်ဝင်စားစရာ Strong Conflict ပါတဲ့ ဇာတ်လမ်းကို စာရေးဆရာစတိုင် ရေးသားပေးရမယ်။

သတ်မှတ်ချက်များ:
၁။ ဘာသာစကား: {lang} ဖြင့် ဇာတ်လမ်းကို ရေးသားပါ။
၂။ ပြသချိန်: စုစုပေါင်း {duration} စက္ကန့်စာ ဖြစ်ရမယ်။
၃။ ရုပ်ရှင်စတိုင်: {visual_style} ဖြစ်ရမယ်။
၄။ ဇာတ်ကောင်ပုံစံ: {character_desc} ကို အခြေခံပါ။

ဇာတ်လမ်းကို အပိုင်း (၂) ပိုင်း ခွဲထုတ်ပေးရမယ်။
အပိုင်း (၁) - Story Title နှင့် Full Story text။
အပိုင်း (၂) - Scene Breakdown ဖြစ်သည်။ (အကယ်၍ Scene Breakdown toggled on ဖြစ်ပါက)
- နေရာနှင့် အချိန်ပေါ်မူတည်ပြီး Scene များ ခွဲခြားပါ။
- Scene တစ်ခုချင်းစီတွင် Narration သို့မဟုတ် Dialogue ပါဝင်ရမည်။
- Scene တစ်ခုချင်းစီအတွင်း 3s, 4s, 5s, 7s စသဖြင့် သင့်တော်မယ့် Shot လေးများ ဖွဲ့စည်းပါ။
- Shot တိုင်းအတွက် Image Prompt, Video Prompt နှင့် Sound Design Prompt (SFX & BGM) တို့ကို သေချာစွာ ထုတ်ပေးပါ။
- **အရေးကြီးချက်:** Image & Video Prompt များကို နိုင်ငံတကာ AI tools များ (Midjourney, Runway) တွင် တန်းသုံးနိုင်ရန် 'အင်္ဂလိပ်လို' သာ အမြဲတမ်း ထုတ်ပေးရမည်။ (Lighting, Camera Angle, Movement, Environment များကို ကွက်တိ ညွှန်ကြားချက် ထည့်ပါ)။
"""

# GENERATE BUTTON ACTION
if st.button("🚀 Generate Cinematic Director's Script"):
    if not API_KEY:
        st.error("Gemini API Key မရှိဘဲ လုပ်ဆောင်၍မရပါ။ Sidebar တွင် ထည့်သွင်းပေးပါ။")
    else:
        with st.spinner("🎬 AI Director မှ ဇာတ်လမ်းနှင့် ရိုက်ကွက်များကို တွက်ချက်ဖန်တီးနေပါသည်... ခေတ္တစောင့်ဆိုင်းပေးပါ..."):
            try:
                # Initialize Gemini client
                client = genai.Client(api_key=API_KEY)
                
                final_user_prompt = user_story if user_story.strip() else "တစ်ခုခုဆန်းသစ်ပြီး စိတ်လှုပ်ရှားစရာကောင်းသော ဇာတ်လမ်းတစ်ပုဒ်အား random စနစ်ဖြင့် ဖန်တီးပေးပါ။"
                
                if not scene_breakdown:
                    final_user_prompt += " (Scene breakdown လုပ်ရန်မလိုပါ၊ ဇာတ်လမ်းစာသား သီးသန့်သာ ထုတ်ပေးပါ)"

                response = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=final_user_prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=system_prompt,
                        temperature=0.7,
                    )
                )
                
                # ရလဒ်များကို သိမ်းဆည်းခြင်း
                st.session_state['director_output'] = response.text
                st.success("🎉 အောင်မြင်စွာ ဖန်တီးပြီးပါပြီ။")
                
            except Exception as e:
                st.error(f"Error အနည်းငယ်ရှိနေပါသည်: {str(e)}")

# 5. OUTPUT DISPLAY AREA (ရလဒ်များကို လှပစွာ ပြသမည့်အပိုင်း)
if 'director_output' in st.session_state:
    st.markdown("### 📄 Generated Screenplay & Director's Cut")
    
    # ရလဒ်စာသား တစ်ခုလုံးကို ပြသခြင်း
    st.markdown(st.session_state['director_output'])
    
    st.markdown("---")
    # DOWNLOAD BUTTON
    st.download_button(
        label="📥 Download Script & Prompts (Text File)",
        data=st.session_state['director_output'],
        file_name="ai_director_script.txt",
        mime="text/plain"
    )
