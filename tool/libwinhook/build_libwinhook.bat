msbuild %~dp0\libwinhook.sln -t:dllloader:rebuild -p:configuration=release -p:Platform=x86 
msbuild %~dp0\libwinhook.sln -t:dllloader:rebuild -p:configuration=release -p:Platform=x64