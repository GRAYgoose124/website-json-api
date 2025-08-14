#!/usr/bin/env python3
"""
Pre-commit coverage checker for Python files.

This script checks if the lines being committed have test coverage.
"""

import subprocess
import sys
import tempfile
import os
import re
from pathlib import Path
from typing import List, Set, Tuple


def run_command(cmd: List[str], capture_output: bool = True) -> Tuple[int, str, str]:
    """Run a command and return exit code, stdout, stderr."""
    try:
        result = subprocess.run(
            cmd, 
            capture_output=capture_output, 
            text=True, 
            check=False
        )
        return result.returncode, result.stdout, result.stderr
    except Exception as e:
        return 1, "", str(e)


def get_staged_python_files() -> List[str]:
    """Get list of staged Python files (excluding test files)."""
    cmd = ["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"]
    exit_code, stdout, stderr = run_command(cmd)
    
    if exit_code != 0:
        print(f"Error getting staged files: {stderr}")
        return []
    
    python_files = []
    for line in stdout.strip().split('\n'):
        if line and line.endswith('.py') and not line.startswith('tests/') and not line.startswith('githooks/'):
            python_files.append(line)
    
    return python_files


def get_changed_lines(file_path: str) -> Set[int]:
    """Get the line numbers that are being changed in the staged file."""
    cmd = ["git", "diff", "--cached", "--unified=0", file_path]
    exit_code, stdout, stderr = run_command(cmd)
    
    if exit_code != 0:
        print(f"Error getting diff for {file_path}: {stderr}")
        return set()
    
    changed_lines = set()
    
    # Parse the unified diff format
    # @@ -old_start,old_count +new_start,new_count @@
    for line in stdout.split('\n'):
        if line.startswith('@@'):
            # Extract the new line range
            match = re.search(r'@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@', line)
            if match:
                start_line = int(match.group(1))
                count = int(match.group(2)) if match.group(2) else 1
                
                # Add all lines in this range
                for i in range(start_line, start_line + count):
                    changed_lines.add(i)
    
    return changed_lines


def run_coverage_tests() -> str:
    """Run tests with coverage and return the coverage data file path."""
    coverage_data = tempfile.mktemp(suffix='.coverage')
    
    cmd = [
        "uv", "run", "coverage", "run", 
        "--source=app,bundled_steps", 
        f"--data-file={coverage_data}",
        "-m", "pytest", "tests/"
    ]
    
    print("Running tests with coverage...")
    exit_code, stdout, stderr = run_command(cmd, capture_output=False)
    
    if exit_code != 0:
        print("Tests failed during coverage run:")
        print(stderr)
        sys.exit(1)
    
    return coverage_data


def get_missing_lines(file_path: str, coverage_data: str) -> Set[int]:
    """Get the line numbers that are not covered by tests."""
    cmd = [
        "uv", "run", "coverage", "report", 
        f"--data-file={coverage_data}", 
        "--show-missing", 
        file_path
    ]
    
    exit_code, stdout, stderr = run_command(cmd)
    
    if exit_code != 0:
        print(f"Warning: Could not get coverage for {file_path}: {stderr}")
        return set()
    
    missing_lines = set()
    
    # Parse the coverage report to find missing lines
    for line in stdout.split('\n'):
        # Look for data lines (not headers or separators)
        if (line.strip() and 
            not line.startswith('---') and 
            not line.startswith('Name') and
            not line.startswith('TOTAL') and
            '%' in line):  # Data lines have percentage
            # Extract the missing line numbers from the end of the line
            parts = line.split()
            if len(parts) >= 5:  # Should have Name, Stmts, Miss, Cover, Missing
                missing_part = parts[-1]  # Last column is Missing
                if missing_part != 'Missing':
                    # Parse comma-separated line numbers and ranges
                    for range_str in missing_part.split(','):
                        if '-' in range_str:
                            # Handle range like "1-13"
                            start, end = range_str.split('-')
                            try:
                                for i in range(int(start), int(end) + 1):
                                    missing_lines.add(i)
                            except ValueError:
                                continue
                        else:
                            # Handle single number
                            try:
                                missing_lines.add(int(range_str))
                            except ValueError:
                                continue
    
    return missing_lines


def main():
    """Main function to run the coverage check."""
    print("Running pre-commit coverage check...")
    
    # Get staged Python files
    staged_files = get_staged_python_files()
    
    if not staged_files:
        print("No Python files staged for commit. Skipping coverage check.")
        return
    
    print("Staged Python files:")
    for file in staged_files:
        print(f"  {file}")
    
    # Run coverage tests
    coverage_data = run_coverage_tests()
    
    try:
        # Analyze coverage for each staged file
        print("\nAnalyzing coverage for staged files...")
        
        uncovered_changes = 0
        total_changes = 0
        
        for file_path in staged_files:
            print(f"\nChecking coverage for: {file_path}")
            
            # Get changed lines
            changed_lines = get_changed_lines(file_path)
            
            if not changed_lines:
                print("  No line changes detected")
                continue
            
            # Get missing lines from coverage
            missing_lines = get_missing_lines(file_path, coverage_data)
            
            # Check each changed line
            for line_num in sorted(changed_lines):
                total_changes += 1
                
                if line_num in missing_lines:
                    print(f"  WARNING: Line {line_num} is not covered by tests")
                    uncovered_changes += 1
        
        # Report results
        print(f"\nCoverage check results:")
        print(f"Total changed lines: {total_changes}")
        print(f"Uncovered lines: {uncovered_changes}")
        
        if uncovered_changes > 0:
            print(f"\n\033[33mWARNING: {uncovered_changes} lines are not covered by tests.\033[0m")
            print("Consider adding tests for these changes before committing.")
            print("\nTo see detailed coverage report, run:")
            print("  uv run coverage run --source=. -m pytest tests/")
            print("  uv run coverage report --show-missing")
            print("\nYou can still commit, but it's recommended to add tests for uncovered code.")
            
            # Ask user if they want to continue
            try:
                input("Press Enter to continue with commit, or Ctrl+C to abort...")
            except KeyboardInterrupt:
                print("\nCommit aborted.")
                sys.exit(1)
        
        print("\n\033[32mPre-commit coverage check completed.\033[0m")
        
    finally:
        # Clean up
        if os.path.exists(coverage_data):
            os.unlink(coverage_data)


if __name__ == "__main__":
    main() 