' Script VBS para iniciar OBPC sem mostrar console
Set objShell = CreateObject("WScript.Shell")
Set objFSO = CreateObject("Scripting.FileSystemObject")

' Diretório atual
strCurrentDir = objFSO.GetParentFolderName(WScript.ScriptFullName)

' Comando para executar
strCommand = "python """ & strCurrentDir & "\iniciar_obpc_automatico.py"""

' Executar sem mostrar janela (WindowStyle = 0)
objShell.Run strCommand, 0, False