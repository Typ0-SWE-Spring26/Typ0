# Typ0

A pygame project with pygbag web support.

## Setup

### 1. Create a virtual environment
```powershell
python -m venv venv
```

### 2. Activate the virtual environment
```powershell
.\venv\Scripts\Activate.ps1
```

If you get an execution policy error, run:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### 3. Install dependencies
```powershell
pip install -r requirements.txt
```

### 4. Run the game
```powershell
python main.py
```

### 5. Build for web

#### Windows:
```powershell
build.bat
```

#### Mac or Linux:
```bash
pygbag .
```

### 6. Deactivate virtual environment when done
```powershell
deactivate
```