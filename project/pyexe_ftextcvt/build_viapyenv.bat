::@echo off
:: use as build_viapyenv.bat path/to/xxx.bat

call %~dp0_env.bat
if not exist "%PYENV_DIR%" mkdir "%PYENV_DIR%"

pushd "%PYENV_DIR%"
python -m venv %PYENV_NAME%
cd %PYENV_NAME%\Scripts
python -m pip install python-docx
call %1
popd 