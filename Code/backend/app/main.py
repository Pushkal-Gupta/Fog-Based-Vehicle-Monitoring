from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import intelligence
from app.api import insights
from app.api import actuation_events
from app.core.db import ping_server
from app.api import vehicle
from app.api import user





app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(intelligence.router, prefix="/api")
app.include_router(insights.router, prefix="/api")
app.include_router(actuation_events.router, prefix="/api")
app.include_router(vehicle.router, prefix="/api")
app.include_router(user.router, prefix='/api')

@app.on_event("startup")
async def startup_event():
    await ping_server()