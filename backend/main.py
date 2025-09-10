from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import os
import json
from datetime import datetime, timezone
# Enable database imports
from sqlalchemy.orm import Session
from database import get_db, create_tables
from models import User, ChatSession, ChatMessage, Medication as MedicationDB
from auth import get_password_hash, authenticate_user, create_access_token, get_current_user
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, END
from dotenv import load_dotenv
import uuid
from sqlalchemy import JSON


load_dotenv()

import re

def format_response(text: str) -> str:
    """
    Format AI response into clean Markdown with:
    - Proper headings
    - Consistent bullet points
    - Bolded keywords
    - Separated disclaimers
    """

    if not text:
        return ""

    # Ensure bullets use '-' instead of '*'
    text = re.sub(r"^\s*\*", "-", text, flags=re.MULTILINE)

    # Fix bullets like "- *Thing:*" → keep them consistent
    text = re.sub(r"-\s*\\(.+?):\\", r"- *\1*:", text)

    # Add line breaks after headings (## or ###)
    text = re.sub(r"(#+\s[^\n]+)", r"\1\n", text)

    # Add spacing after sentences
    text = re.sub(r'([.!?])\s+(?=[A-Z])', r'\1\n\n', text)

    return text.strip()

app = FastAPI()

# Create database tables on startup
@app.on_event("startup")
async def startup_event():
    try:
        from database import migrate_database
        migrate_database()
        print("Database migration completed successfully")
    except Exception as e:
        print(f"Error during database migration: {e}")
        # Fallback to regular table creation
        try:
            from database import create_tables
            create_tables()
            print("Database tables created successfully (fallback)")
        except Exception as e2:
            print(f"Error creating database tables: {e2}")

# List of allowed origins (add your frontend domains here)
origins = [
    "https://health-mate-red.vercel.app",
    "http://localhost:3000",
    "http://localhost:5173",  # Vite default port
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-Requested-With"],
    expose_headers=["Content-Length"],
)

class ChatRequest(BaseModel):
    message: str
    agent_type: Optional[str] = "general"
    response_style: Optional[str] = "concise"  # Add response style parameter

class ChatResponse(BaseModel):
    response: str
    session_id: str

class SignupRequest(BaseModel):
    username: str
    email: str
    password: str
    full_name: Optional[str] = None
    date_of_birth: Optional[str] = None  # ISO format string

class SigninRequest(BaseModel):
    username: str
    password: str

class SymptomAssessmentRequest(BaseModel):
    symptoms: List[dict]

class SymptomAssessmentResponse(BaseModel):
    riskLevel: str
    conditions: List[dict]
    immediateActions: List[str]
    precautions: List[str]
    medications: List[str]
    lifestyleChanges: List[str]
    whenToSeekHelp: List[str]
    followUp: str

llm = None

# Initialize LLM only if API key is available
try:
    api_key = os.getenv("GOOGLE_API_KEY")
    print(f"DEBUG: Google API key found: {api_key is not None}")
    if api_key and api_key != "your_google_api_key_here":
        print("DEBUG: Initializing LLM with Google API key")
        llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash",google_api_key=api_key)
        print("DEBUG: LLM initialized successfully")
    else:
        print("Warning: Google API key not set. AI features will be limited.")
        print("DEBUG: Set GOOGLE_API_KEY environment variable to enable AI features")
except Exception as e:
    print(f"Warning: Could not initialize LLM: {e}. AI features will be limited.")
    print(f"DEBUG: LLM initialization error details: {e}")

# Prompt templates for each agent type
PROMPT_TEMPLATES = {
    "general": (
        "You are a helpful general health assistant. "
        "Response Style: {response_style}\n\n"
        "If response_style is 'concise': Keep your answer brief and to the point (2-3 sentences max). "
        "If response_style is 'detailed': Provide comprehensive information with examples and explanations.\n\n"
        "Always format your response in *Markdown* with:\n"
        "- Clear headings (## Heading)\n"
        "- Bullet points (- item)\n"
        "- Bold keywords (*word*)\n\n"
        "Answer the following user question:\nUser: {message}"
    ),
    "symptom": (
        "You are a symptom checker AI. "
        "Response Style: {response_style}\n\n"
        "If response_style is 'concise': Give brief, direct answers (2-3 sentences max). "
        "If response_style is 'detailed': Provide comprehensive analysis with multiple sections.\n\n"
        "Always format your response in *Markdown* with:\n"
        "- Clear sections (## Symptoms, ## Possible Causes, ## Next Steps)\n"
        "- Bullet points (- item)\n"
        "- Bold important terms (*term*)\n\n"
        "User: {message}"
    ),
    "nutrition": (
        "You are a nutrition expert AI. "
        "Response Style: {response_style}\n\n"
        "If response_style is 'concise': Keep advice brief and actionable (2-3 sentences max). "
        "If response_style is 'detailed': Provide comprehensive guidance with examples and explanations.\n\n"
        "Always format your response in *Markdown* with:\n"
        "- Headings for structure (## Diet Tips, ## Foods to Include, ## Foods to Avoid)\n"
        "- Bullet points for lists\n"
        "- Bold important nutrients and food names\n\n"
        "User: {message}"
    ),
    "mental-health": (
        "You are a mental health coach AI. "
        "Response Style: {response_style}\n\n"
        "If response_style is 'concise': Give brief, supportive advice (2-3 sentences max). "
        "If response_style is 'detailed': Provide comprehensive strategies with examples and resources.\n\n"
        "Always format your response in *Markdown* with:\n"
        "- Headings for clarity (## Coping Strategies, ## Resources, ## Self-Care)\n"
        "- Bullet points for advice\n"
        "- Bold key ideas for emphasis\n\n"
        "User:{message}"
    ),
} 

def get_prompt(agent_type: str, message: str, response_style: str = "concise") -> str:
    print("DEBUG get_prompt called with agent_type:", agent_type, "message:", message, "response_style:", response_style)
    template = PROMPT_TEMPLATES.get(agent_type, PROMPT_TEMPLATES["general"])
    print("DEBUG get_prompt template:", template)
    print("DEBUG get_prompt message:", message)
    return template.format(message=message, response_style=response_style)

def llm_node(state: dict):
    print("DEBUG llm_node state at entry:", state)
    agent_type = state.get("agent_type", "general")
    message = state.get("message", "")
    response_style = state.get("response_style", "concise")
    
    # Check if LLM is available
    if llm is None:
        # Provide fallback response when LLM is not available
        fallback_responses = {
            "general": "I'm currently in maintenance mode. Please try again later or contact support.",
            "symptom": "Symptom checking is temporarily unavailable. Please consult a healthcare professional for medical advice.",
            "nutrition": "Nutrition advice is temporarily unavailable. Please consult a registered dietitian for personalized guidance.",
            "mental-health": "Mental health support is temporarily unavailable. Please contact a mental health professional or crisis hotline if you need immediate help."
        }
        state["response"] = fallback_responses.get(agent_type, fallback_responses["general"])
        return state
    
    prompt = get_prompt(agent_type, message, response_style)
    print("DEBUG llm_node prompt:", prompt)
    try:
        response = llm.invoke(prompt)
        print("DEBUG llm_node raw response:", response)
        # Try to extract the content robustly
        if hasattr(response, "content") and response.content:
            state["response"] = response.content
        elif hasattr(response, "text") and response.text:
            state["response"] = response.text
        elif isinstance(response, str):
            state["response"] = response
        else:
            state["response"] = str(response)
        print("DEBUG llm_node extracted response:", state["response"])
    except Exception as e:
        print("ERROR in llm_node:", e)
        state["response"] = f"Internal error in llm_node: {str(e)}"
    return state

graph = StateGraph(dict)
graph.add_node("llm_node", llm_node)
graph.set_entry_point("llm_node")
graph.add_edge("llm_node", END)
chat_workflow = graph.compile()

class MedicationResponse(BaseModel):
    id: str
    name: str
    dosage: str
    frequency: str
    prescribedBy: str
    startDate: datetime
    endDate: Optional[datetime] = None
    totalDoses: Optional[int] = None
    instructions: Optional[str] = None

class MedicationCreate(BaseModel):
    name: str
    dosage: str
    frequency: str
    prescribedBy:str
    startDate: datetime
    endDate: Optional[datetime] = None
    totalDoses: Optional[int] = None
    instructions: Optional[str] = None

class UserProfileResponse(BaseModel):
    id: int
    username: str
    email: str
    full_name: Optional[str] = None
    date_of_birth: Optional[str] = None

class DoseTakenRequest(BaseModel):
    medicationId: str
    date: str  # ISO date string (YYYY-MM-DD)
    count: int

@app.get("/")
def read_root():
    return {"message": "Welcome to the Health Chatbot FastAPI backend!"}

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.get("/test-symptoms")
def test_symptoms():
    """Test endpoint to check if symptom assessment is working"""
    return {
        "message": "Symptom assessment endpoint is working",
        "llm_available": llm is not None,
        "api_keyset": os.getenv("GOOGLE_API_KEY") is not None,
        "llm_type": str(type(llm)) if llm else "None"
    }

@app.get("/test-llm")
def test_llm():
    """Test endpoint to check if LLM is working"""
    try:
        if llm is None:
            return {"error": "LLM not available"}
        
        # Test a simple prompt
        test_prompt = "Say 'Hello, LLM is working!'"
        response = llm.invoke(test_prompt)
        
        return {
            "success": True,
            "response": str(response.content) if hasattr(response, 'content') else str(response),
            "response_type": str(type(response))
        }
    except Exception as e:
        return {"error": str(e), "traceback": str(e._traceback_)}

@app.post("/api/signup")
async def signup(request: SignupRequest, db: Session = Depends(get_db)):
    """User signup endpoint"""
    try:
        # Check if user already exists
        existing_user = db.query(User).filter(User.username == request.username).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="Username already registered")

        existing_email = db.query(User).filter(User.email == request.email).first()
        if existing_email:
            raise HTTPException(status_code=400, detail="Email already registered")

        # Create new user with hashed password and profile info
        password_hash = get_password_hash(request.password)
        dob = None
        if request.date_of_birth:
            try:
                dob = datetime.strptime(request.date_of_birth, "%Y-%m-%d").date()
            except Exception:
                dob = None
        new_user = User(
            username=request.username,
            email=request.email,
            password_hash=password_hash,
            full_name=request.full_name,
            date_of_birth=dob
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        return {"success": True, "message": "User created successfully", "user_id": new_user.id}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating user: {str(e)}")

# Profile update request model
class ProfileUpdateRequest(BaseModel):
    full_name: Optional[str] = None
    date_of_birth: Optional[str] = None  # ISO format string

# Profile update endpoint
@app.put("/api/profile", response_model=UserProfileResponse)
async def update_profile(
    request: ProfileUpdateRequest, 
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    updated = False
    if request.full_name is not None:
        current_user.full_name = request.full_name
        updated = True
    if request.date_of_birth is not None:
        try:
            current_user.date_of_birth = datetime.strptime(request.date_of_birth, "%Y-%m-%d").date()
            updated = True
        except Exception:
            pass
    if updated:
        db.add(current_user)
        db.commit()
        db.refresh(current_user)
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "date_of_birth": current_user.date_of_birth.isoformat() if current_user.date_of_birth else None
    }

@app.post("/api/signin")
async def signin(request: SigninRequest, db: Session = Depends(get_db)):
    """User signin endpoint"""
    user = authenticate_user(db, request.username, request.password)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password"
        )
    
    # Create access token
    access_token = create_access_token(
        data={"sub": str(user.id), "username": user.username}
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": user.id,
        "username": user.username,
        "email": user.email
    }

@app.post("/api/users")
async def create_user(username: str, email: str, db: Session = Depends(get_db)):
    """Create a test user for development (legacy endpoint)"""
    try:
        # Check if user already exists
        existing_user = db.query(User).filter(User.username == username).first()
        if existing_user:
            return {"success": True, "user": existing_user, "message": "User already exists"}
        
        # Create new user with default password
        password_hash = get_password_hash("password123")  # Default password
        new_user = User(username=username, email=email, password_hash=password_hash)
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        return {"success": True, "user": {"id": new_user.id, "username": username, "email": email}, "message": "User created successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating user: {str(e)}")

@app.get("/api/users")
async def get_users(db: Session = Depends(get_db)):
    """Get all users for testing"""
    users = db.query(User).all()
    return {"users": [{"id": u.id, "username": u.username, "email": u.email} for u in users]}

@app.get("/api/profile")
def get_profile(current_user: User = Depends(get_current_user)):
    return {
        "user_id": current_user.id,
        "email": current_user.email,
        "full_name": current_user.full_name if current_user.full_name else current_user.username if hasattr(current_user, "username") else "",
        "date_of_birth": str(current_user.date_of_birth) if current_user.date_of_birth else "",
        "username": current_user.username if hasattr(current_user, "username") else "",
    }

@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(
    request: ChatRequest, 
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    print("DEBUG /api/chat received:", request)
    try:
        # Use authenticated user
        user_id = current_user.id
        session_id = f"session_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"

        # Create chat session
        chat_session = ChatSession(
            user_id=user_id,
            session_id=session_id,
            agent_type=request.agent_type
        )
        db.add(chat_session)
        db.flush()  # Get the ID without committing yet

        # Store user message
        user_message = ChatMessage(
            session_id=chat_session.id,  # Use the actual session ID
            message_type="user",
            content=request.message,
            message_metadata={"agent_type": request.agent_type}
        )
        db.add(user_message)

        # Generate AI response
        state = {"agent_type": request.agent_type, "message": request.message, "response_style": request.response_style}
        try:
            result = chat_workflow.invoke(state)
            if not result or not isinstance(result, dict):
                response_text = "Sorry, I couldn't generate a response (workflow returned nothing)."
            else:
                raw_response = result.get("response", "Sorry, I couldn't generate a response.")
                response_text = format_response(raw_response)

            # Store AI response
            ai_message = ChatMessage(
                session_id=chat_session.id,  # Use the actual session ID
                message_type="assistant",
                content=response_text,
                message_metadata={"agent_type": request.agent_type}
            )
            db.add(ai_message)

            # Commit everything to database
            db.commit()

            print(f"DEBUG: Chat session {session_id} created, messages stored")
            return ChatResponse(response=response_text, session_id=session_id)

        except Exception as e:
            db.rollback()
            print("ERROR in AI response generation:", e)
            raise HTTPException(status_code=500, detail=f"AI response error: {str(e)}")

    except Exception as e:
        db.rollback()
        print("ERROR in /api/chat:", e)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/api/medications")
async def get_medications(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all medications for the authenticated user"""
    medications = db.query(MedicationDB).filter(MedicationDB.user_id == current_user.id).all()
    
    # Convert database objects to response format
    meds_response = []
    for med in medications:
        meds_response.append({
            "id": med.id,
            "name": med.name,
            "dosage": med.dosage,
            "frequency": med.frequency,
            "prescribedBy": med.prescribedBy,
            "startDate": med.startDate,
            "endDate": med.endDate,
            "totalDoses": med.totalDoses,
            "instructions": med.instructions
        })
    
    return {"medications": meds_response}

@app.post("/api/medications")
async def create_medication(
    medication: MedicationCreate, 
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new medication for the authenticated user"""
    # Generate UUID for medication ID
    new_id = str(uuid.uuid4())
    
    # Create new medication in database
    new_medication = MedicationDB(
        id=new_id,
        user_id=current_user.id,
        name=medication.name,
        dosage=medication.dosage,
        frequency=medication.frequency,
        prescribedBy=medication.prescribedBy,
        startDate=medication.startDate,
        endDate=medication.endDate,
        totalDoses=medication.totalDoses,
        instructions=medication.instructions
    )
    
    db.add(new_medication)
    db.commit()
    db.refresh(new_medication)
    
    # Return the created medication in response format
    return {
        "success": True, 
        "medication": {
            "id": new_medication.id,
            "name": new_medication.name,
            "dosage": new_medication.dosage,
            "frequency": new_medication.frequency,
            "prescribedBy": new_medication.prescribedBy,
            "startDate": new_medication.startDate,
            "endDate": new_medication.endDate,
            "totalDoses": new_medication.totalDoses,
            "instructions": new_medication.instructions
        }
    }

@app.delete("/api/medications/{medication_id}")
async def delete_medication(
    medication_id: str, 
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a medication for the authenticated user"""
    # Find and remove the medication
    medication_to_delete = db.query(MedicationDB).filter(
        MedicationDB.id == medication_id, 
        MedicationDB.user_id == current_user.id
    ).first()
    
    if medication_to_delete:
        db.delete(medication_to_delete)
        db.commit()
        return {"success": True, "message": "Medication deleted successfully"}
    else:
        raise HTTPException(status_code=404, detail="Medication not found")

# Add new endpoints for chat history
@app.get("/api/chat-history/{user_id}")
async def get_chat_history(user_id: int, db: Session = Depends(get_db)):
    """Get chat history for a user"""
    sessions = db.query(ChatSession).filter(ChatSession.user_id == user_id).all()
    return {"sessions": [{"id": s.id, "session_id": s.session_id, "agent_type": s.agent_type, "created_at": s.created_at} for s in sessions]}

@app.get("/api/chat-messages/{session_id}")
async def get_chat_messages(session_id: str, db: Session = Depends(get_db)):
    """Get messages for a specific chat session"""
    messages = db.query(ChatMessage).filter(ChatMessage.session_id == session_id).all()
    return {"messages": [{"id": m.id, "message_type": m.message_type, "content": m.content, "message_metadata": m.message_metadata, "created_at": m.created_at} for m in messages]}

class Symptom(BaseModel):
    name: str
    severity: str | None = None
    bodyPart: str | None = None

class SymptomRequest(BaseModel):
    symptoms: List[Symptom]

class SymptomAssessmentResponse(BaseModel):
    riskLevel: str
    conditions: List[dict]
    immediateActions: List[str]
    precautions: List[str]
    medications: List[str]
    lifestyleChanges: List[str]
    whenToSeekHelp: List[str]
    followUp: str

@app.post("/api/assess-symptoms", response_model=SymptomAssessmentResponse)
async def assess_symptoms(request: SymptomRequest):
    try:
        # Prepare structured symptom text
        formatted_symptoms = [
            f"{s.name} (Severity: {s.severity or 'N/A'}, Body Part: {s.bodyPart or 'General'})"
            for s in request.symptoms
        ]
        symptom_text = "; ".join(formatted_symptoms)

        # Prompt for the LLM to return structured JSON
        prompt = f"""
        Analyze these symptoms: {symptom_text}
        
        Return a structured JSON response with these exact fields:
        - riskLevel: string (low, moderate, high, urgent)
        - conditions: list of objects with name, probability, description, urgent (boolean)
        - immediateActions: list of strings
        - precautions: list of strings  
        - medications: list of strings
        - lifestyleChanges: list of strings
        - whenToSeekHelp: list of strings
        - followUp: string
        
        Make it valid JSON that can be parsed. Example format:
        {{
          "riskLevel": "moderate",
          "conditions": [
            {{
              "name": "Common Cold",
              "probability": 65,
              "description": "Viral infection affecting upper respiratory tract",
              "urgent": false
            }}
          ],
          "immediateActions": ["Rest and hydrate", "Monitor temperature"],
          "precautions": ["Avoid close contact with others", "Practice good hygiene"],
          "medications": ["Acetaminophen for fever", "Ibuprofen for pain"],
          "lifestyleChanges": ["Get adequate sleep", "Eat nutritious foods"],
          "whenToSeekHelp": ["Fever above 103°F", "Difficulty breathing"],
          "followUp": "Consult doctor if symptoms persist beyond 7 days"
        }}
        """

        if llm is None:
            # Return structured fallback response
            return SymptomAssessmentResponse(
                riskLevel="unknown",
                conditions=[],
                immediateActions=["Consult a healthcare professional for proper diagnosis"],
                precautions=[],
                medications=[],
                lifestyleChanges=[],
                whenToSeekHelp=[],
                followUp="Please see a doctor for medical advice"
            )
            
        response = llm.invoke(prompt)
        
        # Parse the LLM response as JSON
        try:
            # Extract JSON from the response (Gemini might wrap it in markdown)
            content = response.content
            # Remove markdown code blocks if present
            if 'json' in content:
                content = content.split('json')[1].split('')[0].strip()
            elif '' in content:
                content = content.split('')[1].split('')[0].strip()
                
            analysis_data = json.loads(content)
            return SymptomAssessmentResponse(**analysis_data)
            
        except json.JSONDecodeError as e:
            print(f"JSON parse error: {e}")
            print(f"Raw response: {response.content}")
            # Fallback if LLM doesn't return proper JSON
            return SymptomAssessmentResponse(
                riskLevel="moderate",
                conditions=[{
                    "name": "General symptoms assessment",
                    "probability": 50, 
                    "description": "Multiple symptoms present requiring evaluation",
                    "urgent": False
                }],
                immediateActions=["Rest and monitor symptoms", "Stay hydrated"],
                precautions=["Avoid strenuous activity", "Monitor for worsening symptoms"],
                medications=["Consider over-the-counter pain relief if appropriate"],
                lifestyleChanges=["Get adequate rest", "Maintain proper nutrition"],
                whenToSeekHelp=["If symptoms worsen or persist for more than 48 hours"],
                followUp="Consult healthcare provider for proper diagnosis and treatment"
            )
            
    except Exception as e:
        print(f"Error in symptom assessment: {e}")
        raise HTTPException(status_code=500, detail=f"Error analyzing symptoms: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)