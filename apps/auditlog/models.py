from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError

class AuditLog(models.Model):
    """
    Log de auditoria do sistema
    Registra todas as ações importantes para rastreabilidade e compliance
    """
    
    # Tipos de ação pré-definidos
    class ActionType(models.TextChoices):
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
    
    # Campos obrigatórios
    action_type = models.CharField(
        max_length=20,
        choices=ActionType.choices,
        verbose_name='Tipo de Ação'
    )
    
    table_name = models.CharField(
        max_length=100,
        verbose_name='Nome da Tabela',
        help_text='Nome do modelo/tabela afetado'
    )
    
    # Campos opcionais
    record_id = models.IntegerField(
        null=True,
        blank=True,
        verbose_name='ID do Registro',
        help_text='ID do registro afetado (NULL para ações como login)'
    )
    
    old_data = models.JSONField(
        null=True,
        blank=True,
        verbose_name='Dados Anteriores',
        help_text='Snapshot dos dados antes da alteração'
    )
    
    new_data = models.JSONField(
        null=True,
        blank=True,
        verbose_name='Dados Novos',
        help_text='Snapshot dos dados após a alteração'
    )
    
    # Metadados da requisição
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name='Endereço IP',
        help_text='IP do usuário que realizou a ação'
    )
    
    user_agent = models.CharField(
        max_length=500,
        null=True,
        blank=True,
        verbose_name='User Agent',
        help_text='Informações do navegador/dispositivo'
    )
    
    session_id = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name='ID da Sessão',
        help_text='Identificador da sessão do usuário'
    )
    
    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Criado em'
    )
    
    # Chave estrangeira
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_logs',
        verbose_name='Usuário',
        help_text='Usuário que realizou a ação (NULL para ações anônimas)'
    )
    
    class Meta:
        verbose_name = 'Log de Auditoria'
        verbose_name_plural = 'Logs de Auditoria'
        
        indexes = [
            models.Index(fields=['user'], name='idx_auditlog_user'),
            models.Index(fields=['table_name'], name='idx_auditlog_table'),
            models.Index(fields=['action_type'], name='idx_auditlog_action'),
            # Índices adicionais para otimização
            models.Index(fields=['created_at'], name='idx_auditlog_created_at'),
            models.Index(fields=['table_name', 'record_id'], name='idx_auditlog_table_record'),
            models.Index(fields=['action_type', 'created_at'], name='idx_auditlog_action_date'),
        ]
        
        # Ordenação padrão (mais recentes primeiro)
        ordering = ['-created_at']
        
        # Permissões customizadas
        permissions = [
            ('can_view_audit_logs', 'Pode visualizar logs de auditoria'),
            ('can_export_audit_logs', 'Pode exportar logs de auditoria'),
        ]
    
    def __str__(self):
        user_info = f"Usuário {self.user}" if self.user else "Usuário anônimo"
        record_info = f" - {self.table_name}" + (f"/{self.record_id}" if self.record_id else "")
        return f"{self.created_at.strftime('%Y-%m-%d %H:%M:%S')} - {self.action_type}{record_info} - {user_info}"
    
    def clean(self):
        """Validações adicionais"""
        super().clean()
        
        # Validação para DELETE: old_data não pode ser nulo
        if self.action_type == 'DELETE' and self.old_data is None:
            raise ValidationError({
                'old_data': 'Para ações de exclusão, os dados antigos são obrigatórios'
            })
        
        # Validação para CREATE: new_data não pode ser nulo
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
        """Valida antes de salvar"""
        self.full_clean()
        super().save(*args, **kwargs)
    
    @classmethod
    def log_action(cls, user, action_type, table_name, record_id=None, 
                   old_data=None, new_data=None, request=None):
        """
        Método utilitário para registrar ações de forma simplificada
        
        Exemplo:
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
        
        # Extrair informações da request se fornecida
        if request:
            log_data['ip_address'] = cls.get_client_ip(request)
            log_data['user_agent'] = request.META.get('HTTP_USER_AGENT', '')[:500]
            log_data['session_id'] = request.session.session_key
        
        return cls.objects.create(**log_data)
    
    @staticmethod
    def get_client_ip(request):
        """Obtém o IP real do cliente considerando proxies"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    @classmethod
    def get_by_table(cls, table_name, record_id=None, limit=100):
        """Busca logs por tabela e opcionalmente por registro"""
        queryset = cls.objects.filter(table_name=table_name)
        if record_id is not None:
            queryset = queryset.filter(record_id=record_id)
        return queryset[:limit]
    
    @classmethod
    def get_by_user(cls, user, limit=100):
        """Busca logs por usuário"""
        return cls.objects.filter(user=user)[:limit]
    
    @classmethod
    def get_by_date_range(cls, start_date, end_date):
        """Busca logs em um intervalo de datas"""
        return cls.objects.filter(
            created_at__gte=start_date,
            created_at__lte=end_date
        ).order_by('created_at')
    
    @property
    def is_mutation(self):
        """Verifica se é uma ação de mutação (CREATE, UPDATE, DELETE)"""
        return self.action_type in ['CREATE', 'UPDATE', 'DELETE']
    
    @property
    def summary(self):
        """Retorna um resumo da ação"""
        if self.action_type == 'CREATE':
            return f"Criado registro em {self.table_name}"
        elif self.action_type == 'UPDATE':
            return f"Atualizado registro {self.record_id} em {self.table_name}"
        elif self.action_type == 'DELETE':
            return f"Excluído registro {self.record_id} de {self.table_name}"
        else:
            return f"{self.action_type} - {self.table_name}"