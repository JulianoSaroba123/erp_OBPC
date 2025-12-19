"""
Módulo Mídia - Sistema OBPC
Responsável por agenda semanal, certificados e carteiras de membro
"""

from .midia_routes import midia_bp

# Blueprint disponível para registro
__all__ = ['midia_bp']