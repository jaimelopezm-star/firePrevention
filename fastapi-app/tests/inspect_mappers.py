import traceback

try:
    import models
    from models import Manager, PasGerente
    print('Imported models successfully')
    print('Manager attributes:', [c for c in dir(Manager) if not c.startswith('__')])
    try:
        mapper = Manager.__mapper__
        print('Manager relationships:')
        for r in mapper.relationships:
            print(' -', r.key, 'foreign_keys=', list(r._calculated_foreign_keys))
    except Exception as e:
        print('Error accessing Manager.__mapper__')
        traceback.print_exc()
    try:
        pm = PasGerente.__mapper__
        print('PasGerente relationships:')
        for r in pm.relationships:
            print(' -', r.key, 'foreign_keys=', list(r._calculated_foreign_keys))
    except Exception as e:
        print('Error accessing PasGerente.__mapper__')
        traceback.print_exc()
except Exception:
    print('Import failed')
    traceback.print_exc()
