@echo off
REM RigMaster AI Launcher - Forces TLS 1.2 for MongoDB Atlas compatibility
set OPENSSL_CONF=%~dp0openssl.cnf
echo Starting RigMaster AI with TLS 1.2 compatibility mode...
python "%~dp0app.py" %*
