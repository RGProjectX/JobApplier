import httpx

from jobapplier.app.config import (
    NAUKRI_APP_ID,
    NAUKRI_BASE_URL,
    NAUKRI_CLIENT_ID,
    NAUKRI_SYSTEM_ID,
)
from jobapplier.app.naukri.utils.nkparam import generate_nkparam


class NaukriClient:
    def __init__(self):
        self.access_token = None
        self.client = httpx.AsyncClient(
            base_url=NAUKRI_BASE_URL,
            headers={
                "accept": "application/json",
                "appid": NAUKRI_APP_ID,
                "clientid": NAUKRI_CLIENT_ID,
                "systemid": NAUKRI_SYSTEM_ID,
                "content-type": "application/json",
                "user-agent": "Mozilla/5.0",
            },
            timeout=30.0,
        )

    def _build_seo_key(self, keyword: str, location: str, page: int) -> str:
        keyword_slug = (
            keyword.strip()
            .lower()
            .replace(".", "-dot-")
            .replace(" ", "-")
            .replace("+", "-")
            .strip("-")
        )

        if location.strip():
            location_slug = location.strip().lower().replace(" ", "-")

            return f"{keyword_slug}-jobs-in-{location_slug}-{page}"

        return f"{keyword_slug}-jobs-{page}"

    async def login(self, email: str, password: str):
        response = await self.client.post(
            "/central-login-services/v1/login",
            headers={
                "appid": "103",
                "systemid": "jobseeker",
            },
            json={
                "username": email,
                "password": password,
            },
        )

        response.raise_for_status()

        data = response.json()

        for cookie in data.get("cookies", []):
            self.client.cookies.set(
                cookie["name"], cookie["value"], domain=cookie.get("domain")
            )

            if cookie["name"] == "nauk_at":
                self.access_token = cookie["value"]

        for cookie in self.client.cookies.jar:
            print(cookie.name)

        return data

    async def send_otp(self, phone: str):
        response = await self.client.post(
            "/central-login-services/v1/otp",
            json={
                "username": phone,
                "isLoginByEmail": False,
                "isLoginByMobile": True,
                "flowId": "login",
            },
        )

        response.raise_for_status()

        return response.json()

    async def verify_otp(self, phone: str, otp: str):
        response = await self.client.post(
            "/central-login-services/v0/otp-login",
            json={
                "username": phone,
                "isLoginByEmail": False,
                "isLoginByMobile": True,
                "token": otp,
                "flowId": "login",
            },
        )

        response.raise_for_status()

        data = response.json()

        for cookie in data.get("cookies", []):
            if cookie["name"] == "nauk_at":
                self.access_token = cookie["value"]
                break

        return data

    async def get_dashboard(self):
        if not self.access_token:
            raise RuntimeError("Naukri authentication required")

        response = await self.client.get(
            "/cloudgateway-mynaukri/resman-aggregator-services/v1/users/self/dashboard",
            headers={
                "authorization": f"Bearer {self.access_token}",
            },
        )

        response.raise_for_status()

        return response.json()

    async def get_profile(self):
        if not self.access_token:
            raise RuntimeError("Naukri authentication required")

        response = await self.client.get(
            "/cloudgateway-mynaukri/resman-aggregator-services/v2/users/self",
            params={"expand_level": 4},
            headers={
                "authorization": f"Bearer {self.access_token}",
                "x-requested-with": "XMLHttpRequest",
            },
        )

        response.raise_for_status()
        return response.json()

    async def update_profile(self, profile_id: str, profile: dict):
        if not self.access_token:
            raise RuntimeError("Naukri authentication required")

        response = await self.client.post(
            "/cloudgateway-mynaukri/resman-aggregator-services/v1/users/self/fullprofiles",
            headers={
                "authorization": f"Bearer {self.access_token}",
                "x-http-method-override": "PUT",
                "x-requested-with": "XMLHttpRequest",
            },
            json={
                "profile": profile,
                "profileId": profile_id,
            },
        )

        response.raise_for_status()

        return response.json()

    async def get_early_interest_jobs(self):
        response = await self.client.get(
            "/jobapi/v1/search/pseudojobs",
            headers={
                "appid": "105",
                "systemid": "Naukri",
                "referer": "https://www.naukri.com/mnjuser/recommended-earjobs",
            },
        )

        response.raise_for_status()
        return response.json()

    async def share_interest(self, job_id: str):
        response = await self.client.post(
            "/chatbot-services/workflow/v1/apply",
            headers={
                "appid": "121",
                "apply-origin": "S2J",
                "systemid": "jobseeker",
            },
            json={
                "strJobsarr": [job_id],
                "applySrc": "s2jlisting-0-F-0-1---",
                "applytype": "single",
            },
        )

        response.raise_for_status()
        return response.json()

    from jobapplier.app.naukri.utils.nkparam import generate_nkparam

    async def search_jobs(
        self,
        keyword: str,
        location: str = "",
        page: int = 1,
        job_age: int = 3,
        experience: int = 2,
        results_per_page: int = 20,
        lat_long: str = "",
    ):
        params = {
            "noOfResults": results_per_page,
            "urlType": "search_by_keyword",
            "searchType": "adv",
            "keyword": keyword,
            "k": keyword,
            "pageNo": page,
            "experience": experience,
            "jobAge": job_age,
            "nignbevent_src": "jobsearchDeskGNB",
            "seoKey": self._build_seo_key(keyword, location, page),
            "src": "jobsearchDesk",
            "latLong": lat_long,
        }

        headers = {
            "appid": "109",
            "gid": "LOCATION,INDUSTRY,EDUCATION,FAREA_ROLE",
            "nkparam": generate_nkparam("srp"),
        }

        response = await self.client.get(
            "/jobapi/v3/search", params=params, headers=headers
        )

        response.raise_for_status()
        return response.json()

    async def close(self):
        await self.client.aclose()
