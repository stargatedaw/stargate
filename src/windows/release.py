# Run this script from Windows, not MSYS2

from glob import iglob
import json
import os
import shutil
import subprocess
import sys

CWD = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        '..',
    ),
)
os.chdir(CWD)

with open("meta.json") as f:
    meta = json.load(f)
MAJOR_VERSION = meta['version']['major']
MINOR_VERSION = meta['version']['minor']

if os.path.isdir('dist/stargate'):
    shutil.rmtree('dist/stargate')

#print("Running Pyinstaller")
#subprocess.check_call(["pyinstaller", "pyinstaller-windows-onedir.spec"])

print("Running Nuitka")
subprocess.check_call([
    sys.executable,
    '-m', 'nuitka',
	'--standalone',
	'--windows-disable-console',
	'--include-module=sgui',
	'--include-module=sglib',
	'--include-qt-plugins=platform,sensible',
	'--enable-plugin=pyqt6',
	'scripts\\stargate',
])

shutil.copy('meta.json', 'stargate.dist')
shutil.copy('COMMIT', 'stargate.dist')
shutil.copytree('files', 'stargate.dist/files')
os.makedirs('stargate.dist/engine')
for path in iglob('engine/*.dll'):
    shutil.copy2(path, 'stargate.dist/engine')
for path in iglob('engine/*.exe'):
    shutil.copy2(path, 'stargate.dist/engine')
os.makedirs('dist', exist_ok=True)
if os.path.exists('dist/stargate'):
    shutil.rmtree('dist/stargate')
shutil.move('stargate.dist', 'dist/stargate')

TEMPLATE = r"""
!define PRODUCT_NAME "stargate"
!define PRODUCT_VERSION "{MAJOR_VERSION_NUM}.0"
!define PRODUCT_PUBLISHER "stargatedaw"

;Require admin rights on NT6+ (When UAC is turned on)
RequestExecutionLevel admin

SetCompressor /SOLID lzma

Name "Stargate DAW {MINOR_VERSION}"
OutFile "dist\StargateDAW-{MINOR_VERSION}-win64-installer.exe"
InstallDir "$PROGRAMFILES64\stargatedaw@github\Stargate"

;--------------------------------
;Interface Settings
  !define MUI_ABORTWARNING
  !define MUI_LICENSEPAGE_CHECKBOX
  !define MUI_FINISHPAGE_RUN "$INSTDIR\program\{MAJOR_VERSION}.exe"
  !define MUI_STARTMENUPAGE_DEFAULTFOLDER "Stargate DAW"

!include MUI2.nsh
!include WinVer.nsh
!include x64.nsh

;--------------------------------
;Modern UI Configuration
;Installer pages
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "windows\gpl-3.0.txt"

!insertmacro MUI_PAGE_COMPONENTS
!insertmacro MUI_PAGE_DIRECTORY

!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

;Uninstaller pages
!insertmacro MUI_UNPAGE_WELCOME
!insertmacro MUI_UNPAGE_CONFIRM
;!insertmacro MUI_UNPAGE_LICENSE textfile
;!insertmacro MUI_UNPAGE_COMPONENTS
!insertmacro MUI_UNPAGE_DIRECTORY
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_UNPAGE_FINISH

;--------------------------------
;Languages
  !insertmacro MUI_LANGUAGE "English"

Function .onInit
  ${{IfNot}} ${{AtLeastWin10}}
    MessageBox MB_OK "Windows 10 or later required, 64 bit only"
    Quit
  ${{EndIf}}
  ${{IfNot}} ${{RunningX64}}
    MessageBox MB_OK "64 bit Windows 10 or later required, 32 bit is not supported"
    Quit
  ${{EndIf}}
FunctionEnd

;Section
;    UserInfo::getAccountType
;    Pop $0
;
;    # compare the result with the string "Admin" to see if the user is admin.
;    # If match, jump 3 lines down.
;    StrCmp $0 "Admin" +3
;
;    # if there is not a match, print message and return
;    MessageBox MB_OK "not admin: $0"
;    Return
;SectionEnd

Section "Base Install" SEC01
    SectionIn RO
    SetOutPath $INSTDIR
    writeUninstaller "$INSTDIR\uninstall.exe"

    ; Clean up the old legacy file structure
    ; TODO: Remove this in mid 2023
    RMDir /r "$PROGRAMFILES64\stargateaudio@github\Stargate\program"
    Delete "$PROGRAMFILES64\stargateaudio@github\Stargate\uninstall.exe"
    ; Only if empty
    RMDir "$PROGRAMFILES64\stargateaudio@github\Stargate"
    RMDir "$PROGRAMFILES64\stargateaudio@github"

    ; Delete the old program
    RMDir /r $INSTDIR\program
    ; Install the program
    CreateDirectory $INSTDIR\program
    SetOutPath $INSTDIR\program
    File /r "dist\stargate\"
    File "files\share\pixmaps\{MAJOR_VERSION}.ico"
    ; Add to the "Add or remove programs" dialog
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\StargateDAW" \
                "DisplayName" "Stargate DAW"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\StargateDAW" \
                "DisplayIcon" "$\"$INSTDIR\program\files\share\pixmaps\stargate.ico$\""
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\StargateDAW" \
                "UninstallString" "$\"$INSTDIR\uninstall.exe$\""
SectionEnd

Section "Start Menu Shortcut" SEC02
    createShortCut \
      "$SMPROGRAMS\Stargate DAW.lnk" \
      "$INSTDIR\program\{MAJOR_VERSION}.exe" \
      "" \
      "$INSTDIR\program\{MAJOR_VERSION}.ico"
SectionEnd

Section /o "Portable Flash Drive Install" SEC03
    SetOutPath $INSTDIR
    ; Create the shortcut to the executable
    File windows\LaunchStargate.cmd
    SetOutPath $INSTDIR\program
    ; The exe looks for this empty file to choose the Stargate home folder
    FileOpen $9 ..\_stargate_home w
    FileWrite $9 "This file tells Stargate it is a portable install."
    FileClose $9
SectionEnd

LangString DESC_SEC03 ${{LANG_ENGLISH}} "Store settings and projects in the same folder as the executable.  Only use this if you are installing to a flash drive, and you must change the install folder to the flash drive in the next step."

!insertmacro MUI_FUNCTION_DESCRIPTION_BEGIN
!insertmacro MUI_DESCRIPTION_TEXT ${{SEC03}} $(DESC_SEC03)
!insertmacro MUI_FUNCTION_DESCRIPTION_END

Section "uninstall"
    ; We do not delete settings, projects or any other files the user may have
    ; stored next to the application, only the application itself
    RMDir /r $INSTDIR\program
    Delete "$SMPROGRAMS\Stargate DAW.lnk"
    DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\StargateDAW"
SectionEnd
"""

NSIS = r"C:\Program Files (x86)\NSIS\Bin\makensis.exe"

template = TEMPLATE.format(
	MINOR_VERSION=MINOR_VERSION,
	MAJOR_VERSION=MAJOR_VERSION,
	MAJOR_VERSION_NUM=MAJOR_VERSION[-1],
)
template_name = "{0}.nsi".format(MAJOR_VERSION)
with open(template_name, "w") as f:
	f.write(template)
print("Running NSIS")
subprocess.check_call([NSIS, template_name])

