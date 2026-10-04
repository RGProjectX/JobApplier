from jobapplier.app.naukri.client import NaukriClient


class NaukriProfileService:
    def __init__(self, naukri: NaukriClient):
        self.naukri = naukri

    async def toggle_headline(self):
        data = await self.naukri.get_profile()

        profile = data["profile"][0]

        profile_id = profile["profileId"]
        headline = profile["resumeHeadline"].rstrip()

        if headline.endswith("."):
            new_headline = headline[:-1]
        else:
            new_headline = headline + "."

        return await self.naukri.update_profile(
            profile_id=profile_id,
            profile={
                "resumeHeadline": new_headline,
            },
        )