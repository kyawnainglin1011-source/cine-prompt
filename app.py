import streamlit as st
import json
import urllib.parse
import random
from google import genai
from google.genai import types

# 1. PAGE CONFIGURATION
st.set_page_config(
    page_title="Cinematic AI Storyboard Pro",
    page_icon="🎬",
    layout="wide"
)

# CUSTOM CSS FOR SMOOTH VISUALS
st.markdown("""
<style>
    .main { background-color: #0f172a; color: #f8fafc; }
    .scene-block {
        background-color: #1e293b;
        border: 1px solid #334155;
        border-radius: 16px;
        padding: 24px;
        margin-bottom: 35px;
    }
    .scene-title-box {
        background: linear-gradient(90deg, #0284c7, #0369a1);
        padding: 12px 20px;
        border-radius: 8px;
        color: white;
        font-weight: bold;
        font-size: 20px;
        margin-bottom: 15px;
    }
    .storyboard-title-line {
        color: #38bdf8;
        font-weight: bold;
        font-size: 16px;
        margin-top: 15px;
        margin-bottom: 10px;
        border-bottom: 1px solid #334155;
        padding-bottom: 5px;
    }
    .shot-detail-card {
        background-color: #0f172a;
        border-left: 4px solid #38bdf8;
        padding: 15px;
        border-radius: 6px;
        margin-bottom: 15px;
    }
    .prompt-tag { color: #f43f5e; font-weight: bold; }
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
st.sidebar.title("🎬 AI Director Pro Panel")
st.sidebar.markdown("---")

lang = st.sidebar.selectbox("Language (ဘာသာစကား)", ["မြန်မာစာ (Burmese)", "English"])

genre = st.sidebar.selectbox("Story Genre (ဇာတ်လမ်းအမျိုးအစား)", [
    "Drama (ရသစုံ ဒရမ်မာ)", "Comedy/Funny (ဟာသ)", 
    "Horror/Thriller (သည်းထိတ်ရင်ဖို)", "Action/Adventure (အက်ရှင်)", 
    "Sci-Fi/Fantasy (သိပ္ပံနှင့် စိတ်ကူးယဉ်)"
])

st.sidebar.markdown("**Video Duration (ဗီဒီယိုကြာချိန်)**")
col_min, col_sec = st.sidebar.columns(2)
with col_min:
    duration_min = st.number_input("မိနစ် (Min)", min_value=0, max_value=60, value=0)
with col_sec:
    duration_sec = st.number_input("စက္ကန့် (Sec)", min_value=0, max_value=59, value=30)

total_seconds = (duration_min * 60) + duration_sec

visual_style = st.sidebar.selectbox("Visual Art Style", [
    "Cinematic Photo-Realistic 8k", "3D Disney Pixar Style", 
    "Modern Anime Illustration", "Cyberpunk Concept Art"
])

character_desc = st.sidebar.text_area("Character Consistency (ဇာတ်ကောင်ပုံစံ)", 
    placeholder="ဥပမာ- မောင်မောင်: အသက် ၁၅ နှစ်၊ မျက်မှန်တပ်ထားသည်၊ အပြာရောင်ဂျာကင်ဝတ်ဆင်သည်။")

# 4. MAIN INTERFACE
st.title("🎬 AI Cinematic Storyboard Workspace")
st.caption("Scene Analysis & Grid Storyboard Layout Engine - Powered by Gemini 2.5 Flash")
st.markdown("---")

user_story = st.text_area("✍️ ဇာတ်လမ်းအကျဉ်း သို့မဟုတ် ခေါင်းစဉ် (ဗလာထားပါက လုံးဝ Random အသစ်များ ထွက်လာပါမည်) :", height=100)

# 5. ADVANCED SYSTEM PROMPT
system_prompt = """
မင်းက ရုပ်ရှင်ဒါရိုက်တာနဲ့ အဆင့်မြင့် Storyboard Artist ဖြစ်တယ်။ ငါပေးတဲ့ စိတ်ကူးအပေါ် မူတည်ပြီး JSON သီးသန့်သာ ပြန်ပေးပါ။

အလုပ်လုပ်ပုံအဆင့်ဆင့် ညွှန်ကြားချက်:
၁။ ပေးထားသော ခေါင်းစဉ်/ဇာတ်လမ်းအပေါ် မူတည်ပြီး {GENRE} ပုံစံ စိတ်လှုပ်ရှားစရာ ဇာတ်လမ်းအသစ်ကို {LANG} ဖြင့် ရေးပါ။
၂။ ဇာတ်လမ်းတစ်ခုလုံး၏ ကြာချိန်သည် စုစုပေါင်း {SECONDS} စက္ကန့် ဖြစ်ရမည်။
၃။ ဇာတ်လမ်းကို နေရာ/အချိန် အလိုက် Scene များ ခွဲခြားပါ။ Scene တစ်ခုချင်းစီတွင် စုစုပေါင်း ကြာချိန် (ဥပမာ- Duration: 8s, 10s) ရှိရမည်။
၄။ ထို Scene တစ်ခုချင်းစီ၏ ကြာချိန်အလိုက် ၎င်း Scene အတွင်း၌သာ အလုပ်လုပ်မည့် Shot များကို မိနစ်/စက္ကန့်အလိုက် ထပ်မံ စိပ်စိပ်ခွဲခြားပါ (Analysis လုပ်ပါ)။ (ဥပမာ- 8s ရှိသော Scene တစ်ခုတွင် Shot 1 (3s), Shot 2 (2s), Shot 3 (3s) ဆိုပြီး ဖြစ်ရမည်)။
၅။ Shot တိုင်းအတွက် ရုပ်ပုံထွက်လန်းစေမည့် English Prompt သီးသန့် ထုတ်ပေးရမည်။

JSON Structure Format:
{
  "title": "ဇာတ်လမ်းခေါင်းစဉ်",
  "full_story": "ဇာတ်လမ်းတစ်ပုဒ်လုံးစာသား",
  "scenes": [
    {
      "scene_number": 1,
      "location_time": "INT. ROOM - DAY",
      "scene_duration": "8s",
      "narration_dialogue": "ဤ Scene တစ်ခုလုံးအတွက် Narration သို့မဟုတ် ဇာတ်ဝင်စကား",
      "shots": [
        {
          "shot_number": 1,
          "shot_duration": "3s",
          "action_description": "Shot အတွင်း လှုပ်ရှားမှုပြကွက် (သတ်မှတ်ဘာသာစကားဖြင့်)",
          "image_prompt": "English detailed image prompt: {STYLE}, {CHAR_DESC}, cinematic lighting, 8k, photorealistic",
          "video_prompt": "English motion prompt: camera movement, panning, zooming, character behavior",
          "sound_prompt": "Sound design, SFX noise and Background Music Cue"
        }
      ]
    }
  ]
}
သတိပြုရန်: image_prompt ထဲတွင် မြန်မာစာ လုံးဝ (လုံးဝ) မပါရပါ။ အင်္ဂလိပ်လိုသာ အသေးစိတ် ရေးပါ။ အဖြေကို JSON သီးသန့်သာ ပေးရမည်၊ အပြင်စာများ လုံးဝမပါရပါ။
"""

final_system_prompt = system_prompt.replace("{GENRE}", genre)\
                                   .replace("{LANG}", lang)\
                                   .replace("{SECONDS}", str(total_seconds))\
                                   .replace("{STYLE}", visual_style)\
                                   .replace("{CHAR_DESC}", character_desc)

# GENERATE PROCESS
if st.button("🚀 Generate Visual Storyboard & Script"):
    if not API_KEY:
        st.error("API Key ထည့်ပေးရန် လိုအပ်ပါသည်။")
    elif total_seconds <= 0:
        st.error("ဗီဒီယိုကြာချိန် သတ်မှတ်ပေးပါ။")
    else:
        with st.spinner("🎬 AI Director မှ Scene များကို တွက်ချက်ပြီး Shot Storyboard ဆွဲနေပါသည်..."):
            try:
                client = genai.Client(api_key=API_KEY)
                
                # Random စနစ် အစစ်အမှန်ဖြစ်စေရန် ဖန်တီးမှု
                rand_id = random.randint(1, 99999)
                final_input = user_story if user_story.strip() else f"ဖန်တီးမှုအသစ် လုံးဝဆန်းသစ်ပြီး မတူညီသော စိတ်လှုပ်ရှားစရာ {genre} ဇာတ်လမ်းတစ်ပုဒ်ကို လုံးဝ random စနစ်ဖြင့် ထုတ်ပေးပါ။ (Seed Token: {rand_id})"
                
                response = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=final_input,
                    config=types.GenerateContentConfig(
                        system_instruction=final_system_prompt,
                        response_mime_type="application/json",
                        temperature=0.95, # Temperature ကို မြှင့်တင်ပြီး လုံးဝ Random ဆန်စေသည်
                    )
                )
                
                st.session_state['storyboard_json'] = json.loads(response.text)
                st.success("🎉 Storyboard ဖန်တီးမှု အောင်မြင်ပါသည်။")
                
            except Exception as e:
                st.error(f"API Error: {str(e)}")

# 6. OUTPUT DISPLAY (Scene & Shot Storyboard Layout)
if 'storyboard_json' in st.session_state:
    data = st.session_state['storyboard_json']
    
    st.header(f"🎬 {data.get('title', 'Untitled Script')}")
    st.markdown("### ✍️ Full Story (ဇာတ်လမ်းအကျဉ်း)")
    st.info(data.get('full_story', 'No story text generated.'))
    
    for scene in data.get('scenes', []):
        st.markdown(f"<div class='scene-block'>", unsafe_allow_html=True)
        
        scene_title = f"🎬 SCENE {scene.get('scene_number', '?')}: {scene.get('location_time', 'UNKNOWN')} ({scene.get('scene_duration', '0s')})"
        st.markdown(f"<div class='scene-title-box'>{scene_title}</div>", unsafe_allow_html=True)
        st.write(f"💬 **Narration / Dialogue:** {scene.get('narration_dialogue', '')}")
        
        st.markdown("<div class='storyboard-title-line'>🖼️ VISUAL STORYBOARD ROW (SHOT SEQUENCES)</div>", unsafe_allow_html=True)
        
        shots_list = scene.get('shots', [])
        num_shots = len(shots_list)
        
        # 🖼️ Storyboard Images Grid Display
        if num_shots > 0:
            cols = st.columns(num_shots)
            for idx, shot in enumerate(shots_list):
                with cols[idx]:
                    img_prompt_str = str(shot.get('image_prompt', 'Cinematic view')).replace('"', '').replace("'", "").replace("\n", " ").strip()
                    encoded_prompt = urllib.parse.quote(img_prompt_str)
                    
                    # Image ရုပ်ထွက်မထပ်စေရန် Shot တစ်ခုစီတိုင်းကို Random Seed တစ်ခုစီ ခွဲပေးသည်
                    shot_seed = random.randint(1, 999999)
                    
                    # FLUX High Quality Image API URL Formatter
                    image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=800&height=450&nologo=true&model=flux&seed={shot_seed}"
                    
                    st.image(image_url, caption=f"Shot {shot.get('shot_number', idx+1)} ({shot.get('shot_duration', '3s')})", use_container_width=True)
        
        # 📋 Technical Breakdown Display
        st.markdown("<div class='storyboard-title-line'>📋 SHOT-BY-SHOT PROMPT BREAKDOWN</div>", unsafe_allow_html=True)
        
        for shot in shots_list:
            st.markdown(f"<div class='shot-detail-card'>", unsafe_allow_html=True)
            st.write(f"🎥 **Shot {shot.get('shot_number', '')} ({shot.get('shot_duration', '')}):** {shot.get('action_description', '')}")
            st.markdown(f"<div class='audio-box'>🔊 **Sound & Music:** {shot.get('sound_prompt', '')}</div>", unsafe_allow_html=True)
            
            with st.expander(f"👁️ Copy Prompts for Shot {shot.get('shot_number', '')}"):
                st.write("<span class='prompt-tag'>🎨 Image Prompt (Flux/Midjourney):</span>", unsafe_allow_html=True)
                st.code(shot.get('image_prompt', ''), language="text")
                st.write("<span class='prompt-tag'>📹 Video Prompt (Runway/Luma):</span>", unsafe_allow_html=True)
                st.code(shot.get('video_prompt', ''), language="text")
            st.markdown("</div>", unsafe_allow_html=True)
            
        st.markdown("</div>", unsafe_allow_html=True)
