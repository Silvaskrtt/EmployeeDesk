

from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import Group
import os

def avatar_upload_path(instance, filename):
    """Gera caminho único para o avatar"""
    ext = filename.split('.')[-1]
    filename = f"{instance.user.username}_avatar.{ext}"
    return os.path.join('avatars', filename)