# mcp_server.py
import os

from dotenv import load_dotenv
from fastmcp import FastMCP

from jobapplier.app.naukri.auth import NaukriAuthService
from jobapplier.app.naukri.client import NaukriClient
from jobapplier.app.naukri.jobs import NaukriJobService
from jobapplier.app.naukri.profile import NaukriProfileService

load_dotenv()

mcp = FastMCP("JobApplier")

client = NaukriClient()
auth = NaukriAuthService(client)
jobs = NaukriJobService(client)
profile = NaukriProfileService(client)


@mcp.tool()
async def naukri_login() -> dict:
    """Log in to Naukri using credentials stored in the server's environment."""
    email, password = os.getenv("NAUKRI_EMAIL"), os.getenv("NAUKRI_PASSWORD")
    if not email or not password:
        return {"error": "NAUKRI_EMAIL / NAUKRI_PASSWORD not set"}
    return await auth.login(email, password)


@mcp.tool()
async def naukri_send_otp() -> dict:
    """Send an OTP to the configured mobile number."""
    phone = os.getenv("NAUKRI_MOBILE_NUMBER")
    if not phone:
        return {"error": "NAUKRI_MOBILE_NUMBER not set"}
    return await auth.send_otp(phone)


@mcp.tool()
async def naukri_verify_otp(otp: str) -> dict:
    """Verify the OTP the user received by SMS."""
    phone = os.getenv("NAUKRI_MOBILE_NUMBER")
    if not phone:
        return {"error": "NAUKRI_MOBILE_NUMBER not set"}
    return await auth.verify_otp(phone, otp)


@mcp.tool()
async def naukri_dashboard() -> dict:
    """Get the profile dashboard."""
    return await client.get_dashboard()


@mcp.tool()
async def naukri_search_jobs(keyword: str, location: str = "") -> dict:
    """Search Naukri jobs."""
    return await jobs.search_jobs(keyword, location)


@mcp.tool()
async def naukri_share_early_interest() -> dict:
    """Share interest on early-access jobs. This takes real action on the account."""
    return await jobs.share_interest_for_early_jobs()


@mcp.tool()
async def naukri_toggle_headline() -> dict:
    """Toggle the profile headline. This takes real action on the account."""
    return await profile.toggle_headline()


if __name__ == "__main__":
    mcp.run()  # stdio; use mcp.run(transport="streamable-http") for remote
