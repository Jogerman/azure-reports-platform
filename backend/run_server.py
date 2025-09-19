import os
import sys
import subprocess

def run_server_with_utf8():
    """Ejecutar servidor Django con encoding UTF-8"""
    
    # Configurar variables de entorno para UTF-8
    env = os.environ.copy()
    env['PYTHONIOENCODING'] = 'utf-8'
    env['LANG'] = 'en_US.UTF-8'
    
    if sys.platform.startswith('win'):
        # Windows
        env['PYTHONIOENCODING'] = 'utf-8'
        subprocess.run(['chcp', '65001'], shell=True)  # Cambiar codepage a UTF-8
    
    # Ejecutar servidor Django
    try:
        subprocess.run([
            sys.executable, 'manage.py', 'runserver'
        ], env=env, cwd=os.path.dirname(__file__))
    except KeyboardInterrupt:
        print("\nServidor detenido por el usuario")

if __name__ == "__main__":
    run_server_with_utf8()