import unittest
import sys
import os

def run_all_tests():
    """Discover and run all tests in the tests folder."""
    # Ensure the project root is in sys.path
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

    print("\n" + "="*50)
    print("RUNNING ALL MAILRESPONDER TESTS")
    print("="*50 + "\n")

    loader = unittest.TestLoader()
    # Discover all files matching 'test_*.py' in the 'tests' directory
    start_dir = os.path.dirname(os.path.abspath(__file__))
    suite = loader.discover(start_dir, pattern='test_*.py')

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Also run the custom verification scripts
    print("\n" + "="*50)
    print("RUNNING ADDITIONAL VERIFICATION SCRIPTS")
    print("="*50 + "\n")

    verification_scripts = [
        "verify_idempotency.py",
        "verify_prompt_structure.py"
    ]

    for script in verification_scripts:
        script_path = os.path.join(start_dir, script)
        if os.path.exists(script_path):
            print(f"Running {script}...")
            # We use os.system or subprocess to run these as they are standalone scripts
            exit_code = os.system(f"{sys.executable} \"{script_path}\"")
            if exit_code != 0:
                print(f"FAILED: {script}")
                # We don't exit immediately so we see all results
            else:
                print(f"PASSED: {script}")
        else:
            print(f"SKIPPING: {script} (not found)")

    if not result.wasSuccessful():
        sys.exit(1)

if __name__ == "__main__":
    run_all_tests()
