from django.db import models
from django.utils.translation import gettext_lazy as _

def validate_zip_code(value):
    """Validador de CEP"""
    if value:
        cep = ''.join(filter(str.isdigit, value))
        if len(cep) != 8:
            raise ValidationError('CEP deve ter 8 dígitos')

class Address(models.Model):
    
    zip_code = models.CharField(max_length=10, blank=True, null=True, validators=[validate_zip_code], verbose_name='CEP')
    country = models.CharField(max_length=100, blank=True, null=True, default='Brasil', verbose_name='País')
    state = models.CharField(max_length=100, verbose_name='Estado')
    city = models.CharField(max_length=100, verbose_name='Cidade')
    neighborhood = models.CharField(max_length=100, verbose_name='Bairro')
    street = models.CharField(max_length=200, verbose_name='Logradouro')
    number = models.CharField(max_length=20, verbose_name='Número')
    complement = models.CharField(max_length=100, blank=True, null=True, verbose_name='Complemento')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Atualizado em')
    
    class Meta:
        verbose_name = _("Endereço")
        verbose_name_plural = _("Endereços")
        ordering = ['country', 'state', 'city']
    
    def __str__(self):
        return f"{self.street}, {self.number} - {self.city}/{self.state}"
    
    def clean(self):
        if self.zip_code:
            cep_clean = ''.join(filter(str.isdigit, self.zip_code))
            if len(cep_clean) == 8:
                self.zip_code = f'{cep_clean[:5]}-{cep_clean[5:]}'
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
    
    @property
    def full_address(self):
        return f"{self.street}, {self.number} - {self.city}/{self.state}"