msbuild %~dp0\libwinhook.sln -t:libwinhook:rebuild -p:configuration=release -p:Platform=x86 
msbuild %~dp0\libwinhook.sln -t:libwinhook:rebuild -p:configuration=release -p:Platform=x64