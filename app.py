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

# 3. SIDEBAR CONTROLS
st.sidebar.title("🎬 Director's Control Panel")
st.sidebar.markdown("---")

lang = st.sidebar.selectbox("Language (ဘာသာစကား)", ["မြန်မာစာ (Burmese)", "English"])

genre = st.sidebar.selectbox("Story Genre (ဇာတ်လမ်းအမျိုးအစား)", [
    "Drama (ရသစုံ ဒရမ်မာ)", 
    "Comedy/Funny (ဟာသ)", 
    "Horror/Thriller (သည်းထိတ်ရင်ဖို)", 
    "Action/Adventure (က်ရွင္)", 
    "Sci-Fi/Fantasy (သိပ္ပံနှင့် စိတ်ကူးယဉ်)"
])

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

# Syntax Error ကင်းဝေးစေရန် ပြင်ဆင်ထားသော System Prompt
system_prompt = """
မင်းက ကမ္ဘာကျော် ရုပ်ရှင်ဒါရိုက်တာနဲ့ ဇာတ်ညွှန်းရေးဆရာ၊ Storyboard Artist ဖြစ်တယ်။ ငါပေးတဲ့ အိုင်ဒီယာအပေါ် အခြေခံပြီး JSON format နဲ့သာ ပြန်ပေးပါ။

သတ်မှတ်ချက်များ:
၁။ ဇာတ်လမ်းပုံစံ: {GENRE} အမျိုးအစားဖြစ်ပြီး စာရေးဆရာစတိုင် စွဲဆောင်မှုရှိရမည်။ ဒါရိုက်တာတွေ ကြိုက်မယ့် Strong Conflict ပါရမည်။
၂။ ဘာသာစကား: {LANG} ဖြင့် ဇာတ်လမ်း၊ ဇာတ်ညွှန်းနှင့် Shot Action များကို ရေးသားပါ။
၃။ ပြသချိန်: စုစုပေါင်း ကြာချိန် {SECONDS} စက္ကန့်စာ ဖြစ်ရမည်။
၄။ ရုပ်ရှင်စတိုင်: {STYLE} ဖြစ်ရမည်။
၅။ ဇာတ်ကောင်ပုံစံ: {CHAR_DESC} ကို အခြေခံပါ။

JSON Structure Format အတိုင်း ကွက်တိပြန်ပေးပါ (အခြားစာများမပါရ):
{
  "title": "ဇာတ်လမ်းခေါင်းစဉ်",
  "full_story": "ဇာတ်လမ်းတစ်ပုဒ်လုံးစာသား",
  "scenes": [
    {
      "scene_number": 1,
      "location_time": "INT. ROOM - DAY",
      "narration_dialogue": "Narration သို့မဟုတ် ဇာတ်ကောင်စကားပြော",
      "shots": [
        {
          "shot_number": 1,
          "duration": "3s",
          "action_description": "သတ်မှတ်ဘာသာစကားဖြင့် Shot လှုပ်ရှားမှုပြကွက်",
          "image_prompt": "English prompt for Midjourney: detailed {STYLE}, {CHAR_DESC}, lighting, camera angle, 8k, --ar 16:9",
          "video_prompt": "English motion instructions for Runway/Luma: camera movement, character action",
          "sound_prompt": "Sound design, SFX and Background music cues"
        }
      ]
    }
  ]
}
အရေးကြီးချက်: image_prompt နှင့် video_prompt များကို နိုင်ငံတကာ AI tools များတွင် တန်းသုံးနိုင်ရန် 'အင်္ဂလိပ်လို' သာ အမြဲတမ်း ထုတ်ပေးရမည်။ အဖြေကို JSON သီးသန့်သာ ပြန်ပေးပါ။
"""

# နေရာလဲလှယ်ခြင်းဖြင့် Dynamic လုပ်သည် (f-string Syntax Error ကို ရှောင်ရန်)
final_system_prompt = system_prompt.replace("{GENRE}", genre)\
                                   .replace("{LANG}", lang)\
                                   .replace("{SECONDS}", str(total_seconds))\
                                   .replace("{STYLE}", visual_style)\
                                   .replace("{CHAR_DESC}", character_desc)

# GENERATE PROCESS
if st.button("🚀 Generate Cinematic Director's Script"):
    if not API_KEY:
        st.error("API Key ထည့်ပေးရန် လိုအပ်ပါသည်။")
    elif total_seconds <= 0:
        st.error("ဗီဒီယိုကြာချိန်ကို အနည်းဆုံး စက္ကန့်အချို့ သတ်မှတ်ပေးပါ။")
    else:
        with st.spinner("🎬 AI Director မှ ဇာတ်လမ်းနှင့် ရိုက်ကွက် Storyboard များကို တွက်ချက်ဖန်တီးနေပါသည်..."):
            try:
                client = genai.Client(api_key=API_KEY)
                final_input = user_story if user_story.strip() else f"တစ်ခုခုဆန်းသစ်ပြီး စိတ်လှုပ်ရှားစရာကောင်းသော {genre} ဇာတ်လမ်းတစ်ပုဒ်အား ဖန်တီးပေးပါ။"
                
                response = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=final_input,
                    config=types.GenerateContentConfig(
                        system_instruction=final_system_prompt,
                        response_mime_type="application/json",
                        temperature=0.7,
                    )
                )
                
                # ရလဒ် JSON ကို သိမ်းဆည်းခြင်း
                st.session_state['raw_json_data'] = json.loads(response.text)
                st.success("🎉 အောင်မြင်စွာ ဖန်တီးပြီးပါပြီ။")
                
            except Exception as e:
                st.error(f"Error: {str(e)}")

# 5. BEAUTIFUL OUTPUT DISPLAY
if 'raw_json_data' in st.session_state:
    data = st.session_state['raw_json_data']
    
    download_text = f"TITLE: {data['title']}\n\nSTORY:\n{data['full_story']}\n\n"
    
    st.header(f"🎬 {data['title']}")
    st.markdown("### ✍️ Full Story (ဇာတ်လမ်းအကျဉ်း)")
    st.info(data['full_story'])
    
    if scene_breakdown and 'scenes' in data:
        for scene in data['scenes']:
            scene_title = f"SCENE {scene['scene_number']}: {scene['location_time']}"
            st.markdown(f"<div class='scene-header'>{scene_title}</div>", unsafe_allow_html=True)
            st.markdown(f"💬 **Narration / Dialogue:** {scene['narration_dialogue']}")
            
            download_text += f"==={scene_title}===\nNarration/Dialogue: {scene['narration_dialogue']}\n\n"
            
            cols = st.columns(2)
            for idx, shot in enumerate(scene['shots']):
                download_text += f"Shot {shot['shot_number']} ({shot['duration']})\nAction: {shot['action_description']}\nImage Prompt: {shot['image_prompt']}\nVideo Prompt: {shot['video_prompt']}\nSound Design: {shot['sound_prompt']}\n\n"
                
                with cols[idx % 2]:
                    st.markdown("<div class='storyboard-card'>", unsafe_allow_html=True)
                    st.markdown(f"<div class='shot-title'>🎬 Shot {shot['shot_number']} ({shot['duration']})</div>", unsafe_allow_html=True)
                    
                    if show_storyboard:
                        encoded_prompt = urllib.parse.quote(shot['image_prompt'])
                        image_url = f"https://pollinations.ai/p/{encoded_prompt}?width=1280&height=720&nologo=true&seed=100"
                        st.image(image_url, use_container_width=True)
                    
                    st.write(f"ℹ️ **Action:** {shot['action_description']}")
                    st.markdown(f"<div class='audio-box'>🔊 **Sound Design:** {shot['sound_prompt']}</div>", unsafe_allow_html=True)
                    
                    with st.expander("👁️ View & Copy AI Prompts"):
                        st.write("🎨 **Image Prompt (Midjourney/SD):**")
                        st.code(shot['image_prompt'], language="text")
                        st.write("📹 **Video Prompt (Runway/Luma):**")
                        st.code(shot['video_prompt'], language="text")
                        
                    st.markdown("</div>", unsafe_allow_html=True)
                    
    st.markdown("---")
    st.download_button(
        label="📥 Download Full Director's Script (Text File)",
        data=download_text,
        file_name=f"{data['title']}_script.txt",
        mime="text/plain"
    )
