from src.core.imports import *

from src.core.logger import logger
from src.core.config import (
    OUTPUT_FOLDER,
    JSON_INDENT,
    JSON_ENSURE_ASCII,
    DEFAULT_JSON_FILENAME,
    DEFAULT_ENCODING,
    DATE_FORMAT
)


class JsonExporter:

    def save(self, jobs, static_data):

        country = static_data["country"]

        website = (
            static_data["website"]
            .replace("www.", "")
            .replace(".com", "")
            .replace(".", "_")
        )

        date = datetime.now().strftime(DATE_FORMAT)

        output_path = os.path.join(
            OUTPUT_FOLDER,
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
            DEFAULT_JSON_FILENAME
        )

        with open(
            file_path,
            "w",
            encoding=DEFAULT_ENCODING
        ) as f:

            json.dump(
                jobs,
                f,
                indent=JSON_INDENT,
                ensure_ascii=JSON_ENSURE_ASCII
            )

        logger.info(
            "JSON saved: %s",
            file_path
        )

        return file_path