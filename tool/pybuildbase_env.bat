:: by_pybase_env envdir runbatpath args
@echo off
set ENVDIR=%1
set RUNBATPATH=%2
SET ARGS=%3 %4 %5 %6 %7 %8 %9
if not exist %ENVDIR% (
    mkdir %ENVDIR%
	pushd %ENVDIR%
	python -m venv %ENVDIR%
    cd /d %ENVDIR%\Scripts
    python -m pip install pyinstaller
	python -m pip install nuitka
	popd 
)
pushd %ENVDIR%
call %RUNBATPATH% %ARGS%
popd 