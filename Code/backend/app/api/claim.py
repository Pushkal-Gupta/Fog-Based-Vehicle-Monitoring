import time
from fastapi import APIRouter, Depends, HTTPException


router = APIRouter(prefix="/vehicles", tags=["vehicles"])


