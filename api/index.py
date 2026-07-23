import os
import sys
from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path so agent & tools modules can be found
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent.agent import plan_trip
from agent.langchain_agent import run_agent
from tools.budget import estimate_budget

app = FastAPI(title="Agentic AI Travel Planner API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/plan")
async def get_trip_plan(
    src: str = Query(..., description="Source City"),
    dest: str = Query(..., description="Destination City"),
    days: int = Query(..., description="Trip Duration in Days")
):
    try:
        # Normalize inputs
        src_clean = src.strip()
        dest_clean = dest.strip()
        
        # Standard coords for mapping
        city_coords = {
            "delhi": [28.6139, 77.2090],
            "goa": [15.2993, 74.1240],
            "mumbai": [19.0760, 72.8777],
            "bangalore": [12.9716, 77.5946],
            "kolkata": [22.5726, 88.3639],
            "chennai": [13.0827, 80.2707],
            "hyderabad": [17.3850, 78.4867],
            "pune": [18.5204, 73.8567],
            "jaipur": [26.9124, 75.7873],
            "agra": [27.1767, 78.0081]
        }
        
        src_lower = src_clean.lower()
        dest_lower = dest_clean.lower()
        
        src_coords = city_coords.get(src_lower, [20.5937, 78.9629])
        dest_coords = city_coords.get(dest_lower, [20.5937, 78.9629])
        
        # Run plan
        plan = plan_trip(
            src=src_clean,
            dest=dest_clean,
            days=days,
            lat=dest_coords[0],
            lon=dest_coords[1]
        )
        
        # Get LangChain AI insights
        query = f"Plan a trip from {src_clean} to {dest_clean} for {days} days, including flights, hotels, places, weather, and budget."
        agent_response = run_agent(query)
        reasoning = agent_response.get("output", "No reasoning provided.")
        
        # Estimate budget
        budget = estimate_budget(plan["flight"], plan["hotel"], days)
        
        return {
            "success": True,
            "plan": plan,
            "reasoning": reasoning,
            "budget": budget,
            "src_coords": src_coords,
            "dest_coords": dest_coords
        }
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Error executing plan: {error_details}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/health")
async def health_check():
    return {"status": "ok"}
