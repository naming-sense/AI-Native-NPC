python "$PSScriptRoot/doc_harness.py" validate --strict
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
