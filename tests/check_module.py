def check_module():
    import core.crypto
    print("Módulo importado correctamente")
    print("Contenido del módulo:")
    print(dir(core.crypto))
    print("\nAtributos de CryptoManager:")
    print(dir(core.crypto.CryptoManager))

if __name__ == "__main__":
    check_module()