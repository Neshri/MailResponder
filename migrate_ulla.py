import json
import os

ULLA_JSON_PATH = "scenarios/ulla_support/problems.json"

def migrate_ulla_problems():
    if not os.path.exists(ULLA_JSON_PATH):
        print(f"File not found: {ULLA_JSON_PATH}")
        return

    with open(ULLA_JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    new_catalog = []
    
    for level in data.get("catalog", []):
        new_level = []
        for problem in level:
            # Extract basic fields
            p_id = problem.get("id")
            start_prompt = problem.get("start_prompt")
            
            # Extract Context Data
            description = problem.get("beskrivning")
            technicals = problem.get("tekniska_fakta")
            solutions = problem.get("losning_nyckelord")
            
            # Build New Structure
            new_problem = {
                "id": p_id,
                "start_prompt": start_prompt,
                "persona_context": {
                    "description": description,
                    "technical_facts": technicals
                },
                "evaluator_context": {
                    "source_problem_description": description, # Evaluator often needs this
                    "solution_keywords": solutions
                }
            }
            new_level.append(new_problem)
        new_catalog.append(new_level)

    data["catalog"] = new_catalog

    with open(ULLA_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
        
    print(f"Migrated {len(new_catalog)} levels in {ULLA_JSON_PATH}")

if __name__ == "__main__":
    migrate_ulla_problems()
