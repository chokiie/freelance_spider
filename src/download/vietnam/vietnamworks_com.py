from src.core.imports import *
from src.core.logger import logger
from src.download.base_download_strategy import BaseDownloadStrategy
from src.core.config import (MAX_CATEGORY_THREADS,MAX_ITEMS_PER_CATEGORY,CATEGORY_RETRY_COUNT)
from src.core.exceptions import (APIError,ParseError,)
class VietnamworksComDownloadStrategy(BaseDownloadStrategy):
    def __init__(self,website,country,url):
        super().__init__(website,country,url)
        self.name = "Vietnamworks"

    def fetch_api_content(self,query,page):
        api_url = "https://ms.vietnamworks.com/job-search/v1.0/search"
        payload = {
            "userId": 0,"query": query,"filter": [],"ranges": [],
            "order": [],"hitsPerPage": 50,"page": page,
            "retrieveFields": ["address","benefits","jobTitle","salaryMax","isSalaryVisible","jobLevelVI",
                "isShowLogo","salaryMin","companyLogo","userId","jobLevel","jobLevelId","jobId","jobUrl",
                "companyId","approvedOn","isAnonymous","alias","expiredOn","industries","industriesV3",
                "workingLocations","services","companyName","salary","onlineOn","onlineOnText","simpleServices",
                "visibilityDisplay","isShowLogoInSearch","priorityOrder","skills","profilePublishedSiteMask",
                "jobDescription","jobRequirement","prettySalary","requiredCoverLetter","languageSelectedVI",
                "languageSelected","languageSelectedId","typeWorkingId","createdOn","isAdrLiteJob","applicantSignal",
                "numOfApplications"
            ],"summaryVersion": ""}

        response = self.client.post(api_url,json=payload)
        try:
            return response.json()
        except Exception as e:
            raise APIError(
                "Invalid API response."
            ) from e
    
    def get_search_query(self,category_url):
        response = self.client.get(category_url)
        soup = BeautifulSoup(response.text,"html.parser")
        query_tag = soup.select_one('meta[name="keywords"]')

        if not query_tag:
            raise ParseError(
                "Meta keywords not found."
            )
        try:
            return query_tag["content"].split("Job search, ")[1]

        except Exception as e:
            raise ParseError(
                "Unable to extract search query."
            ) from e    
        
    def get_category_urls(self):
        categories = []
        try:
            response = self.client.get(self.url)
            soup = BeautifulSoup(response.text,"html.parser")

            industry_tags = soup.select("div.boxLeft div.box h5")
            for tag in industry_tags:
                if tag.get_text(strip=True) != "Search Job by Industry":
                    continue

                box_content = tag.find_next_sibling("div",class_="boxContent")
                if not box_content:
                    continue

                for link in box_content.find_all("a", href=True):
                    categories.append({
                        "name": link.get_text(strip=True),
                        "url": link["href"]})

            logger.info("Found %d categories",len(categories))
            return categories

        except Exception:

            logger.exception("Failed to get category URLs.")
            return categories

    def get_category_product_urls(self,category):
        category_name = category["name"]
        category_url = category["url"]
        results = []

        try:
            query = self.get_search_query(category_url)
            page = self.checkpoint.get_resume_page(category_name)

            while True:
                if len(results) >= MAX_ITEMS_PER_CATEGORY:
                    logger.info("[%s] Reached limit of %d jobs.",
                        category_name,MAX_ITEMS_PER_CATEGORY)
                    break

                logger.info("[%s] Page %d",category_name,page)

                api_data = self.fetch_api_content(query, page)

                if api_data is None:
                    raise APIError(f"API request failed ({category_name}, page {page})")

                jobs = api_data.get("data", [])

                if len(jobs) == 0:
                    logger.info("[%s] No more jobs.",category_name)
                    break

                for job in jobs:
                    if len(results) >= MAX_ITEMS_PER_CATEGORY:
                        break

                    results.append({
                        "category_name": category_name,
                        "category_url": category_url,
                        "job_data": job})

                # Save progress after each page
                self.checkpoint.update_progress(
                    category_name,
                    page,
                    len(jobs)
                )

                page += 1

            logger.info("[%s] Finished. Collected %d jobs.",
                category_name,len(results))

            return results

        except Exception:

            logger.exception("FAILED CATEGORY: %s",category_name)

            raise
        
    def get_product_urls(self,category_data):

        if not category_data:
            logger.warning("No categories found.")
            return {"products": [],"failed_categories": []}

        max_workers = min(len(category_data),MAX_CATEGORY_THREADS)

        logger.info(
            "Processing %d categories using %d threads",
            len(category_data),max_workers)

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            results = list(
                executor.map(
                    self.process_category,
                    category_data))

        product_data = []

        for category_result in results:
            product_data.extend(category_result)

        logger.info("SCRAPING FINISHED")
        logger.info("Products Collected : %d",len(product_data))

        if self.failed_categories:

            logger.warning("FAILED CATEGORIES (%d)",len(self.failed_categories))

            for item in self.failed_categories:
                logger.warning("Category : %s",item["category"])
                logger.warning("URL  : %s",item["url"])
                logger.warning("Error    : %s",item["error"])

        else:
            logger.info("No failed categories.")

        return {"products": product_data,"failed_categories": self.failed_categories}

    def process_category(self,category):

        category_name = category["name"]
        category_url = category["url"]

        if self.checkpoint.is_completed(
            category_name
        ):

            logger.info(
                "Skipping completed category: %s",
                category_name
            )

            return []

        last_error = None

        for attempt in range(CATEGORY_RETRY_COUNT):

            try:

                if attempt > 0:

                    logger.warning(
                        "Retrying category (%d/%d): %s",
                        attempt + 1,
                        CATEGORY_RETRY_COUNT,
                        category_name
                    )

                    time.sleep(2)

                result = self.get_category_product_urls(
                    category
                )

                self.checkpoint.mark_completed(
                    category_name
                )

                return result

            except Exception as e:

                last_error = e

                logger.exception(
                    "Attempt %d failed for %s",
                    attempt + 1,
                    category_name
                )

        logger.error(
            "Category permanently failed: %s",
            category_name
        )

        self.add_failed_category(
            category_name,
            category_url,
            last_error
        )

        self.checkpoint.mark_failed(
            category_name,
            category_url,
            last_error
        )

        return []