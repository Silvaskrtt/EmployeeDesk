from django.db import models
from django.core.exceptions import ValidationError

class EmployeeDepartment(models.Model):
    """
    Tabela associativa entre Employee e Department (N:N)
    Permite que um funcionário pertença a múltiplos departamentos
    """
    
    # Campos com valores padrão
    allocation_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=100.00,
        verbose_name='Percentual de Alocação',
        help_text='Percentual de dedicação ao departamento (0-100%)'
    )
    
    is_primary = models.BooleanField(
        default=False,
        verbose_name='Departamento Principal',
        help_text='Indica se este é o departamento principal do funcionário'
    )
    
    # Datas
    start_date = models.DateField(
        auto_now_add=True,  # Corrigido: deve ser automático
        verbose_name='Data de Início'
    )
    
    end_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='Data de Término',
        help_text='Preencher quando a alocação for encerrada'
    )
    
    # Timestamps de auditoria
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Criado em'
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Atualizado em'
    )
    
    # Chaves Estrangeiras - CORRIGIDAS
    employee = models.ForeignKey(
        'employee.Employee',  
        on_delete=models.CASCADE,
        related_name='department_assignments',
        verbose_name='Funcionário'
    )
    
    department = models.ForeignKey(
        'department.Department',
        on_delete=models.CASCADE,
        related_name='employee_assignments',  
        verbose_name='Departamento'
    )
    
    class Meta:
        verbose_name = 'Alocação de Funcionário'
        verbose_name_plural = 'Alocações de Funcionários'
        
        unique_together = [['employee', 'department']]
        
        indexes = [
            models.Index(fields=['employee'], name='idx_emp_dept_employee'),
            models.Index(fields=['department'], name='idx_emp_dept_department'),
            models.Index(fields=['is_primary'], name='idx_emp_dept_primary'),
            models.Index(fields=['end_date'], name='idx_emp_dept_end_date'),
        ]
        
        # Ordenação padrão
        ordering = ['employee', '-is_primary', 'start_date']
    
    def __str__(self):
        return f"{self.employee} - {self.department} ({self.allocation_percentage}%)"
    
    def clean(self):
        """Validações adicionais"""
        from django.core.exceptions import ValidationError
        
        # 1. Validação do percentual
        if self.allocation_percentage <= 0 or self.allocation_percentage > 100:
            raise ValidationError({
                'allocation_percentage': 'Percentual de alocação deve ser entre 0 e 100%'
            })
        
        # 2. Validação de datas
        if self.end_date and self.start_date and self.end_date < self.start_date:
            raise ValidationError({
                'end_date': 'Data de término não pode ser anterior à data de início'
            })
        
        # 3. Validação: Apenas um departamento principal por funcionário
        if self.is_primary:
            existing_primary = EmployeeDepartment.objects.filter(
                employee=self.employee,
                is_primary=True,
                end_date__isnull=True  # Apenas alocações ativas
            ).exclude(pk=self.pk)
            
            if existing_primary.exists():
                raise ValidationError({
                    'is_primary': f'O funcionário {self.employee} já possui um departamento principal ativo'
                })
        
        # 4. Soma de percentuais não pode exceder 100% para alocações ativas
        if not self.end_date:  # Apenas alocações ativas
            total_percentage = EmployeeDepartment.objects.filter(
                employee=self.employee,
                end_date__isnull=True
            ).exclude(pk=self.pk).aggregate(
                total=models.Sum('allocation_percentage')
            )['total'] or 0
            
            if total_percentage + self.allocation_percentage > 100:
                raise ValidationError({
                    'allocation_percentage': f'Soma dos percentuais de alocação não pode exceder 100%. Atual: {total_percentage + self.allocation_percentage}%'
                })
    
    def save(self, *args, **kwargs):
        self.full_clean()  # Executa validações antes de salvar
        super().save(*args, **kwargs)
    
    @property
    def is_active(self):
        """Propriedade para verificar se a alocação está ativa"""
        return self.end_date is None
    
    @classmethod
    def get_active_allocations(cls, employee=None):
        """Retorna alocações ativas (sem data de término)"""
        queryset = cls.objects.filter(end_date__isnull=True)
        if employee:
            queryset = queryset.filter(employee=employee)
        return queryset