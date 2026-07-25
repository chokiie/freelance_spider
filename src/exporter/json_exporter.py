from src.core.imports import *


class JsonExporter:

    def save(self, jobs, static_data):

        country = static_data["country"]
        website = static_data["website"]

        date = datetime.now().strftime("%Y-%m-%d")

        website = (
            website
            .replace("www.", "")
            .replace(".com", "")
            .replace(".", "_")
        )

        output_path = os.path.join(
            "output",
            country,
            website,
            date
        )

        os.makedirs(
            output_path,
            exist_ok=True
        )

        file_path = os.path.join(
            output_path,
            "jobs.json"
        )

        with open(
            file_path,
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                jobs,
                f,
                indent=4,
                ensure_ascii=False
            )

        logger.info(
            "JSON saved: %s",
            file_path
        )

        return file_path