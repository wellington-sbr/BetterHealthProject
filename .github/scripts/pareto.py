import os
import re
import pandas as pd
import matplotlib.pyplot as plt
import json

# Get issues data from file
issues_file = os.getenv('ISSUES_FILE')
with open(issues_file, 'r') as file:
    issues_data = file.read()

issues = json.loads(issues_data)
print("Total issues fetched:", len(issues))

conventional_commit_pattern = r"^(feat|fix|docs|chore|style|refactor|test|build|ci|perf|merge|revert|workflow|types|wip):"

titles = [issue['title'] for issue in issues]
print("Issue titles:", titles)

# Extract commit type from titles
commit_types = []
for title in titles:
    match = re.match(conventional_commit_pattern, title)
    if match:
        commit_types.append(match.group(1))  # Get the commit type (e.g., feat, fix, docs)

print("Commit types:", commit_types)

# Count frequency of each commit type
commit_counts = pd.Series(commit_types).value_counts().reset_index()
commit_counts.columns = ['Commit Type', 'Count']
print("Commit counts:", commit_counts)

# Sort data in descending order of frequency
commit_counts = commit_counts.sort_values(by='Count', ascending=False)

# Calculate cumulative percentage for Pareto chart
commit_counts['Cumulative Percentage'] = commit_counts['Count'].cumsum() / commit_counts['Count'].sum() * 100

# Plot the Pareto chart
fig, ax1 = plt.subplots(figsize=(10, 6))

# Bar chart for frequency count
ax1.bar(commit_counts['Commit Type'], commit_counts['Count'], color='b', label='Frequency')
ax1.set_ylabel('Frequency', color='b')
ax1.set_xlabel('Commit Type')
ax1.tick_params(axis='y', labelcolor='b')

# Line chart for cumulative percentage
ax2 = ax1.twinx()
ax2.plot(commit_counts['Commit Type'], commit_counts['Cumulative Percentage'], color='r', marker='o', linestyle='-',
         label='Cumulative %')
ax2.set_ylabel('Cumulative Percentage', color='r')
ax2.tick_params(axis='y', labelcolor='r')

plt.title('Pareto Chart of Commit Types')
plt.xticks(rotation=45)
plt.grid(True)

# Save the plot to a file
plt.savefig('pareto_chart.png', bbox_inches='tight')
plt.show()
