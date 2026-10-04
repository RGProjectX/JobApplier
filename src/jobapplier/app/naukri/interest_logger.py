import csv
from datetime import datetime
from pathlib import Path


class InterestLogger:
    def __init__(self):
        self.file_path = Path("early_interest_log.csv")
        self._ensure_file()

    def _ensure_file(self):
        if not self.file_path.exists():
            with self.file_path.open("w", newline="", encoding="utf-8") as file:
                writer = csv.DictWriter(
                    file,
                    fieldnames=[
                        "timestamp",
                        "job_id",
                        "title",
                        "status",
                        "response",
                    ],
                )
                writer.writeheader()

    def has_shared(self, job_id: str) -> bool:
        if not self.file_path.exists():
            return False

        with self.file_path.open("r", newline="", encoding="utf-8") as file:
            reader = csv.DictReader(file)

            return any(
                row["job_id"] == job_id and row["status"] == "SUCCESS"
                for row in reader
            )

    def log(
        self,
        job_id: str,
        title: str,
        status: str,
        response: str,
    ):
        with self.file_path.open("a", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(
                file,
                fieldnames=[
                    "timestamp",
                    "job_id",
                    "title",
                    "status",
                    "response",
                ],
            )

            writer.writerow(
                {
                    "timestamp": datetime.now().isoformat(),
                    "job_id": job_id,
                    "title": title,
                    "status": status,
                    "response": response,
                }
            )