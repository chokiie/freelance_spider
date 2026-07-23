import logging
import requests
import httpx
import asyncio
import random
import json
import os
import pytz
import time
import re
import math
import importlib
import boto3
import base64
import gspread
import aiohttp
import ssl
import urllib.parse
import zlib
import csv
import threading
from urllib.parse import urlencode
from html import unescape
from oauth2client.service_account import ServiceAccountCredentials
from googleapiclient.discovery import build
from dotenv import load_dotenv
from botocore.exceptions import NoCredentialsError, PartialCredentialsError, ClientError
from datetime import datetime, timezone, timedelta
from fake_useragent import UserAgent
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception_type
from playwright.async_api import async_playwright

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logging.getLogger('googleapiclient.discovery_cache').setLevel(logging.ERROR)

logger = logging.getLogger(__name__)