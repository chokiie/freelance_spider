# Freelance Spider

> A modular ETL-based web scraping framework built with Python for collecting, processing, and exporting structured job listing data.

![Python](https://img.shields.io/badge/Python-3.x-blue?logo=python)
![Architecture](https://img.shields.io/badge/Architecture-ETL-orange)
![Status](https://img.shields.io/badge/Status-Active-success)

---

## Overview

Freelance Spider is a reusable web scraping framework that follows an **ETL (Extract, Transform, Load)** architecture.

Instead of creating a custom scraper for every website, the framework separates downloading, parsing, and exporting into independent modules. This makes the project easier to maintain, extend, and reuse for multiple job platforms.

---

## Features

- ETL-based architecture
- Dynamic spider loading
- Multi-threaded processing
- Category-based crawling
- Configurable job limit per category
- Failed category tracking
- JSON exporter
- Modular project structure
- Easy integration of new websites

---

## Architecture

```
               main.py
                   │
                   ▼
              Processor
                   │
        ┌──────────┴──────────┐
        ▼                     ▼
 Download Strategy     Website Strategy
        │                     │
        └──────────┬──────────┘
                   ▼
            JSON Exporter
                   │
                   ▼
         output/vietnamworks.json
```

---

## Project Structure

```
freelance_spider/
│
├── map/
├── output/
├── src/
│   ├── core/
│   ├── download/
│   ├── website/
│   ├── exporter/
│   └── main.py
│
├── test.py
├── requirements.txt
└── README.md
```

---

## Workflow

### 1. Category Collection

Collects available job categories from the target website.

### 2. Job Collection

Downloads job listings for each category with pagination support and configurable limits.

### 3. Website Parsing

Parses each job listing into structured data such as:

- Job Title
- Company
- Location
- Salary
- Description
- Requirements
- Employment Type

### 4. Export

Exports the parsed data into JSON format.

---

## Current Support

| Country | Website | Status |
|----------|----------|--------|
| Vietnam | VietnamWorks | ✅ |

---

## Technologies

- Python 3
- Requests
- BeautifulSoup
- Concurrent Futures
- JSON
- Logging

---

## Installation

Clone the repository

```bash
git clone https://github.com/chokiie/freelance_spider.git
```

Create and activate a virtual environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate
```

Install dependencies

```bash
pip install -r requirements.txt
```

---

## Usage

Run the complete ETL pipeline

```bash
python src/main.py
```

Run a spider for testing

```bash
python test.py
```

---

## Output

Example output:

```
output/
└── vietnamworks.json
```

---

## Roadmap

### Completed

- ETL architecture
- Dynamic spider loading
- Multi-threaded processing
- JSON exporter
- Category job limits

### Planned

- CSV Exporter
- Excel Exporter
- Google Sheets Exporter
- Database Exporter
- Retry mechanism
- Docker support
- Unit tests

---

## Author

**Jave Diaz**

Python Developer focused on web scraping, ETL pipelines, and data extraction.

GitHub: https://github.com/chokiie