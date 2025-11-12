"""
Compatibility shim: re-export CryptoManager from the newer implementation.

Older tests / modules import CryptoManager from `core.crypto`. A newer
implementation lives in `core.crypto_new` and provides the expanded API
(register_device_key, generar_rompecabezas_dispositivo, etc.). To avoid
changing many imports across the codebase, re-export the class here.
"""

from .crypto_new import CryptoManager  # noqa: E402,F401
