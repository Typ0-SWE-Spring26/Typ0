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

echo [Build] Copying audio assets for JS playback...
if not exist build\web\assets mkdir build\web\assets
xcopy /Y assets\*.ogg build\web\assets\

echo [Build] Done!
