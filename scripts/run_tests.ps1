# PowerShell script to run feature tests
Set-Location D:\code-agent
.\.venv\Scripts\Activate.ps1
python scripts\test_features.py
