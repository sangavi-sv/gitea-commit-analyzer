# Gitea Metrics Analyzer Script

## Table of Contents
- [General Info](#general-info)
- [Prerequisites](#prerequisites)
- [Install Dependencies](#install-dependencies)
    - [Configuration](#configuration)
- [Script Workflow](#script-workflow)
- [Usage](#usage)

## General Info
> This Python script automates the process of analyzing commits and pull requests (PRs) in a Gitea repository using Git CLI. It calculates various metrics such as commit count, lines added/deleted, PR details, and identifies the top 100 most frequently changed files. The script generates both CSV and text reports and can send an HTML email containing these reports to specified recipients.

## Prerequisites
- Python 3.12
- Git installed and accessible in system PATH
- `config.ini` configuration file
- `Logging_Framework.py` for logging

## Install Dependencies

Python libraries required (install via `pip` if not already available):

```
configparser
ast
csv
subprocess
collections
datetime
os
sys
```


## Configuration
The script requires a `config.ini` file with the following sections:

- **gitea**:
    - `gitea_DNS`: Gitea server DNS
    - `local_repo_dir`: Local path to store repositories

- **mail**:
    - `sender_email`
    - `sender_username`
    - `sender_password`
    - `smtp_server`
    - `smtp_port`
    - `cc_email` (list of CC recipients)
    - `subject` (email subject)

- **report**:
    - `output_dir`: Directory for generated CSV and text reports

## Script Workflow

1. **Read Configuration**
    - Loads Gitea URL, repository paths, and email settings from `config.ini`.

2. **Set Up Logging**
    - Initializes info and error loggers using `Logging_Framework.py`.

3. **Input from User**
    - Repository name, base commit SHA, head commit SHA, recipient emails, and branch name.

4. **Ensure Local Repository**
    - Clones the repository if missing, or pulls latest changes for the branch.

5. **Compute Metrics**
    - Counts commits, identifies merge commits (PRs), calculates additions, deletions, total changes.
    - Finds the largest PR by total changes and number of files affected.

6. **Generate Reports**
    - CSV: Top 100 frequently changed files with URLs
    - Text: Detailed metrics including average changes and largest PR details

7. **Send Email**
    - Sends an HTML email with the CSV and text reports attached.

8. **Error Handling**
    - Logs errors and stops execution if a critical step fails.

## Usage

Run the script from the terminal:

```bash
python3.12 <script_name> <repo_name> <head_commit_id> <base_commit_id> <to_email_ids> <branch_name>
```
Note:
- <repo_name>: Repository name in Gitea

- <base_commit_id>: SHA of the starting commit

- <head_commit_id>: SHA of the ending commit

- <to_email_ids>: Comma-separated email ids within double quotes

- <branch_name> (optional): Branch name (default: master)

> Ensure that:
> - config.ini and Logging_Framework.py are present in the same directory.
> - The script uses SSH URLs to clone/pull repositories and Git CLI to fetch metrics.