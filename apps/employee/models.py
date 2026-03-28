from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

#Importe de outros models
from accounts.models import User
from status.models import Status 
from position.models import Position 
from address.models import Address

def validate_cpf(value):
    """Validador de CPF"""
    # Remove caracteres não numéricos
    cpf = ''.join(filter(str.isdigit, value))
    
    # Verifica se tem 11 dígitos
    if len(cpf) != 11:
        raise ValidationError('CPF deve ter 11 dígitos')
    
    # Verifica se todos os dígitos são iguais (CPF inválido)
    if cpf == cpf[0] * 11:
        raise ValidationError('CPF inválido')
    
    # Validação dos dígitos verificadores
    for i in range(9, 11):
        value = sum((int(cpf[num]) * ((i+1) - num) for num in range(0, i)))
        digit = ((value * 10) % 11) % 10
        if digit != int(cpf[i]):
            raise ValidationError('CPF inválido')

class Employee(models.Model):

    user = models.OneToOneField(
        User,
        on_delete=models.PROTECT,
        related_name='employee'
    )
    
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    cpf = models.CharField('CPF', max_length=14, unique=True, validators=[validate_cpf])
    personal_email = models.EmailField('E-mail Pessoal', unique=True)
    email = models.EmailField('E-mail Corporativo', unique=True)
    birth_date = models.DateField(help_text="Formato: DD/MM/AAAA")
    hire_date = models.DateField(help_text="Formato: DD/MM/AAAA")
    wage = models.DecimalField(max_digits=10, decimal_places=2)
    emergency_contact = models.CharField(blank=True, null=True, max_length=150)
    emergency_phone = models.CharField(blank=True, null=True, max_length=20)
    resignation_date = models.DateField(blank=True, null=True, help_text="Formato: DD/MM/AAAA")
    
    # Chaves Estrangeiras
    status = models.ForeignKey(Status, on_delete=models.PROTECT, verbose_name='Status')
    position = models.ForeignKey(Position, on_delete=models.PROTECT, verbose_name='Cargo')
    address = models.ForeignKey(Address, on_delete=models.PROTECT, verbose_name='Endereço')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Atualizado em')
    
    class Meta:
        verbose_name = _("Funcionário")
        verbose_name_plural = _("Funcionários")
        ordering = ['first_name', 'last_name']
        
    def __str__(self):
        return f"{self.first_name} {self.last_name}"
    
    def clean(self):
        """Limpa e formata o CPF antes de salvar"""
        if self.cpf:
            # Remove caracteres não numéricos
            cpf_clean = ''.join(filter(str.isdigit, self.cpf))
            # Formata o CPF (XXX.XXX.XXX-XX)
            if len(cpf_clean) == 11:
                self.cpf = f'{cpf_clean[:3]}.{cpf_clean[3:6]}.{cpf_clean[6:9]}-{cpf_clean[9:]}'
    
    def save(self, *args, **kwargs):
        """Salva o objeto com validação"""
        self.full_clean()  #chama clean() antes de salvar
        super().save(*args, **kwargs)
        
    def toggle_status(self):
        """Alterna o status do funcionário"""
        from status.models import Status
        
        try:
            ativo = Status.objects.get(name='Ativo')
            inativo = Status.objects.get(name='Inativo')
        except Status.DoesNotExist:
            raise ValidationError('Status "Ativo" ou "Inativo" não encontrados.')
        
        # Alterna entre Ativo e Inativo
        if self.status == ativo:
            self.status = inativo
        else:
            self.status = ativo
        
        self.save()
        return self.status.name
    
    @property
    def full_name(self):
        """Retorna o nome completo"""
        return f"{self.first_name} {self.last_name}"
    
    @property
    def is_active(self):
        """Verifica se o funcionário está ativo"""
        return self.status.name.upper() == 'ATIVO' and self.resignation_date is None