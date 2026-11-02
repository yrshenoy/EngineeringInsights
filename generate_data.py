"""Deterministically generate fictional employee contributions. No employer data."""
import datetime
import json
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PERSONAS = {
    "diego": {"name": "Diego Messi", "role": "Software Architect", "focus": "AI, computer vision, warehouse fulfillment and future product architecture", "counts": [12,26,7,35,9,22,0,5]},
    "allison": {"name": "Allison Dida", "role": "Quality Engineering Specialist", "focus": "Manual and automated testing and product quality", "counts": [16,46,29,10,14,31,58,67]},
    "maria": {"name": "Maria Graf", "role": "Senior Software Engineer", "focus": "FedEx and UPS shipping integration and defects", "counts": [51,41,35,12,27,47,8,29]},
    "roger": {"name": "Roger Nadal", "role": "AI Workflow Engineer", "focus": "Warehouse agents, agentic workflows and evaluations", "counts": [34,33,14,28,12,37,4,25]},
}
LABELS = ["Merge requests","Code reviews","Defects fixed","Technical spikes","Customer issues","Development tasks","Manual test cases","Automated tests"]
KEYS = ["mrs","reviews","defects","spikes","customer","tasks","manual","automated"]
SOURCES = ["GitLab","GitLab","Jira","Jira","Customer issue tracker","Jira","Jira","GitLab / Jira"]
PREFIXES = ["MR","REV","BUG","SPIKE","CASE","TASK","TEST","AUTO"]
STATUSES = ["Merged","Reviewed","Resolved","Completed","Investigated / resolved","Completed","Executed","Implemented"]
TOPICS = {
    "diego": ["Future fulfillment architecture", "Warehouse computer vision object detection", "AI-assisted warehouse picking", "Inventory architecture boundaries", "Robotics integration strategy", "Dimensional packing proof of concept", "Computer vision accuracy investigation", "Fulfillment service contracts", "Warehouse throughput analysis", "Future product research", "Cross-system data model", "Model inference deployment"],
    "allison": ["Shipment regression testing", "Manual warehouse acceptance testing", "Automated fulfillment edge cases", "Inventory test fixtures", "Flaky integration test investigation", "Return workflow verification", "Carrier label testing", "Release candidate validation", "Quality risk checklist", "Automation stability improvements", "Cross-browser warehouse testing", "End-to-end scenarios"],
    "maria": ["FedEx request-handling migration", "UPS tracking exception logic", "Carrier address validation", "Shipping label retry guard", "Shipping service mappings", "Carrier authentication regression", "International shipment fields", "Rate shopping response handling", "Package weight calculation", "Carrier error diagnostics", "Shipping configuration", "Multi-package label behavior"],
    "roger": ["Warehouse agent tool calling", "Agent reliability evaluation", "Human approval step", "Multi-step inventory assistant", "Agent context retrieval", "Agent evaluation rubric", "Orchestration recovery", "Tool invocation tracing", "Warehouse exception triage agent", "Agent latency review", "Human-in-the-loop escalation", "Prompt and response validation"],
}
SUFFIX = ["implementation","peer review","defect resolution","technical investigation","customer investigation","delivery task","manual verification","test automation"]

def make_data():
    categories = {key: {"label": LABELS[i], "source": SOURCES[i]} for i,key in enumerate(KEYS)}
    personas = {name:{k:v for k,v in p.items() if k!="counts"} for name,p in PERSONAS.items()}
    records=[]
    for pi,(username,p) in enumerate(PERSONAS.items()):
        for fy in [2024,2025,2026,2027]:
            rng=random.Random(712891+pi*100+fy)
            multiplier={2024:.78,2025:.93,2026:1,2027:.58}[fy]
            for ci,key in enumerate(KEYS):
                for idx in range(round(p["counts"][ci]*multiplier)):
                    date=datetime.date(fy-1,6,1)+datetime.timedelta(days=(idx*11+rng.randrange(0,30)+pi*17)%340)
                    topic=TOPICS[username][(idx+fy+pi)%len(TOPICS[username])]
                    records.append({"owner":username,"fy":f"FY{fy%100:02d}","category":key,
                        "id":f"{PREFIXES[ci]}-{fy%100:02d}{pi+1}{idx+101:03d}",
                        "title":f"{topic} ({SUFFIX[ci]})","status":STATUSES[ci],
                        "date":date.isoformat(),"source":SOURCES[ci],
                        "summary":f"Synthetic example of {p['name']}'s contribution to {topic.lower()}. This record illustrates activity, not individual performance."})
    return {"disclaimer":"All employees, counts, descriptions and issue identifiers are fictional.","personas":personas,"categories":categories,"records":records}

def generate():
    data=make_data()
    (ROOT/"synthetic_data.json").write_text(json.dumps(data,indent=2),encoding="utf-8")
    print(f"Generated {len(data['records'])} fictional records across four employees and four fiscal years.")

if __name__=="__main__":
    generate()
