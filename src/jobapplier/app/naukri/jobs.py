import asyncio
import json
import random

from jobapplier.app.naukri.client import NaukriClient
from jobapplier.app.naukri.interest_logger import InterestLogger


class NaukriJobService:
    def __init__(self, naukri: NaukriClient):
        self.naukri = naukri
        self.logger = InterestLogger()

    async def share_interest_for_early_jobs(self):
        data = await self.naukri.get_early_interest_jobs()

        jobs = data.get("jobDetails", [])

        results = []

        for job in jobs:
            job_id = job["jobId"]
            title = job.get("title", "")

            if self.logger.has_shared(job_id):
                results.append(
                    {
                        "jobId": job_id,
                        "title": title,
                        "status": "SKIPPED",
                    }
                )
                continue

            try:
                response = await self.naukri.share_interest(job_id)

                self.logger.log(
                    job_id=job_id,
                    title=title,
                    status="SUCCESS",
                    response=json.dumps(response),
                )

                results.append(
                    {
                        "jobId": job_id,
                        "title": title,
                        "status": "SUCCESS",
                    }
                )

            except Exception as exc:
                self.logger.log(
                    job_id=job_id,
                    title=title,
                    status="FAILED",
                    response=str(exc),
                )

                results.append(
                    {
                        "jobId": job_id,
                        "title": title,
                        "status": "FAILED",
                        "error": str(exc),
                    }
                )

            delay = random.uniform(2, 3)
            await asyncio.sleep(delay)

        return results

    async def search_jobs(self, keyword: str, location: str = ""):
        return await self.naukri.search_jobs(keyword, location)
