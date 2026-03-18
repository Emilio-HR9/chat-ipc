@echo off
echo =======================================================
echo     Configuracion de Red para el Chat (Tarea 7)
echo =======================================================
echo.
echo Este script abrira el puerto 65432 en el Firewall de Windows
echo para permitir que los equipos se comuniquen por TCP y UDP.
echo.
echo SOLICITANDO PERMISOS DE ADMINISTRADOR...
echo.

:: Comprobar si tiene permisos de administrador
net session >nul 2>&1
if %errorLevel% == 0 (
    echo [OK] Permisos concedidos. Configurando firewall...
    echo.

    :: Regla para TCP (Unicast/Anycast)
    netsh advfirewall firewall add rule name="Chat_ASO_TCP" dir=in action=allow protocol=TCP localport=65432 >nul
    echo [+] Puerto TCP 65432 abierto con exito.

    :: Regla para UDP (Broadcast/Multicast)
    netsh advfirewall firewall add rule name="Chat_ASO_UDP" dir=in action=allow protocol=UDP localport=65432 >nul
    echo [+] Puerto UDP 65432 abierto con exito.

    echo.
    echo =======================================================
    echo Todo listo! Ya puedes abrir 'python app.py'.
    echo =======================================================
) else (
    echo [ERROR] No tienes permisos de Administrador.
    echo.
    echo Por favor, haz clic derecho sobre este archivo
    echo y selecciona "Ejecutar como administrador".
    echo.
)

pause
