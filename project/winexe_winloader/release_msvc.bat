msbuild %~dp0\winloader.sln -t:winloader:rebuild -p:configuration=release -p:Platform=x86 
msbuild %~dp0\winloader.sln -t:winloader:rebuild -p:configuration=release -p:Platform=x64