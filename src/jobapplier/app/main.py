import os
from pathlib import Path

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

from jobapplier.app.naukri.auth import NaukriAuthService
from jobapplier.app.naukri.client import NaukriClient
from jobapplier.app.naukri.jobs import NaukriJobService
from jobapplier.app.naukri.model.Job import Job
from jobapplier.app.naukri.profile import NaukriProfileService

load_dotenv()

app = FastAPI(title="JobApplier")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


naukri_client = NaukriClient()
auth_service = NaukriAuthService(naukri_client)
job_service = NaukriJobService(naukri_client)
profile_service = NaukriProfileService(naukri_client)


class OTPRequest(BaseModel):
    phone: str


class OTPVerifyRequest(BaseModel):
    otp: str


class LoginRequest(BaseModel):
    email: str
    password: str


class ApplyRequest(BaseModel):
    src: str = "drecomm_dashboard_apply"
    mandatory_skills: list[str] = []
    optional_skills: list[str] = []


STATIC_DIR = Path(__file__).parent / "naukri" / "static"


@app.get("/")
async def index():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/auth/naukri/login")
async def login():
    request = LoginRequest(
        email=os.getenv("NAUKRI_EMAIL"),
        password=os.getenv("NAUKRI_PASSWORD"),
    )
    if not request.email or not request.password:
        return {
            "error": "NAUKRI_EMAIL and NAUKRI_PASSWORD must be set in the environment variables."
        }
    return await auth_service.login(request.email, request.password)


@app.post("/auth/naukri/send-otp")
async def send_otp():
    request = OTPRequest(phone=os.getenv("NAUKRI_MOBILE_NUMBER"))
    if not request.phone:
        return {
            "error": "NAUKRI_MOBILE_NUMBER must be set in the environment variables."
        }
    return await auth_service.send_otp(request.phone)


@app.post("/auth/naukri/verify-otp")
async def verify_otp(request: OTPVerifyRequest):
    phone = os.getenv("NAUKRI_MOBILE_NUMBER")
    if not phone:
        return {
            "error": "NAUKRI_MOBILE_NUMBER must be set in the environment variables."
        }
    return await auth_service.verify_otp(
        phone,
        request.otp,
    )


@app.get("/naukri/dashboard")
async def dashboard():
    return await naukri_client.get_dashboard()


@app.post("/profile/naukri/toggle-headline")
async def toggle_headline():
    try:
        return await profile_service.toggle_headline()
    except httpx.HTTPStatusError as e:
        status = e.response.status_code
        if status in (401, 403):
            raise HTTPException(401, "Naukri session expired or blocked. Log in again.")
        raise HTTPException(status, e.response.text)
    except RuntimeError as e:
        raise HTTPException(401, str(e))


@app.post("/jobs/naukri/early-interest")
async def share_early_interest():
    return await job_service.share_interest_for_early_jobs()


@app.get("/jobs/naukri/search", response_model=list[Job])
async def search_jobs(keyword: str, location: str = ""):
    return await job_service.search_jobs(keyword, location)


@app.post("/jobs/naukri/{job_id}/apply")
async def apply_to_job(job_id: str, body: ApplyRequest):
    try:
        return await job_service.apply_to_job(
            job_id,
            src=body.src,
            mandatory_skills=body.mandatory_skills,
            optional_skills=body.optional_skills,
        )
    except httpx.HTTPStatusError as e:
        status = e.response.status_code
        if status in (401, 403):
            raise HTTPException(401, "Naukri session expired or blocked. Log in again.")
        raise HTTPException(status, e.response.text)


@app.get("/naukri/cookies")
async def get_cookies():
    return naukri_client.get_cookies()
