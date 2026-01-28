$reports = '.test_reports'
if (-not (Test-Path $reports)) { New-Item -ItemType Directory -Path $reports | Out-Null }
$env:COVERAGE_FILE = Join-Path $reports '.coverage'
pytest `
    --continue-on-collection-errors `
    --junitxml=$(Join-Path $reports 'results.xml') `
    --html=$(Join-Path $reports 'results.html') --self-contained-html `
    --cov=app --cov-report=html:$(Join-Path $reports 'htmlcov') --cov-report term-missing `
    tests/plan
