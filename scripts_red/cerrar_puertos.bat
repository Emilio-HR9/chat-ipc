@echo off
echo =======================================================
echo     Limpieza de Red para el Chat (Tarea 7)
echo =======================================================
echo.
echo Este script cerrara el puerto 65432 en el Firewall de Windows
echo y eliminara las reglas creadas previamente.
echo.
echo SOLICITANDO PERMISOS DE ADMINISTRADOR...
echo.

:: Comprobar si tiene permisos de administrador
net session >nul 2>&1
if %errorLevel% == 0 (
    echo [OK] Permisos concedidos. Limpiando firewall...
    echo.

    :: Eliminar regla para TCP
    netsh advfirewall firewall delete rule name="Chat_ASO_TCP" >nul
    echo [-] Regla TCP eliminada con exito.

    :: Eliminar regla para UDP
    netsh advfirewall firewall delete rule name="Chat_ASO_UDP" >nul
    echo [-] Regla UDP eliminada con exito.

    echo.
    echo =======================================================
    echo Todo limpio! Tu equipo esta seguro de nuevo.
    echo =======================================================
) else (
    echo [ERROR] No tienes permisos de Administrador.
    echo.
    echo Por favor, haz clic derecho sobre este archivo
    echo y selecciona "Ejecutar como administrador".
    echo.
)

pause
