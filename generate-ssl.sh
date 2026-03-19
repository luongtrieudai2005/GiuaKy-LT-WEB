@echo off
REM ============================================================
REM generate-ssl.bat — Windows version
REM Tạo self-signed SSL certificate cho local development.
REM
REM Yêu cầu: OpenSSL đã được cài trên Windows.
REM Cách cài: https://slproweb.com/products/Win32OpenSSL.html
REM Hoặc dùng Git Bash (đã có openssl sẵn) để chạy .sh version.
REM
REM Chạy script này MỘT LẦN trước khi docker compose up:
REM   generate-ssl.bat
REM ============================================================

if not exist "nginx\ssl" mkdir "nginx\ssl"

echo Generating self-signed SSL certificate...

openssl req -x509 ^
    -nodes ^
    -days 365 ^
    -newkey rsa:2048 ^
    -keyout "nginx\ssl\key.pem" ^
    -out    "nginx\ssl\cert.pem" ^
    -subj "/C=VN/ST=HCM/L=HoChiMinh/O=TaskManager/CN=localhost" ^
    -addext "subjectAltName=DNS:localhost,IP:127.0.0.1"

echo.
echo SSL certificate generated:
echo   cert: nginx\ssl\cert.pem
echo   key:  nginx\ssl\key.pem
echo.
echo Done. Now run: docker compose up --build