from jobapplier.app.naukri.client import NaukriClient


class NaukriAuthService:
    def __init__(self, naukri: NaukriClient):
        self.naukri = naukri

    async def send_otp(self, phone: str):
        return await self.naukri.send_otp(phone)

    async def verify_otp(self, phone: str, otp: str):
        return await self.naukri.verify_otp(phone, otp)

    async def login(self, email: str, password: str):
        return await self.naukri.login(email, password)