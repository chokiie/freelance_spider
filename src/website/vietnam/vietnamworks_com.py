from src.core.imports import *
from src.core.logger import logger
from src.core.config import (
    REQUEST_TIMEOUT,
    MAX_CATEGORY_THREADS,
    MAX_WEBSITE_THREADS,
    MAX_ITEMS_PER_CATEGORY
)
class VietnamworksComWebsiteStrategy:

    FIELD_PARSERS = {
        "Title": "title",
        "Company": "company",
        "URL": "url",
        "Address": "address",
        "Category": "category",
        "Job Type": "jobtype",
        "Salary": "salary",
        "Experience": "experience",
        "Job Level": "joblevel",
        "Remaining Days": "remainingdays",
        "Benefits": "benefits",
        "Job Description": "description",
    }

    def __init__(self, website, country, url):
        self.website = website
        self.country = country
        self.base_url = url

    ###########################################################
    # Parse all jobs
    ###########################################################

    def parse_items(self, data_list):

        if not data_list:
            logger.warning("No items to parse.")
            return []

        try:

            thread_count = min(
                len(data_list),
                MAX_WEBSITE_THREADS
            )

            logger.info(
                "Starting parser using %d threads.",
                thread_count
            )

            with ThreadPoolExecutor(
                max_workers=thread_count
            ) as executor:

                results = list(
                    executor.map(
                        self.get_items,
                        data_list
                    )
                )

            logger.info(
                "Finished parsing %d jobs.",
                len(results)
            )

            return results

        except Exception:

            logger.exception("parse_items() failed")

            return []

    ###########################################################
    # Parse ONE job
    ###########################################################

    def get_items(self, job):

        item = {}

        for field_name, method_name in self.FIELD_PARSERS.items():

            parser = getattr(self, method_name)

            try:

                item[field_name] = parser(job)

            except Exception:

                self.log_parser_error(
                    field_name,
                    job
                )

                item[field_name] = None

        return item

    ###########################################################
    # Helpers
    ###########################################################

    def log_parser_error(self, field_name, job):

        category = job.get("category_name")
        category_url = job.get("category_url")
        job_url = job.get("job_data", {}).get("jobUrl")

        logger.exception(
            "Parser failed\n"
            "Field      : %s\n"
            "Category   : %s\n"
            "CategoryURL: %s\n"
            "Job URL    : %s",
            field_name,
            category,
            category_url,
            job_url
        )

    def get_value(self, job, key):
        """
        Safely retrieve a value from job_data.
        """

        job_data = job.get("job_data")

        if not isinstance(job_data, dict):

            logger.warning(
                "Invalid job_data while reading '%s'.",
                key
            )

            return None

        return job_data.get(key)

    ###########################################################
    # Parser Functions
    ###########################################################

    def title(self, job):
        return self.get_value(job, "jobTitle")

    def company(self, job):
        return self.get_value(job, "companyName")

    def url(self, job):
        return self.get_value(job, "jobUrl")

    def salary(self, job):
        return self.get_value(job, "salary")

    def joblevel(self, job):
        return self.get_value(job, "jobLevel")

    def address(self, job):
        return self.get_value(job, "address")

    def jobtype(self, job):
        return self.get_value(job, "typeWorking")

    def experience(self, job):
        return self.get_value(job, "yearsOfExperience")

    def description(self, job):
        # return self.get_value(job, "jobDescription")
        return None

    def benefits(self, job):

        try:

            benefits = self.get_value(job, "benefits")

            if not benefits:
                return None

            return ", ".join(
                f"{benefit.get('benefitName', '')}: {benefit.get('benefitValue', '')}"
                for benefit in benefits
                if isinstance(benefit, dict)
            )

        except Exception:

            logger.exception("Benefits parser failed.")

            return None

    def remainingdays(self, job):

        try:

            expired_on = self.get_value(job, "expiredOn")

            if not expired_on:
                return None

            expired_on = expired_on.replace("Z", "+00:00")

            expired_date = datetime.fromisoformat(expired_on)

            today = datetime.now(timezone.utc)

            remaining = (expired_date - today).days

            if remaining <= 0:
                return "Expired"

            return f"Expires in {remaining} days"

        except Exception:

            logger.exception("Remaining Days parser failed.")

            return None

    def category(self, job):

        try:

            industries = self.get_value(job, "industries")

            if not industries:
                return None

            return ", ".join(
                industry.get("industryName", "")
                for industry in industries
                if isinstance(industry, dict)
            )

        except Exception:

            logger.exception("Category parser failed.")

            return None