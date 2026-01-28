import json
import problem_catalog

# Extract data
data = {
    "start_phrases": problem_catalog.START_PHRASES,
    "catalog": problem_catalog.PROBLEM_CATALOGUES
}

# Write to JSON
with open('scenarios/ulla_support/problems.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=4, ensure_ascii=False)

print("Migration complete.")
