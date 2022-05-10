msbuild %~dp0\libwinhook.sln -t:dllloader:rebuild -p:configuration=release -p:PlatformTarget=x86 
msbuild %~dp0\libwinhook.sln -t:dllloader:rebuild -p:configuration=release -p:PlatformTarget=x64