nuitka ^
	--standalone ^
	--windows-disable-console  ^
	--include-module=sgui ^
	--include-module=sglib ^
	--include-qt-plugins=platform,sensible ^
	--enable-plugin=pyqt6 ^
	scripts\stargate

copy /Y meta.json stargate.dist
copy /Y COMMIT stargate.dist
xcopy /Y /e /k /h /i files dist\stargate
mkdir stargate.dist\engine
copy engine\*.dll stargate.dist\engine
copy engine\*.exe stargate.dist\engine

if not exist dist mkdir dist
move stargate.dist dist
cd dist
rename stargate.dist stargate
cd ..

