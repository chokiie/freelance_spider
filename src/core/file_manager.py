import json
from pathlib import Path
from src.core.logger import logger


class FileManager:
    """
    Centralized file operations.

    Responsibilities:
    - Create folders
    - Save JSON files safely
    - Load JSON files
    """


    def ensure_directory(self, path):

        try:

            Path(path).mkdir(
                parents=True,
                exist_ok=True
            )

        except Exception:

            logger.exception(
                "Failed creating directory: %s",
                path
            )

            raise


    def save_json(
        self,
        filepath,
        data
    ):

        filepath = Path(filepath)

        try:

            self.ensure_directory(
                filepath.parent
            )

            temp_file = filepath.with_suffix(
                ".tmp"
            )

            with open(
                temp_file,
                "w",
                encoding="utf-8"
            ) as file:

                json.dump(
                    data,
                    file,
                    indent=4,
                    ensure_ascii=False
                )


            temp_file.replace(
                filepath
            )


            logger.info(
                "JSON saved: %s",
                filepath
            )

        except Exception:

            logger.exception(
                "Failed saving JSON: %s",
                filepath
            )

            raise


    def load_json(
        self,
        filepath
    ):

        filepath = Path(filepath)

        try:

            if not filepath.exists():

                logger.warning(
                    "File does not exist: %s",
                    filepath
                )

                return {}

            with open(
                filepath,
                "r",
                encoding="utf-8"
            ) as file:

                return json.load(file)

        except Exception:

            logger.exception(
                "Failed loading JSON: %s",
                filepath
            )

            raise