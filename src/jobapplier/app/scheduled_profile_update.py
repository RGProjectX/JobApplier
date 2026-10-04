import asyncio
import os

from jobapplier.app.naukri.auth import NaukriAuthService
from jobapplier.app.naukri.client import NaukriClient
from jobapplier.app.naukri.profile import NaukriProfileService


async def update_profile() -> None:
    email = os.getenv("NAUKRI_EMAIL")
    password = os.getenv("NAUKRI_PASSWORD")

    if not email or not password:
        raise RuntimeError(
            "NAUKRI_EMAIL and NAUKRI_PASSWORD must be set in the environment."
        )

    client = NaukriClient()
    try:
        await NaukriAuthService(client).login(email, password)
        await NaukriProfileService(client).toggle_headline()
        print("Naukri profile headline toggled successfully.")
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(update_profile())
