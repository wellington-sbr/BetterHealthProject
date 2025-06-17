import os
import subprocess
import requests
import json

# Configuration from environment variables
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
GITHUB_REPOSITORY = os.environ.get("GITHUB_REPOSITORY", "")
PR_NUMBER = os.environ.get("PR_NUMBER")
APP_PATH = "betterhealth"

# If not running in Actions, allow fallback for local development
if not GITHUB_REPOSITORY:
    GITHUB_REPOSITORY = "usuario/repositorio"  # Only used if not running in GitHub Actions
    print("Warning: GITHUB_REPOSITORY not found. Using default value for local development.")

GITHUB_API_URL = f"https://api.github.com/repos/{GITHUB_REPOSITORY}"

# Headers for GitHub API
headers = {}
if GITHUB_TOKEN:
    headers["Authorization"] = f"token {GITHUB_TOKEN}"
    headers["Accept"] = "application/vnd.github.v4+json"
else:
    headers["Accept"] = "application/vnd.github.v4+json"
    print("Warning: No GITHUB_TOKEN provided. Using unauthenticated requests (limited rate).")

def get_bug_count():
    """Count issues labeled 'bug'."""
    url = f"{GITHUB_API_URL}/issues"
    params = {"state": "all", "labels": "bug", "per_page": 100}
    bug_count = 0
    page = 1
    while True:
        params["page"] = page
        resp = requests.get(url, params=params, headers=headers)
        if resp.status_code != 200:
            print(f"Failed to fetch issues: {resp.status_code} {resp.text}")
            break
        issues = resp.json()
        if not issues:
            break
        bug_count += len(issues)
        if len(issues) < 100:
            break
        page += 1
    return bug_count

def get_kloc():
    """Get KLOC for the app."""
    try:
        result = subprocess.run(
            ["cloc", APP_PATH, "--json"],
            stdout=subprocess.PIPE,
            text=True
        )
        data = json.loads(result.stdout)
        python_loc = data.get("Python", {}).get("code", 0)
        kloc = python_loc / 1000
        return kloc
    except Exception as e:
        print(f"Error running cloc: {e}")
        return 0

def post_pr_comment(pr_number, message):
    """Post a comment to the PR."""
    url = f"{GITHUB_API_URL}/issues/{pr_number}/comments"
    resp = requests.post(url, headers=headers, json={"body": message})
    if resp.status_code == 201:
        print("Comment posted to PR.")
    else:
        print(f"Failed to post comment: {resp.status_code} {resp.text}")

def main():
    bugs = get_bug_count()
    kloc = get_kloc()
    if kloc == 0:
        result = "No code found in app."
    else:
        defect_density = bugs / kloc if kloc else 0
        result = f"**Defect Density:** {defect_density:.2f} bugs/KLOC ({bugs} bugs, {kloc:.2f} KLOC)"
    print(result)

    # Post comment if running in PR context
    if PR_NUMBER and GITHUB_TOKEN:
        post_pr_comment(PR_NUMBER, result)

if __name__ == "__main__":
    if not GITHUB_TOKEN and not os.environ.get("GITHUB_ACTIONS"):
        print("Warning: GITHUB_TOKEN not set. Some functionality will be limited.")
        print("For full functionality: export GITHUB_TOKEN=ghp_abc123...")

    main()