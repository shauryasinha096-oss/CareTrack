"""Start the installed local application; Ctrl+C stops only processes started here."""
from pathlib import Path
import os
import signal
import socket
import subprocess
import sys
import time
import urllib.request

ROOT=Path(__file__).resolve().parents[1]
owned=[]

def listening(port):
    try:
        with socket.create_connection(('127.0.0.1',port),timeout=0.5): return True
    except OSError: return False

def ready(url):
    try:
        with urllib.request.urlopen(url,timeout=2) as response: return response.status==200
    except Exception: return False

def start(command,cwd):
    process=subprocess.Popen(command,cwd=cwd,start_new_session=True)
    owned.append(process)
    return process

def wait(check,process,label):
    for _ in range(120):
        if check(): return
        if process.poll() is not None: raise RuntimeError(label+' exited; read the startup error above.')
        time.sleep(0.25)
    raise RuntimeError(label+' did not become ready in 30 seconds.')

try:
    if not (ROOT/'.env').exists(): raise RuntimeError('Configure .env and install/seed MySQL using README.md first.')
    mysql=ROOT/'.runtime/mysql-8.4.11-macos15-arm64/bin/mysqld'
    if mysql.exists() and not listening(3307):
        process=start(['bash',str(ROOT/'scripts/start_local_mysql.sh')],ROOT)
        wait(lambda:listening(3307),process,'MySQL')
    if not ready('http://127.0.0.1:8000/api/health'):
        if listening(8000): raise RuntimeError('Port 8000 is occupied by an unhealthy or unrelated service.')
        process=start(['bash',str(ROOT/'scripts/start_backend.sh')],ROOT)
        wait(lambda:ready('http://127.0.0.1:8000/api/health'),process,'API')
    if not ready('http://127.0.0.1:5173'):
        if listening(5173): raise RuntimeError('Port 5173 is occupied by an unhealthy or unrelated service.')
        process=start(['bash',str(ROOT/'scripts/start_frontend.sh')],ROOT)
        wait(lambda:ready('http://127.0.0.1:5173'),process,'Frontend')
    print('\nCareTrack ready: http://127.0.0.1:5173',flush=True)
    print('API reference: http://127.0.0.1:8000/docs\nPress Ctrl+C to stop processes started by this launcher.',flush=True)
    while True:
        if any(p.poll() is not None for p in owned): raise RuntimeError('A CareTrack process stopped unexpectedly.')
        time.sleep(1)
except KeyboardInterrupt:
    print('\nStopping CareTrack processes started by this launcher.')
except Exception as error:
    print(str(error),file=sys.stderr)
    sys.exit(1)
finally:
    for process in reversed(owned):
        if process.poll() is None:
            os.killpg(process.pid,signal.SIGTERM)
            try: process.wait(timeout=10)
            except subprocess.TimeoutExpired: os.killpg(process.pid,signal.SIGKILL)
