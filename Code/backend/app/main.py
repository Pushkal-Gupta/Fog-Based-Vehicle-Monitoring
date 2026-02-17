from fastapi import FastAPI
from app.api import intelligence
from app.api import insights
from app.api import actuation_events
from app.core.db import ping_server
from app.api import vehicle



app = FastAPI()


app.include_router(intelligence.router, prefix="/api")
app.include_router(insights.router, prefix="/api") 
app.include_router(actuation_events.router, prefix="/api")
app.include_router(vehicle.router, prefix="/api")



@app.on_event("startup")
async def startup_event():
    await ping_server()