from jobapplier.app.naukri.model.Job import Job


def parse_jobs(data: dict) -> list[Job]:
    jobs = []

    for raw_job in data.get("jobDetails", []):
        placeholders = {
            item.get("type"): item.get("label")
            for item in raw_job.get("placeholders", [])
        }

        salary = raw_job.get("salaryDetail") or {}

        job = Job(
            job_id=raw_job["jobId"],
            title=raw_job.get("title", ""),
            company=raw_job.get("companyName", ""),
            company_id=raw_job.get("companyId"),
            skills=parse_skills(raw_job.get("tagsAndSkills")),
            description=raw_job.get("jobDescription", ""),
            location=placeholders.get("location"),
            experience=raw_job.get("experienceText"),
            min_experience=to_int(raw_job.get("minimumExperience")),
            max_experience=to_int(raw_job.get("maximumExperience")),
            salary_text=placeholders.get("salary"),
            min_salary=salary.get("minimumSalary"),
            max_salary=salary.get("maximumSalary"),
            salary_hidden=salary.get("hideSalary", True),
            job_url=raw_job.get("jdURL"),
            posted=raw_job.get("footerPlaceholderLabel"),
            todays_job=raw_job.get("todaysJob", False),
            questionnaire_required=raw_job.get("questionnaireIdPresent", False),
            company_apply=raw_job.get("companyApplyJob", False),
            company_apply_url=raw_job.get("companyApplyUrl"),
            apply_redirect_url=raw_job.get("applyRedirectUrl"),
            job_agent_eligible=raw_job.get("jobAgentEligle", False),
            saved=raw_job.get("saved", raw_job.get("isSaved", False)),
            vacancy=raw_job.get("vacancy"),
        )

        jobs.append(job)

    return jobs


def parse_skills(value: str | None) -> list[str]:
    if not value:
        return []

    return [skill.strip().lower() for skill in value.split(",") if skill.strip()]


def to_int(value: str | int | None) -> int | None:
    if value is None:
        return None

    try:
        return int(value)
    except (TypeError, ValueError):
        return None
