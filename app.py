import streamlit as st
import json
import urllib.parse
from google import genai
from google.genai import types

# 1. PAGE CONFIGURATION
st.set_page_config(
    page_title="AI Director & Storyboarder",
    page_icon="🎬",
    layout="wide"
)

# CUSTOM CSS (Storyboard Grid Style)
st.markdown("""
<style>
    .main { background-color: #0f172a; color: #f8fafc; }
    .storyboard-card {
        background-color: #1e293b;
        border-radius: 15px;
        padding: 15px;
        margin-bottom: 25px;
        border: 1px solid #334155;
    }
    .scene-header {
        background: linear-gradient(90deg, #38bdf8, #0369a1);
        padding: 10px 20px;
        border-radius: 8px;
        color: white;
        font-weight: bold;
        margin-bottom: 20px;
    }
    .shot-info { font-size: 14px; color: #94a3b8; margin-top: 10px; }
    .prompt-text { font-style: italic; font-size: 12px; color: #38bdf8; }
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

# 3. SIDEBAR CONTROLS
st.sidebar.title("🎬 AI Director Pro")
lang = st.sidebar.selectbox("Language", ["မြန်မာစာ (Burmese)", "English"])
visual_style = st.sidebar.selectbox("Visual Style", [
    "3D Disney Animation", "Japanese Anime Style", "Cinematic Realistic", "Cyberpunk Art"
])
character_desc = st.sidebar.text_area("Character Consistency", "ဥပမာ- လူငယ်လေး မောင်မောင်၊ အပြာရောင်အင်္ကျီဝတ်ထားသည်။")
show_storyboard = st.sidebar.toggle("Generate Storyboard Images (Free API)", value=True)

# 4. MAIN INTERFACE
st.title("🎬 AI Director & Visual Storyboard")
user_story = st.text_area("✍️ ဇာတ်လမ်း သို့မဟုတ် ခေါင်းစဉ် ရိုက်ထည့်ပါ :", height=100)

# Gemini ကို JSON Format နဲ့ ပြန်ခိုင်းမယ် (ဒါမှ Image တွေကို ပတ်ထုတ်လို့ရမှာပါ)
system_prompt = f"""
မင်းက ရုပ်ရှင်ဒါရိုက်တာနဲ့ Storyboard Artist ဖြစ်တယ်။
ငါပေးတဲ့ ဇာတ်လမ်းကို အခြေခံပြီး ဒါရိုက်တာတစ်ယောက်လို တွေးခေါ်ကာ JSON format နဲ့သာ ပြန်ပေးပါ။

JSON Structure:
{{
  "title": "ဇာတ်လမ်းခေါင်းစဉ်",
  "full_story": "{lang} ဖြင့် ရေးသားထားသော ဇာတ်လမ်းအကျဉ်း",
  "scenes": [
    {{
      "scene_number": 1,
      "location_time": "INT. ROOM - DAY",
      "narration": "အခန်းကြောင်းပြော သို့မဟုတ် Dialogue",
      "shots": [
        {{
          "shot_number": 1,
          "duration": "3s",
          "description": "{lang} ဖြင့် Shot အကြောင်းပြချက်",
          "image_prompt": "English prompt for image generation: {visual_style}, {character_desc}, detailed, high quality",
          "video_prompt": "English movement instructions",
          "sound_prompt": "Sound effect and music cue"
        }}
      ]
    }}
  ]
}}
မှတ်ချက်: Image prompts များကို အင်္ဂလိပ်လိုသာ ရေးပါ။ အဖြေကို JSON သီးသန့်သာ ပြန်ပေးပါ။
"""

if st.button("🚀 Generate Storyboard"):
    if not API_KEY:
        st.error("API Key ထည့်ပေးပါ။")
    else:
        with st.spinner("🎬 AI Director က Storyboard ဆွဲနေပါတယ်..."):
            try:
                client = genai.Client(api_key=API_KEY)
                response = client.models.generate_content(
                    model='gemini-2.0-flash',
                    contents=user_story if user_story else "Random emotional story",
                    config=types.GenerateContentConfig(
                        system_instruction=system_prompt,
                        response_mime_type="application/json", # JSON Mode ကို သုံးထားပါတယ်
                        temperature=0.7
                    )
                )
                
                # JSON ကို ဖတ်မယ်
                data = json.loads(response.text)
                
                # ၁။ ဇာတ်လမ်း အကျဉ်းပြမယ်
                st.header(data['title'])
                st.info(data['full_story'])
                
                # ၂။ Scenes တွေကို ပတ်ထုတ်မယ်
                for scene in data['scenes']:
                    st.markdown(f"<div class='scene-header'>SCENE {scene['scene_number']}: {scene['location_time']}</div>", unsafe_allow_html=True)
                    st.write(f"💬 **Narration:** {scene['narration']}")
                    
                    # Shots တွေကို Grid နဲ့ ပြမယ်
                    cols = st.columns(2) # တစ်တန်းကို ၂ ပုံနှုန်းပြမယ်
                    for idx, shot in enumerate(scene['shots']):
                        with cols[idx % 2]:
                            st.markdown("<div class='storyboard-card'>", unsafe_allow_html=True)
                            
                            # Storyboard Image Generation (Pollinations.ai)
                            if show_storyboard:
                                # Prompt ကို URL format ပြောင်းတယ်
                                encoded_prompt = urllib.parse.quote(shot['image_prompt'])
                                # Seed ထည့်ပေးခြင်းဖြင့် ဇာတ်ကောင် မပြောင်းအောင် အနည်းငယ် ထိန်းတယ်
                                image_url = f"https://pollinations.ai/p/{encoded_prompt}?width=1280&height=720&nologo=true&seed=42"
                                st.image(image_url, caption=f"Shot {shot['shot_number']} ({shot['duration']})", use_container_width=True)
                            
                            st.write(f"🎬 **Action:** {shot['description']}")
                            st.markdown(f"<div class='shot-info'>🔊 {shot['sound_prompt']}</div>", unsafe_allow_html=True)
                            
                            with st.expander("👁️ View Technical Prompts"):
                                st.write("**Image Prompt:**")
                                st.code(shot['image_prompt'])
                                st.write("**Video Motion:**")
                                st.code(shot['video_prompt'])
                                
                            st.markdown("</div>", unsafe_allow_html=True)
                
                st.balloons()
                
            except Exception as e:
                st.error(f"Error: {e}")
