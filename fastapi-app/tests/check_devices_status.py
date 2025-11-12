"""
Script para verificar el estado de los dispositivos en la BD.
Muestra cuáles tienen pasdispositivo y encryption_key.
"""

from database import SessionLocal
from models import Device
from models.pas_dispositivo import PasDispositivo

def check_devices():
    db = SessionLocal()
    try:
        print("\n" + "="*80)
        print("ESTADO DE DISPOSITIVOS EN LA BASE DE DATOS")
        print("="*80)
        
        devices = db.query(Device).all()
        
        if not devices:
            print("\n❌ No hay dispositivos en la base de datos")
            return
        
        print(f"\n✓ Total de dispositivos: {len(devices)}\n")
        print(f"{'ID':<5} {'Nombre':<25} {'Tipo':<20} {'PasDisp ID':<12} {'API Key':<25} {'Enc Key'}")
        print("-" * 115)
        
        devices_ready = []
        devices_need_pas = []
        devices_need_key = []
        
        for device in devices:
            pas_id = device.pasdispositivo_id or "NULL"
            
            if device.pasdispositivo_id:
                pas_disp = db.query(PasDispositivo).filter(
                    PasDispositivo.id == device.pasdispositivo_id
                ).first()
                
                if pas_disp:
                    api_key = pas_disp.api_key[:20] + "..." if pas_disp.api_key else "NULL"
                    has_key = "✓" if pas_disp.encryption_key else "✗"
                    
                    if pas_disp.encryption_key:
                        devices_ready.append(device.id)
                    else:
                        devices_need_key.append(device.id)
                else:
                    api_key = "ERROR"
                    has_key = "✗"
            else:
                api_key = "NULL"
                has_key = "✗"
                devices_need_pas.append(device.id)
            
            nombre = (device.nombre[:22] + "...") if len(device.nombre) > 25 else device.nombre
            tipo = (device.device_type[:17] + "...") if device.device_type and len(device.device_type) > 20 else (device.device_type or "N/A")
            
            print(f"{device.id:<5} {nombre:<25} {tipo:<20} {str(pas_id):<12} {api_key:<25} {has_key}")
        
        print("\n" + "="*80)
        print("RESUMEN:")
        print("="*80)
        
        if devices_ready:
            print(f"\n✅ Dispositivos LISTOS para pruebas (tienen pasdispositivo + encryption_key):")
            print(f"   IDs: {', '.join(map(str, devices_ready))}")
            print(f"\n   💡 Puedes usar cualquiera de estos con POST /device/generate-puzzle-test")
        
        if devices_need_key:
            print(f"\n⚠️  Dispositivos que necesitan encryption_key:")
            print(f"   IDs: {', '.join(map(str, devices_need_key))}")
            print(f"\n   💡 Usa POST /device/init-encryption-key?device_id=<ID>")
        
        if devices_need_pas:
            print(f"\n❌ Dispositivos SIN pasdispositivo (necesitan configuración):")
            print(f"   IDs: {', '.join(map(str, devices_need_pas))}")
            print(f"\n   💡 Necesitas crear un pasdispositivo y asignarlo:")
            print(f"      SQL: INSERT INTO pasdispositivo (api_key) VALUES ('TU_API_KEY');")
            print(f"           UPDATE dispositivo SET pasdispositivo_id = <ID> WHERE id = <DEVICE_ID>;")
        
        print("\n" + "="*80)
        
        # Sugerir un dispositivo para probar
        if devices_ready:
            device_to_test = devices_ready[0]
            device_obj = db.query(Device).filter(Device.id == device_to_test).first()
            pas_obj = db.query(PasDispositivo).filter(PasDispositivo.id == device_obj.pasdispositivo_id).first()
            
            print(f"\n🚀 DISPOSITIVO RECOMENDADO PARA PRUEBA:")
            print(f"   Device ID: {device_to_test}")
            print(f"   Nombre: {device_obj.nombre}")
            print(f"   API Key: {pas_obj.api_key}")
            print(f"\n   Comando Swagger:")
            print(f"   1. POST /device/generate-puzzle-test?device_id={device_to_test}")
            print(f"   2. Copia el puzzle de la respuesta")
            print(f"   3. POST /device/login con el payload completo")
            print("\n" + "="*80)
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    check_devices()
