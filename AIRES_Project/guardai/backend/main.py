from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
import hashlib
import json
from datetime import datetime
from database import get_db, engine
from models import User, Behavior, RiskScore, AuditLog, MerkleTree
from sqlalchemy.orm import sessionmaker

app = FastAPI(title="GuardAI API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Pydantic models
class BehaviorCreate(BaseModel):
    user_id: int
    action: str
    details: Optional[str] = None

class RiskScoreResponse(BaseModel):
    user_id: int
    score: float
    level: str

class AuditLogResponse(BaseModel):
    id: int
    user_id: int
    action: str
    timestamp: datetime
    hash: str

class MerkleProofResponse(BaseModel):
    proof: List[str]
    root: str

# Endpoints
@app.post("/behaviors/", response_model=dict)
def capture_behavior(behavior: BehaviorCreate, db: Session = Depends(get_db)):
    db_behavior = Behavior(
        user_id=behavior.user_id,
        action=behavior.action,
        details=behavior.details,
        timestamp=datetime.utcnow()
    )
    db.add(db_behavior)
    db.commit()
    db.refresh(db_behavior)
    
    # Log to audit
    log_entry = AuditLog(
        user_id=behavior.user_id,
        action=f"Behavior: {behavior.action}",
        timestamp=datetime.utcnow()
    )
    db.add(log_entry)
    db.commit()
    
    return {"message": "Behavior captured"}

@app.get("/risk-scores/{user_id}", response_model=RiskScoreResponse)
def get_risk_score(user_id: int, db: Session = Depends(get_db)):
    behaviors = db.query(Behavior).filter(Behavior.user_id == user_id).all()
    score = calculate_risk_score(behaviors)
    level = "Low" if score < 0.3 else "Medium" if score < 0.7 else "High"
    
    # Save or update risk score
    db_score = db.query(RiskScore).filter(RiskScore.user_id == user_id).first()
    if db_score:
        db_score.score = score
        db_score.level = level
    else:
        db_score = RiskScore(user_id=user_id, score=score, level=level)
        db.add(db_score)
    db.commit()
    
    return RiskScoreResponse(user_id=user_id, score=score, level=level)

@app.get("/audit-logs/", response_model=List[AuditLogResponse])
def get_audit_logs(user_id: Optional[int] = None, db: Session = Depends(get_db)):
    query = db.query(AuditLog)
    if user_id:
        query = query.filter(AuditLog.user_id == user_id)
    logs = query.all()
    return [AuditLogResponse(id=log.id, user_id=log.user_id, action=log.action, timestamp=log.timestamp, hash=log.hash) for log in logs]

@app.get("/merkle-proof/{log_id}", response_model=MerkleProofResponse)
def get_merkle_proof(log_id: int, db: Session = Depends(get_db)):
    log = db.query(AuditLog).filter(AuditLog.id == log_id).first()
    if not log:
        raise HTTPException(status_code=404, detail="Log not found")
    
    # Simple Merkle proof simulation
    proof = ["hash1", "hash2"]  # Placeholder
    root = "root_hash"  # Placeholder
    
    return MerkleProofResponse(proof=proof, root=root)

@app.post("/simulate-attacker/")
def simulate_attacker(user_id: int, db: Session = Depends(get_db)):
    # Simulate suspicious behaviors
    behaviors = [
        {"action": "unusual_login", "details": "Login from unknown IP"},
        {"action": "rapid_clicks", "details": "High frequency actions"},
        {"action": "data_access", "details": "Accessing sensitive data"}
    ]
    
    for b in behaviors:
        db_behavior = Behavior(
            user_id=user_id,
            action=b["action"],
            details=b["details"],
            timestamp=datetime.utcnow()
        )
        db.add(db_behavior)
        
        log_entry = AuditLog(
            user_id=user_id,
            action=f"Simulated: {b['action']}",
            timestamp=datetime.utcnow()
        )
        db.add(log_entry)
    
    db.commit()
    return {"message": "Attacker simulation completed"}

def calculate_risk_score(behaviors):
    score = 0
    for b in behaviors:
        if "unusual" in b.action:
            score += 0.3
        elif "rapid" in b.action:
            score += 0.2
        elif "data" in b.action:
            score += 0.4
    return min(score, 1.0)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
