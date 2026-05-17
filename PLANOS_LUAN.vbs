Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
root = fso.GetParentFolderName(WScript.ScriptFullName)
WshShell.Run """" & root & "\AbrirPLANOS_LUAN.bat" & """", 0, False
