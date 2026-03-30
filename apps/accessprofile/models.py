from django.db import models

class AccessProfile(models.Model):
    """
    Perfil de acesso do sistema
    Define permissões e níveis de acesso dos usuários
    """
    
    name = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='Nome do Perfil'
    )
    
    description = models.TextField(
        blank=True,
        verbose_name='Descrição'
    )
    
    permissions = models.JSONField(
        blank=True,
        null=True,
        verbose_name='Permissões'
    )
    
    is_system = models.BooleanField(
        default=False,
        verbose_name='Perfil do Sistema'
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Criado em'
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Atualizado em'
    )
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = 'Perfil de Acesso'
        verbose_name_plural = 'Perfis de Acesso'
        ordering = ['name']  # Ordenação padrão

    def has_permission(self, module, action):
        """
        Verifica se o perfil tem uma permissão específica
        Exemplo: profile.has_permission('employees', 'add')
        """
        if not self.permissions:
            return False
        
        module_perms = self.permissions.get(module, [])
        return action in module_perms