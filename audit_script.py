import re
import subprocess
import os

def run_command(command):
    """Runs a shell command and returns its output."""
    result = subprocess.run(command, capture_output=True, text=True, shell=True)
    return result.stdout, result.stderr

def main():
    """
    Reads the tasks.md file, extracts Python files for quality checking,
    and runs ruff and mypy on them.
    """
    tasks_file_path = "/home/juanjo/Documentos/python/ContextPython/ContextEngineering/.kiro/specs/project-audit-and-correction/tasks.md"
    base_dir = "/home/juanjo/Documentos/python/ContextPython/ContextEngineering"
    hook_name = "python-code-quality.kiro.hook"
    
    print(f"Starting Python code quality audit based on {tasks_file_path}")

    try:
        with open(tasks_file_path, "r") as f:
            tasks_content = f.read()
    except FileNotFoundError:
        print(f"Error: Could not find tasks file at {tasks_file_path}")
        return

    # Regex to find unchecked tasks for the specified hook
    task_pattern = re.compile(r"- \[ \] Audit and correct `(.*?)` against `" + re.escape(hook_name) + r"`")
    file_paths = task_pattern.findall(tasks_content)

    if not file_paths:
        print(f"No pending tasks found for hook: {hook_name}")
        return

    print(f"Found {len(file_paths)} files to check for '{hook_name}'...")

    all_issues = []

    for file_path in file_paths:
        # Ensure the file path is absolute and exists
        if not os.path.isabs(file_path):
            file_path = os.path.join(base_dir, file_path)
        
        if not os.path.exists(file_path):
            print(f"\n--- SKIPPING (Not Found): {file_path} ---")
            continue

        print(f"\n--- Checking: {file_path} ---")
        
        # 1. Run ruff check
        ruff_command = f"ruff check '{file_path}'"
        ruff_stdout, ruff_stderr = run_command(ruff_command)
        
        if ruff_stdout:
            print("Ruff Issues Found:")
            print(ruff_stdout)
            all_issues.append(f"Ruff issues in {file_path}:\n{ruff_stdout}")
        else:
            print("Ruff: No issues found.")

        if ruff_stderr:
            print(f"Ruff Error:\n{ruff_stderr}")


        # 2. Run mypy check
        # Note: mypy needs to be configured to run on a single file in a Django context,
        # which can be tricky. We run it with --ignore-missing-imports for simplicity.
        mypy_command = f"mypy '{file_path}' --ignore-missing-imports"
        mypy_stdout, mypy_stderr = run_command(mypy_command)

        if "Success: no issues found" not in mypy_stdout:
            print("MyPy Issues Found:")
            print(mypy_stdout)
            all_issues.append(f"MyPy issues in {file_path}:\n{mypy_stdout}")
        else:
            print("MyPy: No issues found.")
            
        if mypy_stderr:
            print(f"MyPy Error:\n{mypy_stderr}")


    print("\n--- Audit Summary ---")
    if not all_issues:
        print("✅ All checked files are compliant with Python code quality standards.")
    else:
        print(f"Found {len(all_issues)} files with issues.")
        print("Please review the logs above for details.")

if __name__ == "__main__":
    main()
