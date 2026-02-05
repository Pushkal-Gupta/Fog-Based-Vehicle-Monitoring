from fastapi import FastAPI
from app.api import ingest
from app.api import intelligence


app = FastAPI()

app.include_router(ingest.router, prefix="/api") 
app.include_router(intelligence.router, prefix="/api/intelligence")