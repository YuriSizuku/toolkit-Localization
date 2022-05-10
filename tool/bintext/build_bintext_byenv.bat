::@echo off
if not exist "%~dp0\..\..\env" (
    mkdir "%~dp0\..\..\env"
)
pushd "%~dp0\..\..\env"
python -m venv python_base
cd .\python_base\Scripts
python -m pip install pyinstaller
%1
popd 