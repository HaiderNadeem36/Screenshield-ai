# 🛡️ ScreenShield AI
### Offline Mental Health Journal for Pakistani Users
**Samsung Innovation Campus — Capstone Project**

---

## 🎯 Project Scope

**ScreenShield AI** is a private, offline AI-powered mental health journal. It uses Natural Language Processing to detect emotional distress from daily written reflections and provides age-appropriate, culturally relevant mental health suggestions for Pakistani users aged 15–65.

**One input. One model. One output.**
The user writes about their day → the app predicts their distress level → they receive a meaningful suggestion tailored to their age group.

---

## 🌟 Key Features

- **🧠 Mood Detection** — Uses TF-IDF Vectorization and Multinomial Naive Bayes to classify journal entries into Low, Medium, or High Distress.
- **🎯 Confidence-Based Fallback** — When model confidence is below threshold, a keyword-based emotion scan ensures the user always receives a helpful, compassionate response — never a dead end.
- **👤 Age-Appropriate Suggestions** — Users set their age once at launch. Suggestions are filtered from SQLite by both predicted mood and age group (15–25, 26–40, 41–65) for more relevant, life-stage-aware support.
- **🗄️ Unified SQLite Storage** — All data — journal entries and suggestion content — lives in a single SQLite database (`wellbeing.db`). No runtime file I/O. No CSV scanning on every submission.
- **📜 Personal Journal History** — Every reflection is saved securely on-device with mood and timestamp. Users can browse, reload, or delete past entries from the sidebar.
- **📈 Mood Trend Chart** — A visual timeline of mood scores across all entries to help users identify patterns in their emotional wellbeing.

---

## 🛠️ Technology Stack

| Layer | Technology |
|---|---|
| Frontend | Streamlit (Python Web Framework) |
| Machine Learning | Scikit-learn — Multinomial Naive Bayes |
| Vectorization | TF-IDF (Term Frequency–Inverse Document Frequency) |
| Model Persistence | Joblib |
| Database | SQLite3 (via Python standard library) |
| Data Handling | Pandas |
| Styling | Custom CSS — Glassmorphism UI |

---

## 🚀 How to Run Locally

### 1. Clone the Project
```bash
git clone <your-repo-link>
cd ScreenShield-AI
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Start the Application
```bash
streamlit run app.py
```

The app will open in your browser. On first launch, you will be asked to enter your age — this sets your age group for suggestion filtering and is stored only for the current session.

---

## 📁 File Structure

```
ScreenShield-AI/
│
├── app.py                  — Main Streamlit application
├── database_manager.py     — SQLite operations (journals + suggestions)
├── knowledge_base.csv      — Source data for suggestions (loaded once into DB)
├── journal_data.csv        — Training dataset archive (not used at runtime)
├── nb_model.pkl            — Trained Naive Bayes model
├── vectorizer.pkl          — Trained TF-IDF vectorizer
├── requirements.txt        — Python dependencies
└── README.md               — This file
```

---

## 🔒 Privacy First

ScreenShield AI is completely offline. No data ever leaves your device. All journal entries are stored locally in `wellbeing.db` — a SQLite database file on your own machine. There is no server, no cloud sync, and no analytics tracking.

---

## 🇵🇰 Why ScreenShield AI?

Mental health stigma remains a significant barrier in Pakistan. ScreenShield AI provides a safe, private, and judgment-free space for users to reflect on their emotional state without fear of exposure. Built specifically for the Pakistani context, with age-appropriate suggestions grounded in local life stages — from student pressure (15–25) to career and family stress (26–40) to the challenges of later adulthood (41–65).

---

## 🔭 Future Work

The following enhancements are planned for future versions:

- **Multilingual Support** — Proper handling of Roman Urdu, Urdu script, and code-switched (mixed language) input using multilingual transformer models such as mBERT or XLM-RoBERTa. This is a known challenge in South Asian NLP and requires a dedicated training dataset in these languages.
- **Expanded Training Data** — Adding more labeled journal entries to `journal_data.csv` and retraining the Naive Bayes model to improve mood prediction accuracy across a wider range of vocabulary.
- **User Authentication** — Persistent user profiles with secure login, allowing multiple users on the same device with isolated journal histories.
- **Mood Analytics Dashboard** — Deeper trend analysis with weekly and monthly emotional pattern visualizations.

---

*Built with ❤️ for the Samsung Innovation Campus — © 2026*
