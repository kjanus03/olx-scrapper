Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

' Get the folder where this VBS file lives
currentFolder = fso.GetParentFolderName(WScript.ScriptFullName)
WshShell.CurrentDirectory = currentFolder

' Run the virtual environment's invisible Python (pythonw.exe) directly
command = chr(34) & "venv\Scripts\pythonw.exe" & chr(34) & " -m src.main"
WshShell.Run command, 0, False

Set WshShell = Nothing
Set fso = Nothing