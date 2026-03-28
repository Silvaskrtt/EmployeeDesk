from django.db import models
from django.contrib.auth.models import User
# imports necessários parar os grupos
#from django.db.models.signals import post_save
#from django.dispatch import receiver
#from django.contrib.auth.models import Group
import os


# =============================================================================
# FUNÇÕES AUXILIARES
# =============================================================================

def avatar_upload_path(instance, filename):
    """
    Determina o caminho de upload para arquivos de avatar.
    
    Esta função gera um nome de arquivo único para o avatar baseado no
    username do usuário, garantindo que não haja conflitos de nomes
    no sistema de arquivos.
    
    Args:
        instance (Profile): Instância do modelo Profile que está sendo salva.
        filename (str): Nome original do arquivo enviado.
    
    Returns:
        str: Caminho completo para armazenamento do avatar no formato
             'avatars/{username}_avatar.{extensao}'.
    
    Note:
        Se o username ainda não estiver disponível (ex: durante criação
        do usuário), utiliza o ID como fallback para garantir unicidade.
    
    Example:
        >>> avatar_upload_path(profile, 'foto.jpg')
        'avatars/johndoe_avatar.jpg'
    """
    # Extrai extensão do arquivo original
    ext = filename.split('.')[-1]
    
    # Usa o ID se o username ainda não estiver disponível (fallback para segurança)
    username = instance.user.username if instance.user.username else str(instance.user.id)
    
    # Gera nome do arquivo no padrão: username_avatar.extensao
    filename = f"{username}_avatar.{ext}"
    
    # Retorna caminho dentro do diretório 'avatars' da media
    return os.path.join('avatars', filename)


# =============================================================================
# MODELO DE PERFIL DE USUÁRIO
# =============================================================================

class Profile(models.Model):
    """
    Modelo que estende as informações do usuário padrão do Django.
    
    Este modelo utiliza uma relação OneToOne com o User nativo do Django
    para adicionar campos customizados como permissões de acesso (role),
    avatar, telefone e biografia. A relação OneToOne garante que cada
    usuário tenha exatamente um perfil e vice-versa.
    
    Attributes:
        user (OneToOneField): Relacionamento com o modelo User do Django.
        role (CharField): Papel/função do usuário no sistema (admin, RH, gestor).
        avatar (ImageField): Foto de perfil do usuário.
        phone (CharField): Número de telefone para contato.
        bio (TextField): Biografia ou descrição pessoal.
        created_at (DateTimeField): Data/hora de criação do perfil.
        updated_at (DateTimeField): Data/hora da última atualização.
    
    Meta:
        verbose_name: Nome singular para interface administrativa.
        verbose_name_plural: Nome plural para interface administrativa.
    """
    
    # -------------------------------------------------------------------------
    # DEFINIÇÃO DE ESCOLHAS (CHOICES)
    # -------------------------------------------------------------------------
    
    ROLE_CHOICES = [
        ('ADMINISTRADOR', 'admin'),           # Administrador do sistema
        ('RH', 'Recursos Humanos'),            # Equipe de Recursos Humanos
        ('GESTOR', 'Manager'),                 # Gestor/Manager
    ]
    
    # -------------------------------------------------------------------------
    # CAMPOS DO MODELO
    # -------------------------------------------------------------------------
    
    # Relacionamento um-para-um com o modelo User nativo do Django
    # on_delete=CASCADE: Remove o perfil quando o usuário for excluído
    # related_name='profile': Permite acessar o perfil via user.profile
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile'
    )
    
    # Papel/função do usuário no sistema, com valor padrão 'RH'
    # Define as permissões e acessos disponíveis para este usuário
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='RH'
    )
    
    # Avatar do usuário com upload gerenciado pela função avatar_upload_path
    # Campo opcional para permitir usuários sem foto de perfil
    avatar = models.ImageField(
        upload_to=avatar_upload_path,
        null=True,
        blank=True,
        verbose_name='Avatar'
    )
    
    # Telefone para contato, campo opcional
    phone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name='Telefone'
    )
    
    # Biografia ou descrição pessoal do usuário, campo opcional
    bio = models.TextField(
        blank=True,
        null=True
    )
    
    # -------------------------------------------------------------------------
    # CAMPOS DE AUDITORIA (TIMESTAMPS)
    # -------------------------------------------------------------------------
    
    # Data/hora de criação do perfil (preenchido automaticamente)
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Criado em'
    )
    
    # Data/hora da última atualização do perfil (atualizado automaticamente)
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Atualizado em'
    )
    
    # -------------------------------------------------------------------------
    # METADADOS DO MODELO
    # -------------------------------------------------------------------------
    
    class Meta:
        """Configurações de metadados para o modelo Profile."""
        verbose_name = 'Perfil'
        verbose_name_plural = 'Perfis'
    
    # -------------------------------------------------------------------------
    # MÉTODOS PÚBLICOS
    # -------------------------------------------------------------------------
    
    def __str__(self):
        """
        Representação em string do objeto Profile.
        
        Utilizada em interfaces administrativas, debug e logs para
        identificação rápida do perfil associado a um usuário.
        
        Returns:
            str: String no formato "Perfil de {username}"
        
        Example:
            >>> profile.__str__()
            'Perfil de johndoe'
        """
        return f"Perfil de {self.user.username}"