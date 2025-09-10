## 🏥 HealthAI : Your AI-Powered Health Companion 

HealthAI is designed to be a comprehensive health assistant. Its backend is built using Python with the FastAPI framework, integrating with a PostgreSQL database for persistent storage and leveraging advanced AI models (via Google Generative AI) for its core functionalities. The application supports user authentication, chat interactions with specialized AI agents, medication management, and symptom assessment.

## Key Features 

- **AI-Powered Chat Assistant**: Engage in conversations with specialized AI agents (General Health, Symptom Checker, Nutritionist, Mental Health Coach) for tailored advice.

- **User Authentication**: Secure signup and sign-in process with JWT-based authentication.

- **Medication Management**: Track prescribed medications, dosages, and schedules, with reminders and dose tracking.

- **Symptom Assessment**: Input symptoms to receive AI-driven analysis, potential conditions, and recommended actions.

- **Health Metrics Tracking**: Monitor key health indicators like sleep quality and hydration.

- **User Profile Management**: Store and update user profile information.

## 💻 Technology Stack

- **Backend Framework**: FastAPI

- **Frontend**: React/Vite 

- **Language**: Python 3.9+ 

- **Database**: PostgreSQL

- **ORM**: SQLAlchemy

- **AI Models**: Langchain, LangGraph, Google Generative AI (Gemini)

- **Authentication**: JWT (JSON Web Tokens)

- **Deployment**: Used Render for deploying the FastApi backend and Vercel for the frontend, and then joined them using CORS

- **Frontend Integration**: CORS middleware configured for a frontend likely running on http://localhost:5173 

## Try the web APP 

🌐 Live : https://health-ai-nine-rho.vercel.app/

## How to Use HealthAI locally 

1. **Clone the Repository**:

   ```bash
   git clone https://github.com/DRITI2906/HealthAI.git
   cd HealthAI
   ```

2. **Setup Backend**:

   ```bash
   cd backend
   python -m venv venv
   .\venv\Scripts\activate     
   pip install -r requirements.txt
   uvicorn main:app --reload --port 8000
   ```   

3. **Setup Frontend**:

   ```bash 
   npm run dev
   ```    

## ❓ Why HealthAI

Existing health apps usually focus on one problem at a time — step tracking, symptom lookup, or medication reminders. HealthAI is different because it brings all of these together in one AI-powered platform.

- **🤖 AI-Driven Symptom Checker**: Instead of static symptom checkers that give vague results, HealthAI leverages Google’s Gemini + LangChain to provide context-aware analysis, possible conditions, and actionable next steps.

- **💊 Medication Management**: Beyond reminders, HealthAI stores doses, tracks adherence, and supports future expansion for smart notifications.

- **🧠 Multi-Specialized AI Agents**: Not just a chatbot — HealthAI has specialized personas (General Health, Symptom Checker, Nutritionist, Mental Health Coach) that provide more relevant and tailored advice.

- **📊 Comprehensive Health View**: Tracks lifestyle metrics like sleep and hydration, along with symptoms and medications, so users get a 360° perspective of their health in one place.

- **🔐 Secure & Scalable**: Built with FastAPI + PostgreSQL + JWT authentication, making it production-ready, secure, and capable of scaling with real user data.

- **🌍 Frontend + Backend Integration**: With React/Vite on the frontend and FastAPI on the backend, it’s fully designed for smooth integration and deployment. 

## ScreenShots



## Developers Information

Created by Driti Rathod. Connect with me on 

- [GitHub](https://github.com/DRITI2906)
- [LinkedIn](https://www.linkedin.com/in/driti-rathod-ab038a294/)
- [Email](mailto:dritirathod2906@gmail.com)
