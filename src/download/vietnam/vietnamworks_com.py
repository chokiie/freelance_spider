from core.imports import *
from core.logger import logger
from download.base_download_strategy import BaseDownloadStrategy
from core.config import MAX_ITEMS_PER_CATEGORY
from core.exceptions import (APIError,ParseError,)
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
        return self.post_json(api_url,json=payload,error_message="Invalid API response.")
    
    def get_search_query(self,category_url):
        soup = self.get_soup(category_url)
        query_tag = soup.select_one('meta[name="keywords"]')
        if not query_tag:
            raise ParseError("Meta keywords not found.")
        try:
            return query_tag["content"].split("Job search, ")[1]
        except Exception as e:
            raise ParseError(
                "Unable to extract search query."
            ) from e    
    def add_jobs_to_results(self,results,jobs,category_name,category_url,):
        """
        Append jobs to the result list while respecting
        MAX_ITEMS_PER_CATEGORY.
        """
        for job in jobs:
            if len(results) >= MAX_ITEMS_PER_CATEGORY:
                break
            results.append(
                {
                    "category_name": category_name,
                    "category_url": category_url,
                    "job_data": job,})
    def collect_category_jobs(self,query,category_name,category_url,page,):
        """
        Collect all jobs for a category using pagination.
        """
        results = []
        while True:
            if len(results) >= MAX_ITEMS_PER_CATEGORY:
                logger.info("[%s] Reached limit of %d jobs.",category_name, MAX_ITEMS_PER_CATEGORY,)
                break
            logger.info("[%s] Page %d",category_name,page,)
            api_data = self.fetch_api_content(query,page,)
            if api_data is None:
                raise APIError(f"API request failed ({category_name}, page {page})")
            jobs = api_data.get("data", [])
            if not jobs:
                logger.info("[%s] No more jobs.",category_name,)
                break
            self.add_jobs_to_results(results,jobs,category_name,category_url,)
            self.checkpoint.update_progress(category_name,page,len(jobs),)
            page += 1
        return results

    def get_category_urls(self):
        categories = []
        try:
            soup = self.get_soup(self.url)
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

    def get_category_product_urls(self, category):
        category_name = category["name"]
        category_url = category["url"]
        try:
            query = self.get_search_query(category_url)
            page = self.checkpoint.get_resume_page(category_name)
            results = self.collect_category_jobs(query=query,category_name=category_name,category_url=category_url,page=page,)
            logger.info("[%s] Finished. Collected %d jobs.",category_name,len(results),)
            return results
        except Exception:
            logger.exception("FAILED CATEGORY: %s",category_name,)
            raise
