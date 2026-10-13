"""
Run verify_resilience.py and print only the result lines
to avoid terminal truncation.
"""
import subprocess, sys

result = subprocess.run(
    [sys.executable, 'verify_resilience.py'],
    capture_output=True, text=True, cwd='.'
)

lines = result.stdout.split('\n')
for line in lines:
    if line.strip():
        # Print short enough lines for the terminal
        print(line[:120])
