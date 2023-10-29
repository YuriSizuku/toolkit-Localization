msbuild %~dp0\libwinpe.sln -t:libwinpe:rebuild -p:configuration=release -p:Platform=x86 
msbuild %~dp0\libwinpe.sln -t:libwinpe:rebuild -p:configuration=release -p:Platform=x64