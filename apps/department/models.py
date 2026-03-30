from django.db import models
from employee.models import Employee


# =============================================================================
# MODELO DE DEPARTAMENTO
# =============================================================================

class Department(models.Model):
    """
    Modelo que representa um departamento ou unidade organizacional da empresa.
    
    Este modelo define as unidades organizacionais que compõem a estrutura
    hierárquica da empresa, como: TI, Recursos Humanos, Financeiro, Comercial,
    Operações, etc. Cada departamento pode ter um gestor responsável e múltiplos
    funcionários associados.
    
    Attributes:
        name (CharField): Nome único do departamento.
        description (TextField): Descrição detalhada das responsabilidades e
                                  finalidade do departamento.
        manager (ForeignKey): Funcionário responsável pela gestão do departamento.
        active (BooleanField): Flag que indica se o departamento está em operação.
        created_at (DateTimeField): Data/hora de criação do registro.
        updated_at (DateTimeField): Data/hora da última atualização.
    
    Meta:
        verbose_name: Nome singular para interface administrativa.
        verbose_name_plural: Nome plural para interface administrativa.
        ordering: Ordenação padrão por nome do departamento.
    
    Note:
        O relacionamento com Employee utiliza on_delete=models.SET_NULL para
        preservar o histórico do departamento mesmo quando o gestor é desligado
        ou removido do sistema, evitando perda de dados.
    """
    
    # -------------------------------------------------------------------------
    # CAMPOS DO MODELO
    # -------------------------------------------------------------------------
    
    # Nome do departamento (ex: Tecnologia da Informação, Recursos Humanos)
    # unique=True garante que não haja duplicidade de nomes na organização
    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name='Nome do Departamento'
    )
    
    # Descrição detalhada do departamento, incluindo suas atribuições,
    # responsabilidades e objetivos estratégicos
    # Campo opcional para flexibilidade no cadastro
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name='Descrição'
    )
    
    # -------------------------------------------------------------------------
    # RELACIONAMENTOS
    # -------------------------------------------------------------------------
    
    # Gestor responsável pelo departamento
    # SET_NULL: Quando o funcionário gestor for removido, mantém o departamento
    #           e define manager como NULL, preservando o histórico
    # null=True e blank=True: Permite departamentos sem gestor definido
    # related_name='managed_departments': Permite acessar employee.managed_departments
    #                                     para listar todos os departamentos que o
    #                                     funcionário gerencia
    manager = models.ForeignKey(
        Employee,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='managed_departments',
        verbose_name='Gestor'
    )
    
    # -------------------------------------------------------------------------
    # FLAGS DE CONTROLE
    # -------------------------------------------------------------------------
    
    # Indica se o departamento está ativo e em operação
    # Departamentos inativos podem ser mantidos no sistema para histórico,
    # mas não devem ser exibidos em seleções para novos funcionários ou
    # alocações
    active = models.BooleanField(
        default=True,
        verbose_name='Ativo'
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
        Representação em string do objeto Department.
        
        Utilizada em interfaces administrativas, dropdowns, selects e logs
        para identificação rápida do departamento.
        
        Returns:
            str: Nome do departamento.
        
        Example:
            >>> department.__str__()
            'Tecnologia da Informação'
            >>> Department.objects.get(name='Recursos Humanos').__str__()
            'Recursos Humanos'
        """
        return self.name
    
    # -------------------------------------------------------------------------
    # METADADOS DO MODELO
    # -------------------------------------------------------------------------
    
    class Meta:
        """Configurações de metadados para o modelo Department."""
        verbose_name = 'Departamento'
        verbose_name_plural = 'Departamentos'
        ordering = ['name']  # Ordenação alfabética por nome do departamento