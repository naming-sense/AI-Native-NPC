@echo off
python "%~dp0doc_harness.py" validate --strict
exit /b %ERRORLEVEL%
