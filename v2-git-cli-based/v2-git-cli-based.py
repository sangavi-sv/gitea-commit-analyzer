import configparser
import subprocess
from collections import Counter
from datetime import datetime
import sys
import ast
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import os
import csv
import time


# -------------------------
# Utility to run shell cmds
# -------------------------
def run(cmd, cwd=None):
    try:
        return subprocess.check_output(cmd, shell=True, cwd=cwd).decode().strip()
    except subprocess.CalledProcessError as e:
        print(f"Command failed: {cmd} - {e}")
        sys.exit(1)

# -------------------------
# Repository Utilities
# -------------------------
def ensure_repo(repo_dir, repo_name, remote_url, branch="master"):
    full_path = os.path.join(repo_dir, repo_name)
    if os.path.exists(full_path) and os.path.exists(os.path.join(full_path, ".git")):
        print(f"Repository {repo_name} exists. Pulling latest changes...")
        run(f"git checkout {branch}", cwd=full_path)
        run(f"git pull origin {branch}", cwd=full_path)
    else:
        print(f"Repository {repo_name} not found. Cloning into {repo_dir}...")
        if not os.path.exists(repo_dir):
            os.makedirs(repo_dir)
        run(f"git clone -b {branch} {remote_url} {full_path}", cwd=repo_dir)
    return full_path

# -------------------------
# Core Git CLI Metric Logic
# -------------------------
def get_commit_count(base, head):
    return int(run(f"git rev-list --count {base}..{head}")) + 1

def get_changed_files_and_totals(base, head):
    output = run(f"git log --numstat {base}..{head}")
    file_changes = Counter()
    total_add, total_del = 0, 0
    for line in output.splitlines():
        parts = line.split()
        if len(parts) == 3 and parts[0].isdigit():
            adds = int(parts[0])
            dels = int(parts[1])
            fname = parts[2]
            total_add += adds
            total_del += dels
            file_changes[fname] += 1
    return file_changes, total_add, total_del, total_add + total_del

def get_merge_commits(base, head):
    output = run(f'git log --merges --pretty="%H %s" {base}..{head}')
    merges = []
    for line in output.splitlines():
        parts = line.split(" ", 1)
        sha = parts[0]
        msg = parts[1] if len(parts) > 1 else ""
        if "Merge pull request" in msg:
            merges.append((sha, msg))
    return merges

def get_pr_size(merge_sha):
    output = run(f"git show --numstat {merge_sha}")
    adds, deletes = 0, 0
    for line in output.splitlines():
        parts = line.split()
        if len(parts) >= 3 and parts[0].isdigit():
            adds += int(parts[0])
            deletes += int(parts[1])
    return adds, deletes, adds + deletes

# -------------------------
# Report Generators
# -------------------------
def generate_report(gitea_url, repo, file_changes, output_dir="."):
    print("Generating CSV report...")
    current_date_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    csv_filename = os.path.join(output_dir, f"Top_100_frequently_changed_files_{current_date_time}.csv")
    top_files = file_changes.most_common(100)
    with open(csv_filename, mode="w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["Rank", "File URL", "Changes"])
        for rank, (file_path_item, change_count) in enumerate(top_files, 1):
            file_url = f"{gitea_url}/onebill/{repo}/src/branch/master/{file_path_item.lstrip('/')}"
            writer.writerow([rank, file_url, change_count])
    print(f"CSV report generated successfully: {csv_filename}")
    return csv_filename, len(file_changes)

def generate_text_report(commit_count, total_additions, total_deletions, total_changes,
                         PR_count, total_number_of_files_changed, avg_additions,
                         avg_deletions, avg_changes, max_PR_details,
                         repository, branch_name, output_dir="."):
    current_date_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    txt_filename = os.path.join(output_dir, f"Report_{current_date_time}.txt")
    report_content = f"""
========== Commit Analysis Report ==========
Repository Name: {repository}
Branch Name: {branch_name}

Total number of commits between base and head: {commit_count}

Total Additions: {total_additions}
Total Deletions: {total_deletions}
Total Changes: {total_changes}

Total number of PR merged: {PR_count}
Total number of files changed: {total_number_of_files_changed}

Average Additions: {avg_additions:.2f}
Average Deletions: {avg_deletions:.2f}
Average Changes: {avg_changes:.2f}

Details of PR with Max size:
PR SHA: {max_PR_details['PR_sha'] if max_PR_details else 'N/A'}
Additions: {max_PR_details['additions'] if max_PR_details else 0}
Deletions: {max_PR_details['deletions'] if max_PR_details else 0}
Files Changed: {max_PR_details['files_changed'] if max_PR_details else 0}
===========================================
    """
    with open(txt_filename, "w", encoding="utf-8") as f:
        f.write(report_content)
    print(f"Text report generated successfully: {txt_filename}")
    return txt_filename

# -------------------------
# Email Sender
# -------------------------
def send_mail(subject, body, attachment=None, is_html=False):
    try:
        message = MIMEMultipart()
        message['From'] = sender_mail
        message['To'] = ', '.join(receiver_emails)
        message['Cc'] = ', '.join(cc_email)
        message['Subject'] = subject

        if is_html:
            message.attach(MIMEText(body, 'html'))
        else:
            message.attach(MIMEText(body, 'plain'))

        if attachment:
            paths = attachment if isinstance(attachment, list) else [attachment]
            for file_path in paths:
                if os.path.exists(file_path):
                    with open(file_path, "rb") as file:
                        part = MIMEBase('application', 'octet-stream')
                        part.set_payload(file.read())
                        encoders.encode_base64(part)
                        part.add_header('Content-Disposition', f'attachment; filename="{os.path.basename(file_path)}"')
                        message.attach(part)
                else:
                    print(f"Attachment {file_path} not found")
                    sys.exit(1)

        all_recipients = receiver_emails + cc_email
        with smtplib.SMTP(smtp_server, int(smtp_port)) as server:
            server.starttls()
            server.login(sender_username, sender_password)
            server.sendmail(sender_mail, all_recipients, message.as_string())

        print("Email sent successfully")

    except Exception as e:
        print(f"Failed to send email: {e}")
        sys.exit(1)

# -------------------------
# Master Metrics Computation
# -------------------------
def compute_all_metrics(repository, base_sha, head_sha):
    start = time.time()
    print("Computing metrics via Git CLI...")

    commit_count = get_commit_count(base_sha, head_sha)
    file_changes, total_additions, total_deletions, total_changes = get_changed_files_and_totals(base_sha, head_sha)
    merges = get_merge_commits(base_sha, head_sha)
    PR_count = len(merges)

    max_pr_size = 0
    max_pr_details = None
    for sha, _ in merges:
        adds, dels, total = get_pr_size(sha)
        if total > max_pr_size:
            max_pr_size = total
            parents = run(f"git rev-list --parents -n 1 {sha}").split()
            if len(parents) >= 3:  # merge commit has two parents
                parent1 = parents[1]
                parent2 = parents[2]
                files_changed = run(f"git diff --name-only {parent1} {sha}").splitlines()
            else:
                files_changed = run(f"git diff --name-only {parents[1]} {sha}").splitlines()
            files_changed = [f for f in files_changed if f.strip()]

            max_pr_details = {
                "PR_sha": sha,
                "additions": adds,
                "deletions": dels,
                "files_changed": len(files_changed)
            }

    avg_additions = total_additions / commit_count
    avg_deletions = total_deletions / commit_count
    avg_changes = total_changes / commit_count

    elapsed = time.time() - start
    print(f"Metrics computed in {elapsed:.2f} seconds")

    return (commit_count, PR_count, file_changes,
            avg_additions, avg_deletions, avg_changes,
            max_pr_details, total_additions, total_deletions, total_changes)

# -------------------------
# Main Script
# -------------------------
if __name__ == "__main__":
    try:
        config = configparser.ConfigParser()
        config.read("config.ini")

        gitea_config = config['gitea']
        gitea_url = gitea_config['gitea_DNS'].rstrip('/')
        repo_dir = gitea_config.get("local_repo_dir", ".")

        email_config = config['mail']
        sender_mail = email_config['sender_email']
        sender_username = email_config['sender_username']
        sender_password = email_config['sender_password']
        smtp_server = email_config['smtp_server']
        smtp_port = email_config['smtp_port']
        cc_email = ast.literal_eval(email_config['cc_email'])
        subject = email_config['subject']

        report_config = config['report']
        output_dir = report_config.get('output_dir', '.')
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        repository = sys.argv[1].strip()
        head_sha = sys.argv[2].strip()
        base_sha = sys.argv[3].strip()
        receiver_emails = [email.strip() for email in sys.argv[4].strip().split(",")]
        branch_name = sys.argv[5].strip() if len(sys.argv) > 5 else "master"

        repo_ssh_url = f"git@{gitea_url}:onebill/{repository}.git"

        # Ensure repo exists locally and switch to it
        local_repo_path = ensure_repo(repo_dir, repository, repo_ssh_url, branch_name)
        os.chdir(local_repo_path)

        # Compute metrics
        (commit_count, PR_count, file_changes,
         avg_additions, avg_deletions, avg_changes,
         max_PR_details, total_additions, total_deletions, total_changes) = compute_all_metrics(repository, base_sha, head_sha)

        # Generate reports
        csv_file_name, total_files_changed = generate_report(gitea_url, repository, file_changes, output_dir)
        text_file_name = generate_text_report(
            commit_count, total_additions, total_deletions, total_changes,
            PR_count, total_files_changed, avg_additions,
            avg_deletions, avg_changes, max_PR_details,
            repository, branch_name, output_dir
        )
        print(f"Total number of commits between the entered commit IDs (including Base and Head): {commit_count}")
        print(f"total_additions: {total_additions}")
        print(f"total_deletions: {total_deletions}")
        print(f"total_changes: {total_changes}")
        print(f"Total number of PR merged: {PR_count}")
        print(f"Total number of files changed: {total_files_changed}")
        print(f"CSV file name: {csv_file_name}")
        print(f"Average addition: {avg_additions} Average deletion: {avg_deletions} Average changes: {avg_changes}")
        print(f"Details of PR with Max size: {max_PR_details}")


# Build HTML email body
        body = f"""
        <html>
        <body>
            <p>Hello All,</p>
            <p><b>Repository:</b> {repository}<br>
            <b>Branch:</b> {branch_name}<br>
            <b>Commit Range:</b> {base_sha} → {head_sha}<br>
            <b>Total Commits:</b> {commit_count}<br>
            <b>Total Additions:</b> {total_additions}<br>
            <b>Total Deletions:</b> {total_deletions}<br>
            <b>Total Changes:</b> {total_changes}<br>
            <b>Total PR Merges:</b> {PR_count}<br>
            <b>Total Files Changed:</b> {total_files_changed}<br>
            <b>Average Additions:</b> {avg_additions:.2f}<br>
            <b>Average Deletions:</b> {avg_deletions:.2f}<br>
            <b>Average Changes:</b> {avg_changes:.2f}<br>
            <b>Largest PR Details:</b> {max_PR_details}</p>

            <p><b>Top 100 Frequently Changed Files</b></p>
            <table border="1" cellpadding="5" cellspacing="0">
        """
        with open(csv_file_name, "r") as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                if len(row) >= 3:
                    body += f"<tr><td>{row[0]}</td><td>{row[1]}</td><td>{row[2]}</td></tr>\n"

        body += """
            </table>
            <p>The same file is attached as CSV.</p>
            <p>Regards,<br>OneBill DevOps</p>
        </body>
        </html>
        """

        send_mail(subject, body, [csv_file_name, text_file_name], is_html=True)

    except Exception as err:
        print(f"Error in main execution: {err}")
        sys.exit(1)