;--------------------------------
;Header Files

!include "MUI2.nsh"
!include "Sections.nsh"
!include "LogicLib.nsh"
!include "Memento.nsh"
!include "WordFunc.nsh"

;--------------------------------
;General

  ; Name and file
  Name "Numenta Vision Toolkit"
  Caption "Numenta Vision Toolkit"
  OutFile "VisionToolkit.exe"

  ; installation folder
  ;InstallDir "$PROGRAMFILES\Numenta Vision Toolkit"

  ; Request application privileges for Windows Vista
  RequestExecutionLevel admin

  ; Compression options for best compression
  SetCompressor /FINAL /SOLID lzma
  SetCompressorDictSize 64

  ;AutoCloseWindow true

;--------------------------------
;Interface Settings

  !define MUI_ABORTWARNING

  !define MUI_HEADERIMAGE "demo_header.bmp"
  !define MUI_WELCOMEFINISHPAGE_BITMAP "demo_left.bmp"

  !define MUI_ICON "demo.ico"
  !define MUI_UNICON "demo.ico"

;--------------------------------
;Pages
  !define MUI_WELCOMEPAGE_TITLE "Welcome to the Numenta Vision Toolkit Setup"
  !define MUI_WELCOMEPAGE_TEXT "This wizard will guide you through the installation of the vision toolkit. It is recommended to uninstall previous versions of the application and make sure it is not running. $\r$\n$\r$\nThe Numenta Vision Toolkit is a standalone application that allows you train, test and share your own HTM vision networks. $\r$\n$\r$\n$_CLICK"

  !insertmacro MUI_PAGE_WELCOME

  ;
  ;!define MUI_PAGE_LICENSE_TEXT_TOP " " DOES NOT WORK
  !define MUI_PAGE_CUSTOMFUNCTION_SHOW "ShowLicensePage"
  !insertmacro MUI_PAGE_LICENSE "LICENSE"
  !insertmacro MUI_PAGE_DIRECTORY
  !insertmacro MUI_PAGE_INSTFILES

  !define MUI_FINISHPAGE_LINK "Visit the Numenta web site for the latest news."
  !define MUI_FINISHPAGE_LINK_LOCATION "http://www.numenta.com"

  !define MUI_FINISHPAGE_RUN
  !define MUI_FINISHPAGE_RUN_TEXT "Run the Vision Toolkit"
  !define MUI_FINISHPAGE_RUN_FUNCTION "RunVisionToolkit"

  !define MUI_FINISHPAGE_NOREBOOTSUPPORT

  !insertmacro MUI_PAGE_FINISH

  !insertmacro MUI_UNPAGE_CONFIRM
  !insertmacro MUI_UNPAGE_INSTFILES

;--------------------------------
Function ShowLicensePage
  ;Get conrol handles
  FindWindow $mui.LicensePage "#32770" "" $HWNDPARENT
  GetDlgItem $mui.LicensePage.TopText $mui.LicensePage 1040
  GetDlgItem $mui.LicensePage.Text $mui.LicensePage 1006
  GetDlgItem $mui.LicensePage.LicenseText $mui.LicensePage 1000

  ;Top text
  SendMessage $mui.LicensePage.TopText ${WM_SETTEXT} 0 "STR: "

  !insertmacro MUI_PAGE_FUNCTION_CUSTOM SHOW
FunctionEnd
;--------------------------------
Function RunVisionToolkit
  ExecShell "" "$DESKTOP\Numenta Vision Toolkit.lnk"
FunctionEnd

;--------------------------------

;--------------------------------
;Languages

!insertmacro MUI_LANGUAGE "English"


;--------------------------------
; Installer Functions
Function .onInit
; Must set $INSTDIR here to avoid adding 'Numenta\Vision Toolkit'
; to the end of the path when user selects a new directory using the
; 'Browse' button.
  System::Call 'kernel32::CreateMutexA(i 0, i 0, t "Numenta.Vision.Toolkit.Installer") ?e'
  Pop $R0
  StrCmp $R0 0 +3
    MessageBox MB_OK "The installer is already running."
    Abort

  StrCpy $INSTDIR "$PROGRAMFILES\Numenta\Vision Toolkit"
FunctionEnd


;--------------------------------
; Installer section
Section ""

  ; Set output path to the installation directory.
  SetOutPath "$INSTDIR"

  ; put here requiered files
  File /r DLLs
  File /r data
  File /r install
  File /r networks
  File /r projects
  ; File /r VisionToolkitHelp
  File /r Lib
  File "*.*"
  File VisionToolkitLauncher.pyw

  Var /GLOBAL NAME
  StrCpy $NAME "Numenta Vision Toolkit"

  Var /GLOBAL UNINSTALL_PATH
  StrCpy $UNINSTALL_PATH "Software\Microsoft\Windows\CurrentVersion\Uninstall\$NAME"

  WriteUninstaller $INSTDIR\uninstall.exe
  WriteRegStr   HKCU "$UNINSTALL_PATH" "DisplayName" "$NAME"
  WriteRegStr   HKCU "$UNINSTALL_PATH" "UninstallString" '"$INSTDIR\uninstall.exe"'
  WriteRegDWORD HKCU "$UNINSTALL_PATH" "NoModify" "1"
  WriteRegDWORD HKCU "$UNINSTALL_PATH" "NoRepair" "1"

  CreateShortCut "$DESKTOP\$NAME.lnk" "$INSTDIR\pythonw.exe" \
  '"$INSTDIR\VisionToolkitLauncher.pyw"' "$INSTDIR\demo.ico" 0 SW_SHOWNORMAL \
  ALT|CONTROL|SHIFT|F5 "Runs the $NAME"

  CreateShortCut "$SMPROGRAMS\$NAME.lnk" "$INSTDIR\pythonw.exe" \
  '"$INSTDIR\VisionToolkitLauncher.pyw"' "$INSTDIR\demo.ico" 0 SW_SHOWNORMAL \
  ALT|CONTROL|SHIFT|F5 "Runs the $NAME"

;  CreateShortCut "$DESKTOP\$NAME.lnk" "$INSTDIR\pythonw.exe" \
;  '"$INSTDIR\VisionToolkitLauncher.pyw" "--log"' "$INSTDIR\demo.ico" 0 SW_SHOWNORMAL \
;  ALT|CONTROL|SHIFT|F5 "Runs the $NAME"
;
;  CreateShortCut "$SMPROGRAMS\$NAME.lnk" "$INSTDIR\pythonw.exe" \
;  '"$INSTDIR\VisionToolkitLauncher.pyw" "--log"' "$INSTDIR\demo.ico" 0 SW_SHOWNORMAL \
;  ALT|CONTROL|SHIFT|F5 "Runs the $NAME"
SectionEnd

;--------------------------------
; Uninstaller section
Section "un.Uninstall"
  ;SetAutoClose true
  Delete "$DESKTOP\Numenta Vision Toolkit.lnk"
  Delete "$SMPROGRAMS\Numenta Vision Toolkit.lnk"
  DeleteRegKey HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\Numenta Vision Toolkit"

  RMDir /r $INSTDIR
SectionEnd
