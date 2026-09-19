' Launches CameraX_Watchdog.bat completely hidden (no console window), then
' exits immediately - the watchdog loop keeps running in the background.
' Put this .vbs (not the .bat) in the Windows Startup folder.
Dim shell, fso, scriptDir
Set shell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
scriptDir = fso.GetParentFolderName(WScript.ScriptFullName)
shell.Run """" & scriptDir & "\CameraX_Watchdog.bat""", 0, False
