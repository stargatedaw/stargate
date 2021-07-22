pyinstaller -F ^
  --add-data "meta.json;." ^
  --add-data "files;." ^
  --add-data "scripts;." ^
  --add-binary "engine/stargate-engine.exe;scripts/stargate-engine.exe" ^
  --add-binary "scripts/libportaudio-2.dll;scripts/libportaudio-2.dll" ^
  --add-binary "scripts/libportmidi.dll;scripts/libportmidi.dll" ^
  --add-binary "scripts/rubberband.exe;scripts/rubberband.exe" ^
  scripts\stargate

