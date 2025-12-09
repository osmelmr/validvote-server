# apps/users/serializers.py
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

# 1. Recuperar el modelo de usuario personalizado
User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    """
    Serializer base para exponer la información del usuario autenticado (perfil).
    Se han ELIMINADO los campos 'meta' y 'created_at'.
    """
    class Meta:
        model = User
        fields = (
            'id', 
            'email', 
            'name', 
        )
        read_only_fields = ('email',)


class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer para manejar el registro de nuevos usuarios.
    Mantiene la validación de contraseñas.
    """
    password2 = serializers.CharField(
        style={'input_type': 'password'}, 
        write_only=True, 
        label=_("Confirmación de Contraseña")
    )
    
    class Meta:
        model = User
        fields = ('email', 'name', 'password', 'password2')
        extra_kwargs = {
            'password': {'write_only': True, 'style': {'input_type': 'password'}}
        }

    def validate(self, data):
        """
        Valida que las contraseñas coincidan y que el email no esté ya registrado.
        """
        if data['password'] != data.pop('password2'):
            raise serializers.ValidationError({"password": _("Las contraseñas no coinciden.")})

        if User.objects.filter(email=data['email']).exists():
            raise serializers.ValidationError({"email": _("Este correo electrónico ya está registrado.")})
            
        return data

    def create(self, validated_data):
        """
        Crea un nuevo usuario utilizando el manager personalizado.
        """
        user = User.objects.create_user(
            email=validated_data['email'],
            name=validated_data['name'],
            password=validated_data['password']
        )
        return user