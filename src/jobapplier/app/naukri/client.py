import json
import os
from pathlib import Path

import httpx

from jobapplier.app.config import (
    NAUKRI_APP_ID,
    NAUKRI_BASE_URL,
    NAUKRI_CLIENT_ID,
    NAUKRI_SYSTEM_ID,
)
from jobapplier.app.naukri.utils.job_parser import parse_jobs
from jobapplier.app.naukri.utils.nkparam import generate_nkparam

SESSION_FILE = Path(os.getenv("NAUKRI_SESSION_FILE", ".naukri_session.json"))


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
        self._load_session()

    def _save_session(self):
        data = {
            "access_token": self.access_token,
            "cookies": [
                {"name": c.name, "value": c.value, "domain": c.domain, "path": c.path}
                for c in self.client.cookies.jar
            ],
        }
        SESSION_FILE.write_text(json.dumps(data))
        os.chmod(SESSION_FILE, 0o600)  # tokens inside, keep it private

    def _load_session(self):
        if not SESSION_FILE.exists():
            return
        try:
            data = json.loads(SESSION_FILE.read_text())
        except (json.JSONDecodeError, OSError):
            return

        self.access_token = data.get("access_token")
        for c in data.get("cookies", []):
            self.client.cookies.set(
                c["name"],
                c["value"],
                domain=c.get("domain") or "",
                path=c.get("path") or "/",
            )

    def clear_session(self):
        self.access_token = None
        self.client.cookies.clear()
        SESSION_FILE.unlink(missing_ok=True)

    def _apply_login_cookies(self, data: dict):
        """Shared by login() and verify_otp(): set cookies, grab token, persist."""
        for cookie in data.get("cookies", []):
            self.client.cookies.set(
                cookie["name"], cookie["value"], domain=cookie.get("domain") or ""
            )
            if cookie["name"] == "nauk_at":
                self.access_token = cookie["value"]
        self._save_session()

    def get_cookies(self) -> httpx.Cookies:
        """Return the client's current cookie jar."""
        return self.client.cookies

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
            headers={"appid": "103", "systemid": "jobseeker"},
            json={"username": email, "password": password},
        )
        response.raise_for_status()
        data = response.json()
        self._apply_login_cookies(data)
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
        self._apply_login_cookies(data)
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
        experience: int = 3,
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
        return parse_jobs(response.json())

    async def apply_to_job(
        self,
        job_id: str,
        src: str = "drecomm_dashboard_apply",
        mandatory_skills: list[str] | None = None,
        optional_skills: list[str] | None = None,
    ):
        if not self.access_token:
            raise RuntimeError("Naukri authentication required")

        payload = {
            "strJobsarr": [job_id],
            "logstr": f"--{src}--F-0-1---",
            "flowtype": "show",
            "crossdomain": True,
            "jquery": 1,
            "rdxMsgId": "",
            "chatBotSDK": True,
            "mandatory_skills": mandatory_skills or [],
            "optional_skills": optional_skills or [],
            "applyTypeId": "107",
            "closebtn": "y",
            "applySrc": src,
            "sid": "",
            "mid": "",
        }

        response = await self.client.post(
            "/cloudgateway-workflow/workflow-services/apply-workflow/v1/apply",
            headers={
                "appid": "121",
                "systemid": "jobseeker",
                # note: this endpoint uses "ACCESSTOKEN = <token>", not "Bearer"
                "authorization": f"ACCESSTOKEN = {self.access_token}",
                "origin": "https://www.naukri.com",
                "referer": "https://www.naukri.com/",
            },
            json=payload,
        )
        print(f"Apply response: {response.status_code} {response}")
        response.raise_for_status()
        return response.json()

    async def close(self):
        await self.client.aclose()
