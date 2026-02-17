import unittest
import sys
import os
import shutil
import tempfile
import json
from unittest.mock import patch

# Add project root to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scenario_manager import ScenarioManager, Scenario
from scenario_handlers import ArgaAlexHandler, BaseScenarioHandler

class TestScenarioManager(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.scenarios_dir = os.path.join(self.test_dir, "scenarios")
        os.makedirs(self.scenarios_dir)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def create_mock_scenario(self, name, enabled=True, persona_name="Support"):
        dir_path = os.path.join(self.scenarios_dir, name.lower().replace(" ", "_"))
        os.makedirs(dir_path)
        
        config = {
            "scenario_name": name,
            "persona_name": persona_name,
            "enabled": enabled,
            "target_email": f"{name.lower().replace(' ', '_')}@test.com",
            "db_prefix": "test_"
        }
        with open(os.path.join(dir_path, "config.json"), "w") as f:
            json.dump(config, f)
            
        problems = {"catalog": [[{"id": "P1"}]], "start_phrases": ["start"]}
        with open(os.path.join(dir_path, "problems.json"), "w") as f:
            json.dump(problems, f)
            
        with open(os.path.join(dir_path, "persona_prompt.txt"), "w") as f:
            f.write("Persona Prompt")
        with open(os.path.join(dir_path, "evaluator_prompt.txt"), "w") as f:
            f.write("Eval Prompt")
            
        return dir_path

    def test_load_valid_scenario(self):
        self.create_mock_scenario("Arga Alex")
        manager = ScenarioManager(self.scenarios_dir)
        manager.load_scenarios()
        
        self.assertEqual(len(manager.scenarios), 1)
        scenario = manager.scenarios[0]
        self.assertEqual(scenario.name, "Arga Alex")
        self.assertIsInstance(scenario.handler, ArgaAlexHandler)

    def test_load_disabled_scenario(self):
        self.create_mock_scenario("Disabled Scenario", enabled=False)
        manager = ScenarioManager(self.scenarios_dir)
        manager.load_scenarios()
        self.assertEqual(len(manager.scenarios), 0)

    def test_handler_assignment(self):
        self.create_mock_scenario("Default Scenario")
        manager = ScenarioManager(self.scenarios_dir)
        manager.load_scenarios()
        
        scenario = manager.scenarios[0]
        self.assertIsInstance(scenario.handler, BaseScenarioHandler)
        self.assertNotIsInstance(scenario.handler, ArgaAlexHandler)

    def test_missing_files(self):
        os.makedirs(os.path.join(self.scenarios_dir, "broken_scenario"))
        manager = ScenarioManager(self.scenarios_dir)
        manager.load_scenarios()
        self.assertEqual(len(manager.scenarios), 0)

if __name__ == "__main__":
    unittest.main()
