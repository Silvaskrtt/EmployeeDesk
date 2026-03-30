from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


# =============================================================================
# MODELO DE PERFIL DE ACESSO
# =============================================================================

class AccessProfile(models.Model):
    """
    Modelo que representa um perfil de acesso e suas permissões no sistema.
    
    Este modelo implementa o controle de acesso baseado em perfis (RBAC - Role-Based
    Access Control), permitindo definir diferentes níveis de permissão para grupos
    de usuários. Cada perfil contém um conjunto de permissões estruturadas por
    módulos e ações do sistema.
    
    Attributes:
        name (CharField): Nome único do perfil (ex: 'Administrador', 'Usuário Comum').
        description (TextField): Descrição detalhada do propósito e escopo do perfil.
        permissions (JSONField): Estrutura JSON contendo as permissões do perfil,
                                  organizadas por módulo e ações permitidas.
        is_system (BooleanField): Flag que identifica perfis nativos do sistema.
        created_at (DateTimeField): Data/hora de criação do registro.
        updated_at (DateTimeField): Data/hora da última atualização.
    
    Meta:
        verbose_name: Nome singular para interface administrativa.
        verbose_name_plural: Nome plural para interface administrativa.
        ordering: Ordenação padrão por nome do perfil.
    
    Note:
        Perfis marcados como is_system=True são considerados críticos e não
        devem ser removidos ou ter suas permissões básicas alteradas, pois
        são fundamentais para o funcionamento do sistema.
    
    Example:
        >>> perfil_admin = AccessProfile.objects.create(
        ...     name='Administrador',
        ...     permissions={
        ...         'employees': ['add', 'change', 'delete', 'view'],
        ...         'departments': ['add', 'change', 'delete', 'view']
        ...     }
        ... )
        >>> perfil_admin.has_permission('employees', 'add')
        True
    """
    
    # -------------------------------------------------------------------------
    # CAMPOS DO MODELO
    # -------------------------------------------------------------------------
    
    # Nome do perfil de acesso (ex: Administrador, Gestor, Operador, Consultor)
    # unique=True garante que não haja perfis duplicados no sistema
    name = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='Nome do Perfil'
    )
    
    # Descrição detalhada do perfil, explicando quais tipos de usuários
    # devem recebê-lo e quais são suas responsabilidades no sistema
    description = models.TextField(
        blank=True,
        verbose_name='Descrição'
    )
    
    # -------------------------------------------------------------------------
    # PERMISSÕES (ESTRUTURA JSON)
    # -------------------------------------------------------------------------
    
    # Estrutura JSON que armazena as permissões do perfil
    # Formato esperado:
    # {
    #     "modulo1": ["acao1", "acao2", "acao3"],
    #     "modulo2": ["acao1", "acao2"],
    #     ...
    # }
    #
    # Exemplo:
    # {
    #     "employees": ["add", "change", "delete", "view"],
    #     "departments": ["view"],
    #     "reports": ["generate", "export"]
    # }
    #
    # Campo opcional (blank=True, null=True) permite perfis sem permissões
    permissions = models.JSONField(
        blank=True,
        null=True,
        verbose_name='Permissões'
    )
    
    # -------------------------------------------------------------------------
    # FLAGS DE CONTROLE
    # -------------------------------------------------------------------------
    
    # Flag que identifica se este é um perfil nativo do sistema
    # Perfis de sistema devem ser tratados como imutáveis ou com restrições
    # especiais de edição/exclusão
    is_system = models.BooleanField(
        default=False,
        verbose_name='Perfil do Sistema'
    )
    
    # -------------------------------------------------------------------------
    # CAMPOS DE AUDITORIA
    # -------------------------------------------------------------------------
    
    # Data/hora de criação do registro (preenchido automaticamente)
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Criado em'
    )
    
    # Data/hora da última atualização do registro (atualizado automaticamente)
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Atualizado em'
    )
    
    # -------------------------------------------------------------------------
    # MÉTODOS PÚBLICOS
    # -------------------------------------------------------------------------
    
    def __str__(self):
        """
        Representação em string do objeto AccessProfile.
        
        Utilizada em interfaces administrativas, dropdowns, selects e logs
        para identificação rápida do perfil de acesso.
        
        Returns:
            str: Nome do perfil.
        
        Example:
            >>> profile.__str__()
            'Administrador'
            >>> AccessProfile.objects.get(name='Consultor').__str__()
            'Consultor'
        """
        return self.name
    
    # -------------------------------------------------------------------------
    # MÉTODOS DE VERIFICAÇÃO DE PERMISSÕES
    # -------------------------------------------------------------------------
    
    def has_permission(self, module, action):
        """
        Verifica se o perfil possui uma permissão específica.
        
        Este método implementa a lógica de verificação de acesso, consultando
        a estrutura de permissões JSON para determinar se a ação solicitada
        está autorizada para o módulo especificado.
        
        Args:
            module (str): Nome do módulo/sistema onde a ação será executada.
                          Exemplos: 'employees', 'departments', 'reports', 'settings'
            action (str): Nome da ação/permissão a ser verificada.
                          Exemplos: 'add', 'change', 'delete', 'view', 'generate'
        
        Returns:
            bool: True se o perfil possui a permissão solicitada,
                  False caso contrário.
        
        Example:
            >>> # Verifica se o perfil pode adicionar funcionários
            >>> perfil_admin.has_permission('employees', 'add')
            True
            
            >>> # Verifica se o perfil pode visualizar relatórios
            >>> perfil_consultor.has_permission('reports', 'view')
            True
            
            >>> # Verifica se o perfil pode excluir departamentos
            >>> perfil_operador.has_permission('departments', 'delete')
            False
        
        Note:
            - Se o perfil não tiver permissões definidas (permissions=None ou vazio),
              o método retorna False para todas as verificações.
            - A estrutura de permissões deve ser mantida consistente com as
              definições de módulos e ações do sistema.
            - Este método pode ser utilizado em views, templates e serviços
              para controle de acesso granular.
        
        Example de uso em template Django:
            {% if request.user.profile.has_permission 'employees' 'add' %}
                <a href="{% url 'employee_create' %}">Adicionar Funcionário</a>
            {% endif %}
        """
        # Verifica se existe estrutura de permissões definida
        if not self.permissions:
            return False
        
        # Busca as permissões do módulo especificado
        # Retorna lista vazia se módulo não existir na estrutura
        module_perms = self.permissions.get(module, [])
        
        # Verifica se a ação solicitada está na lista de permissões do módulo
        return action in module_perms
    
    # -------------------------------------------------------------------------
    # PROPRIEDADES (PROPERTIES) - SUGESTÕES DE MELHORIA
    # -------------------------------------------------------------------------
    # 
    # As seguintes propriedades poderiam ser adicionadas em versões futuras:
    #
    # @property
    # def is_system_protected(self):
    #     """Indica se o perfil é de sistema e deve ser protegido."""
    #     return self.is_system
    #
    # @property
    # def permission_summary(self):
    #     """Retorna um resumo legível das permissões do perfil."""
    #     if not self.permissions:
    #         return "Nenhuma permissão definida"
    #     modules = list(self.permissions.keys())
    #     return f"{len(modules)} módulo(s) configurado(s)"
    #
    # @property
    # def has_any_permission(self):
    #     """Verifica se o perfil possui pelo menos uma permissão."""
    #     return bool(self.permissions and any(self.permissions.values()))
    
    # -------------------------------------------------------------------------
    # METADADOS DO MODELO
    # -------------------------------------------------------------------------
    
    class Meta:
        """Configurações de metadados para o modelo AccessProfile."""
        verbose_name = 'Perfil de Acesso'
        verbose_name_plural = 'Perfis de Acesso'
        ordering = ['name']  # Ordenação alfabética por nome do perfil