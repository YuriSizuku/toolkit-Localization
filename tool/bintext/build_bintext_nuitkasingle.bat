:: build_nuitkafile scriptpath [outdir] [outpath] [iconpath] [argss]
set SCRIPTPATH=%1
set OUTDIR=%2
set OUTPATH=%3
set ICONPATH=%4
set ARGS=%5 %6 %7 %8 %9
nuitka --standalone --onefile --full-compat --show-progress %SCRIPTPATH% --output-dir=%OUTPATH% -o=%OUTPATH% --windows-icon-from-ico=%ICONPATH% --assume-yes-for-downloads %ARGS%