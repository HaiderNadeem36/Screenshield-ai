import streamlit as st
import joblib
import pandas as pd
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import time
import database_manager as db

# Initialize Database
db.init_db()

st.set_page_config(page_title="ScreenShield AI", page_icon="🛡️", layout="centered")

st.markdown("""
<style>
    .stTextArea textarea { border-radius: 12px; border: 1px solid #e0e6ed; padding: 15px; font-size: 1.05rem; }
    .stButton>button { border-radius: 8px; font-weight: bold; transition: all 0.2s ease; }

    [data-testid="stDeployButton"] { display: none !important; }
    footer { visibility: hidden; }

    section[data-testid="stSidebar"] div[data-testid="stSidebarUserContent"] {
        padding-top: 0rem !important;
        margin-top: -3.5rem !important;
    }
    
    div[data-testid="stSidebar"] .stButton button[kind="primary"] {
        background-color: #0A2540 !important;
        color: white !important;
        border: 1px solid rgba(255,255,255,0.1) !important;
        padding: 10px !important;
        margin-top: 5px !important;
    }
    
    .st-emotion-cache-12w0qpk { padding: 0.5rem 1rem !important; }
    div[data-testid="stSidebarUserContent"] button {
        background-color: transparent !important;
        border: none !important;
        text-align: left !important;
        padding: 0.8rem !important;
        margin-bottom: 2px !important;
        border-radius: 10px !important;
        color: #333 !important;
        width: 100% !important;
    }
    div[data-testid="stSidebarUserContent"] button:hover {
        background-color: #f0f2f6 !important;
    }
    h1, h2, h3 { color: #0A2540; font-family: 'Inter', sans-serif; }
</style>
""", unsafe_allow_html=True)

if 'screen_hours_val' not in st.session_state:
    st.session_state['screen_hours_val'] = 3.0
if 'active_analysis' not in st.session_state:
    st.session_state['active_analysis'] = None

def start_new_chat():
    st.session_state['main_journal_input'] = ""
    st.session_state['screen_hours_val'] = 3.0
    st.session_state['active_analysis'] = None

# Sidebar History using Database
with st.sidebar:
    st.markdown(
        """
        <div style="margin-left: 5px; margin-bottom: 10px;">
            <h2 style="margin:0; padding:0; font-size: 1.6rem; color:#0A2540; font-family:'Inter', sans-serif;">🛡️ ScreenShield</h2>
        </div>
        """, unsafe_allow_html=True
    )
    st.button("➕ New Journal", on_click=start_new_chat, type="primary", use_container_width=True)
    st.divider()
    
    st.caption("📜 YOUR RECENT HISTORY")
    history = db.get_all_entries()
    
    if not history:
        st.info("No logs yet. Start writing!")
    else:
        for entry in history:
            c1, c2 = st.columns([0.85, 0.15])
            with c1:
                display_label = f"📝 {entry['mood']} Distress ({entry['time']})"
                if st.button(display_label, key=f"load_{entry['id']}"):
                    st.session_state['main_journal_input'] = entry['text']
                    st.session_state['screen_hours_val'] = entry['screen_hours']
                    st.session_state['active_analysis'] = entry
                    st.rerun()
            with c2:
                if st.button("🗑️", key=f"del_{entry['id']}", help="Delete from database"):
                    db.delete_entry(entry['id'])
                    if st.session_state['active_analysis'] and st.session_state['active_analysis']['id'] == entry['id']:
                        st.session_state['active_analysis'] = None
                    st.rerun()

# Optimized Model Loading
@st.cache_resource
def load_models():
    nb = joblib.load('nb_model.pkl')
    vec = joblib.load('vectorizer.pkl')
    lr = joblib.load('lr_model.pkl')
    return nb, vec, lr

nb_model, vectorizer, lr_model = load_models()

st.title("🛡️ ScreenShield AI")
st.subheader("Offline Digital Wellbeing Guardian for Pakistan Youth")

user_text = st.text_area("How was your day?", 
                        height=160, 
                        placeholder="Share your thoughts here...",
                        key="main_journal_input")

screen_hours = st.slider("Phone Usage (Hours)", 0.0, 12.0, 
                        key="screen_hours_val", step=0.1)

def get_conversational_response(text):
    text = text.lower().strip()
    words = text.split()
    
    # Time-based Greeting Helper
    from datetime import datetime
    hour = datetime.now().hour
    time_greeting = "Good Morning" if hour < 12 else "Good Afternoon" if hour < 18 else "Good Evening"

    # 1. Greetings & Introductions
    greetings = ["hi", "hello", "hey", "hello world", "asap", "morning", "night"]
    if any(g in text for g in greetings) and len(words) < 8:
        return f"{time_greeting}! 👋 I'm your ScreenShield AI guardian. It's nice to meet you! How are you feeling today?"
    
    # 2. Name Capture Patterns
    import re
    name_match = re.search(r"(?:my name is|i am|this is|call me|i'm)\s+([a-zA-Z]+)", text)
    if name_match:
        user_name = name_match.group(1).lower()
        ignore_words = ["in", "not", "feeling", "going", "very", "so", "stress", "stressed", "sad", "happy", "depressed", "a", "an", "the", "fine", "good", "bad"]
        if user_name not in ignore_words:
            return f"It's a pleasure to meet you, {user_name.capitalize()}! 😊 I'm ScreenShield AI, built to support your digital wellbeing. How has your day been so far?"
    
    # 3. Direct Name Only Support
    if len(words) == 1 and text not in ["sad", "happy", "stressed", "good", "fine"]:
        return f"Hi {text.capitalize()}! 👋 Please tell me a bit more about your day so I can provide a professional analysis for you. What's on your mind?"

    # 4. Small Talk / Social Manners
    if any(x in text for x in ["how are you", "how r u", "how you doing"]):
        return "I'm doing great, thank you for asking! 🤖 I'm always energized to help you manage your wellbeing. How's everything on your end?"
    
    if any(x in text for x in ["goodnight", "good night", "sleepy", "bye"]):
        return "Goodnight! 🌙 Wishing you a peaceful rest. Remember to put your phone away at least 30 minutes before bed for better sleep!"

    # 5. Identity & Purpose
    if any(x in text for x in ["who are you", "what do you do", "who built you", "your mission"]):
        return "I am ScreenShield AI, a privacy-focused wellbeing guardian designed for the Samsung Innovation Campus. My mission is to help youth balance their digital lives with mental peace. 🛡️"

    # 6. Gratitude
    if any(x in text for x in ["thanks", "thank you", "shukriya", "jazakallah"]):
        return "You're very welcome! ✨ I'm happy to be of service. Always remember, your mental health is a priority."

    # 7. Short Feelings Fallback
    feeling_words = ["sad", "depressed", "anxious", "stressed", "unhappy", "angry", "lonely"]
    if any(w == text for w in feeling_words):
        return "I'm sorry you're feeling this way. 😔 It takes courage to acknowledge these feelings. Can you share a bit more about what triggered this mood?"
    
    # 8. Length-based Humanized Fallback
    if len(words) < 4:
        return "👋 This seems a bit brief. For a professional analysis, I'd love to hear a few more details about your day or what's on your mind right now!"

    return None

if st.button("Analyze My Wellbeing ✨", use_container_width=True):
    # check for conversational intent first
    conv_response = get_conversational_response(user_text)
    
    if user_text.strip() == "":
        st.warning("Please share something about your day first.")
    elif conv_response:
        st.info(conv_response)
    else:
        # Proceed with model analysis
        with st.spinner("AI is reflecting on your day..."):
            vec = vectorizer.transform([user_text])
            mood = nb_model.predict(vec)[0]
            
            # Professional Burnout Calculation (Hybrid)
            base_risk = lr_model.predict([[screen_hours]])[0]
            
            # Mood Impact Adjustment
            mood_bonus = {"High": 15, "Medium": 5, "Low": -10}
            final_risk = base_risk + mood_bonus.get(mood, 0)
            
            # Add some randomness to feel "Human/Realistic"
            import random
            final_risk += random.uniform(-2, 2)
            
            final_risk = max(5, min(100, round(final_risk)))

            suggestions = []
            lt = user_text.lower()
            
            import csv
            try:
                with open('knowledge_base.csv', mode='r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        if row['trigger'].lower() in lt:
                            suggestions.append(row['suggestion'])
            except:
                pass

            if not suggestions:
                suggestions = ["Take a 5-minute break and breathe deeply.", "Put your phone away and talk to a friend."]

            # Save to Database
            db.add_entry(user_text, mood, final_risk, screen_hours, suggestions)
            
            # Fetch the latest entry to set as active analysis
            latest_history = db.get_all_entries()
            if latest_history:
                st.session_state['active_analysis'] = latest_history[0]
            
            st.rerun()

if st.session_state['active_analysis']:
    # Tabs for a Professional Dashboard layout
    tab1, tab2, tab3 = st.tabs(["📊 Today's Analysis", "📈 Wellbeing Trends", "🆘 Help & Resources"])
    
    with tab1:
        result = st.session_state['active_analysis']
        st.divider()
        
        # Bilingual Emotional Engine (Dominant Language Detection)
        def detect_language(text):
            urdu_keywords = ["bohat", "preshan", "hai", "kaam", "nahi", "parhai", "dil", "bura", "sukoon", "thak", "tention", "tension", "acha", "tha", "raha", "hoon", "ghar", "baat", "preshani"]
            words = text.lower().split()
            ur_count = sum(1 for w in words if w in urdu_keywords)
            en_count = len(words) - ur_count
            return "ur" if ur_count > (len(words) * 0.3) else "en" # Threshold 30% for Urdu detection

        user_lang = detect_language(result['text'])
        
        # Professional Narratives (Bilingual)
        narratives = {
            "en": {
                "header_low": "It's wonderful to see you're doing well! 🌟",
                "header_med": "I've noticed some tension in your day, but you've got this. 💪",
                "header_high": "I can feel things are a bit heavy for you right now. 🛡️",
                "body": "Based on your reflection, you are experiencing **{mood} Distress**. It seems like **{stressor}** is weighing on your mind. With a **Burnout Risk of {risk}%**, focus on the plan below to feel grounded. Small breaks build strength."
            },
            "ur": {
                "header_low": "MashAllah! Aapka din bohat acha guzra! 🌟",
                "header_med": "Maine mehsoos kiya ke aaj aap thora pareshan hain, lekin fikr na karein. 💪",
                "header_high": "Main samajh sakta hoon ke aaj bohat bhojh hai aap par. 🛡️",
                "body": "Aapki baaton se lagta hai ke aap **{mood} Distress** (bohat pareshani) mehsoos kar rahe hain. Aisa lagta hai ke **{stressor}** ki wajah se aapka dil udaas hai. Aapka **Burnout Risk {risk}%** hai. Neeche diye gaye mashwaray par amal karein, sukoon milay ga."
            }
        }
        
        # Humanized Narrative choice
        n = narratives[user_lang]
        if result['mood'] == "Low": msg_header = n["header_low"]
        elif result['mood'] == "Medium": msg_header = n["header_med"]
        else: msg_header = n["header_high"]

        # Localized Stressors translation (Simple map)
        stressors = []
        lt = result['text'].lower() 
        if any(x in lt for x in ["exam", "test", "parhai", "paper"]): 
            stressors.append("parhai ka bhojh" if user_lang == "ur" else "academic pressure")
        if any(x in lt for x in ["social", "phone", "scrolling", "insta"]): 
            stressors.append("mobile ka zyada use" if user_lang == "ur" else "excessive digital media")
        if any(x in lt for x in ["heavy", "carry", "weight", "burden", "tension"]): 
            stressors.append("zehni dabao" if user_lang == "ur" else "emotional burden")
        
        str_j = " aur " if user_lang == "ur" else " and "
        stressor_str = str_j.join(stressors) if stressors else ("saari baton" if user_lang == "ur" else "your daily challenges")

        narrative_msg = n["body"].format(mood=result['mood'], stressor=stressor_str, risk=result['burnout'])
        
        st.info(msg_header)
        st_narrative = st.empty()
        full_msg = ""
        words = narrative_msg.split(" ")
        for word in words:
            full_msg += word + " "
            st_narrative.info(full_msg + "▌")
            time.sleep(0.04) 
        st_narrative.info(full_msg)

        st.markdown("---")
        st.write("**💡 Analysis-Based Suggestions:**" if user_lang == "en" else "**💡 Aap ke liye khas mashwaray:**")
        
        # Fetching proper bilingual suggestions
        for i, sug in enumerate(result['suggestions'][:3], 1):
            st.write(f"{i}. {sug}")

        st.subheader("🌥️ Emotional Word Cloud")
        wordcloud = WordCloud(width=800, height=400, background_color='white').generate(result['text'])
        fig, ax = plt.subplots()
        ax.imshow(wordcloud, interpolation='bilinear')
        ax.axis('off')
        st.pyplot(fig)

    with tab2:
        st.subheader("🗓️ Your Wellbeing Journey")
        history_data = db.get_all_entries()
        
        if history_data:
            history_df = pd.DataFrame(history_data)
            
            # Map mood to numeric for charting
            mood_map = {"Low": 1, "Medium": 2, "High": 3}
            history_df['mood_num'] = history_df['mood'].map(mood_map)
            
            # Ensure chronological order by sorting by ID
            plot_df = history_df.sort_values('id')
            
            # Performance Cards
            m1, m2, m3 = st.columns(3)
            avg_burnout = round(plot_df['burnout'].mean())
            avg_hours = round(plot_df['screen_hours'].mean(), 1)
            most_common_mood = plot_df['mood'].mode()[0] if not plot_df['mood'].mode().empty else "N/A"
            
            m1.metric("Avg. Burnout Risk", f"{avg_burnout}%")
            m2.metric("Avg. Phone Usage", f"{avg_hours}h")
            m3.metric("Common Mood", most_common_mood)

            # Charting
            st.divider()
            st.write("📈 **Burnout Risk Progress**")
            # Using time as index but ensuring it's sorted
            st.line_chart(plot_df.set_index('time')['burnout'], color="#0A2540")
            
            st.write("📊 **Mood Stability (1=Calm, 3=Stressed)**")
            st.area_chart(plot_df.set_index('time')['mood_num'], color="#81C784")
            
        else:
            st.info("Log more entries to see your personal trends! Once you have 3+ entries, these charts will show your progress.")

    with tab3:
        st.info("💡 **Take a break, you've earned it.**")
        
        col_a, col_b = st.columns(2)
        with col_a:
            with st.expander("🆘 Professional Help", expanded=True):
                st.markdown("""
                **Pakistani Helplines:**
                *   **Umang (24/7):** `0311-7786264`
                *   **Taskeen:** `0332-5267883`
                *   **Rozan:** `0800-22444`
                *   **Website:** [umang.com.pk](https://www.umang.com.pk)
                """)

        with col_b:
            with st.expander("🌬️ Calming Breath", expanded=True):
                st.markdown("""
                <style>
                @keyframes breathe {
                    0% { transform: scale(1); background-color: #81C784; opacity: 0.6; }
                    50% { transform: scale(1.4); background-color: #4CAF50; opacity: 1; }
                    100% { transform: scale(1); background-color: #81C784; opacity: 0.6; }
                }
                .breathe-box { display: flex; justify-content: center; align-items: center; height: 100px; }
                .breathe-circle {
                    width: 50px; height: 50px; border-radius: 50%;
                    animation: breathe 5s infinite ease-in-out;
                    display: flex; justify-content: center; align-items: center;
                    color: white; font-weight: bold; font-family: sans-serif; font-size: 10px;
                }
                </style>
                <div class="breathe-box"><div class="breathe-circle">BREATHE</div></div>
                """, unsafe_allow_html=True)
                st.caption("Inhale as it grows, exhale as it shrinks.")

st.divider()
st.caption("🛡️ ScreenShield: Social Awareness Project for Samsung AI Innovation Campus • © 2026 Copyright Policy")