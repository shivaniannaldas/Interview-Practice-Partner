# 🤖 AI Interview Practice Partner  
A Voice-Enabled, Resume-Aware, Human-Like Mock Interview System

This project is built as part of the **Agentic AI Internship Assignment**, delivering a fully interactive mock interview experience with:

- Real-time voice interaction  
- Adaptive questioning  
- Resume-aware intelligence  
- Structured feedback at the end  

---

## 🌟 Key Features

### 🎙️ Real-Time Voice Interaction
- AI interviewer **speaks each question** using Text-to-Speech  
- User answers using **SpeechRecognition API**  
- Hands-free, realistic interview practice  

### 🧠 Human-Like Interviewer Intelligence
- Adaptive tone (Supportive / Strict)  
- Avoids robotic or template-like phrasing  
- Auto follow-up questions when answers are:
  - too short  
  - unclear  
  - off-topic  

### 📄 Resume-Aware Questioning
When the user pastes a resume:

- Skills, tools, projects auto-detected  
- AI asks targeted questions like:
  - “Your resume mentions Water Quality Monitoring — what was your role?”
  - “Can you walk me through a challenge you faced in your Streamlit project?”

### 🔄 Adaptive, Agentic Interview Flow
The interviewer:
- Redirects off-topic users  
- Handles confusion  
- Moves on politely  
- Ends cleanly when user clicks **End Interview**  

### 📝 Automatic Feedback Generation
At the end, AI produces structured feedback:

- 🎯 Overall Summary  
- 🗣️ Communication Skills (x/10)  
- 💻 Technical Strength (x/10)  
- 🧩 Clarity & Structure (x/10)  
- 📌 Resume Usage  
- 🚀 Areas to Improve  

---

## 🗂️ Tech Stack

### **Frontend (React)**
- React + JavaScript  
- Web Speech API (STT)  
- SpeechSynthesis (TTS)  
- Resume text input  
- Live conversation UI  

### **Backend (FastAPI)**
- Python FastAPI  
- Endpoints:
  - `/start-interview`
  - `/answer`
- Groq Llama 3.3 70B for:
  - Resume summary  
  - Dynamic questioning  
  - Follow-up logic  
  - Feedback generation  

### **AI Model**
- **Groq Llama 3.3 70B Versatile**
- Ultra fast inference  
- Perfect for real-time conversations  

---

## 🧠 Architecture Overview

**React UI** ⇄ **FastAPI Backend** ⇄ **Groq LLM**

## State Flow
1. Frontend sends settings  
2. Backend stores interview state  
3. AI asks questions & follow-ups  
4. On end → closing message + feedback  

---

## 🎯 Agentic Behaviors Implemented

### 1️⃣ Conversational Quality
- Short, human-like questions  
- Supportive mode uses mild fillers  
- Strict mode is crisp and professional  

### 2️⃣ Agentic Intelligence
- Detects short/unclear answers → follow-up  
- Redirects when user goes off-topic  
- Warns in strict mode if user avoids answering  

### 3️⃣ Technical Backend Logic
- Resume parsing and summarizing  
- Follow-up detection function  
- Conversation state stored in backend  
- Closing messages + structured feedback  

---

## 🎬 Recommended Demo Scenarios

### 🟦 Scenario 1: Normal User (Supportive Mode)
- Role: Software Engineer  
- Resume attached  

### 🟩 Scenario 2: Confused User
- Very short replies  
- Shows follow-up logic  

### 🟥 Scenario 3: Strict Mode
- Role: Data Analyst  
- Shows warning when avoiding answers  

### 🟨 Scenario 4: Edge Cases
- User says “stop”  
- User goes off-topic  

---

## 🛠️ Installation & Running Locally

### 🔧 Backend Setup (FastAPI)

'''sh
cd backend
python -m venv venv

# Windows
.\venv\Scripts\activate

# Mac/Linux
source venv/bin/activate

pip install -r requirements.txt

# Set API Key
set GROQ_API_KEY=your_key_here      # Windows
export GROQ_API_KEY=your_key_here   # Mac/Linux

uvicorn main:app --reload --port 8000'''

### 💻 Frontend Setup (React)
cd frontend
npm install
npm start

## 📡 API Endpoints

### **POST /start-interview**
Starts the interview and returns the first question.

### **POST /answer**
Sends user answer → returns:
- next question  
- or final feedback  

Supports both **text & voice** flows.

---

## 🧩 Design Decisions
- Follow-up logic mimics real interviewers  
- Resume summarization enables personalization  
- Supportive/Strict modes simulate interviewer variety  
- End interview button allows flexible flow  

---

## 🚀 Future Improvements
- ATS-style resume scoring  
- Coding interview module  
- Multi-round interview support  
- Downloadable PDF feedback  
