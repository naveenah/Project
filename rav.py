#!/usr/bin/env python3
"""
RAV - Requirements Automation & Virtualization
A simple task runner for Python dependency management and virtual environment setup.

Usage:
    python rav.py <task_name>
    python rav.py --list
    python rav.py --help

Examples:
    python rav.py compile
    python rav.py install-dev
    python rav.py setup-dev
    python rav.py bootstrap-dev
"""

import sys
import yaml
import subprocess
import os
from pathlib import Path


class RAV:
    def __init__(self, config_file="rav.yaml"):
        self.config_file = Path(config_file)
        if not self.config_file.exists():
            print(f"Error: Configuration file '{config_file}' not found.")
            sys.exit(1)
        
        with open(self.config_file, 'r') as f:
            self.config = yaml.safe_load(f)
        
        self.tasks = self.config.get('tasks', {})
        self.venv = self.config.get('venv', {})
        self.requirements = self.config.get('requirements', {})
        self.executed_tasks = set()

    def _replace_placeholders(self, text):
        """Replace placeholders in text with actual values from config."""
        replacements = {
            '{venv.name}': self.venv.get('name', 'venv'),
            '{venv.python}': self.venv.get('python', 'python3'),
            '{requirements.directory}': self.requirements.get('directory', 'src/requirements'),
            '{requirements.prod.input}': self.requirements.get('prod', {}).get('input', 'requirements-prod.in'),
            '{requirements.prod.output}': self.requirements.get('prod', {}).get('output', 'requirements-prod.txt'),
            '{requirements.dev.input}': self.requirements.get('dev', {}).get('input', 'requirements-dev.in'),
            '{requirements.dev.output}': self.requirements.get('dev', {}).get('output', 'requirements-dev.txt'),
        }
        
        for placeholder, value in replacements.items():
            text = text.replace(placeholder, value)
        
        return text

    def _run_command(self, command, description=None):
        """Execute a shell command."""
        command = self._replace_placeholders(command)
        
        if description:
            print(f"\n🔹 {description}")
        print(f"   $ {command}")
        
        try:
            result = subprocess.run(
                command,
                shell=True,
                check=True,
                text=True,
                capture_output=False
            )
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Command failed with exit code {e.returncode}")
            return False

    def _run_task(self, task_name, indent=0):
        """Execute a task by name."""
        if task_name in self.executed_tasks:
            return True
        
        if task_name not in self.tasks:
            print(f"❌ Task '{task_name}' not found.")
            return False
        
        task = self.tasks[task_name]
        prefix = "  " * indent
        
        print(f"\n{prefix}{'='*60}")
        print(f"{prefix}📦 Running task: {task_name}")
        if 'description' in task:
            print(f"{prefix}   {task['description']}")
        print(f"{prefix}{'='*60}")
        
        steps = task.get('steps', [])
        for step in steps:
            if 'command' in step:
                success = self._run_command(
                    step['command'],
                    step.get('description')
                )
                if not success:
                    return False
            elif 'task' in step:
                # Run nested task
                success = self._run_task(step['task'], indent + 1)
                if not success:
                    return False
        
        self.executed_tasks.add(task_name)
        print(f"\n{prefix}✅ Task '{task_name}' completed successfully!")
        return True

    def list_tasks(self):
        """List all available tasks."""
        print("\n📋 Available tasks:\n")
        for task_name, task_config in self.tasks.items():
            description = task_config.get('description', 'No description')
            print(f"  • {task_name:<20} - {description}")
        print()

    def run(self, task_name):
        """Run a specific task."""
        success = self._run_task(task_name)
        if success:
            print("\n🎉 All tasks completed successfully!")
        else:
            print("\n❌ Task execution failed.")
            sys.exit(1)


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    
    arg = sys.argv[1]
    
    if arg in ['--help', '-h', 'help']:
        print(__doc__)
        sys.exit(0)
    
    rav = RAV()
    
    if arg in ['--list', '-l', 'list']:
        rav.list_tasks()
        sys.exit(0)
    
    task_name = arg
    rav.run(task_name)


if __name__ == "__main__":
    main()
