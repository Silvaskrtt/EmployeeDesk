from django.db import models
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
    
    name = models.CharField(max_length=100, verbose_name='Nome do Cargo')
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES, blank=True, null=True, verbose_name='Nível')
    min_wage = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, verbose_name='Salário Mínimo')
    max_wage = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, verbose_name='Salário Máximo')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Atualizado em')
    
    #Chaves Estrangeiras
    department = models.ForeignKey(Department, on_delete=models.PROTECT, related_name='positions', verbose_name='Departamento')
    
    class Meta:
        verbose_name = _("Cargo")
        verbose_name_plural = _("Cargos")
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} - {self.get_level_display()}" if self.level else self.name
    
    def clean(self):
        if self.min_wage and self.max_wage and self.min_wage > self.max_wage:
            raise ValidationError(_('Salário mínimo não pode ser maior que o salário máximo.'))
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
    
    @property
    def salary_range(self):
        if self.min_wage and self.max_wage:
            return f"R$ {self.min_wage:,.2f} - R$ {self.max_wage:,.2f}"
        return "Não definida"