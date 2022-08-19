# ClickUp PDF Task Export

Small script to export tasks from ClickUp as PDF (if one does not have admin rights).

Disclaimer: This was built for a very specific use case and is not maintained.

## Prerequisites

Clone this repository to `<REPO_PATH>`.
Have Python and Pip installed (I would recommend using `virtualenv`).
Install requirements with `pip install -r requirements.txt`.

Install a Chrome driver (e.g., `brew install --cask chromedriver` on Mac).

Copy `config.example.yml` to `config.yml` and add your ClickUp email and password.

You need to download the browser data from your dashboard as HAR using the network tab in the developer console.
Make sure you scroll down to load all tasks. 
Save the export as `<REPO_PATH>/api-communication.har`.

## Usage
* Start a terminal in `<REPO_PATH>`
* Run the script with `python script.py`
* Your PDFs will be written to `<REPO_PATH>/task-exports` and sorted by subcategories