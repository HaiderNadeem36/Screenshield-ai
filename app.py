import streamlit as st
import joblib
import pandas as pd
import time
import database_manager as db

# ─────────────────────────────────────────────
# DATABASE & KNOWLEDGE BASE INITIALISATION
# init_db()            — creates journals + suggestions tables if not exist
# init_knowledge_base() — populates suggestions table from CSV on first launch only
# ─────────────────────────────────────────────
db.init_db()
db.init_knowledge_base()

# ─────────────────────────────────────────────
# PAGE CONFIGURATION
# ─────────────────────────────────────────────
st.set_page_config(page_title="ScreenShield AI", page_icon="🛡️", layout="centered")

# ─────────────────────────────────────────────
# CUSTOM CSS — Glassmorphism styling
# ─────────────────────────────────────────────
st.markdown("""
<style>

/* Sidebar main background */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0A2540 0%, #071826 100%);
    color: white;
}

/* Sidebar buttons (history items) */
div[data-testid="stSidebarUserContent"] button {
    background-color: rgba(255,255,255,0.05) !important;
    border: none !important;
    text-align: left !important;
    padding: 0.8rem !important;
    margin-bottom: 6px !important;
    border-radius: 10px !important;
    color: #E3F2FD !important;   /* LIGHT TEXT ✅ */
    width: 100% !important;
    font-size: 0.95rem;
}

/* Hover effect */
div[data-testid="stSidebarUserContent"] button:hover {
    background: linear-gradient(90deg, #1E88E5, #42A5F5) !important;
    color: white !important;
    transform: translateX(3px);
    transition: 0.2s ease;
}

/* Active / selected feel */
div[data-testid="stSidebarUserContent"] button:focus {
    background-color: #1565C0 !important;
    color: white !important;
}

/* Sidebar headings */
section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3 {
    color: #BBDEFB !important;
}

/* Divider line */
section[data-testid="stSidebar"] hr {
    border-color: rgba(255,255,255,0.1);
}

/* New Journal button */
div[data-testid="stSidebar"] .stButton button[kind="primary"] {
    background: linear-gradient(90deg, #00C6FF, #0072FF) !important;
    color: white !important;
    border: none !important;
    border-radius: 12px !important;
    padding: 10px !important;
    font-weight: bold;
}

/* Improve contrast for icons/text */
section[data-testid="stSidebar"] * {
    color: #E3F2FD;
}

</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# AGE GROUP REGISTRATION — ONE-TIME ON FIRST LAUNCH
# User enters age once per session.
# Age is mapped to one of three brackets:
#   15-25  → student / early adult
#   26-40  → working adult
#   41-65  → middle / senior adult
# Age group is stored in session state and used
# to filter suggestions from the SQLite DB.
# ─────────────────────────────────────────────
if "age_group" not in st.session_state:
    st.title("🛡️ ScreenShield AI")
    st.subheader("Your Private Mental Health Journal")
    st.divider()
    st.markdown("### Welcome! Before we begin, tell us your age.")
    st.caption("This helps us give you suggestions that are relevant to your stage of life.")

    age = st.number_input("Your Age", min_value=15, max_value=65, value=20, step=1)

    if st.button("Continue →", use_container_width=True):
        # Map age to bracket — 41 starts third bracket to avoid overlap with 26-40
        if age <= 25:
            st.session_state["age_group"] = "15-25"
        elif age <= 40:
            st.session_state["age_group"] = "26-40"
        else:
            st.session_state["age_group"] = "41-65"
        st.rerun()

    st.stop()  # Do not render rest of app until age is set


# ─────────────────────────────────────────────
# SESSION STATE INITIALISATION
# ─────────────────────────────────────────────
if 'active_analysis' not in st.session_state:
    st.session_state['active_analysis'] = None


def start_new_chat():
    """Clears current journal input and active analysis for a fresh entry."""
    st.session_state['main_journal_input'] = ""
    st.session_state['active_analysis'] = None


# ─────────────────────────────────────────────
# SIDEBAR — JOURNAL HISTORY
# Displays all past entries from SQLite journals table.
# Each entry shows mood and timestamp.
# User can load or delete any past entry.
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown(
        """
        <div style="margin-left: 5px; margin-bottom: 10px;">
            <h2 style="margin:0; padding:0; font-size: 1.6rem;
                color:#0A2540; font-family:'Inter', sans-serif;">
                🛡️ ScreenShield
            </h2>
        </div>
        """, unsafe_allow_html=True
    )
    st.button("➕ New Journal", on_click=start_new_chat,
              type="primary", use_container_width=True)
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
                    st.session_state['active_analysis'] = entry
                    st.rerun()
            with c2:
                if st.button("🗑️", key=f"del_{entry['id']}", help="Delete this entry"):
                    db.delete_entry(entry['id'])
                    if (st.session_state['active_analysis'] and
                            st.session_state['active_analysis']['id'] == entry['id']):
                        st.session_state['active_analysis'] = None
                    st.rerun()


# ─────────────────────────────────────────────
# MODEL LOADING — CACHED
# Loads Naive Bayes model and TF-IDF vectorizer once.
# lr_model (Linear Regression burnout) is removed — no longer used.
# ─────────────────────────────────────────────
@st.cache_resource
def load_models():
    nb = joblib.load('nb_model.pkl')
    vec = joblib.load('vectorizer.pkl')
    return nb, vec

nb_model, vectorizer = load_models()


# ─────────────────────────────────────────────
# CONFIDENCE-BASED FALLBACK — MOOD INFERENCE
# Called when NB model confidence is below 0.45 threshold.
# Two-layer fallback:
#   Layer 1 — scan 15 basic emotion keywords
#   Layer 2 — default to Medium if no keywords found
# This ensures user always receives a helpful response
# and is never asked to rephrase their feelings.
# ─────────────────────────────────────────────
def fallback_mood(text):
    negative_words = [
        "sad", "tired", "angry", "lonely", "scared",
        "worried", "upset", "confused", "lost", "empty"
    ]
    positive_words = ["happy", "good", "fine", "okay", "great"]

    text_lower = text.lower()
    neg_count = sum(1 for w in negative_words if w in text_lower)
    pos_count = sum(1 for w in positive_words if w in text_lower)

    if neg_count > pos_count:
        return "Medium"   # Distressed signal — Medium is compassionate middle ground
    elif pos_count > neg_count:
        return "Low"      # Positive signal
    else:
        return "Medium"   # No signal — safe default, not alarming


# ─────────────────────────────────────────────
# CONVERSATIONAL RESPONSE HANDLER
# Intercepts casual, greeting, or short inputs
# before they reach the ML model.
# Returns a friendly string response or None
# if the input should proceed to full analysis.
# ─────────────────────────────────────────────
def get_conversational_response(text):
    text_lower = text.lower().strip()
    words = text_lower.split()

    from datetime import datetime
    hour = datetime.now().hour
    time_greeting = ("Good Morning" if hour < 12
                     else "Good Afternoon" if hour < 18
                     else "Good Evening")

    # Greetings
    greetings = ["hi", "hello", "hey", "morning", "night"]
    if any(g in text_lower for g in greetings) and len(words) < 8:
        return (f"{time_greeting}! 👋 I'm your ScreenShield AI guardian. "
                f"How are you feeling today?")

    # Name capture
    import re
    name_match = re.search(
        r"(?:my name is|i am|this is|call me|i'm)\s+([a-zA-Z]+)", text_lower)
    if name_match:
        user_name = name_match.group(1)
        ignore = ["in", "not", "feeling", "going", "very", "so", "stress",
                  "stressed", "sad", "happy", "depressed", "fine", "good", "bad"]
        if user_name not in ignore:
            return (f"It's a pleasure to meet you, {user_name.capitalize()}! 😊 "
                    f"I'm ScreenShield AI, here to support your mental wellbeing. "
                    f"How has your day been?")

    # Small talk
    if any(x in text_lower for x in ["how are you", "how r u", "how you doing"]):
        return ("I'm doing great, thank you for asking! 🤖 "
                "I'm always here to help you manage your wellbeing. "
                "How are you feeling today?")

    if any(x in text_lower for x in ["goodnight", "good night", "bye"]):
        return "Goodnight! 🌙 Wishing you a peaceful rest. Take care of yourself."

    # Identity
    if any(x in text_lower for x in ["who are you", "what do you do", "who built you"]):
        return ("I am ScreenShield AI — a private, offline mental health journal "
                "built for the Samsung Innovation Campus. I help you reflect on "
                "your day and understand your emotional wellbeing. 🛡️")

    # Gratitude
    if any(x in text_lower for x in ["thanks", "thank you", "shukriya", "jazakallah"]):
        return ("You're very welcome! ✨ "
                "Remember, your mental health matters. I'm always here.")

    # Single feeling words
    feeling_words = ["sad", "depressed", "anxious", "stressed",
                     "unhappy", "angry", "lonely"]
    if any(w == text_lower for w in feeling_words):
        return ("I'm sorry you're feeling this way. 😔 "
                "It takes courage to acknowledge these feelings. "
                "Can you share a bit more so I can understand better?")

    return None  # Proceed to full ML analysis


# ─────────────────────────────────────────────
# MAIN APP — TITLE & JOURNAL INPUT
# ─────────────────────────────────────────────
st.title("🛡️ ScreenShield AI")
st.subheader("Your Private Mental Health Journal")

# Display current age group context
age_group = st.session_state["age_group"]
st.caption(f"👤 Age group: {age_group}")

# Journal text area — max 1500 characters (~300 words)
user_text = st.text_area(
    "How was your day? Share your thoughts freely.",
    height=160,
    placeholder="Write about how you are feeling today...",
    key="main_journal_input",
    max_chars=1500
)

# Live word counter display
word_count = len(user_text.split()) if user_text.strip() else 0
counter_class = "word-counter over" if word_count > 300 else "word-counter"
st.markdown(
    f'<p class="{counter_class}">{word_count} / 300 words</p>',
    unsafe_allow_html=True
)


# ─────────────────────────────────────────────
# ANALYSIS BUTTON — FULL PIPELINE
# ─────────────────────────────────────────────
if st.button("Analyze My Wellbeing ✨", use_container_width=True):

    # ── INPUT VALIDATION (Error Handlers A, B, C) ──────────────────
    # Error A — Empty input
    if not user_text.strip():
        st.error("Please write something before submitting.")
        st.stop()

    # Error B — Numeric only input
    elif user_text.strip().isdigit():
        st.error("Please describe your feelings in words, not numbers.")
        st.stop()

    # Error C — Too short (under 5 words)
    elif len(user_text.split()) < 5:
        st.error("Please write at least 5 words so we can understand how you're feeling.")
        st.stop()

    else:
        # ── CONVERSATIONAL INTENT CHECK ────────────────────────────
        conv_response = get_conversational_response(user_text)
        if conv_response:
            st.info(conv_response)

        else:
            # ── FULL ML ANALYSIS PIPELINE ──────────────────────────
            with st.spinner("Reflecting on your day..."):

                # Step 1 — Vectorize input text using trained TF-IDF
                vec = vectorizer.transform([user_text])

                # Step 2 — Predict mood with Naive Bayes
                proba = nb_model.predict_proba(vec)[0]
                max_confidence = max(proba)

                # Step 3 — Confidence threshold check (0.45)
                # If confidence is low (out-of-vocabulary / unclear input),
                # use keyword fallback instead of model prediction.
                # User is never asked to rephrase — always gets a helpful output.
                used_fallback = False
                if max_confidence >= 0.45:
                    mood = nb_model.predict(vec)[0]
                else:
                    mood = fallback_mood(user_text)
                    used_fallback = True

                # Step 4 — Fetch age-appropriate suggestion from SQLite
                # SQL: WHERE mood = ? AND age_group = ? ORDER BY RANDOM() LIMIT 1
                suggestion = db.get_suggestion(mood, age_group)

                # Step 5 — Save entry to journals table
                db.add_entry(user_text, mood, [suggestion])

                # Step 6 — Set as active analysis for display
                latest_history = db.get_all_entries()
                if latest_history:
                    st.session_state['active_analysis'] = latest_history[0]
                    st.session_state['used_fallback'] = used_fallback

                st.rerun()


# ─────────────────────────────────────────────
# ANALYSIS RESULTS DISPLAY
# Shown after a successful analysis is saved.
# Two tabs: Today's Analysis | Wellbeing Trends
# ─────────────────────────────────────────────
if st.session_state['active_analysis']:
    tab1, tab2 = st.tabs(["📊 Today's Analysis", "📈 Wellbeing Trends"])

    with tab1:
        result = st.session_state['active_analysis']
        used_fallback = st.session_state.get('used_fallback', False)
        st.divider()

        # ── EMPATHETIC FALLBACK MESSAGE ─────────────────────────────
        # Shown only when low-confidence fallback was triggered.
        # Validates the user's experience without asking them to rewrite.
        if used_fallback:
            st.info(
                "It seems like today's feelings are hard to put into words — "
                "and that's completely okay. Here are some gentle reminders for you."
            )

        # ── MOOD HEADER MESSAGE ─────────────────────────────────────
        mood_headers = {
            "Low":    "It's wonderful to see you're doing well today! 🌟",
            "Medium": "I've noticed some tension in your day, but you've got this. 💪",
            "High":   "I can feel things are a bit heavy for you right now. 🛡️"
        }
        st.info(mood_headers.get(result['mood'], ""))

        # ── ANIMATED NARRATIVE ──────────────────────────────────────
        narrative = (
            f"Based on your reflection, you are experiencing "
            f"**{result['mood']} Distress**. "
            f"Small steps forward are still progress — "
            f"please be kind to yourself today."
        )

        st_narrative = st.empty()
        full_msg = ""
        for word in narrative.split(" "):
            full_msg += word + " "
            st_narrative.info(full_msg + "▌")
            time.sleep(0.04)
        st_narrative.info(full_msg)

        # ── SUGGESTION DISPLAY ──────────────────────────────────────
        st.markdown("---")
        st.write("**💡 Suggestion for You:**")
        for i, sug in enumerate(result['suggestions'], 1):
            st.write(f"{i}. {sug}")

    with tab2:
        st.subheader("🗓️ Your Wellbeing Journey")
        history_data = db.get_all_entries()

        if history_data:
            history_df = pd.DataFrame(history_data)

            # Map mood to numeric for chart — 1=Low, 2=Medium, 3=High
            mood_map = {"Low": 1, "Medium": 2, "High": 3}
            history_df['mood_num'] = history_df['mood'].map(mood_map)
            plot_df = history_df.sort_values('id')

            # Summary metric — most common mood
            most_common_mood = (plot_df['mood'].mode()[0]
                                if not plot_df['mood'].mode().empty else "N/A")
            st.metric("Most Common Mood", most_common_mood)

            st.divider()
            st.write("📊 **Mood Trend (1=Calm, 2=Moderate, 3=High Distress)**")
            st.area_chart(plot_df.set_index('time')['mood_num'], color="#0A2540")

        else:
            st.info("Log more entries to see your personal mood trends here.")


# ─────────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────────
st.divider()
st.caption(
    "🛡️ ScreenShield AI — Mental Health Journal | "
    "Samsung Innovation Campus © 2026"
)
