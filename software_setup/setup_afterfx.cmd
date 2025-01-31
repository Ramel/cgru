rem Source general for all soft directives:
call %CGRU_LOCATION%\software_setup\setup__all.cmd


set "ADOBE_LOCATION=C:\Program Files\Adobe"

set "AE_SEARCH=%ADOBE_LOCATION%\Adobe After Effects"
For /F "Tokens=*" %%I in ('dir /b "%AE_SEARCH%*"') Do set "AE_LOCATION=%%I"

set "AE_LOCATION=%ADOBE_LOCATION%\%AE_LOCATION%\Support Files"

set "APP_DIR=%AE_LOCATION%"
set "APP_EXE=%AE_LOCATION%\aerender.exe"

rem Define location:
set "locate_file=%CGRU_LOCATION%\software_setup\locate_afterfx.cmd"
if exist %locate_file% call %locate_file%

set "AE_LOCATION=%APP_DIR%"
