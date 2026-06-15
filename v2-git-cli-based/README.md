# Gitea Metrics Analyzer (V2 - Git CLI Based)

## Table of Contents

* [Overview](#overview)
* [Features](#features)
* [Prerequisites](#prerequisites)
* [Dependencies](#dependencies)
* [Configuration](#configuration)
* [Workflow](#workflow)
* [Usage](#usage)
* [Output](#output)

## Overview

This Python automation tool analyzes commits and pull requests (PRs) in a Gitea repository using native Git CLI commands. Unlike the API-based implementation, this version performs repository analysis locally by cloning or updating repositories and extracting metrics directly from Git history.

The tool generates detailed reports, identifies frequently modified files, tracks merged pull requests, and automatically emails the results to stakeholders.

## Features

* Automatically clones repositories if not available locally
* Updates existing repositories using Git pull
* Analyzes commits between two commit SHAs
* Calculates:

  * Total commits
  * Total additions
  * Total deletions
  * Total code changes
  * Average additions, deletions, and changes per commit
* Identifies merged pull requests
* Detects the largest pull request based on change volume
* Generates:

  * CSV report (Top 100 Frequently Changed Files)
  * Text report (Commit and PR statistics)
* Sends automated HTML email reports with attachments
* Works using Git CLI without relying on Gitea REST APIs

## Prerequisites

* Python 3.12 or later
* Git installed and available in the system PATH
* Access to the target Gitea repository via SSH
* Valid SMTP credentials for email notifications
* `config.ini` configuration file

## Dependencies

No external Python packages are required.

The script uses the following Python standard libraries:

* configparser
* subprocess
* collections
* datetime
* csv
* os
* sys
* ast
* smtplib
* email
* time

## Configuration

Create a `config.ini` file with the following sections:

### Gitea Configuration

```ini
[gitea]
gitea_DNS=<gitea_server_dns>
local_repo_dir=<local_repository_directory>
```

### Mail Configuration

```ini
[mail]
sender_email=
sender_username=
sender_password=
smtp_server=
smtp_port=
cc_email=
subject=
```

### Report Configuration

```ini
[report]
output_dir=
```

## Workflow

### 1. Load Configuration

Reads repository, email, and report settings from `config.ini`.

### 2. Accept User Inputs

Receives:

* Repository Name
* Head Commit SHA
* Base Commit SHA
* Recipient Email IDs
* Branch Name

### 3. Synchronize Repository

* Clones the repository if it does not exist locally.
* Pulls the latest changes if the repository already exists.

### 4. Analyze Repository Metrics

Calculates:

* Commit Count
* Additions
* Deletions
* Total Changes
* Pull Request Count
* Frequently Modified Files

### 5. Identify Largest Pull Request

Determines the pull request with the highest number of code changes and records its statistics.

### 6. Generate Reports

Creates:

* CSV report containing the Top 100 Frequently Changed Files
* Text report containing commit and pull request statistics

### 7. Send Email Notification

Builds an HTML summary email and attaches generated reports automatically.

### 8. Error Handling

Handles Git command failures, repository access issues, configuration errors, file generation failures, and email delivery errors.

## Usage

Run the script from the terminal:

```bash
python3 script.py <repository_name> <head_commit_sha> <base_commit_sha> <recipient_emails> <branch_name>
```

### Example

```bash
python3 script.py billing-service a1b2c3d e4f5g6h "user1@example.com,user2@example.com" master
```

## Output

### CSV Report

Contains:

* Top 100 Frequently Changed Files
* File URLs
* Number of Changes

### Text Report

Contains:

* Commit Statistics
* Pull Request Statistics
* Average Changes Per Commit
* Largest Pull Request Details

### Email Report

An HTML email containing:

* Repository Information
* Commit Metrics
* Pull Request Metrics
* Frequently Changed Files Summary
* CSV and Text Report Attachments

## Optimization Over V1

Compared to the API-based implementation:

* Eliminates dependency on Gitea REST APIs
* Reduces network calls and API overhead
* Uses native Git commands for faster analysis
* Automatically manages repository cloning and synchronization
* More scalable for large commit ranges
* Can be adapted easily for GitHub, GitLab, Bitbucket, and other Git-based platforms

