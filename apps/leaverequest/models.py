"""
Módulo de gerenciamento de solicitações de ausência.

Este módulo fornece a estrutura para gerenciar solicitações de férias,
atestados médicos e demais tipos de afastamento dos funcionários,
incluindo fluxo de aprovação e validações de negócio.
"""

# Imports de terceiros
from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta


class LeaveRequest(models.Model):
    """
    Modelo responsável pelo gerenciamento de solicitações de ausência.

    Esta classe representa o processo de solicitação de afastamento dos
    funcionários, desde a requisição inicial até a aprovação/rejeição,
    garantindo o cumprimento das políticas internas e legislação trabalhista.
    Implementa fluxo de aprovação completo com auditoria.
    """

    # -------------------------------------------------------------------------
    #  CONSTANTES DA CLASSE
    # -------------------------------------------------------------------------

    class LeaveType(models.TextChoices):
        """
        Enumeração que define os tipos de ausência permitidos.

        Cada tipo possui regras específicas de validação, documentação
        necessária e limites de dias conforme políticas da empresa e
        legislação trabalhista brasileira.
        """
        VACATION = 'VACATION', 'Férias'
        SICK_LEAVE = 'SICK_LEAVE', 'Atestado Médico'
        PERSONAL = 'PERSONAL', 'Assuntos Pessoais'
        MATERNITY = 'MATERNITY', 'Licença Maternidade'
        PATERNITY = 'PATERNITY', 'Licença Paternidade'
        BEREAVEMENT = 'BEREAVEMENT', 'Luto'
        UNPAID = 'UNPAID', 'Licença Não Remunerada'
        OTHER = 'OTHER', 'Outros'

    class Status(models.TextChoices):
        """
        Enumeração que define os estados do fluxo de aprovação.

        Representa o ciclo de vida completo da solicitação, desde a criação
        até a decisão final ou cancelamento.
        """
        PENDING = 'PENDING', 'Pendente'
        APPROVED = 'APPROVED', 'Aprovado'
        REJECTED = 'REJECTED', 'Rejeitado'
        CANCELLED = 'CANCELLED', 'Cancelado'

    # -------------------------------------------------------------------------
    #  CAMPOS OBRIGATÓRIOS
    # -------------------------------------------------------------------------

    leave_type = models.CharField(
        max_length=50,
        choices=LeaveType.choices,
        verbose_name='Tipo de Ausência'
    )
    """Tipo de ausência solicitada, selecionado a partir do enum LeaveType."""

    start_date = models.DateField(
        verbose_name='Data de Início'
    )
    """
    Data de início do período de ausência.
    Deve ser uma data futura no momento da solicitação.
    """

    end_date = models.DateField(
        verbose_name='Data de Término'
    )
    """
    Data de término do período de ausência.
    Não pode ser anterior à data de início.
    """

    days_requested = models.IntegerField(
        verbose_name='Dias Solicitados'
    )
    """
    Número total de dias úteis/calendário solicitados.
    Utilizado para cálculos de saldo e relatórios.
    """

    # -------------------------------------------------------------------------
    #  CAMPOS OPCIONAIS
    # -------------------------------------------------------------------------

    reason = models.TextField(
        null=True,
        blank=True,
        verbose_name='Motivo',
        help_text='Justificativa para a solicitação (obrigatório para alguns tipos)'
    )
    """
    Justificativa detalhada da solicitação.
    Obrigatório para tipos específicos como atestado médico.
    """

    attachment = models.CharField(
        max_length=500,
        null=True,
        blank=True,
        verbose_name='Anexo',
        help_text='Caminho do arquivo anexado (ex: atestado médico)'
    )
    """
    Caminho do arquivo anexado à solicitação.
    Utilizado para documentos comprobatórios como atestados médicos.
    """

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        verbose_name='Status'
    )
    """
    Status atual da solicitação no fluxo de aprovação.
    Padrão é PENDING para novas solicitações.
    """

    rejection_reason = models.TextField(
        null=True,
        blank=True,
        verbose_name='Motivo da Rejeição',
        help_text='Preenchido quando a solicitação é rejeitada'
    )
    """
    Motivo detalhado da rejeição, quando aplicável.
    Obrigatório para solicitações rejeitadas, garantindo transparência.
    """

    # -------------------------------------------------------------------------
    #  TIMESTAMPS
    # -------------------------------------------------------------------------

    approved_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Aprovado em'
    )
    """
    Data e hora da aprovação ou rejeição da solicitação.
    Permite auditoria do tempo de resposta do fluxo de aprovação.
    """

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Criado em'
    )
    """Timestamp de criação da solicitação no sistema."""

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Atualizado em'
    )
    """Timestamp da última atualização da solicitação."""

    # -------------------------------------------------------------------------
    #  CHAVES ESTRANGEIRAS
    # -------------------------------------------------------------------------

    employee = models.ForeignKey(
        'employee.Employee',
        on_delete=models.CASCADE,
        related_name='leave_requests',
        verbose_name='Funcionário'
    )
    """
    Funcionário que está solicitando a ausência.
    CASCADE garante que solicitações sejam removidas ao excluir o funcionário.
    """

    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_leave_requests',
        verbose_name='Aprovado por'
    )
    """
    Usuário responsável pela aprovação ou rejeição da solicitação.
    SET_NULL mantém o histórico mesmo se o aprovador for removido.
    """

    # -------------------------------------------------------------------------
    #  CONFIGURAÇÕES DO MODELO
    # -------------------------------------------------------------------------

    class Meta:
        """Configurações de metadados do modelo LeaveRequest."""
        verbose_name = 'Solicitação de Ausência'
        verbose_name_plural = 'Solicitações de Ausência'

        # Índices para otimização de consultas frequentes
        indexes = [
            models.Index(fields=['employee'], name='idx_leaverequest_employee'),
            models.Index(fields=['status'], name='idx_leaverequest_status'),
            models.Index(fields=['start_date', 'end_date'], name='idx_leaverequest_dates'),
            models.Index(fields=['leave_type'], name='idx_leaverequest_type'),
            models.Index(fields=['created_at'], name='idx_leaverequest_created'),
            models.Index(fields=['employee', 'status'], name='idx_leaverequest_emp_status'),
        ]

        # Ordenação padrão - solicitações mais recentes primeiro
        ordering = ['-created_at']

        # Permissões customizadas para controle de acesso granular
        permissions = [
            ('can_approve_leaverequest', 'Pode aprovar solicitações de ausência'),
            ('can_view_all_leaverequests', 'Pode visualizar todas as solicitações'),
        ]

    # -------------------------------------------------------------------------
    #  MÉTODOS PÚBLICOS
    # -------------------------------------------------------------------------

    def __str__(self):
        """
        Representação em string do objeto para exibição no admin e logs.

        Returns:
            str: Formato padrão: "FUNCIONÁRIO - TIPO (DATA_INÍCIO a DATA_FIM)"
        """
        return f"{self.employee} - {self.get_leave_type_display()} ({self.start_date} a {self.end_date})"

    def clean(self):
        """
        Realiza validações de negócio específicas para solicitações de ausência.

        Este método implementa todas as regras de negócio relacionadas a
        solicitações de afastamento, incluindo validações de datas,
        limites legais, documentação obrigatória e prevenção de conflitos
        de período.

        Raises:
            ValidationError: Quando alguma das regras de negócio não é satisfeita.
        """
        super().clean()

        # Validação 1: Integridade das datas
        if self.start_date and self.end_date:
            # Validação 1.1: Data de término não pode ser anterior à data de início
            if self.end_date < self.start_date:
                raise ValidationError({
                    'end_date': 'Data de término não pode ser anterior à data de início'
                })

            # Validação 1.2: Data de início deve ser futura
            today = timezone.now().date()
            if self.start_date < today:
                raise ValidationError({
                    'start_date': 'Data de início não pode ser anterior à data atual'
                })

        # Validação 2: Consistência dos dias solicitados
        if self.start_date and self.end_date:
            calculated_days = (self.end_date - self.start_date).days + 1
            if self.days_requested != calculated_days:
                raise ValidationError({
                    'days_requested': f'Número de dias solicitado ({self.days_requested}) não corresponde ao período ({calculated_days} dias)'
                })

        # Validação 3: Regras específicas para atestado médico
        if self.leave_type == self.LeaveType.SICK_LEAVE:
            if not self.attachment:
                raise ValidationError({
                    'attachment': 'Para atestado médico, é obrigatório anexar o documento'
                })
            if not self.reason:
                raise ValidationError({
                    'reason': 'Para atestado médico, é obrigatório informar o motivo'
                })

        # Validação 4: Regras específicas para férias
        if self.leave_type == self.LeaveType.VACATION:
            if self.days_requested < 5:
                raise ValidationError({
                    'days_requested': 'Férias devem ter no mínimo 5 dias'
                })
            if self.days_requested > 30:
                raise ValidationError({
                    'days_requested': 'Férias não podem exceder 30 dias'
                })

        # Validação 5: Regras para licenças maternidade/paternidade
        if self.leave_type in [self.LeaveType.MATERNITY, self.LeaveType.PATERNITY]:
            if self.days_requested > 180:  # 6 meses conforme legislação
                raise ValidationError({
                    'days_requested': 'Licença maternidade/paternidade não pode exceder 180 dias'
                })

        # Validação 6: Consistência do fluxo de aprovação
        if self.status == self.Status.APPROVED and not self.approved_at:
            raise ValidationError({
                'approved_at': 'Ao aprovar a solicitação, a data de aprovação é obrigatória'
            })

        if self.status == self.Status.REJECTED and not self.rejection_reason:
            raise ValidationError({
                'rejection_reason': 'Ao rejeitar a solicitação, é obrigatório informar o motivo'
            })

        # Validação 7: Prevenção de sobreposição de períodos
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
        """
        Sobrescreve o método save para gerenciar datas de aprovação e validações.

        Gerencia automaticamente o campo approved_at com base no status,
        garantindo que a data de aprovação seja registrada corretamente
        quando o status é alterado para APPROVED.
        """
        # Atualiza approved_at quando status muda para APPROVED
        if self.status == self.Status.APPROVED and not self.approved_at:
            self.approved_at = timezone.now()

        # Limpa approved_at quando status não é APPROVED
        if self.status != self.Status.APPROVED:
            self.approved_at = None

        self.full_clean()
        super().save(*args, **kwargs)

    def approve(self, approved_by_user):
        """
        Método utilitário para aprovar uma solicitação.

        Encapsula a lógica de aprovação, definindo status, aprovador e
        data de aprovação em uma única operação.

        Args:
            approved_by_user (User): Usuário que está realizando a aprovação.
        """
        self.status = self.Status.APPROVED
        self.approved_by = approved_by_user
        self.approved_at = timezone.now()
        self.save()

    def reject(self, approved_by_user, reason):
        """
        Método utilitário para rejeitar uma solicitação com justificativa.

        Encapsula a lógica de rejeição, definindo status, aprovador,
        motivo da rejeição e data de decisão.

        Args:
            approved_by_user (User): Usuário que está realizando a rejeição.
            reason (str): Motivo detalhado da rejeição.
        """
        self.status = self.Status.REJECTED
        self.approved_by = approved_by_user
        self.rejection_reason = reason
        self.approved_at = timezone.now()  # Data da rejeição para auditoria
        self.save()

    def cancel(self):
        """
        Método utilitário para cancelar uma solicitação.

        Permite que o funcionário ou gestor cancele uma solicitação
        que ainda não foi aprovada ou que já foi aprovada mas ainda
        não iniciou.
        """
        self.status = self.Status.CANCELLED
        self.save()

    # -------------------------------------------------------------------------
    #  PROPRIEDADES COMPUTADAS
    # -------------------------------------------------------------------------

    @property
    def is_approved(self):
        """
        Verifica se a solicitação está aprovada.

        Returns:
            bool: True se status for APPROVED, False caso contrário.
        """
        return self.status == self.Status.APPROVED

    @property
    def is_pending(self):
        """
        Verifica se a solicitação está pendente de aprovação.

        Returns:
            bool: True se status for PENDING, False caso contrário.
        """
        return self.status == self.Status.PENDING

    @property
    def is_rejected(self):
        """
        Verifica se a solicitação foi rejeitada.

        Returns:
            bool: True se status for REJECTED, False caso contrário.
        """
        return self.status == self.Status.REJECTED

    @property
    def duration_days(self):
        """
        Retorna a duração em dias (alias para days_requested).

        Mantido para compatibilidade com interfaces existentes que esperam
        este nome de propriedade.

        Returns:
            int: Número de dias solicitados.
        """
        return self.days_requested

    @property
    def is_active(self):
        """
        Verifica se a solicitação está ativa (aprovada e período futuro/presente).

        Utilizado para identificar solicitações que impactam o presente
        ou futuro próximo.

        Returns:
            bool: True se aprovada e data de término não passada.
        """
        if self.is_approved:
            today = timezone.now().date()
            return self.end_date >= today
        return False

    @property
    def is_in_progress(self):
        """
        Verifica se a solicitação está em andamento no momento atual.

        Utilizado para identificar funcionários que estão atualmente
        em período de ausência.

        Returns:
            bool: True se aprovada e data atual está entre início e fim.
        """
        if self.is_approved:
            today = timezone.now().date()
            return self.start_date <= today <= self.end_date
        return False

    # -------------------------------------------------------------------------
    #  MÉTODOS DE CLASSE (FACADES)
    # -------------------------------------------------------------------------

    @classmethod
    def get_pending_requests(cls):
        """
        Retorna todas as solicitações pendentes de aprovação.

        Método de conveniência para listas de trabalho e dashboards
        de gestores que precisam visualizar solicitações aguardando decisão.

        Returns:
            QuerySet: QuerySet com todas as solicitações com status PENDING.
        """
        return cls.objects.filter(status=cls.Status.PENDING)

    @classmethod
    def get_by_employee(cls, employee, status=None):
        """
        Retorna solicitações de um funcionário específico.

        Permite filtrar opcionalmente por status para consultas mais
        específicas, como visualizar apenas solicitações pendentes do
        funcionário.

        Args:
            employee (Employee): Funcionário para filtrar.
            status (str, optional): Status para filtrar.

        Returns:
            QuerySet: QuerySet com as solicitações do funcionário.
        """
        queryset = cls.objects.filter(employee=employee)
        if status:
            queryset = queryset.filter(status=status)
        return queryset

    @classmethod
    def get_upcoming(cls, days=30):
        """
        Retorna solicitações aprovadas que começam nos próximos X dias.

        Útil para planejamento de recursos, notificações antecipadas
        e preparação para ausências programadas.

        Args:
            days (int): Número de dias para considerar como horizonte de busca.
                       Padrão é 30 dias.

        Returns:
            QuerySet: QuerySet ordenada por data de início com solicitações
                      aprovadas que começam no período informado.
        """
        today = timezone.now().date()
        future_date = today + timedelta(days=days)

        return cls.objects.filter(
            status=cls.Status.APPROVED,
            start_date__gte=today,
            start_date__lte=future_date
        ).order_by('start_date')