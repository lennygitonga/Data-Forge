# System Architecture: AI-Powered Web Scraper & Summarizer

This document details the modular architecture of the automated scraping and summarization system.

---

## Workflow Overview

### Step 1 — User Interfaces
The system supports two entry points for triggering data collection:
* **Web UI:** A user-friendly interface featuring HTML forms for site submission, email configuration, and scheduling.
* **CLI:** A command-line interface for automated tasks, allowing users to scrape sites with flags like `--email` and `--every 1h`.

### Step 2 — Flask Backend
The central management layer built with Python:
* **Routes:** Handles incoming requests via `POST /scrape` and `GET /jobs`.
* **Job Model:** Managed through **PostgreSQL** and **SQLAlchemy** for persistent storage of tasks.
* **Job Queue:** An **APScheduler** async runner that maintains the scheduler loop for recurring tasks.

### Step 3 — AI Bot (Claude API)
Intelligence is injected into the pipeline via LLM integration:
* **Site Resolver:** Resolves natural language or partial names (e.g., "bbc news") into full URLs (`bbc.com/news`).
* **Selector Generator:** Analyzes HTML structure to generate specific extraction rules (selectors).
* **Summariser:** Processes raw extracted data into a concise email summary.

### Step 4 — Scrape Engine
A robust dual-engine approach for data retrieval:
* **Static Fetcher:** Powered by **httpx** for fast, efficient fetching of non-JS dependent pages.
* **JS Renderer:** Uses **Playwright** as a fallback for dynamic, JavaScript-heavy websites.
* **Extractor:** Outputs clean, structured **JSON** data.

### Step 5 — Email Output (Resend)
The final delivery stage:
* **HTML Email:** Sends the AI-generated summary and highlights to the user.
* **Attachment:** Includes raw data in **CSV** and **JSON** formats.
* **Resend Sender:** Manages the API calls with built-in retry logic.

---

## Tech Stack Summary

| Component | Technology |
| :--- | :--- |
| **Language** | Python |
| **Web Framework** | Flask |
| **Database** | PostgreSQL + SQLAlchemy |
| **Scraping** | HTTPX & Playwright |
| **AI Processing** | Claude API |
| **Job Scheduling** | APScheduler |
| **Email Delivery** | Resend API |

---

# 4-Day Implementation Roadmap: AI Scraper & Summarizer

This plan breaks down the development of the AI-powered scraping system into four intensive phases.

---

## Day 1: Foundation & Backend Orchestration
**Goal:** Set up the core environment, database, and basic request handling.

* **Environment Setup:** Initialize Python virtual environment and install Flask, SQLAlchemy, and APScheduler.
* **Database Schema:** Design and implement the `Job` model in PostgreSQL to track URL, email, frequency, and status.
* **Flask Routes:** Build the basic `POST /scrape` and `GET /jobs` endpoints.
* **Scheduler Integration:** Configure APScheduler to watch the database and trigger "placeholder" tasks.

## Day 2: The Scrape Engine (Data Retrieval)
**Goal:** Build the logic to fetch content from any website.

* **Static Fetcher:** Implement `httpx` logic for high-speed HTML retrieval.
* **Dynamic Fallback:** Set up **Playwright** to handle JavaScript-heavy sites (SPAs) when static fetching fails.
* **Extractor Module:** Create a utility to clean raw HTML and return structured JSON (removing scripts, ads, and nav bars).
* **Integration:** Connect the Scrape Engine to the Flask backend so scheduled jobs actually fetch data.

## Day 3: AI Bot Intelligence (Claude API)
**Goal:** Use LLMs to make the scraper "smart" and process the results.

* **Site Resolver:** Build the prompt logic to turn search terms (e.g., "Nairobi news") into verified URLs.
* **Selector Generation:** Implement logic to send HTML snippets to the API to identify the best CSS selectors for the data you want.
* **The Summariser:** Create the final processing step where raw JSON is sent to the AI to produce a concise, bulleted summary.

## Day 4: User Interfaces & Email Delivery
**Goal:** Connect the user to the system and finalize the output loop.

* **Web UI:** Build a simple HTML/CSS dashboard to submit new jobs and view the status of current ones.
* **CLI Tool:** Create a Python script using `argparse` to allow terminal-based control.
* **Resend Integration:** Implement the final step to format the AI summary into an HTML email and attach CSV/JSON data.
* **End-to-End Testing:** Run a full loop from Web UI submission to receiving the summary email.

---

## Success Metrics
| Day | Deliverable |
| :--- | :--- |
| **1** | Working API that saves jobs to a database. |
| **2** | System that can extract text from both static and dynamic sites. |
| **3** | AI-generated summaries of extracted web data. |
| **4** | Automated email delivery triggered by a Web/CLI request. |