# Portsy - Port Scanner & Route Analyzer

```
 ██▓███   ▒█████   ██▀███  ▄▄▄█████▓  ██████▓██   ██▓
▓██░  ██▒▒██▒  ██▒▓██ ▒ ██▒▓  ██▒ ▓▒▒██    ▒ ▒██  ██▒
▓██░ ██▓▒▒██░  ██▒▓██ ░▄█ ▒▒ ▓██░ ▒░░ ▓██▄    ▒██ ██░
▒██▄█▓▒ ▒▒██   ██░▒██▀▀█▄  ░ ▓██▓ ░   ▒   ██▒ ░ ▐██▓░
▒██▒ ░  ░░ ████▓▒░░██▓ ▒██▒  ▒██▒ ░ ▒██████▒▒ ░ ██▒▓░
▒▓▒░ ░  ░░ ▒░▒░▒░ ░ ▒▓ ░▒▓░  ▒ ░░   ▒ ▒▓▒ ▒ ░  ██▒▒▒ 
░▒ ░       ░ ▒ ▒░   ░▒ ░ ▒░    ░    ░ ░▒  ░ ░▓██ ░▒░ 
░░       ░ ░ ░ ▒    ░░   ░   ░      ░  ░  ░  ▒ ▒ ░░  
             ░ ░     ░                    ░  ░ ░      
                                             ░ ░      
```

A highly optimized, super simple command-line and GUI tool that locates what's running on what ports, discovers exposed routes, and identifies potential duplicate dev servers.

<p align="center">
  <img src="assets/icon.svg" alt="Portsy Logo" width="64" height="64">
</p>

## Features

- 🚀 **Lightning Fast** - Multi-threaded port scanning (100 concurrent connections)
- 🔍 **Smart Detection** - Identifies Python/Node.js frameworks (Flask, FastAPI, Express, React, etc.)
- 🌐 **Deep Route Discovery** - 70+ framework-specific endpoints 
- 🎯 **Scan Presets** - Quick, dev, web, full, and services modes
- 📊 **Duplicate Detection** - Finds potential duplicate services
- 💻 **Dual Interface** - Both CLI and GUI available
- 📄 **Export Support** - JSON export for integration

## Installation

### 📦 **Easy Installers (Click & Install)**

**Windows:** 
- [📥 Download portsy-windows.zip](https://github.com/CrazyDubya/portsy/releases/latest/download/portsy-windows.zip)
- Extract and run `install_windows.bat`

**macOS:** 
- [📥 Download portsy-macos.zip](https://github.com/CrazyDubya/portsy/releases/latest/download/portsy-macos.zip)  
- Extract and run `install_unix.sh`

**Linux:**
- [📥 Download portsy-linux.zip](https://github.com/CrazyDubya/portsy/releases/latest/download/portsy-linux.zip)
- Extract and run `install_unix.sh`

### 🛠 **From Source**
```bash
git clone https://github.com/CrazyDubya/portsy.git
cd portsy
pip install -e .
```

### 🚀 **One-line Install**
```bash
pip install psutil requests && curl -o portsy.py https://raw.githubusercontent.com/CrazyDubya/portsy/master/portsy.py && chmod +x portsy.py
```

## Usage

### Command Line Examples

```bash
# Quick scan (default dev ports 3000-9000)
portsy

# Full system scan (1-65535 ports)
portsy --preset full

# Development server scan with deep route discovery  
portsy --preset dev --comprehensive-routes

# Scan specific port range
portsy -s 8000 -e 8100

# List all available scan presets
portsy --list-presets

# Export results to JSON
portsy --json results.json

# Launch GUI (if tkinter available)
portsy --gui
```

### Scan Presets

- **`quick`** - Common dev ports (3000-9000, 8000-8100)
- **`dev`** - Extended dev ranges (3000-3100, 4000-4100, 5000-5100, 8000-8100, 9000-9100, 8080-8090)
- **`web`** - Web server ports (80, 443, 8080, 8443, plus dev ranges)
- **`full`** - Complete port scan (1-65535) ⚠️ Slow
- **`services`** - Database & service ports (MySQL, PostgreSQL, Redis, MongoDB, etc.)

### Framework Detection

Portsy automatically detects and provides enhanced analysis for:

**Python Frameworks:**
- Flask, Django, FastAPI, Streamlit, Gradio, Jupyter

**Node.js Frameworks:**  
- Express, Next.js, React Dev Server, Vue Dev Server

**Other Services:**
- Ollama, Spring Boot, Nginx, Apache, and more

## 🎬 Demo Output

```bash
$ portsy --preset dev --comprehensive-routes

🔍 Running dev scan: Extended dev server ranges
🌐 Using comprehensive route discovery (all frameworks)
✅ Found 10 open ports
🌐 Discovering HTTP routes (comprehensive mode)...

📋 Running Services:
────────────────────────────────────────────────────────────────────────────────────
Port     PID      Process         Framework       Routes                              Response
────────────────────────────────────────────────────────────────────────────────────
5000     586      ControlCenter   Unknown                                             4.5ms
8000     97793    Python          Flask           /assets, /                          2.6ms
8001     4858     Python          FastAPI         /api/v1/health, /docs               2.5ms
8003     71448    Python          Django          /admin, /                           5.4ms
8005     2740     Python          FastAPI         /api/v1/health, /redoc              2.7ms
8080     14722    node            React Dev       /webpack-dev-server, /              3.2ms
9023     55001    node            Express         /api, /                             2.8ms
9922     52709    Python          FastAPI         /docs, /redoc, /openapi.json        4.5ms
11434    1781     ollama          Ollama          /api/tags, /api/version             3.6ms

🐍 Python Services Analysis:
  Port 8001 (FastAPI)
    API Endpoints: /api/v1/health, /docs, /redoc
    PID: 4858, Response: 2.5ms
    
  Port 8005 (FastAPI)  
    API Endpoints: /api/v1/health, /redoc
    PID: 2740, Response: 2.7ms
    
  Port 9922 (FastAPI)
    API Endpoints: /docs, /redoc, /openapi.json
    PID: 52709, Response: 4.5ms

🟢 Node.js Services Analysis:
  Port 8080 (React Dev Server)
    Dev Server: /webpack-dev-server
    API Endpoints: /
    PID: 14722, Response: 3.2ms

⚠️ Potential Duplicate Services:
🔄 process_Python_1:
   - Port 8001: Python (PID: 4858) - FastAPI
   - Port 8005: Python (PID: 2740) - FastAPI  
   - Port 9922: Python (PID: 52709) - FastAPI

✅ Scan complete! Found 3 FastAPI servers and 1 React dev server.
```

### 🎯 **Key Features Demonstrated**

✅ **Multi-framework Detection** - Identified Flask, FastAPI, Django, React, Express, and Ollama  
✅ **Route Discovery** - Found API endpoints, documentation routes, and dev server paths  
✅ **Duplicate Detection** - Spotted 3 similar FastAPI services  
✅ **Performance Metrics** - Response times ranging from 2.5ms to 5.4ms  
✅ **Detailed Analysis** - Separate Python and Node.js service breakdowns

## Requirements

- Python 3.8+
- psutil
- requests
- tkinter (optional, for GUI)

## License

MIT License