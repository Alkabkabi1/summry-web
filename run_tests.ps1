Set-Location $PSScriptRoot
pip install -r requirements.txt
python -m pytest -v @args
