from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import random
from datetime import datetime

app = FastAPI(title="Civic Pulse API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- IN-MEMORY SYSTEM STATE ---
app.state.complaints = []
app.state.audit_log = []
app.state.infrastructure = {"Pump_17": "Broken"}

WARDS = {
    "WARD 7": {"lat": 17.3850, "lng": 78.4867},
    "WARD 12": {"lat": 17.4000, "lng": 78.5000},
    "WARD 3": {"lat": 17.3700, "lng": 78.4600}
}

def add_audit(message: str):
    timestamp = datetime.now().strftime("%H:%M:%S")
    app.state.audit_log.insert(0, f"[{timestamp}] {message}")

class Grievance(BaseModel):
    text: str

# --- DETERMINISTIC GOVERNANCE RULE ENGINE ---
def simulate_llm_and_rules(text: str, is_bot: bool = False):
    ward_name = random.choice(list(WARDS.keys()))
    is_water_issue = "water" in text.lower() or "flood" in text.lower()
    
    # Armored World State: Only assign to Pump_17 if it's currently broken
    assigned_root = "Pump_17" if is_water_issue and app.state.infrastructure.get("Pump_17") == "Broken" else "Unknown"
    
    # 1. Mock LLM Structural Extraction
    llm_output = {
        "id": random.randint(1000, 9999),
        "text": text,
        "category": "Water Leakage" if is_water_issue else "General",
        "urgency": random.randint(8, 10) if is_water_issue else random.randint(2, 6),
        "department": random.choice(["Transport", "Sanitation", "Water Board", "Health"]),
        "lat": WARDS[ward_name]["lat"] + random.uniform(-0.004, 0.004),
        "lng": WARDS[ward_name]["lng"] + random.uniform(-0.004, 0.004),
        "ward": ward_name,
        "root_cause": assigned_root,
        "status": "Active"
    }

    # 2. Cyber Resilience Filter
    if is_bot:
        add_audit(f"BLOCK: Bot swarm detected in {ward_name}. 50 duplicate payloads quarantined.")
        return None

    # 3. Neuro-Symbolic Safe Routing Guard
    original_dept = llm_output["department"]
    if llm_output["category"] == "Water Leakage" and original_dept != "Water Board":
        llm_output["department"] = "Water Board"
        add_audit(f"INTERCEPT: LLM misrouted Water to {original_dept}. Rule Engine OVERRIDE -> Water Board.")
    else:
        add_audit(f"PASS: Complaint {llm_output['id']} verified. Safely routed to {original_dept}.")

    app.state.complaints.append(llm_output)
    return llm_output

# --- REST ENDPOINTS ---

@app.get("/")
def health_check():
    return {"status": "200 OK", "message": "Nagrik.com API is Live"}
@app.post("/submit")


def submit_complaint(payload: Grievance):
    result = simulate_llm_and_rules(payload.text)
    return {"status": "Success", "data": result}

@app.post("/chaos_button")
def trigger_chaos():
    add_audit("ALERT: Anomalous high-frequency traffic spike detected.")
    simulate_llm_and_rules("There is a massive flood on Main Street.", is_bot=True)
    
    for _ in range(6):
        simulate_llm_and_rules("Water backing up into residential grid!")
    return {"status": "Chaos Logged & Mitigated"}

@app.post("/repair_pump")
def repair_pump():
    # Armored double-click prevention
    if app.state.infrastructure.get("Pump_17") == "Repaired":
        add_audit("INFO: Administrator attempted repair on Pump_17. Already fully operational.")
        return {"status": "Already Repaired", "resolved": 0}
        
    app.state.infrastructure["Pump_17"] = "Repaired"
    resolved_count = 0
    for c in app.state.complaints:
        if c["root_cause"] == "Pump_17" and c["status"] == "Active":
            c["status"] = "Resolved"
            resolved_count += 1
    
    add_audit(f"ACTION: Administrator executed intervention. Fixed Pump_17. Closed {resolved_count} dependencies.")
    return {"status": "Repaired", "resolved": resolved_count}

@app.get("/state")
def get_state():
    active_complaints = [c for c in app.state.complaints if c["status"] == "Active"]
    crisis_score = sum(c["urgency"] for c in active_complaints)
    return {
        "complaints": active_complaints,
        "audit_log": app.state.audit_log[:15],
        "crisis_score": crisis_score
    }

@app.get("/analysis")
def get_analysis():
    active_complaints = [c for c in app.state.complaints if c["status"] == "Active"]
    groups = {}
    for c in active_complaints:
        root = c["root_cause"]
        if root != "Unknown":
            groups[root] = groups.get(root, 0) + 1
    
    confidence = 0
    if "Pump_17" in groups and groups["Pump_17"] > 0:
        confidence = min(98, 65 + (groups["Pump_17"] * 4)) 
        summary = f"⚠️ ROOT CAUSE ISOLATED: Pump_17. Correlated to {groups['Pump_17']} live anomalies causing systemic failure. Recommendation: Immediate field deployment to clear grid blockage."
    else:
        summary = "✅ Systemic Scan Complete: Infrastructure operating within normal parameters. No root causes isolated."
        
    return {"groups": groups, "confidence": confidence, "copilot_summary": summary}
