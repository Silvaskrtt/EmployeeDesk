from django.db import models
    
# Importe de outros modelos
from department.models import Department

class Position(models.Model):
    
    LEVEL_CHOICES = [
        ('TRAINEE', 'Trainee'),
        ('JUNIOR', 'Júnior'),
        ('PLENO', 'Pleno'),
        ('SENIOR', 'Sênior'),
        ('SPECIALIST', 'Especialista'),
        ('MANAGER', 'Gerente'),
        ('DIRECTOR', 'Diretor'),
    ]
    
    name = models.CharField(max_length=100, verbose_name='Nome do Cargo',)
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES, blank=True, null=True, verbose_name='Nível', help_text='Nível de senioridade do cargo')
    min_wage = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, verbose_name='Salário Mínimo')
    max_wage = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, verbose_name='Salário Máximo')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Atualizado em')
    
    # Chaves estrangeiras
    
    department = models.ForeignKey(Department, on_delete=models,PROTECT, related_name='positions', verbose_name='Departamento')
    
     class Meta:
        verbose_name = _("Cargo")
        verbose_name_plural = _("Cargos")
        ordering = ['name', 'level']  # Ordenação padrão
        indexes = [
            models.Index(fields=['name'], name='idx_position_name'),
            models.Index(fields=['department'], name='idx_position_department'),
            models.Index(fields=['level'], name='idx_position_level'),
        ]
        unique_together = ['name', 'department']  # Evita cargos duplicados no mesmo departamento
    
    def __str__(self):
        """Representação string do cargo"""
        if self.level:
            return f"{self.name} - {self.get_level_display()}"
        return self.name
    
    def clean(self):
        """Validações personalizadas"""
        # Valida se min_wage < max_wage quando ambos estão preenchidos
        if self.min_wage is not None and self.max_wage is not None:
            if self.min_wage > self.max_wage:
                raise ValidationError({
                    'min_wage': _('Salário mínimo não pode ser maior que o salário máximo.'),
                    'max_wage': _('Salário máximo não pode ser menor que o salário mínimo.')
                })
        
        # Valida se wage está dentro da faixa (opcional, pode ser usado em Employee)
        pass
    
    def save(self, *args, **kwargs):
        """Salva o objeto com validação"""
        self.full_clean()
        super().save(*args, **kwargs)
    
    @property
    def salary_range(self):
        """Retorna a faixa salarial formatada"""
        if self.min_wage and self.max_wage:
            return f"R$ {self.min_wage:,.2f} - R$ {self.max_wage:,.2f}"
        elif self.min_wage:
            return f"a partir de R$ {self.min_wage:,.2f}"
        elif self.max_wage:
            return f"até R$ {self.max_wage:,.2f}"
        return "Não definida"
    
    @property
    def full_name(self):
        """Retorna o nome completo do cargo com nível"""
        return self.__str__()