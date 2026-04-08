# 🛡️ ScreenShield AI
### Offline Digital Wellbeing Guardian for Pakistani Youth

**ScreenShield AI** is an innovative wellbeing assistant designed for the **Samsung Innovation Campus**. It leverages machine learning to help young Pakistanis manage screen-time burnout and monitor their mental health in a completely private, offline-first environment.

---

## 🌟 Key Features
- **🧠 Mood Prediction**: Uses **TF-IDF Vectorization** and **Naive Bayes** to analyze daily journals and predict emotional states (Low, Medium, or High Distress).
- **🔥 Burnout Risk Assessment**: Implements **Linear Regression** to calculate the percentage of future burnout risk based on current phone usage hours.
- **🌬️ Interactive Breathing Guide**: A non-blocking, fluid CSS-animated breathing assistant to help users ground themselves during high stress.
- **🆘 Professional Crisis Support**: A dedicated directory of Pakistani mental helplines (Umang, Taskeen, Rozan) built directly into the app.
- **☁️ Emotional Word Clouds**: Visualizes your thoughts to help identify recurring stressors and patterns in your day.
- **📜 Smart History**: Keeps a persistent database log of your past reflections and tracks your wellbeing trends over time, stored completely securely on your device.

---

## 🛠️ Technology Stack
- **Frontend**: Streamlit (Python-based Web Framework)
- **Machine Learning**: 
  - `Scikit-learn` (Multinomial Naive Bayes & Linear Regression)
  - `Joblib` (Model Persistence)
- **Data Engineering**: `Pandas`, `CSV`, `SQLite3` (Database)
- **Visualization**: `Matplotlib`, `WordCloud`
- **Styling**: Custom CSS for premium glassmorphism effect.

---

## 🚀 How to Run Locally

### 1. Clone the Project
```bash
git clone <your-repo-link>
cd Samsung-Final-Project
```

### 2. Install Dependencies
Make sure you have Python installed, then run:
```bash
pip install -r requirements.txt
```

### 3. Start the Application
```bash
streamlit run app.py
```

---

## 🇵🇰 Why ScreenShield?
In Pakistan, mental health is often stigmatized. **ScreenShield AI** provides a safe, **private**, and **completely offline** way for students to reflect on their day without their data ever leaving their device.

Built with ❤️ for the **Samsung Innovation Campus**.
