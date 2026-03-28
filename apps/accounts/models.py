

from django.db import models
from django.contrib.auth.models import User
# imports necessários parar os grupos
#from django.db.models.signals import post_save
#from django.dispatch import receiver
#from django.contrib.auth.models import Group
import os

def avatar_upload_path(instance, filename):
    """Gera caminho único para o avatar"""
    ext = filename.split('.')[-1]
    # Usa o ID se o username ainda não estiver disponível
    username = instance.user.username if instance.user.username else str(instance.user.id)
    filename = f"{username}_avatar.{ext}"
    return os.path.join('avatars', filename)

class Profile(models.Model):
    
    ROLE_CHOICHES = [
        ('ADMINISTRADOR', 'admin'),
        ('RH', 'Recursos Humanos'),
        ('GESTOR ', 'Manager')
    ]
    
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        related_name='profile'
    )
    
    role = models.CharField(max_length=20, choices=ROLE_CHOICHES, default='RH')
    avatar = models.ImageField(upload_to=avatar_upload_path, null=True, blank=True, verbose_name='Avatar')
    phone = models.CharField(max_length=20, blank=True, null=True, verbose_name='Telefone')
    bio = models.TextField(blank=True, null=True)
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Atualizado em')
    
    def __str__(self):
        return f"Perfil de {self.user.username}"
    
    class Meta:
        verbose_name = 'Perfil'
        verbose_name_plural = 'Perfis'