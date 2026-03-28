from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
import re


def validate_color_code(value):
    """Valida se o código de cor é um hexadecimal válido"""
    if value:
        # Remove o # se existir
        color = value.lstrip('#')
        
        # Verifica se tem 6 dígitos hexadecimais
        if not re.match(r'^[0-9A-Fa-f]{6}$', color):
            raise ValidationError(
                _('Código de cor inválido. Use formato hexadecimal (ex: #FF0000)')
            )


class Status(models.Model):
    """Modelo de Status do Funcionário"""
    
    STATUS_PRESETS = [
        ('ATIVO', 'Ativo', '#00FF00'),
        ('INATIVO', 'Inativo', '#FF0000'),
        ('FERIAS', 'Férias', '#FFFF00'),
        ('LICENCA', 'Licença', '#FFA500'),
        ('AFASTADO', 'Afastado', '#808080'),
        ('TREINAMENTO', 'Em Treinamento', '#0000FF'),
    ]
    
    name = models.CharField(max_length=50, unique=True, verbose_name='Nome do Status', help_text='Ex: Ativo, Inativo, Férias, Licença, etc.')
    description = models.CharField(max_length=200, blank=True, null=True, verbose_name='Descrição', help_text='Descrição detalhada do status')
    color_code = models.CharField(max_length=7, blank=True, null=True, validators=[validate_color_code], verbose_name='Código da Cor', help_text='Código hexadecimal da cor (ex: #FF0000 para vermelho)')
    is_active = models.BooleanField(default=True, verbose_name='Status Ativo', help_text='Indica se este status está disponível para uso')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Atualizado em')
    
    class Meta:
        verbose_name = _("Status")
        verbose_name_plural = _("Status")
        ordering = ['order', 'name']  # Ordenação personalizada
        indexes = [
            models.Index(fields=['name'], name='idx_status_name'),
            models.Index(fields=['is_active'], name='idx_status_active'),
        ]
    
    def __str__(self):
        """Representação string do status"""
        return self.name
    
    def clean(self):
        """Validações personalizadas"""
        # Garante que o código de cor tenha #
        if self.color_code and not self.color_code.startswith('#'):
            self.color_code = f'#{self.color_code}'
        
        # Valida se o código de cor tem o tamanho correto
        if self.color_code and len(self.color_code) != 7:
            raise ValidationError({
                'color_code': _('Código de cor deve ter 7 caracteres (ex: #FF0000)')
            })
    
    def save(self, *args, **kwargs):
        """Salva o objeto com validação"""
        self.full_clean()
        super().save(*args, **kwargs)
    
    def delete(self, *args, **kwargs):
        """Protege contra exclusão de status do sistema ou em uso"""
        if self.is_system:
            raise ValidationError(_('Não é possível excluir um status padrão do sistema.'))
        
        # Verifica se existem funcionários com este status
        if hasattr(self, 'employees') and self.employees.exists():
            raise ValidationError(
                _('Não é possível excluir um status que está sendo usado por funcionários.')
            )
        
        super().delete(*args, **kwargs)
    
    @property
    def html_color(self):
        """Retorna o código de cor formatado para HTML/CSS"""
        return self.color_code if self.color_code else '#CCCCCC'
    
    @classmethod
    def get_default_status(cls):
        """Retorna o status padrão (Ativo)"""
        return cls.objects.get_or_create(
            name='Ativo',
            defaults={
                'description': 'Funcionário ativo na empresa',
                'color_code': '#00FF00',
                'is_active': True,
                'is_system': True,
                'order': 1
            }
        )[0]
    
    @classmethod
    def get_inactive_status(cls):
        """Retorna o status inativo"""
        return cls.objects.get_or_create(
            name='Inativo',
            defaults={
                'description': 'Funcionário inativo/demitido',
                'color_code': '#FF0000',
                'is_active': True,
                'is_system': True,
                'order': 2
            }
        )[0]