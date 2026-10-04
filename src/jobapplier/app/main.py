import os

from dotenv import load_dotenv
from fastapi import FastAPI
from pydantic import BaseModel

from jobapplier.app.naukri.auth import NaukriAuthService
from jobapplier.app.naukri.client import NaukriClient
from jobapplier.app.naukri.jobs import NaukriJobService

load_dotenv()

app = FastAPI(title="JobApplier")


naukri_client = NaukriClient()
auth_service = NaukriAuthService(naukri_client)
job_service = NaukriJobService(naukri_client)


class OTPRequest(BaseModel):
    phone: str


class OTPVerifyRequest(BaseModel):
    otp: str


class LoginRequest(BaseModel):
    email: str
    password: str


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


@app.post("/jobs/naukri/early-interest")
async def share_early_interest():
    return await job_service.share_interest_for_early_jobs()


@app.get("/jobs/naukri/search")
async def search_jobs(keyword: str, location: str = ""):
    return await job_service.search_jobs(keyword, location)
