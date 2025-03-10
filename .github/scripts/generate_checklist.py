import os
import requests
from datetime import datetime, timedelta
import calendar
import yaml
import json
import sys

# Configuration from environment variables
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
GITHUB_REPOSITORY = os.environ.get("GITHUB_REPOSITORY", "")  # This env var is set by GitHub Actions

# If not running in Actions, allow fallback for local development
if not GITHUB_REPOSITORY:
    GITHUB_REPOSITORY = "usuario/repositorio"  # Only used if not running in GitHub Actions
    print("Warning: GITHUB_REPOSITORY not found. Using default value for local development.")

GITHUB_API_URL = f"https://api.github.com/repos/{GITHUB_REPOSITORY}"

# Headers for GitHub API
headers = {}
if GITHUB_TOKEN:
    headers["Authorization"] = f"token {GITHUB_TOKEN}"
    headers["Accept"] = "application/vnd.github.v3+json"
else:
    # We can still make some unauthenticated requests, with lower rate limits
    headers["Accept"] = "application/vnd.github.v3+json"
    print("Warning: No GITHUB_TOKEN provided. Using unauthenticated requests (limited rate).")


def create_devops_labels():
    """Create default DevOps labels if they don't exist"""
    default_labels = [
        {"name": "Plan", "color": "0052cc", "description": "Planning phase tasks"},
        {"name": "Code", "color": "006b75", "description": "Coding phase tasks"},
        {"name": "Build", "color": "ff9f1c", "description": "Build phase tasks"},
        {"name": "Test", "color": "e99695", "description": "Testing phase tasks"},
        {"name": "Release", "color": "bfd4f2", "description": "Release phase tasks"},
        {"name": "Deploy", "color": "7057ff", "description": "Deployment phase tasks"},
        {"name": "Operate", "color": "008672", "description": "Operation phase tasks"},
        {"name": "Monitor", "color": "d73a4a", "description": "Monitoring phase tasks"},
    ]

    for label in default_labels:
        try:
            response = requests.post(
                f"{GITHUB_API_URL}/labels",
                headers=headers,
                json=label
            )
            if response.status_code == 201:
                print(f"Label '{label['name']}' created successfully.")
            elif response.status_code == 422:
                print(f"Label '{label['name']}' already exists.")
            else:
                print(f"Failed to create label '{label['name']}'. Status code: {response.status_code}")
        except Exception as e:
            print(f"Error creating label '{label['name']}': {e}")


def get_devops_phases():
    """Get DevOps phases from GitHub labels"""
    try:
        response = requests.get(f"{GITHUB_API_URL}/labels", headers=headers)
        response.raise_for_status()

        # Filter only DevOps-related labels
        all_labels = response.json()
        devops_labels = [label["name"] for label in all_labels if "devops" in label["name"].lower()]

        # If no specific DevOps labels, use default set
        if not devops_labels:
            devops_labels = [
                "Plan", "Code", "Build", "Test",
                "Release", "Deploy", "Operate", "Monitor"
            ]

        return devops_labels
    except Exception as e:
        print(f"Error fetching GitHub labels: {e}")
        # Return default phases in case of error
        return [
            "Plan", "Code", "Build", "Test",
            "Release", "Deploy", "Operate", "Monitor"
        ]


def get_completed_issues_by_week(phase, start_date, end_date):
    """Get completed issues for a phase in date range"""
    try:
        # Format dates for GitHub API
        start_date_str = start_date.strftime('%Y-%m-%d')
        end_date_str = end_date.strftime('%Y-%m-%d')

        # Query closed issues with specific label in date range
        query = f"repo:{GITHUB_REPOSITORY} label:\"{phase}\" closed:{start_date_str}..{end_date_str}"
        response = requests.get(
            "https://api.github.com/search/issues",
            headers=headers,
            params={"q": query}
        )
        response.raise_for_status()

        return response.json()["total_count"]
    except Exception as e:
        print(f"Error fetching issues for {phase}: {e}")
        return 0


def generate_month_checklist(year, month):
    """Generate checklist data for a specific month"""
    # Get DevOps phases
    devops_phases = get_devops_phases()

    # Calculate dates for weeks in month
    first_day = datetime(year, month, 1)
    _, last_day_num = calendar.monthrange(year, month)
    last_day = datetime(year, month, last_day_num)

    # Divide month into 4 weeks (approximately)
    days_in_month = (last_day - first_day).days + 1
    days_per_week = days_in_month // 4

    weeks = []
    for i in range(4):
        start = first_day + timedelta(days=(i * days_per_week))
        end = first_day + timedelta(days=((i + 1) * days_per_week) - 1)
        if i == 3:  # For last week, ensure it includes last day
            end = last_day
        weeks.append((start, end))

    # Create checklist structure
    checklist_data = {
        "month": datetime(year, month, 1).strftime('%B %Y'),
        "phases": {}
    }

    # Get data for each phase
    for phase in devops_phases:
        phase_data = {
            "week1": {
                "completed": False,
                "issues_count": get_completed_issues_by_week(phase, weeks[0][0], weeks[0][1])
            },
            "week2": {
                "completed": False,
                "issues_count": get_completed_issues_by_week(phase, weeks[1][0], weeks[1][1])
            },
            "week3": {
                "completed": False,
                "issues_count": get_completed_issues_by_week(phase, weeks[2][0], weeks[2][1])
            },
            "week4": {
                "completed": False,
                "issues_count": get_completed_issues_by_week(phase, weeks[3][0], weeks[3][1])
            }
        }

        # Calculate total issues
        total_issues = sum([phase_data[f"week{i + 1}"]["issues_count"] for i in range(4)])
        phase_data["total_issues"] = total_issues

        checklist_data["phases"][phase] = phase_data

    return checklist_data


def save_checklist_to_yaml(checklist_data, output_file):
    """Save checklist data in YAML format"""
    with open(output_file, 'w') as file:
        yaml.dump(checklist_data, file, default_flow_style=False)
    print(f"Checklist saved to {output_file}")


def generate_markdown_table(checklist_data):
    """Generate markdown table to visualize checklist"""
    month = checklist_data["month"]
    phases = checklist_data["phases"]

    markdown = f"# DevOps Checklist - {month}\n\n"
    markdown += "| Phase | Week 1 | Week 2 | Week 3 | Week 4 | Total Issues |\n"
    markdown += "|------|---------|---------|---------|---------|-------------|\n"

    for phase, data in phases.items():
        week1 = "✅" if data["week1"]["completed"] else "⬜"
        week2 = "✅" if data["week2"]["completed"] else "⬜"
        week3 = "✅" if data["week3"]["completed"] else "⬜"
        week4 = "✅" if data["week4"]["completed"] else "⬜"
        total = data["total_issues"]

        markdown += f"| {phase} | {week1} ({data['week1']['issues_count']}) | {week2} ({data['week2']['issues_count']}) | {week3} ({data['week3']['issues_count']}) | {week4} ({data['week4']['issues_count']}) | {total} |\n"

    return markdown


def generate_monthly_checklist():
    """Main function to generate current month's checklist"""
    now = datetime.now()
    year = now.year
    month = now.month

    # Create DevOps labels if they don't exist
    create_devops_labels()

    # Generate checklist data
    checklist_data = generate_month_checklist(year, month)

    # Save to YAML
    output_file = "devops_checklist.yml"
    save_checklist_to_yaml(checklist_data, output_file)

    # Generate markdown for visualization
    markdown = generate_markdown_table(checklist_data)
    with open("health_checklist.md", 'w') as file:
        file.write(markdown)

    print(f"Health checklist generated at health_checklist.md")
    return checklist_data


if __name__ == "__main__":
    # Script can run without token in GitHub Actions for basic functionality
    if not GITHUB_TOKEN and not os.environ.get("GITHUB_ACTIONS"):
        print("Warning: GITHUB_TOKEN not set. Some functionality will be limited.")
        print("For full functionality: export GITHUB_TOKEN=ghp_abc123...")

    generate_monthly_checklist()
