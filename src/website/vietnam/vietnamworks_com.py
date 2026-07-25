from src.core.imports import *


class VietnamworksComWebsiteStrategy:

    def __init__(self, website, country, url):
        self.website = website
        self.country = country
        self.base_url = url

    ###########################################################
    # Parse all jobs
    ###########################################################

    def parse_items(self, data_list):

        try:

            logger.info(
                "Starting parser using %d threads.",
                min(len(data_list), 5)
            )

            with ThreadPoolExecutor(
                max_workers=min(len(data_list), 5)
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

        fields = {
            "Title": self.title,
            "Company": self.company,
            "URL": self.url,
            "Address": self.address,
            "Category": self.category,
            "Job Type": self.jobtype,
            "Salary": self.salary,
            "Experience": self.experience,
            "Job Level": self.joblevel,
            "Remaining Days": self.remainingdays,
            "Benefits": self.benefits,
            "Job Description": self.description,
        }

        for field_name, parser in fields.items():

            try:

                item[field_name] = parser(job)

            except Exception:

                logger.exception(
                    "Parser failed\n"
                    "Field      : %s\n"
                    "Category   : %s\n"
                    "CategoryURL: %s\n"
                    "Job URL    : %s",
                    field_name,
                    job.get("category_name"),
                    job.get("category_url"),
                    job.get("job_data", {}).get("jobUrl")
                )

                item[field_name] = None

        return item

    ###########################################################
    # Generic helper
    ###########################################################

    def get_value(self, job, key):
        """
        Safely retrieve a value from job_data.
        Returns None if the key doesn't exist.
        """

        try:

            return (
                job
                .get("job_data", {})
                .get(key)
            )

        except Exception:

            logger.exception(
                "Failed reading key '%s'\n"
                "Category   : %s\n"
                "CategoryURL: %s",
                key,
                job.get("category_name"),
                job.get("category_url")
            )

            return None

    # ------------------------
    # Parser Functions
    # ------------------------

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

    def address(self,job):
        return self.get_value(job, "address")

    def jobtype(self, job):
        return self.get_value(job, "typeWorking")

    def experience(self, job):
        return self.get_value(job, "yearsOfExperience")

    def description(self, job):
        #return self.get_value(job, "jobDescription")
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