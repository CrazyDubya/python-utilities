# Portsy Demo Output


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

Port Scanner & Route Analyzer v1.0.0
High-performance development server discovery


## Sample Scan Results

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

## Key Features Demonstrated

✅ **Multi-framework Detection** - Identified Flask, FastAPI, Django, React, Express, and Ollama  
✅ **Route Discovery** - Found API endpoints, documentation routes, and dev server paths  
✅ **Duplicate Detection** - Spotted 3 similar FastAPI services  
✅ **Performance Metrics** - Response times ranging from 2.5ms to 5.4ms  
✅ **Detailed Analysis** - Separate Python and Node.js service breakdowns  

Perfect for developers managing multiple microservices and development environments!
