from imports import *
from gspread.exceptions import APIError

class Helper:

    def __init__(self):
        self.sheet = self.connect_google_sheet()

    def connect_google_sheet(self):
        """
        Connect to Google Sheet using credentials.json
        """

        scope = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive"
        ]

        creds = ServiceAccountCredentials.from_json_keyfile_name(
            "credentials.json",
            scope
        )

        client = gspread.authorize(creds)

        spreadsheet = client.open("Freelance Spider")

        logger.info("Connected to Google Sheet: %s", spreadsheet.title)

        return spreadsheet.sheet1

    def save_to_google_sheet(self, data, scraper_name):
        """
        Save scraped jobs directly to Google Sheet.
        """

        try:

            if not data:
                logger.warning("No data to upload.")
                return False

            worksheet = self.sheet

            logger.info("=" * 70)
            logger.info("SCRAPER : %s", scraper_name)
            logger.info("TOTAL JOBS : %d", len(data))
            logger.info("=" * 70)

            worksheet.clear()

            headers = list(data[0].keys())

            rows = [headers]

            for job in data:

                row = []

                for column in headers:

                    value = job.get(column, "")

                    if value is None:
                        value = ""

                    elif isinstance(value, (dict, list, tuple, set)):
                        value = json.dumps(value, ensure_ascii=False)

                    else:
                        value = str(value)

                    row.append(value)

                rows.append(row)

            logger.info("Columns : %d", len(headers))
            logger.info("Prepared %d rows.", len(rows))

            batch_size = 1000
            max_retry = 6

            start_row = 1

            for start in range(0, len(rows), batch_size):

                batch = rows[start:start + batch_size]

                end = start + len(batch) - 1

                logger.info(
                    "Uploading rows %d - %d",
                    start + 1,
                    end + 1
                )

                success = False

                for retry in range(max_retry):

                    try:

                        worksheet.update(
                            range_name=f"A{start_row}",
                            values=batch,
                            value_input_option="RAW"
                        )

                        success = True

                        logger.info(
                            "Batch uploaded successfully (%d rows)",
                            len(batch)
                        )

                        break

                    except APIError as e:

                        status = None

                        try:
                            status = e.response.status_code
                        except Exception:
                            pass

                        if status in (429, 500, 503):

                            wait = 2 ** retry

                            logger.warning(
                                "Google API returned %s. Retrying in %d seconds (%d/%d)...",
                                status,
                                wait,
                                retry + 1,
                                max_retry
                            )

                            time.sleep(wait)

                        else:
                            raise

                if not success:

                    logger.error(
                        "Failed uploading batch starting at row %d",
                        start_row
                    )

                    return False

                start_row += len(batch)

                # Small pause to reduce quota pressure
                time.sleep(1)

            logger.info("=" * 70)
            logger.info("GOOGLE SHEET UPLOAD SUCCESS")
            logger.info("Rows Uploaded : %d", len(data))
            logger.info("=" * 70)

            return True

        except Exception:

            logger.exception("Failed uploading to Google Sheet.")
            return False