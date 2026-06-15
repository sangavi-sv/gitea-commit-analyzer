# Gitea Commit Analyzer (V1 - API Based)

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

This Python automation tool analyzes commit activity within a Gitea repository by consuming Gitea REST APIs. Given a repository name and a commit range (base SHA and head SHA), the script collects commit statistics, tracks merged pull requests, identifies frequently modified files, and generates detailed reports.

The tool automatically generates CSV and text reports and emails the results to the specified recipients.

## Features

* Fetches commit information using Gitea REST APIs
* Analyzes commits between two commit IDs
* Calculates:

  * Total commits
  * Total additions
  * Total deletions
  * Total code changes
  * Total merged pull requests
  * Average additions, deletions, and changes per commit
* Identifies the Top 100 Frequently Changed Files
* Detects the largest pull request based on size
* Generates CSV and text reports
* Sends automated email reports with attachments

## Prerequisites

* Python 3.12 or later
* Access to a Gitea instance
* Valid Gitea API Token
* SSL certificate (if required by your environment)
* SMTP mail server credentials

## Dependencies

Install the required packages:

```bash
pip install requests configparser
```

The script also uses the following Python standard libraries:

* collections
* datetime
* csv
* smtplib
* email
* os
* sys
* ast

## Configuration

Create a `config.ini` file containing the following sections:

### Gitea Configuration

* Gitea URL
* API Token
* SSL Certificate Path

### Email Configuration

* Sender Email
* Sender Username
* Sender Password
* SMTP Server
* SMTP Port
* CC Email List
* Email Subject

### Report Configuration

* Output Directory

## Workflow

### 1. Load Configuration

Reads Gitea, email, and report settings from `config.ini`.

### 2. Accept User Inputs

Receives:

* Repository Name
* Head Commit ID
* Base Commit ID
* Recipient Email IDs
* Branch Name

### 3. Retrieve Commit Information

Uses Gitea APIs to fetch commit data for all commits between the specified commit IDs.

### 4. Analyze Commit Metrics

Calculates:

* Commit Count
* Additions
* Deletions
* Total Changes
* Pull Request Count
* Frequently Modified Files

### 5. Identify Largest Pull Request

Tracks the pull request with the highest number of changes and records its details.

### 6. Generate Reports

Creates:

* CSV report containing Top 100 Frequently Changed Files
* Text report containing commit and pull request statistics

### 7. Send Email Notification

Builds an HTML email summary and attaches generated reports automatically.

### 8. Error Handling

Handles API failures, configuration issues, file errors, and email delivery failures.

## Usage

Run the script from the terminal:

```bash
python3 script.py <repository_name> <head_commit_id> <base_commit_id> <recipient_emails> <branch_name>
```

### Example

```bash
python3 script.py billing-service a1b2c3d e4f5g6h user1@example.com,user2@example.com master
```

## Output

The script generates:

### CSV Report

* Top 100 Frequently Changed Files
* File URLs
* Change Counts

### Text Report

* Commit Statistics
* Pull Request Statistics
* Average Changes
* Largest Pull Request Details

### Email Report

An HTML summary email containing:

* Repository Information
* Commit Metrics
* Pull Request Metrics
* Frequently Changed Files Table
* CSV and Text Report Attachments

