# apps/core/permissions.py
from rest_framework import permissions

class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Permite el acceso de lectura (GET, HEAD, OPTIONS) a cualquiera,
    pero solo permite la escritura (PUT, POST, DELETE) al propietario del objeto.
    """
    def has_object_permission(self, request, view, obj):
        # Permiso de lectura permitido para cualquier solicitud
        if request.method in permissions.SAFE_METHODS:
            return True

        # Permiso de escritura solo permitido para el dueño del objeto 'owner'.
        # El objeto 'obj' debe tener un atributo 'owner' (como Election lo tiene).
        return obj.owner == request.user