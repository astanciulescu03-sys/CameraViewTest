@echo off
rem Keeps CameraX running: relaunches it immediately whenever it exits,
rem whether that's a crash, a freeze that got killed, or a normal close.
rem Must live in the same folder as CameraX.exe.
title CameraX Watchdog

:loop
start "" /wait "%~dp0CameraX.exe"
timeout /t 5 /nobreak >nul
goto loop
