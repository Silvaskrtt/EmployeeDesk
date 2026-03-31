"""
Módulo de auditoria do sistema.

Este módulo fornece a estrutura para registrar todas as ações importantes
no sistema, garantindo rastreabilidade completa para fins de compliance,
investigação de incidentes e auditoria interna.
"""

# Imports de terceiros
from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError


class AuditLog(models.Model):
    """
    Modelo responsável pelo registro de auditoria do sistema.

    Esta classe implementa um sistema completo de logging para todas as
    operações críticas, capturando quem fez o quê, quando, de onde e
    quais dados foram alterados. Essencial para conformidade com normas
    como LGPD, SOX e ISO 27001.
    """

    # -------------------------------------------------------------------------
    #  CONSTANTES DA CLASSE
    # -------------------------------------------------------------------------

    class ActionType(models.TextChoices):
        """
        Enumeração que define os tipos de ações auditáveis no sistema.

        Utiliza TextChoices do Django para garantir consistência nos valores
        armazenados e facilitar a manutenção. Cada ação representa uma
        operação distinta que pode ser registrada para auditoria.
        """
        CREATE = 'CREATE', 'Criação'
        UPDATE = 'UPDATE', 'Atualização'
        DELETE = 'DELETE', 'Exclusão'
        VIEW = 'VIEW', 'Visualização'
        LOGIN = 'LOGIN', 'Login'
        LOGOUT = 'LOGOUT', 'Logout'
        EXPORT = 'EXPORT', 'Exportação'
        IMPORT = 'IMPORT', 'Importação'
        APPROVE = 'APPROVE', 'Aprovação'
        REJECT = 'REJECT', 'Rejeição'

    # -------------------------------------------------------------------------
    #  CAMPOS OBRIGATÓRIOS
    # -------------------------------------------------------------------------

    action_type = models.CharField(
        max_length=20,
        choices=ActionType.choices,
        verbose_name='Tipo de Ação'
    )
    """Tipo da ação realizada, selecionado a partir do enum ActionType."""

    table_name = models.CharField(
        max_length=100,
        verbose_name='Nome da Tabela',
        help_text='Nome do modelo/tabela afetado'
    )
    """
    Nome da tabela ou modelo Django que foi alvo da ação.
    Facilita consultas e filtragem por entidade específica.
    """

    # -------------------------------------------------------------------------
    #  CAMPOS OPCIONAIS
    # -------------------------------------------------------------------------

    record_id = models.IntegerField(
        null=True,
        blank=True,
        verbose_name='ID do Registro',
        help_text='ID do registro afetado (NULL para ações como login)'
    )
    """
    Identificador único do registro afetado.
    Pode ser NULL para ações que não envolvem um registro específico,
    como login/logout ou exportações em massa.
    """

    old_data = models.JSONField(
        null=True,
        blank=True,
        verbose_name='Dados Anteriores',
        help_text='Snapshot dos dados antes da alteração'
    )
    """
    Snapshot dos dados antes da modificação, armazenado em formato JSON.
    Permite reconstruir o estado anterior em caso de necessidade de rollback
    ou investigação de alterações indevidas.
    """

    new_data = models.JSONField(
        null=True,
        blank=True,
        verbose_name='Dados Novos',
        help_text='Snapshot dos dados após a alteração'
    )
    """
    Snapshot dos dados após a modificação, armazenado em formato JSON.
    Complementa o old_data para fornecer visibilidade completa das alterações.
    """

    # -------------------------------------------------------------------------
    #  METADADOS DA REQUISIÇÃO
    # -------------------------------------------------------------------------

    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name='Endereço IP',
        help_text='IP do usuário que realizou a ação'
    )
    """
    Endereço IP do cliente que realizou a ação.
    Suporta tanto IPv4 quanto IPv6 através do GenericIPAddressField.
    """

    user_agent = models.CharField(
        max_length=500,
        null=True,
        blank=True,
        verbose_name='User Agent',
        help_text='Informações do navegador/dispositivo'
    )
    """
    String completa do User Agent HTTP, fornecendo informações sobre
    navegador, sistema operacional e dispositivo utilizado.
    """

    session_id = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name='ID da Sessão',
        help_text='Identificador da sessão do usuário'
    )
    """
    Identificador único da sessão HTTP do usuário.
    Permite rastrear todas as ações realizadas em uma mesma sessão de navegação.
    """

    # -------------------------------------------------------------------------
    #  TIMESTAMPS
    # -------------------------------------------------------------------------

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Criado em'
    )
    """
    Data e hora exata do registro do log.
    Auto-populado no momento da criação para garantir precisão temporal.
    """

    # -------------------------------------------------------------------------
    #  CHAVES ESTRANGEIRAS
    # -------------------------------------------------------------------------

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_logs',
        verbose_name='Usuário',
        help_text='Usuário que realizou a ação (NULL para ações anônimas)'
    )
    """
    Usuário autenticado que realizou a ação.
    SET_NULL preserva o histórico mesmo se o usuário for removido do sistema,
    mantendo a integridade da trilha de auditoria.
    """

    # -------------------------------------------------------------------------
    #  CONFIGURAÇÕES DO MODELO
    # -------------------------------------------------------------------------

    class Meta:
        """Configurações de metadados do modelo AuditLog."""
        verbose_name = 'Log de Auditoria'
        verbose_name_plural = 'Logs de Auditoria'

        # Índices para otimização de consultas de auditoria
        indexes = [
            models.Index(fields=['user'], name='idx_auditlog_user'),
            models.Index(fields=['table_name'], name='idx_auditlog_table'),
            models.Index(fields=['action_type'], name='idx_auditlog_action'),
            models.Index(fields=['created_at'], name='idx_auditlog_created_at'),
            models.Index(fields=['table_name', 'record_id'], name='idx_auditlog_table_record'),
            models.Index(fields=['action_type', 'created_at'], name='idx_auditlog_action_date'),
        ]

        # Ordenação padrão - logs mais recentes primeiro
        ordering = ['-created_at']

        # Permissões customizadas para controle de acesso granular
        permissions = [
            ('can_view_audit_logs', 'Pode visualizar logs de auditoria'),
            ('can_export_audit_logs', 'Pode exportar logs de auditoria'),
        ]

    # -------------------------------------------------------------------------
    #  MÉTODOS PÚBLICOS
    # -------------------------------------------------------------------------

    def __str__(self):
        """
        Representação em string do objeto para exibição no admin e logs.

        Returns:
            str: Formato padrão: "DATA - AÇÃO - TABELA/ID - USUÁRIO"
        """
        user_info = f"Usuário {self.user}" if self.user else "Usuário anônimo"
        record_info = f" - {self.table_name}" + (f"/{self.record_id}" if self.record_id else "")
        return f"{self.created_at.strftime('%Y-%m-%d %H:%M:%S')} - {self.action_type}{record_info} - {user_info}"

    def clean(self):
        """
        Realiza validações de negócio específicas para o log de auditoria.

        Garante que os dados estejam consistentes com o tipo de ação registrada,
        evitando logs inconsistentes que poderiam comprometer a confiabilidade
        da trilha de auditoria.

        Raises:
            ValidationError: Quando as regras de negócio não são satisfeitas.
        """
        super().clean()

        # Validação para DELETE: old_data é obrigatório
        if self.action_type == 'DELETE' and self.old_data is None:
            raise ValidationError({
                'old_data': 'Para ações de exclusão, os dados antigos são obrigatórios'
            })

        # Validação para CREATE: new_data é obrigatório
        if self.action_type == 'CREATE' and self.new_data is None:
            raise ValidationError({
                'new_data': 'Para ações de criação, os novos dados são obrigatórios'
            })

        # Validação para UPDATE: ambos old_data e new_data são obrigatórios
        if self.action_type == 'UPDATE':
            if self.old_data is None:
                raise ValidationError({
                    'old_data': 'Para ações de atualização, os dados antigos são obrigatórios'
                })
            if self.new_data is None:
                raise ValidationError({
                    'new_data': 'Para ações de atualização, os novos dados são obrigatórios'
                })

    def save(self, *args, **kwargs):
        """
        Sobrescreve o método save para garantir validações antes da persistência.

        Executa a validação completa do modelo antes de salvar, garantindo
        a integridade e consistência dos dados de auditoria.
        """
        self.full_clean()
        super().save(*args, **kwargs)

    # -------------------------------------------------------------------------
    #  MÉTODOS DE CLASSE (FACADES)
    # -------------------------------------------------------------------------

    @classmethod
    def log_action(cls, user, action_type, table_name, record_id=None,
                   old_data=None, new_data=None, request=None):
        """
        Método utilitário para registrar ações de forma simplificada.

        Este método encapsula toda a complexidade de criação de um log,
        extraindo automaticamente informações da request quando disponível.
        Deve ser utilizado como interface principal para registro de auditoria.

        Args:
            user (User): Usuário que realizou a ação.
            action_type (str): Tipo de ação (valor do enum ActionType).
            table_name (str): Nome da tabela/modelo afetado.
            record_id (int, optional): ID do registro afetado.
            old_data (dict, optional): Snapshot dos dados anteriores.
            new_data (dict, optional): Snapshot dos novos dados.
            request (HttpRequest, optional): Objeto request para extrair metadados.

        Returns:
            AuditLog: Instância do log recém-criado.

        Example:
            AuditLog.log_action(
                user=request.user,
                action_type=AuditLog.ActionType.UPDATE,
                table_name='employee',
                record_id=employee.id,
                old_data={'name': 'Old Name'},
                new_data={'name': 'New Name'},
                request=request
            )
        """
        log_data = {
            'user': user,
            'action_type': action_type,
            'table_name': table_name,
            'record_id': record_id,
            'old_data': old_data,
            'new_data': new_data,
        }

        # Extrai informações da request se fornecida
        if request:
            log_data['ip_address'] = cls.get_client_ip(request)
            log_data['user_agent'] = request.META.get('HTTP_USER_AGENT', '')[:500]
            log_data['session_id'] = request.session.session_key

        return cls.objects.create(**log_data)

    @staticmethod
    def get_client_ip(request):
        """
        Obtém o endereço IP real do cliente considerando proxies reversos.

        Verifica o cabeçalho HTTP_X_FORWARDED_FOR para casos onde o sistema
        está atrás de load balancers ou proxies, garantindo a captura do
        IP original do cliente.

        Args:
            request (HttpRequest): Objeto request do Django.

        Returns:
            str: Endereço IP real do cliente.
        """
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            # Em casos de múltiplos proxies, o primeiro é o IP do cliente
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

    @classmethod
    def get_by_table(cls, table_name, record_id=None, limit=100):
        """
        Busca logs de auditoria filtrados por tabela e opcionalmente por registro.

        Método de conveniência para consultas frequentes que precisam
        investigar alterações em uma entidade específica.

        Args:
            table_name (str): Nome da tabela/modelo a ser filtrado.
            record_id (int, optional): ID do registro para filtrar.
            limit (int, optional): Limite máximo de registros retornados.

        Returns:
            QuerySet: QuerySet com os logs filtrados, limitados pelo parâmetro.
        """
        queryset = cls.objects.filter(table_name=table_name)
        if record_id is not None:
            queryset = queryset.filter(record_id=record_id)
        return queryset[:limit]

    @classmethod
    def get_by_user(cls, user, limit=100):
        """
        Busca logs de auditoria filtrados por um usuário específico.

        Útil para investigar o histórico completo de ações de um determinado
        usuário no sistema.

        Args:
            user (User): Usuário para filtrar os logs.
            limit (int, optional): Limite máximo de registros retornados.

        Returns:
            QuerySet: QuerySet com os logs do usuário, ordenados do mais recente.
        """
        return cls.objects.filter(user=user)[:limit]

    @classmethod
    def get_by_date_range(cls, start_date, end_date):
        """
        Busca logs de auditoria em um intervalo de datas específico.

        Método essencial para relatórios de auditoria e investigações
        temporais, permitindo analisar atividades em períodos determinados.

        Args:
            start_date (datetime): Data e hora inicial do intervalo.
            end_date (datetime): Data e hora final do intervalo.

        Returns:
            QuerySet: QuerySet com os logs no intervalo, ordenados cronologicamente.
        """
        return cls.objects.filter(
            created_at__gte=start_date,
            created_at__lte=end_date
        ).order_by('created_at')

    # -------------------------------------------------------------------------
    #  PROPRIEDADES COMPUTADAS
    # -------------------------------------------------------------------------

    @property
    def is_mutation(self):
        """
        Verifica se a ação registrada é uma operação de mutação de dados.

        Identifica ações que modificaram o estado dos dados no sistema,
        útil para filtros que separam operações de consulta de operações
        que alteram o banco de dados.

        Returns:
            bool: True para CREATE, UPDATE e DELETE, False para outras ações.
        """
        return self.action_type in ['CREATE', 'UPDATE', 'DELETE']

    @property
    def summary(self):
        """
        Retorna um resumo legível da ação registrada.

        Fornece uma descrição textual simplificada da ação, útil para
        exibição em interfaces de usuário e relatórios de auditoria.

        Returns:
            str: Descrição resumida da ação realizada.
        """
        if self.action_type == 'CREATE':
            return f"Criado registro em {self.table_name}"
        elif self.action_type == 'UPDATE':
            return f"Atualizado registro {self.record_id} em {self.table_name}"
        elif self.action_type == 'DELETE':
            return f"Excluído registro {self.record_id} de {self.table_name}"
        else:
            return f"{self.action_type} - {self.table_name}"