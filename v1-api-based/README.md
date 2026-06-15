# Gitea commit ID data analyzer script 

## Table of contents
- [General Info](#general-info)
- [Prerequisites](#prerequisites)
- [Install Dependencies](#install-dependencies)
    - [Configuration](#configuration)
- [Script Workflow](#script-workflow)
- [Usage](#usage)

## General Info
>This script is designed to automate the process of tracking and analyzing commits and pull requests (PRs) within a Gitea repository. It fetches commit data from the Gitea API, processes each commit to determine if it is part of a PR, tracks the changes made in the repository (such as lines added or deleted), and generates a report on the top 100 most frequently changed files. The script also handles error logging, reporting, and provides details about the largest PRs (in terms of size) processed during the execution.

## Prerequisites
- Python 3.12
- config.ini file 
- Logging_Framework.py for logging setup


## Install Dependencies

Install the required Python libraries:

```
configparser
requests
collections
sys
csv
```
## Configuration
- The configuration file contains 
  - Gitea url 
  - API token
  - Location of SSL certificate
  - And the required details to send mail


## Script Workflow

1. **Read Configuration**
    - Loads gitea url and the API token from the config.ini file.

2. **Set Up Logging framework**
    - Initializes logging for info and error messages.

3. **Getting input from user** 
    - Prompt to enter the repository name , base commit ID , head commit ID and the branch name.

4. **Track Commit Metrics**
    - Initializes variables to track commit count, PR count, files changed, and largest PR.
   
5. **Fetch Commit Data**
    - Retrieves commit data from Gitea API using commit SHA and handles errors.
 
6. **Process Commits and PRs**
    - Iterates through commits, tracks PRs (merge commits), and updates metrics for additions, deletions, and changes.
   
7. **Generate Report**
    - Generates a text report with commit and PR statistics, including the most frequently changed files.

8. **Send Email**
    - Generates a text report with commit and PR statistics, including the most frequently changed files.

9. **Error Handling**
    - Logs errors and raises exceptions to halt execution when needed.


## Usage

Run the script from the terminal:

```bash
python3.12 script.py <repo_name> <base_commit_id> <head_commit_id> <to_email_ids> <branch_name>
```
Note: Email IDs should be separated by commas.

> Ensure that:
> - config.ini and Logging_Framework.py are present
> - A valid API token to access gitea without the login credentials