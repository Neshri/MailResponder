import os
import json
import logging
from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Tuple
from database import DatabaseManager

from dotenv import load_dotenv
import config as global_config
from config import EVAL_MODEL

@dataclass
class Scenario:
    name: str
    description: str
    target_email: str
    persona_model: str
    eval_model: str
    db_manager: DatabaseManager
    problems: List[List[Dict[str, Any]]]
    start_phrases: List[str]
    image_warning: str
    persona_prompt: str
    evaluator_prompt: str

    def get_problem_by_id(self, problem_id: str) -> Tuple[Optional[Dict], int]:
        for level_idx, level_catalogue in enumerate(self.problems):
            for problem in level_catalogue:
                if problem['id'] == problem_id:
                    return problem, level_idx
        return None, -1

class ScenarioManager:
    def __init__(self, scenarios_dir: str = "scenarios"):
        self.scenarios_dir = scenarios_dir
        self.scenarios: List[Scenario] = []

    def load_scenarios(self):
        """Loads all valid scenarios from the scenarios directory."""
        if not os.path.exists(self.scenarios_dir):
            logging.error(f"Scenarios directory not found: {self.scenarios_dir}")
            return

        for entry in os.scandir(self.scenarios_dir):
            if entry.is_dir():
                self._load_scenario_from_dir(entry.path)

    def _load_scenario_from_dir(self, dir_path: str):
        # 1. Load Scenario-specific .env if it exists
        scenario_env_path = os.path.join(dir_path, ".env")
        if os.path.exists(scenario_env_path):
            logging.info(f"Loading scenario specific .env from {scenario_env_path}")
            load_dotenv(scenario_env_path, override=True)

        config_path = os.path.join(dir_path, "config.json")
        problems_path = os.path.join(dir_path, "problems.json")

        if not os.path.exists(config_path) or not os.path.exists(problems_path):
            logging.warning(f"Skipping directory {dir_path}: Missing config.json or problems.json")
            return

        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            with open(problems_path, 'r', encoding='utf-8') as f:
                problems_data = json.load(f)

            if not config.get("enabled", True):
                logging.info(f"Skipping disabled scenario in {dir_path}")
                return

            # Resolve Email from Env Var if specified
            target_email = config.get("target_email")
            env_var_name = config.get("target_email_env_var")
            if env_var_name:
                env_email = os.getenv(env_var_name)
                if env_email:
                    target_email = env_email
                else:
                    logging.warning(f"Environment variable {env_var_name} not found for scenario {config.get('scenario_name')}")

            if not target_email:
                 logging.error(f"No target email found for scenario in {dir_path}. Skipping.")
                 return

            # Initialize Database Manager for this scenario
            # We place DBs inside the scenario folder by default
            db_manager = DatabaseManager(db_dir=dir_path, db_prefix=config.get("db_prefix", ""))
            db_manager.init_dbs()

            # Load Prompts (Try file, then default)
            persona_prompt = None
            evaluator_prompt = None
            
            persona_path = os.path.join(dir_path, "persona_prompt.txt")
            if os.path.exists(persona_path):
                with open(persona_path, "r", encoding="utf-8") as f: persona_prompt = f.read()
            
            evaluator_path = os.path.join(dir_path, "evaluator_prompt.txt")
            if os.path.exists(evaluator_path):
                with open(evaluator_path, "r", encoding="utf-8") as f: evaluator_prompt = f.read()

            if not persona_prompt:
                logging.error(f"Scenario {config.get('scenario_name')}: Missing persona_prompt.txt!")
                persona_prompt = "Du är en hjälpsam assistent." # Generic fallback
                
            if not evaluator_prompt:
                logging.error(f"Scenario {config.get('scenario_name')}: Missing evaluator_prompt.txt!")
                evaluator_prompt = "Bedöm om studenten har löst problemet. Svara [LÖST] eller [EJ_LÖST]." # Generic fallback
            
            # Determine Models (Config -> Global Env -> Fail)
            p_model = config.get("persona_model") or os.getenv("PERSONA_MODEL") or global_config.PERSONA_MODEL
            e_model = config.get("eval_model") or os.getenv("EVAL_MODEL") or global_config.EVAL_MODEL
            
            if not p_model or not e_model:
                logging.warning(f"Missing model configuration for scenario {config.get('scenario_name')}. Using defaults/fallbacks might fail.")

            scenario = Scenario(
                name=config.get("scenario_name", "Unknown"),
                description=config.get("description", ""),
                target_email=target_email,
                persona_model=p_model,
                eval_model=e_model,
                db_manager=db_manager,
                problems=problems_data.get("catalog", []),
                start_phrases=problems_data.get("start_phrases", []),
                image_warning=config.get("image_warning_message", ""),
                persona_prompt=persona_prompt,
                evaluator_prompt=evaluator_prompt
            )
            
            self.scenarios.append(scenario)
            logging.info(f"Loaded scenario: {scenario.name} ({scenario.target_email})")

        except Exception as e:
            logging.error(f"Failed to load scenario from {dir_path}: {e}")

    def get_scenarios(self) -> List[Scenario]:
        return self.scenarios
