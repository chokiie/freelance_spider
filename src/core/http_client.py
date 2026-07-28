import time
import requests
from fake_useragent import UserAgent
from tenacity import (retry,stop_after_attempt,wait_fixed,retry_if_exception,)
from core.logger import logger
from core.config import (REQUEST_TIMEOUT,MAX_RETRIES,RETRY_DELAY)

##################################################
# Retry Logger
##################################################

def log_retry(retry_state):
    exception = retry_state.outcome.exception()
    logger.warning(
        "Retry attempt %s/%s failed. Waiting %s seconds. Error: %s",
        retry_state.attempt_number,MAX_RETRIES,RETRY_DELAY,exception)

##################################################
# Retry Decision
##################################################

def should_retry(exception):
    """
    Decide whether request should retry.
    Retry:
    - Network errors
    - Timeout
    - 429
    - 500
    - 502
    - 503
    - 504
    """
    if isinstance(exception,requests.exceptions.HTTPError):
        if exception.response is None:
            return False
        status = exception.response.status_code
        return status in [429,500,502,503,504]
    return isinstance(exception,requests.exceptions.RequestException)

##################################################
# HTTP Client
##################################################

class HttpClient:
    """
    Central HTTP engine.
    Responsibilities:
    - Maintain session
    - Maintain cookies
    - Maintain headers
    - GET requests
    - POST requests
    - Retry failed requests
    - Request logging
    Future:
    - Proxy support
    - Rate limiting
    - Rotating user agents
    """

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": UserAgent().random,"Accept": "*/*"})

    ##################################################
    # Context Manager
    ##################################################

    def __enter__(self):
        return self

    def __exit__(self,exc_type,exc_value,traceback):
        self.close()

    ##################################################
    # Cookies
    ##################################################

    def get_cookies(self):
        """
        Return current session cookies.
        """
        return self.session.cookies.get_dict()

    def build_cookie_header(self):
        """
        Convert cookies to header format.
        Example:
        {"session":"abc"}
        becomes:
        session=abc
        """
        cookies = self.get_cookies()
        return "; ".join([f"{key}={value}"for key, value in cookies.items()])

    ##################################################
    # GET Request
    ##################################################

    @retry(
        stop=stop_after_attempt(MAX_RETRIES),
        wait=wait_fixed(RETRY_DELAY),
        retry=retry_if_exception(
            should_retry
        ),
        before_sleep=log_retry,
        reraise=True
    )
    def get(self,url,headers=None,params=None,timeout=REQUEST_TIMEOUT,**kwargs):
        start = time.time()
        response = self.session.get(url,headers=headers,params=params,timeout=timeout,**kwargs)
        elapsed = time.time() - start
        logger.info("GET %s [%s] %.2fs",url,response.status_code,elapsed)
        response.raise_for_status()
        return response

    ##################################################
    # POST Request
    ##################################################

    @retry(
        stop=stop_after_attempt(MAX_RETRIES),
        wait=wait_fixed(RETRY_DELAY),
        retry=retry_if_exception(should_retry),
        before_sleep=log_retry,
        reraise=True)
    
    def post(self,url,json=None,data=None,headers=None,timeout=REQUEST_TIMEOUT,**kwargs):
        start = time.time()
        response = self.session.post(url,json=json,data=data,headers=headers,timeout=timeout,**kwargs)
        elapsed = time.time() - start
        logger.info("POST %s [%s] %.2fs",url,response.status_code,elapsed)
        response.raise_for_status()
        return response

    ##################################################
    # Close Session
    ##################################################

    def close(self):
        logger.info("Closing HTTP session")
        self.session.close()