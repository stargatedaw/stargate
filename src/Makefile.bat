pyinstaller -F ^
  --add-data "meta.json;." ^
  --add-data "files;." ^
  --add-data "scripts;." ^
  scripts\stargate

