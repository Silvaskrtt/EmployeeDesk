from django.db import models

def validate_zip_code(value):
    """Validador de CEP"""
    if value:
        # Remove caracteres não numéricos
        cep = ''.join(filter(str.isdigit, value))
        
        # Verifica se tem 8 dígitos
        if len(cep) != 8:
            raise ValidationError('CEP deve ter 8 dígitos')
        
        # Verifica se todos os dígitos são iguais
        if cep == cep[0] * 8:
            raise ValidationError('CEP inválido')

class Address(models.Model):
    
    zip_code = models.CharField(max_length=10, blank=True, null=True, validators=[validate_zip_code], verbose_name='CEP', help_text='Formato: 12345-678')
    country = models.CharField(max_length=100, blank=True, null=True, default='Brasil', verbose_name='País')
    state = models.CharField(max_length=100, verbose_name='Estado', help_text='Ex: São Paulo, Rio de Janeiro, etc.')
    city = models.CharField(max_length=100, verbose_name='Cidade')
    neighborhood = models.CharField(max_length=100, verbose_name='Bairro')
    street = models.CharField(max_length=200, verbose_name='Logradouro', help_text='Rua, Avenida, Alameda, etc.')
    number = models.CharField(max_length=20, verbose_name='Número',
        help_text='Número da residência, ou "S/N" para sem número')
    complement = models.CharField(max_length=100, blank=True, null=True, verbose_name='Complemento', help_text='Apto, Bloco, Casa, etc.')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Atualizado em')
    
    class Meta:
        verbose_name = _("Endereço")
        verbose_name_plural = _("Endereços")
        ordering = ['country', 'state', 'city', 'street', 'number']
        indexes = [
            models.Index(fields=['zip_code'], name='idx_address_zip_code'),
            models.Index(fields=['city', 'state'], name='idx_address_city_state'),
            models.Index(fields=['country'], name='idx_address_country'),
        ]
        
    def __str__(self):
        """Representação string do endereço"""
        address_parts = []
        
        if self.street:
            address_parts.append(self.street)
        if self.number:
            address_parts.append(f", {self.number}")
        if self.complement:
            address_parts.append(f" - {self.complement}")
        if self.neighborhood:
            address_parts.append(f"\n{self.neighborhood}")
        if self.city and self.state:
            address_parts.append(f"\n{self.city} - {self.state}")
        if self.zip_code:
            address_parts.append(f"\nCEP: {self.format_zip_code()}")
        if self.country and self.country != 'Brasil':
            address_parts.append(f"\n{self.country}")
        
        return ''.join(address_parts) if address_parts else "Endereço não informado"
    
    def clean(self):
        """Validações personalizadas"""
        # Formata o CEP se existir
        if self.zip_code:
            cep_clean = ''.join(filter(str.isdigit, self.zip_code))
            if len(cep_clean) == 8:
                self.zip_code = f'{cep_clean[:5]}-{cep_clean[5:]}'
    
    def save(self, *args, **kwargs):
        """Salva o objeto com validação"""
        self.full_clean()
        super().save(*args, **kwargs)
    
    def format_zip_code(self):
        """Retorna o CEP formatado"""
        if self.zip_code:
            cep_clean = ''.join(filter(str.isdigit, self.zip_code))
            if len(cep_clean) == 8:
                return f'{cep_clean[:5]}-{cep_clean[5:]}'
        return self.zip_code
    
    @property
    def full_address(self):
        """Retorna o endereço completo em uma linha"""
        parts = []
        
        if self.street:
            parts.append(self.street)
        if self.number:
            parts.append(self.number)
        if self.complement:
            parts.append(self.complement)
        if self.neighborhood:
            parts.append(self.neighborhood)
        if self.city:
            parts.append(self.city)
        if self.state:
            parts.append(self.state)
        if self.zip_code:
            parts.append(self.format_zip_code())
        
        return ', '.join(parts) if parts else "Endereço não informado"
    
    @property
    def short_address(self):
        """Retorna endereço resumido"""
        parts = []
        if self.street:
            parts.append(self.street)
        if self.number:
            parts.append(self.number)
        if self.city:
            parts.append(self.city)
        return ', '.join(parts) if parts else "Endereço não informado"