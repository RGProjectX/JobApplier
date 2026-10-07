from pydantic import BaseModel, Field


class Job(BaseModel):
    job_id: str
    title: str
    company: str
    company_id: int | None = None

    skills: list[str] = Field(default_factory=list)
    description: str = ""

    location: str | None = None

    experience: str | None = None
    min_experience: int | None = None
    max_experience: int | None = None

    salary_text: str | None = None
    min_salary: int | None = None
    max_salary: int | None = None
    salary_hidden: bool = True

    job_url: str | None = None

    posted: str | None = None
    todays_job: bool = False

    questionnaire_required: bool = False

    company_apply: bool = False
    company_apply_url: str | None = None
    apply_redirect_url: str | None = None

    job_agent_eligible: bool = False

    saved: bool = False
    vacancy: int | None = None
