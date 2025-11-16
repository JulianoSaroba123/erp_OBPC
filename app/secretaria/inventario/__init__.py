# Módulo de Inventário Patrimonial
from .inventario_model import ItemInventario
from .inventario_routes import inventario_bp

__all__ = ['ItemInventario', 'inventario_bp']