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
if %errorlevel% neq 0 (
    echo [Build] pygbag failed. Aborting.
    exit /b %errorlevel%
)

echo [Build] Copying audio assets and JS audio manager for web...
if not exist build\web\assets mkdir build\web\assets
xcopy /Y assets\*.ogg build\web\assets\
if %errorlevel% neq 1 (
    echo [Build] Failed to copy OGG assets (xcopy exit code %errorlevel%). Aborting.
    exit /b 1
)
copy /Y assets\audio_manager.js build\web\audio_manager.js
if %errorlevel% neq 0 (
    echo [Build] Failed to copy audio_manager.js. Aborting.
    exit /b %errorlevel%
)

echo [Build] Injecting audio manager script tag into index.html...
powershell -NoProfile -Command "try { if (-not (Test-Path 'build\web\index.html')) { throw 'build\web\index.html not found' }; $c = Get-Content 'build\web\index.html' -Raw -ErrorAction Stop; $c = $c -replace '</head>', ('<script src=""audio_manager.js""></script>' + [char]10 + '</head>'); Set-Content 'build\web\index.html' $c -NoNewline -ErrorAction Stop } catch { [Console]::Error.WriteLine($_.Exception.Message); exit 1 }"
if %errorlevel% neq 0 (
    echo [Build] Failed to inject audio manager script tag. Aborting.
    exit /b 1
)

echo [Build] Done!
