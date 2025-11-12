"""
Script simplificado para generar el puzzle de dispositivo.
Reutiliza el código que ya tienes (rompecabezas.py y cifrado_aes256.py).

Este script genera el JSON que debes copiar y pegar en Swagger.

Requisitos:
- Tener los archivos rompecabezas.py y cifrado_aes256.py en el mismo directorio
- O adaptar las importaciones según tu estructura

Uso:
    python generate_device_puzzle.py
"""

import sys
import os

# Intenta importar desde tu código original
try:
    # Ajusta estas importaciones según donde tengas tus archivos
    sys.path.insert(0, os.path.dirname(__file__))
    from rompecabezas import generar_rompecabezas_dispositivo, key_database, server_key, server_id
    print("✓ Módulos de rompecabezas cargados correctamente\n")
except ImportError as e:
    print(f"❌ Error al importar módulos: {e}")
    print("\nPor favor, copia este script a la misma carpeta donde tengas:")
    print("  - rompecabezas.py")
    print("  - cifrado_aes256.py")
    sys.exit(1)

import json


def main():
    print("="*70)
    print("GENERADOR DE PUZZLE PARA LOGIN DE DISPOSITIVO")
    print("="*70)
    
    # Mostrar dispositivos disponibles en la BD simulada
    print("\nDispositivos disponibles:")
    for idx, device_id in enumerate(key_database.keys(), 1):
        print(f"  {idx}. {device_id}")
    
    # Pedir al usuario que elija un dispositivo
    print("\n¿Qué dispositivo quieres usar?")
    choice = input("Ingresa el nombre del dispositivo (ej: ID_sensor_temperatura): ").strip()
    
    if choice not in key_database:
        print(f"\n❌ Dispositivo '{choice}' no encontrado en la base de datos simulada")
        print("   Dispositivos válidos:", list(key_database.keys()))
        sys.exit(1)
    
    # Generar el puzzle
    print(f"\n{'─'*70}")
    print(f"Generando puzzle para: {choice}")
    print(f"{'─'*70}")
    
    try:
        puzzle = generar_rompecabezas_dispositivo(choice)
        
        print("\n✓ Puzzle generado exitosamente\n")
        print("="*70)
        print("COPIA ESTE JSON PARA USAR EN SWAGGER:")
        print("="*70)
        
        # Formato para Swagger (campo puzzle_response en DeviceLogin)
        swagger_payload = {
            "device_id": 5,  # AJUSTA ESTE ID según tu BD real
            "api_key": "CFr9woIVKTSQ3YPnwUcYvKOc1FqKx8bi",  # AJUSTA según tu BD real
            "puzzle_response": puzzle
        }
        
        print("\n" + json.dumps(swagger_payload, indent=2))
        
        print("\n" + "="*70)
        print("INSTRUCCIONES PARA SWAGGER:")
        print("="*70)
        print("1. Ve a Swagger UI: http://localhost:8000/docs")
        print("2. Busca el endpoint: POST /device/login")
        print("3. Haz clic en 'Try it out'")
        print("4. COPIA y PEGA el JSON de arriba en el campo 'Request body'")
        print("5. IMPORTANTE: Ajusta 'device_id' y 'api_key' con los valores reales de tu BD")
        print("6. Haz clic en 'Execute'")
        print("\n✓ Si todo está correcto, recibirás un access_token")
        
        # Guardar en archivo
        output_file = "device_puzzle_payload.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(swagger_payload, f, indent=2, ensure_ascii=False)
        
        print(f"\n✓ Payload guardado en: {output_file}")
        print("  (Puedes copiar desde ahí si prefieres)")
        
    except Exception as e:
        print(f"\n❌ Error al generar puzzle: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Operación cancelada por el usuario")
        sys.exit(0)
