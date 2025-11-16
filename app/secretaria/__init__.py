# Módulo Secretaria - Gestão Administrativa
from .atas import atas_bp, Ata
from .inventario import inventario_bp, ItemInventario

__all__ = ['atas_bp', 'Ata', 'inventario_bp', 'ItemInventario']