import os
import requests
import datetime
import calendar
import json
from prettytable import PrettyTable
from collections import defaultdict

class DevOpsChecklist:
    def __init__(self, repo_owner, repo_name):
        self.token = os.getenv('GITHUB_TOKEN')
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.headers = {
            'Authorization': f'token {self.token}',
            'Accept': 'application/vnd.github.v3+json'
        }
        self.base_url = f'https://api.github.com/repos/{repo_owner}/{repo_name}'
        self.devops_labels = self.get_devops_labels()
        self.monthly_data = {}  # Store data for each month


    def get_devops_labels(self):
        """Get DevOps related labels from GitHub repository"""
        url = f'{self.base_url}/labels'
        response = requests.get(url, headers=self.headers)

        if response.status_code != 200:
            print(f"Error fetching labels: {response.status_code}")
            return ["CI/CD", "Infrastructure", "Monitoring", "Security", "Testing"]

        all_labels = response.json()
        # Filter for DevOps-related labels - adjust this filter as needed
        devops_labels = [label['name'] for label in all_labels
                         if any(keyword in label['name'].lower()
                                for keyword in ['devops', 'ci', 'cd', 'infra', 'monitor',
                                                'security', 'test', 'deploy', 'automation'])]

        # If no DevOps labels found, use default ones
        if not devops_labels:
            devops_labels = ["CI/CD", "Infrastructure", "Monitoring", "Security", "Testing"]

        return devops_labels

    def get_week_boundaries(self, year, month):
        """Calculate the boundaries for each week in a month"""
        cal = calendar.monthcalendar(year, month)
        weeks = []

        for week_num, week in enumerate(cal, 1):
            if week_num > 4:  # Only consider first 4 weeks
                break

            # Find first and last day of this week (excluding zeros)
            days = [day for day in week if day != 0]
            if days:
                start_day = min(days)
                end_day = max(days)

                start_date = datetime.date(year, month, start_day)
                end_date = datetime.date(year, month, end_day)

                weeks.append({
                    'week_num': week_num,
                    'start_date': start_date,
                    'end_date': end_date
                })

        return weeks

    def get_completed_issues(self, label, start_date, end_date):
        """Get number of completed issues for a specific label in date range"""
        url = f'{self.base_url}/issues'

        # Format dates for GitHub API
        start_str = start_date.isoformat()
        end_str = end_date.isoformat()

        params = {
            'labels': label,
            'state': 'closed',
            'since': start_str,
            'until': end_str,
            'per_page': 100
        }

        response = requests.get(url, headers=self.headers, params=params)

        if response.status_code != 200:
            print(f"Error fetching issues: {response.status_code}")
            return 0

        issues = response.json()
        return len(issues)

    def generate_month_data(self, year, month):
        """Generate data for a specific month"""
        month_name = calendar.month_name[month]
        month_key = f"{year}-{month:02d}"

        # Initialize data structure for this month
        self.monthly_data[month_key] = {
            'year': year,
            'month': month,
            'month_name': month_name,
            'weeks': self.get_week_boundaries(year, month),
            'data': defaultdict(lambda: {'weeks': [0, 0, 0, 0], 'total': 0})
        }

        # For each DevOps label and week, get completed issues
        for label in self.devops_labels:
            for i, week in enumerate(self.monthly_data[month_key]['weeks']):
                if i < 4:  # Ensure we only process 4 weeks
                    count = self.get_completed_issues(
                        label,
                        week['start_date'],
                        week['end_date']
                    )

                    self.monthly_data[month_key]['data'][label]['weeks'][i] = count
                    self.monthly_data[month_key]['data'][label]['total'] += count

        return self.monthly_data[month_key]

    def display_month_checklist(self, year, month):
        """Display checklist for a specific month"""
        # Generate data if it doesn't exist
        month_key = f"{year}-{month:02d}"
        if month_key not in self.monthly_data:
            self.generate_month_data(year, month)

        month_data = self.monthly_data[month_key]

        # Create table
        table = PrettyTable()
        table.field_names = ["DevOps Area", "Week 1", "Week 2", "Week 3", "Week 4", "Total"]

        # Add rows
        for label in self.devops_labels:
            if label in month_data['data']:
                weeks_data = month_data['data'][label]['weeks']
                total = month_data['data'][label]['total']

                # Format each cell with count and checkbox
                week_cells = []
                for count in weeks_data:
                    checkbox = "[x]" if count > 0 else "[ ]"
                    week_cells.append(f"{checkbox} ({count})")

                table.add_row([label] + week_cells + [total])

        print(f"\n{month_data['month_name']} {month_data['year']} DevOps Checklist")
        print(table)

        return table

    def save_to_json(self, filename="devops_checklists.json"):
        """Save all monthly data to JSON file"""
        with open(filename, 'w') as f:
            json.dump(self.monthly_data, f, indent=2, default=str)
        print(f"Data saved to {filename}")

    def load_from_json(self, filename="devops_checklists.json"):
        """Load monthly data from JSON file"""
        if os.path.exists(filename):
            with open(filename, 'r') as f:
                data = json.load(f)

            # Convert back to our expected structure
            for month_key, month_data in data.items():
                # Convert string dates back to datetime
                for week in month_data['weeks']:
                    week['start_date'] = datetime.datetime.fromisoformat(week['start_date']).date()
                    week['end_date'] = datetime.datetime.fromisoformat(week['end_date']).date()

                # Convert defaultdict
                month_data['data'] = defaultdict(lambda: {'weeks': [0, 0, 0, 0], 'total': 0},
                                                 month_data['data'])

            self.monthly_data = data
            print(f"Data loaded from {filename}")
        else:
            print(f"File {filename} not found")

    def generate_current_month(self):
        """Generate checklist for current month"""
        today = datetime.date.today()
        return self.generate_month_data(today.year, today.month)

    def generate_all_months_this_year(self):
        """Generate checklists for all months of current year"""
        today = datetime.date.today()
        year = today.year

        for month in range(1, 13):
            self.generate_month_data(year, month)


# Example usage
if __name__ == "__main__":
    # Replace these with your actual values
    github_token = "your_github_token"
    repo_owner = "your_username"
    repo_name = "your_repo"

    checklist = DevOpsChecklist(github_token, repo_owner, repo_name)

    # Generate current month's checklist
    current_month_data = checklist.generate_current_month()
    checklist.display_month_checklist(current_month_data['year'], current_month_data['month'])

    # Save data to JSON
    checklist.save_to_json()

    # To generate for a specific month
    # checklist.display_month_checklist(2025, 3)  # March 2025

    # To load from previously saved data
    # checklist.load_from_json()