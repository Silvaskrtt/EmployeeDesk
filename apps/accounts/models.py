

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
    filename = f"{instance.user.username}_avatar.{ext}"
    return os.path.join('avatars', filename)

class Profile(models.Model):
    
    ROLE_CHOICHES = [
        ('ADMIN', 'Administrador'),
        ('USER', 'Usuário'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=10, choices=ROLE_CHOICHES, default='USER')
    avatar = models.ImageField(upload_to=avatar_upload_path, null=True, blank=True, verbose_name='Avatar')
    phone = models.CharField(max_length=20, blank=True, null=True, verbose_name='Telefone')
    