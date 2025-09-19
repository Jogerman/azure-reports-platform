import os
import sys

def clear_logs():
    """Limpiar logs con problemas de encoding"""
    log_file = os.path.join(os.path.dirname(__file__), 'logs', 'azure_reports.log')
    
    if os.path.exists(log_file):
        try:
            os.remove(log_file)
            print("Log file eliminado exitosamente")
        except Exception as e:
            print(f"Error eliminando log file: {e}")
    
    # Crear nuevo log file con encoding correcto
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    
    with open(log_file, 'w', encoding='utf-8') as f:
        f.write("# Azure Reports Platform Log File\n")
        f.write("# Encoding: UTF-8\n")
        f.write(f"# Created: {datetime.now().isoformat()}\n\n")
    
    print("Nuevo log file creado con encoding UTF-8")

if __name__ == "__main__":
    from datetime import datetime
    clear_logs()