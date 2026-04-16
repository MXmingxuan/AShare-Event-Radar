from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import os
import sys

# Ensure backend imports can hit the local modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from event_radar_agent import EventRadarAgent

app = FastAPI(title="A-Share Event Radar API")

# Initialize our singleton agent
agent = EventRadarAgent()

from typing import Optional

class AnalysisRequest(BaseModel):
    symbol: str
    days_back: int = 30
    api_key: Optional[str] = None
    model_name: Optional[str] = "MiniMax-M2.7"

@app.post("/api/analyze")
def analyze(req: AnalysisRequest):
    try:
        if not req.symbol or len(req.symbol) != 6:
            return JSONResponse(status_code=400, content={"error": "无效的股票代码，请提供6位数字代码"})
            
        final_report = agent.run_analysis_pipeline(
            symbol=req.symbol, 
            days_back=req.days_back,
            custom_api_key=req.api_key,
            custom_model=req.model_name
        )
        return {"report": final_report}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

# Mount the frontend
app.mount("/", StaticFiles(directory="static", html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
