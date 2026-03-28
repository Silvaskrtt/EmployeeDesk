from django.db import models
from django.utils.translation import gettext_lazy as _

def validate_color_code(value):
    """Valida se o código de cor é um hexadecimal válido"""
    if value:
        color = value.lstrip('#')
        if not re.match(r'^[0-9A-Fa-f]{6}$', color):
            raise ValidationError(_('Código de cor inválido. Use formato hexadecimal (ex: #FF0000)'))


class Status(models.Model):
    """Modelo de Status do Funcionário"""
    
    name = models.CharField(max_length=50, unique=True, verbose_name='Nome do Status')
    description = models.CharField(max_length=200, blank=True, null=True, verbose_name='Descrição')
    color_code = models.CharField(max_length=7, blank=True, null=True, validators=[validate_color_code], verbose_name='Código da Cor')
    is_active = models.BooleanField(default=True, verbose_name='Status Ativo')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Atualizado em')
    
    class Meta:
        verbose_name = _("Status")
        verbose_name_plural = _("Status")
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def clean(self):
        if self.color_code and not self.color_code.startswith('#'):
            self.color_code = f'#{self.color_code}'
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
    
    @property
    def html_color(self):
        return self.color_code if self.color_code else '#CCCCCC'