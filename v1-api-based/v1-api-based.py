import configparser
import requests
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
            if isinstance(attachment, list):
                for file_path in attachment:
                    if os.path.exists(file_path):
                        with open(file_path, "rb") as file:
                            part = MIMEBase('application', 'octet-stream')
                            part.set_payload(file.read())
                            encoders.encode_base64(part)
                            part.add_header('Content-Disposition', f'attachment; filename="{os.path.basename(file_path)}"')
                            message.attach(part)
                    else:
                        print(f"Attachment file {file_path} not found")
                        sys.exit(1)
            else:
                if os.path.exists(attachment):
                    with open(attachment, "rb") as file:
                        part = MIMEBase('application', 'octet-stream')
                        part.set_payload(file.read())
                        encoders.encode_base64(part)
                        part.add_header('Content-Disposition', f'attachment; filename="{os.path.basename(attachment)}"')
                        message.attach(part)
                else:
                    print(f"Attachment file {attachment} not found")
                    sys.exit(1)

        all_recipients = receiver_emails + cc_email
        with smtplib.SMTP(smtp_server, int(smtp_port)) as server:
            server.starttls()
            server.login(sender_username, sender_password)
            server.sendmail(sender_mail, all_recipients, message.as_string())

        print(f"Email sent successfully")

    except Exception as mail_error:
        print(f"Failed to send email with subject '{subject}': {mail_error}")
        sys.exit(1)

# Function to fetch commit data from the API
def fetch_commit_data(gitea_url, repo, current_sha, headers, verify):
    url = f"{gitea_url}/api/v1/repos/onebill/{repo}/git/commits/{current_sha}"

    try:
        print(f"Fetching commit data for SHA: {current_sha}")
        response = requests.get(url, headers=headers, verify=verify)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as http_error:
        print(f"HTTP error occurred while fetching commit {current_sha}: {http_error}")
        sys.exit(1)
    except Exception as error:
        print(f"An error occurred while fetching commit {current_sha}: {error}")
        sys.exit(1)

# Function to process a commit and track PRs
def process_commit(commit_data, current_sha, file_changes, total_additions, total_deletions, total_changes, max_PR_size, max_PR_details, PR_count):
    try:
        stats = commit_data.get("stats", {})
        additions = stats.get("additions", 0)
        deletions = stats.get("deletions", 0)

        total_additions += additions
        total_deletions += deletions
        total_changes += additions + deletions
        for file in commit_data.get("files", []):
            filename = file.get("filename")

            if filename in file_changes:
                file_changes[filename] += 1
            else:
                file_changes[filename] = 1

        parents = commit_data.get("parents", [])

        if len(parents) > 1:
            PR_count += 1
            print(f"Merge commit detected for SHA: {current_sha}")
            PR_additions, PR_deletions, PR_files_changed = 0, 0, 0

            PR_additions += additions
            PR_deletions += deletions

            PR_files_changed += sum(1 for file in commit_data.get("files", []))
            PR_size = PR_additions + PR_deletions

            if PR_size > max_PR_size:
                max_PR_size = PR_size
                max_PR_details = {
                    "PR_sha": current_sha,
                    "additions": PR_additions,
                    "deletions": PR_deletions,
                    "files_changed": PR_files_changed
                }
        return PR_count, total_additions, total_deletions, total_changes, file_changes, max_PR_size, max_PR_details
    except Exception as e:
        print(f"Error occurred while processing commit {current_sha}: {e}")
        sys.exit(1)


def generate_report(gitea_url, repo, file_changes, count, PR_count, output_dir="."):
    try:
        print("Generating CSV report...")
        current_date_time = datetime.now().strftime("%Y-%m-%d_%H:%M:%S")
        csv_filename = f"Top_100_frequently_changed_files_{current_date_time}.csv"
        file_path = os.path.join(output_dir, csv_filename)

        top_files = file_changes.most_common(100)

        with open(file_path, mode="w", newline="", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["Rank", "File URL", "Changes"])

            for rank, (file_path_item, change_count) in enumerate(top_files, 1):
                file_url = f"{gitea_url}/onebill/{repo}/src/branch/master/{file_path_item.lstrip('/')}"
                writer.writerow([rank, file_url, change_count])

        print(f"CSV report generated successfully: {file_path}")
        return file_path, len(file_changes)

    except Exception as error:
        print(f"Error generating CSV report: {error}")
        sys.exit(1)


def list_commits_between(gitea_url, repo_name, base_sha, head_sha, headers, branch_name="master", verify=True, PR_count=0):
    try:
        url = f"{gitea_url}/api/v1/repos/onebill/{repo_name}/commits?sha={branch_name}&limit=100"
        commit_ids = []
        record_commits = False

        while url:
            response = requests.get(url, headers=headers, verify=verify)
            if response.status_code == 200:
                commits = response.json()
                for commit in commits:
                    if commit['sha'] == base_sha:
                        record_commits = True
                    if record_commits:
                        commit_ids.append(commit['sha'])
                    if commit['sha'] == head_sha:
                        commit_ids.append(commit['sha'])
                        break
                # Check if there is another page of results
                if 'next' in response.links:
                    url = response.links['next']['url']
                else:
                    break
            else:
                print(f"Error: Unable to fetch commits. Status code: {response.status_code}")
                sys.exit(1)

        if base_sha not in commit_ids:
            commit_ids = [base_sha] + commit_ids
        if head_sha not in commit_ids:
            commit_ids.append(head_sha)

        commit_ids.reverse()
        return commit_ids, PR_count

    except Exception as e:
        print(f"An error occurred while fetching commits: {e}")
        sys.exit(1)



def generate_text_report(commit_count, total_additions, total_deletions, total_changes, PR_count, total_number_of_files_changed, avg_additions, avg_deletions, avg_changes, max_PR_details, repository, branch_name ,output_dir="."):
    try:
        report_content = f"""
========== Commit Analysis Report ==========
Repository Name: {repository}
Branch Name: {branch_name}

Total number of commits between the entered commit IDs (with head and base commit): {commit_count}
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

        current_date_time = datetime.now().strftime("%Y-%m-%d_%H:%M:%S")
        txt_filename = f"Report_{current_date_time}.txt"
        txt_file_path = os.path.join(output_dir, txt_filename)

        with open(txt_file_path, "w", encoding="utf-8") as txtfile:
            txtfile.write(report_content)

        print(f"Text report generated successfully: {txt_file_path}")
        return txt_file_path

    except Exception as error:
        print(f"Error generating text report: {error}")
        sys.exit(1)


# Main function to get the commit and PR count
def get_commit_and_PR_count(gitea_url, repo, branch, base_sha, head_sha, headers, verify=True):
    visited = set()
    commit_id = None
    count = 0
    PR_count = 0
    file_changes = Counter()
    total_additions = 0
    total_deletions = 0
    total_changes = 0
    max_PR_size = 0
    max_PR_details = None

    commit_ids, PR_count = list_commits_between(gitea_url, repo, base_sha, head_sha, headers, branch, verify, PR_count)
    if commit_ids:
        print(f"Commit IDs between {base_sha} and {head_sha} on branch '{branch}': {commit_ids}")
    else:
        print(f"No commits found between {base_sha} and {head_sha} on branch '{branch}' or an error occurred.")
        sys.exit(1)

    try:
        for commit_id in commit_ids:
            if commit_id in visited:
                continue
            visited.add(commit_id)

            commit_data = fetch_commit_data(gitea_url, repo, commit_id, headers, verify)
            if not commit_data:
                print(f"Failed to fetch commit data for {commit_id}")
                sys.exit(1)
            PR_count, total_additions, total_deletions, total_changes, file_changes, max_PR_size, max_PR_details = process_commit(
                commit_data, commit_id, file_changes, total_additions, total_deletions, total_changes, max_PR_size, max_PR_details, PR_count)
            count += 1

        avg_additions = total_additions / count if count else 0
        avg_deletions = total_deletions / count if count else 0
        avg_changes = total_changes / count if count else 0

        csv_file_name, total_files_changed = generate_report(gitea_url, repo, file_changes, count, PR_count, output_dir=output_dir)

        return count, PR_count, total_files_changed, avg_additions, avg_deletions, avg_changes, csv_file_name, max_PR_details, total_additions, total_deletions, total_changes
    except Exception as e:
        print(f"An error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    try:
        config = configparser.ConfigParser()
        config.read("config.ini")

        gitea_config = config['gitea']
        gitea_url = gitea_config['gitea_url'].rstrip('/')
        API_token = gitea_config['API_token']
        SSL_certificate_path=gitea_config['ssl_certificate_path']

        email_config=config['mail']
        sender_mail=email_config['sender_email']
        sender_username=email_config['sender_username']
        sender_password=email_config['sender_password']
        smtp_server=email_config['smtp_server']
        smtp_port=email_config['smtp_port']
        cc_email=ast.literal_eval(email_config['cc_email'])
        subject=email_config['subject']
        report_config = config['report']
        output_dir = report_config.get('output_dir', '.')

        headers = {
            "Authorization": f"token {API_token}",
            'Content-Type': 'application/json',
            "Accept": "application/json"
        }

        repository = sys.argv[1].strip()
        commit_id_head = sys.argv[2].strip()
        commit_id_base = sys.argv[3].strip()
        receiver_emails = sys.argv[4].strip().split(",")
        receiver_emails = [email.strip() for email in receiver_emails]
        branch_name = sys.argv[5].strip() if len(sys.argv) > 5 else "master"

        commit_count, PR_count ,total_number_of_files_changed ,avg_additions, avg_deletions, avg_changes, csv_file_name, max_PR_details,total_additions,total_deletions,total_changes = get_commit_and_PR_count(gitea_url, repository, branch_name, commit_id_base, commit_id_head,headers,verify = SSL_certificate_path)
        text_file_name = generate_text_report(commit_count, total_additions, total_deletions, total_changes, PR_count, total_number_of_files_changed, avg_additions, avg_deletions, avg_changes, max_PR_details, repository, branch_name, output_dir)
        print("Total number of commits between the entered commit IDs(including Base and Head):", commit_count)
        print(f"total_additions: {total_additions}")
        print(f"total_deletions: {total_deletions}")
        print(f"total_changes: {total_changes}")
        print("Total  number of PR merged :" ,PR_count)
        print("Total number of files changed: ", total_number_of_files_changed)
        print("Text file name:", csv_file_name)
        print("Average addition :",avg_additions ,"Average deletion:",avg_deletions,"Average changes:",avg_changes)
        print("Details of PR with Max size: ",max_PR_details)

        body = f"""
        <html>
        <body>
            <p>Hello All,</p>
            <p><b>Repository:</b> {repository}<br>
            <b>Branch:</b> {branch_name}<br>
            <b>Commit Range:</b> {commit_id_base} → {commit_id_head}<br>
            <b>Total Commits:</b> {commit_count - 1}<br>
            <b>Total Additions:</b> {total_additions}<br>
            <b>Total Deletions:</b> {total_deletions}<br>
            <b>Total PR Merges:</b> {PR_count}<br>
            <b>Total Files Changed:</b> {total_number_of_files_changed}<br>
            <b>Average Additions:</b> {avg_additions}<br>
            <b>Average Deletions:</b> {avg_deletions}<br>
            <b>Average Changes:</b> {avg_changes}<br>
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

    except Exception as error:
        print(f"Error occurred in main execution: {error}")
        sys.exit(1)