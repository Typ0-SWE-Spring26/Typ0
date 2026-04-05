@echo off

echo [Build] Compiling TypeScript audio manager...
cd web
npm run build
if %errorlevel% neq 0 (
    echo [Build] TypeScript compile failed. Aborting.
    cd ..
    exit /b 1
)
cd ..

echo [Build] Running pygbag...
pygbag --ume_block=0 .

echo [Build] Copying audio assets and JS audio manager for web...
if not exist build\web\assets mkdir build\web\assets
xcopy /Y assets\*.ogg build\web\assets\
copy /Y assets\audio_manager.js build\web\audio_manager.js

echo [Build] Injecting audio manager script tag into index.html...
powershell -Command "(Get-Content build\web\index.html -Raw) -replace '</head>', '<script src=""audio_manager.js""></script>`n</head>' | Set-Content build\web\index.html -NoNewline"

echo [Build] Done!
