from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


# =============================================================================
# MODELO DE ALOCAÇÃO FUNCIONÁRIO-DEPARTAMENTO
# =============================================================================

class EmployeeDepartment(models.Model):
    """
    Modelo de tabela associativa para relacionamento muitos-para-muitos (N:N)
    entre Employee e Department.
    
    Este modelo implementa um relacionamento N:N com atributos adicionais,
    permitindo que um funcionário seja alocado a múltiplos departamentos
    com diferentes percentuais de dedicação e períodos de atuação.
    
    Características principais:
    - Suporte a múltiplas alocações simultâneas por funcionário
    - Controle de percentual de dedicação por departamento
    - Definição de departamento principal
    - Controle temporal com datas de início e término
    - Validações robustas para garantir consistência dos dados
    
    Attributes:
        allocation_percentage (DecimalField): Percentual de dedicação ao departamento.
        is_primary (BooleanField): Indica se é o departamento principal.
        start_date (DateField): Data de início da alocação.
        end_date (DateField): Data de término da alocação (opcional).
        employee (ForeignKey): Referência ao funcionário.
        department (ForeignKey): Referência ao departamento.
        created_at (DateTimeField): Data/hora de criação do registro.
        updated_at (DateTimeField): Data/hora da última atualização.
    
    Meta:
        verbose_name: Nome singular para interface administrativa.
        verbose_name_plural: Nome plural para interface administrativa.
        unique_together: Garante que um funcionário não seja alocado duas vezes
                         ao mesmo departamento.
        indexes: Índices otimizados para consultas frequentes.
        ordering: Ordenação padrão por funcionário, prioridade e data de início.
    
    Note:
        Este modelo é essencial para casos de negócio onde um funcionário pode
        atuar em múltiplos departamentos (ex: projetos compartilhados, alocações
        parciais, funções de liderança com dupla subordinação).
    """
    
    # -------------------------------------------------------------------------
    # CAMPOS DE ALOCAÇÃO
    # -------------------------------------------------------------------------
    
    # Percentual de dedicação do funcionário ao departamento
    # Valores entre 0 e 100%, com duas casas decimais para maior precisão
    # Exemplos: 100% (dedicação exclusiva), 50% (meio período), 25% (parcial)
    allocation_percentage = models.DecimalField(
        max_digits=5,          # Suporta até 999.99%
        decimal_places=2,      # Duas casas decimais (ex: 33.33%)
        default=100.00,        # Por padrão, dedicação integral
        verbose_name='Percentual de Alocação',
        help_text='Percentual de dedicação ao departamento (0-100%)'
    )
    
    # Flag que identifica o departamento principal do funcionário
    # Utilizado para contextos onde um departamento precisa ser considerado
    # como o principal (ex: hierarquia organizacional, aprovações)
    is_primary = models.BooleanField(
        default=False,
        verbose_name='Departamento Principal',
        help_text='Indica se este é o departamento principal do funcionário'
    )
    
    # -------------------------------------------------------------------------
    # DATAS DE VIGÊNCIA
    # -------------------------------------------------------------------------
    
    # Data de início da alocação no departamento
    # Preenchida automaticamente com a data atual na criação
    start_date = models.DateField(
        auto_now_add=True,     # Define automaticamente a data atual
        verbose_name='Data de Início'
    )
    
    # Data de término da alocação (opcional)
    # Quando preenchida, indica que a alocação foi encerrada
    # Alocações com end_date=None são consideradas ativas
    end_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='Data de Término',
        help_text='Preencher quando a alocação for encerrada'
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
    # RELACIONAMENTOS (CHAVES ESTRANGEIRAS)
    # -------------------------------------------------------------------------
    
    # Funcionário associado à alocação
    # CASCADE: Remove alocações quando o funcionário for excluído
    # related_name='department_assignments': Permite acessar employee.department_assignments
    employee = models.ForeignKey(
        'employee.Employee',   # Referência por string para evitar importação circular
        on_delete=models.CASCADE,
        related_name='department_assignments',
        verbose_name='Funcionário'
    )
    
    # Departamento associado à alocação
    # CASCADE: Remove alocações quando o departamento for excluído
    # related_name='employee_assignments': Permite acessar department.employee_assignments
    department = models.ForeignKey(
        'department.Department',
        on_delete=models.CASCADE,
        related_name='employee_assignments',
        verbose_name='Departamento'
    )
    
    # -------------------------------------------------------------------------
    # METADADOS DO MODELO
    # -------------------------------------------------------------------------
    
    class Meta:
        """
        Configurações de metadados para o modelo EmployeeDepartment.
        
        Define restrições de unicidade, índices otimizados e ordenação padrão
        para garantir performance e integridade dos dados.
        """
        verbose_name = 'Alocação de Funcionário'
        verbose_name_plural = 'Alocações de Funcionários'
        
        # Garante que um funcionário não seja alocado duas vezes ao mesmo departamento
        # Evita duplicidade de alocações ativas ou inativas
        unique_together = [['employee', 'department']]
        
        # Índices otimizados para consultas frequentes
        indexes = [
            models.Index(fields=['employee'], name='idx_emp_dept_employee'),
            models.Index(fields=['department'], name='idx_emp_dept_department'),
            models.Index(fields=['is_primary'], name='idx_emp_dept_primary'),
            models.Index(fields=['end_date'], name='idx_emp_dept_end_date'),
        ]
        
        # Ordenação padrão: funcionário, prioridade (principal primeiro), data de início
        # -is_primary: ordena decrescente (True vem antes de False)
        ordering = ['employee', '-is_primary', 'start_date']
    
    # -------------------------------------------------------------------------
    # MÉTODOS PÚBLICOS
    # -------------------------------------------------------------------------
    
    def __str__(self):
        """
        Representação em string do objeto EmployeeDepartment.
        
        Utilizada em interfaces administrativas, logs e debug para
        identificação rápida da alocação.
        
        Returns:
            str: String no formato "Funcionário - Departamento (percentual%)"
        
        Example:
            >>> allocation.__str__()
            'João Silva - Tecnologia da Informação (100.00%)'
        """
        return f"{self.employee} - {self.department} ({self.allocation_percentage}%)"
    
    def clean(self):
        """
        Realiza validações complexas de negócio antes da persistência.
        
        Este método implementa regras de validação críticas para garantir
        a consistência dos dados de alocação:
        
        1. Validação do percentual (0-100%)
        2. Validação de datas (término não pode ser anterior ao início)
        3. Garantia de apenas um departamento principal ativo por funcionário
        4. Controle da soma dos percentuais (não pode exceder 100%)
        
        Raises:
            ValidationError: Quando alguma regra de negócio é violada,
                            com mensagem específica apontando o campo problemático.
        
        Note:
            Este método é chamado automaticamente pelo full_clean() no save().
            As validações consideram apenas alocações ativas (sem end_date)
            para as regras de percentual e departamento principal.
        """
        
        # ---------------------------------------------------------------------
        # VALIDAÇÃO 1: Percentual de alocação
        # ---------------------------------------------------------------------
        # Garante que o percentual esteja dentro do intervalo válido
        if self.allocation_percentage <= 0 or self.allocation_percentage > 100:
            raise ValidationError({
                'allocation_percentage': 'Percentual de alocação deve ser entre 0 e 100%'
            })
        
        # ---------------------------------------------------------------------
        # VALIDAÇÃO 2: Consistência de datas
        # ---------------------------------------------------------------------
        # Data de término não pode ser anterior à data de início
        if self.end_date and self.start_date and self.end_date < self.start_date:
            raise ValidationError({
                'end_date': 'Data de término não pode ser anterior à data de início'
            })
        
        # ---------------------------------------------------------------------
        # VALIDAÇÃO 3: Apenas um departamento principal ativo
        # ---------------------------------------------------------------------
        # Cada funcionário pode ter apenas um departamento principal ativo
        # (sem data de término) em determinado momento
        if self.is_primary:
            existing_primary = EmployeeDepartment.objects.filter(
                employee=self.employee,
                is_primary=True,
                end_date__isnull=True  # Apenas alocações ativas
            ).exclude(pk=self.pk)      # Exclui o próprio registro em edição
            
            if existing_primary.exists():
                raise ValidationError({
                    'is_primary': f'O funcionário {self.employee} já possui um departamento principal ativo'
                })
        
        # ---------------------------------------------------------------------
        # VALIDAÇÃO 4: Soma dos percentuais não pode exceder 100%
        # ---------------------------------------------------------------------
        # A soma dos percentuais de todas as alocações ativas de um funcionário
        # não pode ultrapassar 100% (dedicação total)
        if not self.end_date:  # Apenas valida para alocações ativas
            # Calcula a soma dos percentuais das outras alocações ativas
            total_percentage = EmployeeDepartment.objects.filter(
                employee=self.employee,
                end_date__isnull=True  # Considera apenas alocações ativas
            ).exclude(pk=self.pk).aggregate(
                total=models.Sum('allocation_percentage')
            )['total'] or 0  # Se não houver outras, total = 0
            
            # Verifica se a nova alocação excederia 100%
            if total_percentage + self.allocation_percentage > 100:
                raise ValidationError({
                    'allocation_percentage': f'Soma dos percentuais de alocação não pode exceder 100%. Atual: {total_percentage + self.allocation_percentage}%'
                })
    
    def save(self, *args, **kwargs):
        """
        Sobrescreve o método save para garantir validação antes da persistência.
        
        Executa a validação completa do modelo (incluindo as regras de negócio
        definidas em clean()) antes de salvar no banco de dados, garantindo a
        integridade dos dados.
        
        Args:
            *args: Argumentos posicionais para o método save original.
            **kwargs: Argumentos nomeados para o método save original.
        
        Note:
            O full_clean() levanta ValidationError se alguma regra de negócio
            for violada, impedindo a persistência de dados inconsistentes.
        """
        # Executa validação completa (incluindo clean()) antes de salvar
        self.full_clean()
        # Chama o método save da classe pai
        super().save(*args, **kwargs)
    
    # -------------------------------------------------------------------------
    # PROPRIEDADES (PROPERTIES)
    # -------------------------------------------------------------------------
    
    @property
    def is_active(self):
        """
        Propriedade que verifica se a alocação está ativa.
        
        Uma alocação é considerada ativa quando não possui data de término,
        indicando que o funcionário ainda está alocado ao departamento.
        
        Returns:
            bool: True se a alocação está ativa (end_date é None),
                  False caso contrário.
        
        Example:
            >>> allocation.is_active
            True
            >>> allocation.end_date = date.today()
            >>> allocation.is_active
            False
        """
        return self.end_date is None
    
    # -------------------------------------------------------------------------
    # MÉTODOS DE CLASSE (CLASS METHODS)
    # -------------------------------------------------------------------------
    
    @classmethod
    def get_active_allocations(cls, employee=None):
        """
        Retorna todas as alocações ativas, opcionalmente filtradas por funcionário.
        
        Método de classe utilitário para consultas frequentes de alocações
        ativas (sem data de término).
        
        Args:
            employee (Employee, optional): Funcionário para filtrar as alocações.
                                          Se não informado, retorna todas as
                                          alocações ativas do sistema.
        
        Returns:
            QuerySet: QuerySet contendo as alocações ativas, ordenadas pelo
                     padrão definido em Meta.ordering.
        
        Example:
            >>> # Todas as alocações ativas
            >>> active_all = EmployeeDepartment.get_active_allocations()
            >>> 
            >>> # Apenas alocações ativas de um funcionário específico
            >>> employee_allocs = EmployeeDepartment.get_active_allocations(
            ...     employee=joao
            ... )
            >>> 
            >>> # Verifica se funcionário está alocado a algum departamento
            >>> if employee_allocs.exists():
            ...     print(f"{employee} está alocado a {employee_allocs.count()} departamentos")
        
        Note:
            Este método é útil para relatórios, verificações de disponibilidade
            e validações que precisam considerar apenas alocações ativas.
        """
        # Filtra alocações sem data de término (ativas)
        queryset = cls.objects.filter(end_date__isnull=True)
        
        # Aplica filtro por funcionário se especificado
        if employee:
            queryset = queryset.filter(employee=employee)
        
        return queryset