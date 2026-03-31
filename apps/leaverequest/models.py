from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta

class LeaveRequest(models.Model):
    """
    Solicitações de férias e ausências
    Gerencia requisições de afastamento dos funcionários
    """
    
    # Tipos de solicitação pré-definidos
    class LeaveType(models.TextChoices):
        VACATION = 'VACATION', 'Férias'
        SICK_LEAVE = 'SICK_LEAVE', 'Atestado Médico'
        PERSONAL = 'PERSONAL', 'Assuntos Pessoais'
        MATERNITY = 'MATERNITY', 'Licença Maternidade'
        PATERNITY = 'PATERNITY', 'Licença Paternidade'
        BEREAVEMENT = 'BEREAVEMENT', 'Luto'
        UNPAID = 'UNPAID', 'Licença Não Remunerada'
        OTHER = 'OTHER', 'Outros'
    
    # Status possíveis
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pendente'
        APPROVED = 'APPROVED', 'Aprovado'
        REJECTED = 'REJECTED', 'Rejeitado'
        CANCELLED = 'CANCELLED', 'Cancelado'
    
    # Campos obrigatórios
    leave_type = models.CharField(
        max_length=50,
        choices=LeaveType.choices,
        verbose_name='Tipo de Ausência'
    )
    
    start_date = models.DateField(
        verbose_name='Data de Início'
    )
    
    end_date = models.DateField(
        verbose_name='Data de Término'
    )
    
    days_requested = models.IntegerField(
        verbose_name='Dias Solicitados'
    )
    
    # Campos opcionais
    reason = models.TextField(
        null=True,
        blank=True,
        verbose_name='Motivo',
        help_text='Justificativa para a solicitação (obrigatório para alguns tipos)'
    )
    
    attachment = models.CharField(
        max_length=500,
        null=True,
        blank=True,
        verbose_name='Anexo',
        help_text='Caminho do arquivo anexado (ex: atestado médico)'
    )
    
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        verbose_name='Status'
    )
    
    rejection_reason = models.TextField(
        null=True,
        blank=True,
        verbose_name='Motivo da Rejeição',
        help_text='Preenchido quando a solicitação é rejeitada'
    )
    
    # Timestamps
    approved_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Aprovado em'
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Criado em'
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Atualizado em'
    )
    
    # Chaves estrangeiras - CORRIGIDAS
    employee = models.ForeignKey(
        'employee.Employee',
        on_delete=models.CASCADE,
        related_name='leave_requests',
        verbose_name='Funcionário'
    )
    
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_leave_requests',
        verbose_name='Aprovado por'
    )
    
    class Meta:
        verbose_name = 'Solicitação de Ausência'
        verbose_name_plural = 'Solicitações de Ausência'
        
        indexes = [
            models.Index(fields=['employee'], name='idx_leaverequest_employee'),
            models.Index(fields=['status'], name='idx_leaverequest_status'),
            models.Index(fields=['start_date', 'end_date'], name='idx_leaverequest_dates'),
            # Índices adicionais para otimização
            models.Index(fields=['leave_type'], name='idx_leaverequest_type'),
            models.Index(fields=['created_at'], name='idx_leaverequest_created'),
            models.Index(fields=['employee', 'status'], name='idx_leaverequest_emp_status'),
        ]
        
        # Ordenação padrão
        ordering = ['-created_at']
        
        # Permissões customizadas
        permissions = [
            ('can_approve_leaverequest', 'Pode aprovar solicitações de ausência'),
            ('can_view_all_leaverequests', 'Pode visualizar todas as solicitações'),
        ]
    
    def __str__(self):
        return f"{self.employee} - {self.get_leave_type_display()} ({self.start_date} a {self.end_date})"
    
    def clean(self):
        """Validações adicionais"""
        super().clean()
        
        # 1. Validação de datas
        if self.start_date and self.end_date:
            if self.end_date < self.start_date:
                raise ValidationError({
                    'end_date': 'Data de término não pode ser anterior à data de início'
                })
            
            # Verificar se a solicitação é para o futuro
            today = timezone.now().date()
            if self.start_date < today:
                raise ValidationError({
                    'start_date': 'Data de início não pode ser anterior à data atual'
                })
        
        # 2. Validação de dias solicitados
        if self.start_date and self.end_date:
            calculated_days = (self.end_date - self.start_date).days + 1
            if self.days_requested != calculated_days:
                raise ValidationError({
                    'days_requested': f'Número de dias solicitado ({self.days_requested}) não corresponde ao período ({calculated_days} dias)'
                })
        
        # 3. Validação para atestado médico
        if self.leave_type == self.LeaveType.SICK_LEAVE:
            if not self.attachment:
                raise ValidationError({
                    'attachment': 'Para atestado médico, é obrigatório anexar o documento'
                })
            if not self.reason:
                raise ValidationError({
                    'reason': 'Para atestado médico, é obrigatório informar o motivo'
                })
        
        # 4. Validação para férias (mínimo 5 dias, máximo 30)
        if self.leave_type == self.LeaveType.VACATION:
            if self.days_requested < 5:
                raise ValidationError({
                    'days_requested': 'Férias devem ter no mínimo 5 dias'
                })
            if self.days_requested > 30:
                raise ValidationError({
                    'days_requested': 'Férias não podem exceder 30 dias'
                })
        
        # 5. Validação para licenças maternidade/paternidade
        if self.leave_type in [self.LeaveType.MATERNITY, self.LeaveType.PATERNITY]:
            if self.days_requested > 180:  # 6 meses
                raise ValidationError({
                    'days_requested': 'Licença maternidade/paternidade não pode exceder 180 dias'
                })
        
        # 6. Validação de status
        if self.status == self.Status.APPROVED and not self.approved_at:
            raise ValidationError({
                'approved_at': 'Ao aprovar a solicitação, a data de aprovação é obrigatória'
            })
        
        if self.status == self.Status.REJECTED and not self.rejection_reason:
            raise ValidationError({
                'rejection_reason': 'Ao rejeitar a solicitação, é obrigatório informar o motivo'
            })
        
        # 7. Validação de sobreposição de solicitações
        if self.status != self.Status.REJECTED and self.status != self.Status.CANCELLED:
            overlapping = LeaveRequest.objects.filter(
                employee=self.employee,
                status__in=[self.Status.PENDING, self.Status.APPROVED],
                start_date__lte=self.end_date,
                end_date__gte=self.start_date
            ).exclude(pk=self.pk)
            
            if overlapping.exists():
                raise ValidationError(
                    'Já existe uma solicitação de ausência para este período'
                )
    
    def save(self, *args, **kwargs):
        """Valida antes de salvar e atualiza datas de aprovação"""
        # Atualiza approved_at quando status muda para APPROVED
        if self.status == self.Status.APPROVED and not self.approved_at:
            self.approved_at = timezone.now()
        
        # Limpa approved_at quando status não é APPROVED
        if self.status != self.Status.APPROVED:
            self.approved_at = None
        
        self.full_clean()  # Executa validações
        super().save(*args, **kwargs)
    
    def approve(self, approved_by_user):
        """Método utilitário para aprovar solicitação"""
        self.status = self.Status.APPROVED
        self.approved_by = approved_by_user
        self.approved_at = timezone.now()
        self.save()
    
    def reject(self, approved_by_user, reason):
        """Método utilitário para rejeitar solicitação"""
        self.status = self.Status.REJECTED
        self.approved_by = approved_by_user
        self.rejection_reason = reason
        self.approved_at = timezone.now()  # Data da rejeição
        self.save()
    
    def cancel(self):
        """Método utilitário para cancelar solicitação"""
        self.status = self.Status.CANCELLED
        self.save()
    
    @property
    def is_approved(self):
        """Verifica se a solicitação está aprovada"""
        return self.status == self.Status.APPROVED
    
    @property
    def is_pending(self):
        """Verifica se a solicitação está pendente"""
        return self.status == self.Status.PENDING
    
    @property
    def is_rejected(self):
        """Verifica se a solicitação foi rejeitada"""
        return self.status == self.Status.REJECTED
    
    @property
    def duration_days(self):
        """Retorna a duração em dias (alias para days_requested)"""
        return self.days_requested
    
    @property
    def is_active(self):
        """Verifica se a solicitação está ativa (aprovada e período futuro)"""
        if self.is_approved:
            today = timezone.now().date()
            return self.end_date >= today
        return False
    
    @property
    def is_in_progress(self):
        """Verifica se a solicitação está em andamento"""
        if self.is_approved:
            today = timezone.now().date()
            return self.start_date <= today <= self.end_date
        return False
    
    @classmethod
    def get_pending_requests(cls):
        """Retorna todas as solicitações pendentes"""
        return cls.objects.filter(status=cls.Status.PENDING)
    
    @classmethod
    def get_by_employee(cls, employee, status=None):
        """Retorna solicitações de um funcionário"""
        queryset = cls.objects.filter(employee=employee)
        if status:
            queryset = queryset.filter(status=status)
        return queryset
    
    @classmethod
    def get_upcoming(cls, days=30):
        """Retorna solicitações aprovadas nos próximos X dias"""
        today = timezone.now().date()
        future_date = today + timedelta(days=days)
        
        return cls.objects.filter(
            status=cls.Status.APPROVED,
            start_date__gte=today,
            start_date__lte=future_date
        ).order_by('start_date')