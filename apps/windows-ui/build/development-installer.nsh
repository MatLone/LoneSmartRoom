; Development distribution: no silent/automatic replacement or post-install launch.
; No credentials, firewall, services, Run keys or scheduled tasks.
!macro customInstallMode
  StrCpy $isForceCurrentInstall "1"
!macroend

!macro loneCheckPrevious ROOT_KEY VIEW
  SetRegView ${VIEW}
  ReadRegStr $R0 ${ROOT_KEY} "${UNINSTALL_REGISTRY_KEY}" "UninstallString"
  ${If} $R0 != ""
    StrCpy $R1 "1"
  ${EndIf}
!macroend

!macro customInit
  IfSilent loneSilentRejected loneInteractive
  loneSilentRejected:
    SetErrorLevel 2
    Quit
  loneInteractive:
  ${If} ${isForAllUsers}
    MessageBox MB_OK|MB_ICONSTOP "This development build supports the current Windows user only."
    SetErrorLevel 2
    Quit
  ${EndIf}
  StrCpy $R1 "0"
  !insertmacro loneCheckPrevious HKLM 64
  !insertmacro loneCheckPrevious HKLM 32
  ${If} $R1 == "1"
    MessageBox MB_OK|MB_ICONSTOP "A machine-wide installation exists. Stop and review its backup and migration plan before using this per-user development installer."
    SetErrorLevel 2
    Quit
  ${EndIf}
  !insertmacro loneCheckPrevious HKCU 64
  !insertmacro loneCheckPrevious HKCU 32
  SetRegView 64
  ${If} $R1 == "1"
    MessageBox MB_YESNO|MB_DEFBUTTON2|MB_ICONEXCLAMATION "An existing Lone Smart Room installation was detected. Update only after the approved backup procedure and explicit authorization. Replace its application files now? User data is not intentionally removed." IDYES loneUpdateApproved
    SetErrorLevel 2
    Quit
    loneUpdateApproved:
  ${EndIf}
!macroend

!include "${BUILD_RESOURCES_DIR}\runtime-preservation.nsh"
