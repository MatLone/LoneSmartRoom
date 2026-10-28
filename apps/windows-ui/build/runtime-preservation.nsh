; Included only at build time. Fixed helper, no shell string or arbitrary command.
!include LogicLib.nsh
!include x64.nsh
!include "${BUILD_RESOURCES_DIR}\package-remove.nsh"
!ifndef BUILD_UNINSTALLER
Var loneRuntimeJournal
Var loneRuntimePowerShell
Function lonePreserveBeforeInstall
  Call instFilesPre
  ; NSIS is x86, the application/helper contract is x64. Select the native host
  ; explicitly rather than letting System32 silently redirect to SysWOW64.
  ; No execution-policy override, shell setting, elevation or global redirector change.
  ${If} ${RunningX64}
    StrCpy $loneRuntimePowerShell "$WINDIR\Sysnative\WindowsPowerShell\v1.0\powershell.exe"
  ${Else}
    MessageBox MB_OK|MB_ICONSTOP "The x64 runtime preservation helper requires 64-bit Windows."
    SetErrorLevel 2
    Quit
  ${EndIf}
  InitPluginsDir
  File /oname=$PLUGINSDIR\preserve-runtime.ps1 "${BUILD_RESOURCES_DIR}\preserve-runtime.ps1"
  File /oname=$PLUGINSDIR\package-files.txt "${BUILD_RESOURCES_DIR}\package-files.txt"
  System::Call 'kernel32::GetTickCount() i.r0'
  StrCpy $loneRuntimeJournal "$LOCALAPPDATA\LoneSmartRoom-RuntimePreservation\$0"
  nsExec::ExecToStack '"$loneRuntimePowerShell" -NoProfile -NonInteractive -File "$PLUGINSDIR\preserve-runtime.ps1" -Mode prepare -Source "$INSTDIR" -Journal "$loneRuntimeJournal" -Known "$PLUGINSDIR\package-files.txt"'
  Pop $0
  Pop $1
  ${If} $0 != 0
    MessageBox MB_OK|MB_ICONSTOP "Runtime preservation failed. Installation stopped before removing the previous version."
    SetErrorLevel 2
    Quit
  ${EndIf}
FunctionEnd
!macro customPageAfterChangeDir
  !undef MUI_PAGE_CUSTOMFUNCTION_PRE
  !define MUI_PAGE_CUSTOMFUNCTION_PRE lonePreserveBeforeInstall
!macroend
!macro customInstall
  nsExec::ExecToStack '"$loneRuntimePowerShell" -NoProfile -NonInteractive -File "$PLUGINSDIR\preserve-runtime.ps1" -Mode restore -Source "$INSTDIR" -Journal "$loneRuntimeJournal"'
  Pop $0
  Pop $1
  ${If} $0 != 0
    MessageBox MB_OK|MB_ICONSTOP "Application files installed, but runtime restoration failed. Do not open the app. Recovery copy: $loneRuntimeJournal"
    SetErrorLevel 2
    Quit
  ${EndIf}
!macroend
!endif
