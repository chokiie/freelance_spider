from src.core.imports import *

class VietnamworksComDownloadStrategy():
    def __init__(self, website, country, url):
            self.name = "Vietnamworks"
            self.website = website
            self.country = country
            self.url = url
            self.failed_categories = []
            self.failed_lock = threading.Lock()

    def init_headers(self):
            # instantiate the HttpxFetcher with appropriate headers and settings
            cookies = self.get_cookies()
            headers = {
                "accept": "*/*",
                "accept-encoding": "gzip, deflate",
                "connection": "keep-alive",
                "cookies": "; ".join([f"{key}={value}" for key, value in cookies.items()]),
                "user-agent": UserAgent().random,
            }
            return headers

    def get_cookies(self):
            try:
                '''
                Get cookies from the website.
                Returns a dictionary of cookies.
                '''
                base_url = f"https://www.vietnamworks.com"
                headers = {
                    "user-agent": UserAgent().random,
                }
                res = requests.get(base_url, headers=headers)
                return res.cookies.get_dict()
            except Exception as e:
                logger.error(f"Error in get_cookies: {e}")
                return {}

    def getRequester(self, url):
        logging.info(f"Fetching Base URL: {url}")
        headers = self.init_headers()
        response = requests.get(url, headers=headers, timeout=30)
        if response.status_code != 200:
            logging.warning(f"Failed to fetch {url}, status code: {response.status_code}")
            return None
        else:
            return response.text

    def fetch_api_content(self,query,page,category_name="",category_url=""):
            #Data in API
            api_url = f'https://ms.vietnamworks.com/job-search/v1.0/search'

            payload = {
                "userId": 0,
                "query": query,
                "filter": [],
                "ranges": [],
                "order": [],
                "hitsPerPage": 50,
                "page": page,
                "retrieveFields": ["address","benefits","jobTitle","salaryMax","isSalaryVisible","jobLevelVI","isShowLogo",
                    "salaryMin","companyLogo","userId","jobLevel","jobLevelId","jobId","jobUrl","companyId","approvedOn",
                    "isAnonymous","alias","expiredOn","industries","industriesV3","workingLocations","services",
                    "companyName","salary","onlineOn","onlineOnText","simpleServices","visibilityDisplay","isShowLogoInSearch",
                    "priorityOrder","skills","profilePublishedSiteMask","jobDescription","jobRequirement","prettySalary",
                    "requiredCoverLetter","languageSelectedVI","languageSelected","languageSelectedId","typeWorkingId",
                    "createdOn","isAdrLiteJob","applicantSignal","numOfApplications"],"summaryVersion": ""}
    
            headers = self.init_headers()

            response = requests.post(api_url,json=payload, headers=headers, timeout=30)
            if response.status_code == 200:
                return response.json()

            logger.error(
                "[%s] HTTP %s | Page %s | URL: %s",
                category_name,
                response.status_code,
                page,
                category_url
            )

            return None

    def parse_items(self, data_list):
            try:
                # sample data_list: [{'url': 'https://example.com', 'response': 'raw HTML response from the website'}]
                #data_list = [data for data in data_list if data.get('response') is not None]
                logger.info('Starting processing with %d threads', len(data_list))
                
                # Use ThreadPoolExecutor instead of multiprocessing.Pool
                with ThreadPoolExecutor(max_workers=min(len(data_list), 5)) as executor:
                    results = list(executor.map(self.get_items, data_list))
                
                #logger.info('Processing complete')
                return results
            except Exception as e:
                logger.error('Error in processor multi_process: %s', e)
                return []
            
    def get_category_urls(self):
        data = []  # store all Category Name and Category URLs here
        try:
            response = self.getRequester(self.url)
            try:
                _data = json.loads(response)
                # raw_data is now a Python dict/list
                #logger.info("Raw data is JSON.")
            except (json.JSONDecodeError, TypeError):
                _data = BeautifulSoup(response, "html.parser")
                # Not valid JSON, so parse as HTML
                #logger.info("Raw data is HTML.")
            
            category_list = []
            
            if 'data' in _data:
                for category in _data.get("data", []):
                    category_list.append({
                        "id": category.get("industry_id"),
                        "name": category.get("industry_name_en")
                    })
            else:
                industry_tags = _data.select('div.boxLeft div.box h5')
                #Get Industry Text
                        
                if industry_tags:
                    for i_tag in industry_tags:
                        if i_tag.get_text(strip=True) == "Search Job by Industry":
                            box_content = i_tag.find_next_sibling("div", class_="boxContent")
            
                            if box_content:
                                category_tags = box_content.find_all("a")
            
                                if category_tags:
                                    for category in category_tags:
                                        if category and category.has_attr('href'):
                                            data.append({
                                                "name": category.get_text(strip=True),
                                                "url": category['href']
                                            })             
            return data

        except Exception as e:
            logging.error(f"Unexpected error in get_urls(): {e}")
            return data  # return whatever URLs were collected

    def get_category_product_urls(self, category):

        category_name = category["name"]
        category_url = category["url"]

        #logger.info("START CATEGORY : %s", category_name)
        #logger.info("URL            : %s", category_url)

        results = []
        MAX_ITEMS_PER_CATEGORY = 50

        try:

            # -------------------------------------------------------
            # STEP 1: Request category page
            # -------------------------------------------------------

            response = self.getRequester(category_url)

            if not response:
                raise Exception("Category page returned empty response")

            # -------------------------------------------------------
            # STEP 2: Parse HTML
            # -------------------------------------------------------

            soup = BeautifulSoup(response, "html.parser")

            query_tag = soup.select_one('meta[name="keywords"]')

            if not query_tag:
                raise Exception("Meta keywords not found")

            try:
                query = query_tag["content"].split("Job search, ")[1]
            except Exception:
                raise Exception("Unable to extract query")

            # -------------------------------------------------------
            # STEP 3: Pagination
            # -------------------------------------------------------

            page = 0
            total_pages = None

            while True:
                # Stop before requesting another page
                if len(results) >= MAX_ITEMS_PER_CATEGORY:
                    logger.info(
                        "[%s] Reached limit of %d jobs.",
                        category_name,
                        MAX_ITEMS_PER_CATEGORY
                    )
                    break

                logger.info("[%s] Page %s", category_name, page)

                api_data = self.fetch_api_content(
                    query=query,
                    page=page,
                    category_name=category_name,
                    category_url=category_url
                )

                if api_data is None:
                    raise Exception(f"API request failed on page {page}")

                jobs = api_data.get("data", [])

                if not jobs:
                    logger.info("[%s] No more jobs.", category_name)
                    break

                # Calculate total pages once
                if total_pages is None:

                    total_jobs = api_data.get("meta", {}).get("nbHits", 0)

                    page_size = len(jobs)

                    if page_size == 0:
                        break

                    total_pages = math.ceil(total_jobs / page_size)

                    logger.info(
                        "[%s] Total Jobs: %d | Total Pages: %d",
                        category_name,
                        total_jobs,
                        total_pages
                    )

                # Save jobs
                for job in jobs:

                    # Stop once this category reaches the limit
                    if len(results) >= MAX_ITEMS_PER_CATEGORY:
                        break

                    results.append({
                        "category_name": category_name,
                        "category_url": category_url,
                        "job_data": job
                    })

                page += 1

                if page >= total_pages:
                    break

            logger.info(
                "[%s] Finished. Collected %d jobs.",
                category_name,
                len(results)
            )

            return results

        except Exception as e:

            logger.exception(
                "FAILED CATEGORY: %s",
                category_name
            )

            # Thread-safe append
            with self.failed_lock:

                self.failed_categories.append({
                    "category": category_name,
                    "url": category_url,
                    "error": str(e)
                })

            return []
        
    def get_product_urls(self, category_data):

        if not category_data:
            return []

        logger.info(
            "Processing %d categories using %d threads",
            len(category_data),
            min(len(category_data), 5)
        )

        with ThreadPoolExecutor(
            max_workers=min(len(category_data), 5)
        ) as executor:

            results = list(
                executor.map(
                    self.get_category_product_urls,
                    category_data
                )
            )

        # ---------------------------------------
        # Flatten all category results
        # ---------------------------------------

        product_data = []

        for category_result in results:
            product_data.extend(category_result)

        logger.info("SCRAPING FINISHED")

        logger.info("Products Collected : %d", len(product_data))

        if self.failed_categories:

            logger.warning("FAILED CATEGORIES (%d)", len(self.failed_categories))

            for item in self.failed_categories:

                logger.warning("Category : %s", item["category"])
                logger.warning("URL      : %s", item["url"])
                logger.warning("Error    : %s", item["error"])

        else:

            logger.info("No failed categories.")

        return {
            "products": product_data,
            "failed_categories": self.failed_categories
        }