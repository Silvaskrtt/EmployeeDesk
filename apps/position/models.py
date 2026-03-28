from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from department.models import Department


# =============================================================================
# MODELO DE CARGO
# =============================================================================

class Position(models.Model):
    """
    Modelo que representa um cargo ou posição na estrutura organizacional.
    
    Este modelo define os cargos disponíveis na empresa, incluindo suas
    características como nível hierárquico, faixa salarial e o departamento
    ao qual pertence. Utilizado para classificação e gestão de funcionários.
    
    Attributes:
        name (CharField): Nome do cargo (ex: Analista de Sistemas).
        level (CharField): Nível hierárquico do cargo (Trainee, Júnior, etc).
        min_wage (DecimalField): Salário mínimo da faixa para este cargo.
        max_wage (DecimalField): Salário máximo da faixa para este cargo.
        department (ForeignKey): Departamento ao qual o cargo pertence.
        created_at (DateTimeField): Data/hora de criação do registro.
        updated_at (DateTimeField): Data/hora da última atualização.
    
    Meta:
        verbose_name: Nome singular para interface administrativa.
        verbose_name_plural: Nome plural para interface administrativa.
        ordering: Ordenação padrão por nome do cargo.
    
    Note:
        A validação garante que min_wage nunca seja maior que max_wage,
        mantendo a consistência da faixa salarial.
    """
    
    # -------------------------------------------------------------------------
    # DEFINIÇÃO DE ESCOLHAS (CHOICES) - NÍVEIS HIERÁRQUICOS
    # -------------------------------------------------------------------------
    
    # Lista de níveis hierárquicos disponíveis para cargos
    # Organizados em ordem crescente de senioridade/responsabilidade
    LEVEL_CHOICES = [
        ('TRAINEE', 'Trainee'),           # Programa de estágio/trainee
        ('JUNIOR', 'Júnior'),              # Nível inicial (0-2 anos experiência)
        ('PLENO', 'Pleno'),                # Nível intermediário (3-5 anos)
        ('SENIOR', 'Sênior'),              # Nível avançado (5+ anos)
        ('SPECIALIST', 'Especialista'),    # Especialista técnico
        ('MANAGER', 'Gerente'),            # Cargo de gestão de pessoas/equipes
        ('DIRECTOR', 'Diretor'),           # Cargo de alta gestão
    ]
    
    # -------------------------------------------------------------------------
    # CAMPOS DO MODELO
    # -------------------------------------------------------------------------
    
    # Nome do cargo (ex: Desenvolvedor de Software, Analista de RH)
    name = models.CharField(
        max_length=100,
        verbose_name='Nome do Cargo'
    )
    
    # Nível hierárquico do cargo (opcional para cargos sem hierarquia definida)
    level = models.CharField(
        max_length=20,
        choices=LEVEL_CHOICES,
        blank=True,
        null=True,
        verbose_name='Nível'
    )
    
    # -------------------------------------------------------------------------
    # FAIXA SALARIAL
    # -------------------------------------------------------------------------
    
    # Salário mínimo da faixa para este cargo
    # Opcional para cargos onde a faixa ainda não foi definida
    min_wage = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name='Salário Mínimo'
    )
    
    # Salário máximo da faixa para este cargo
    # Opcional para cargos onde a faixa ainda não foi definida
    max_wage = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name='Salário Máximo'
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
    # CHAVES ESTRANGEIRAS (RELACIONAMENTOS EXTERNOS)
    # -------------------------------------------------------------------------
    
    # Departamento ao qual este cargo pertence
    # PROTECT: Impede exclusão de Department se houver Position associada
    # related_name='positions': Permite acessar department.positions para listar
    #                           todos os cargos de um departamento
    department = models.ForeignKey(
        Department,
        on_delete=models.PROTECT,
        related_name='positions',
        verbose_name='Departamento'
    )
    
    # -------------------------------------------------------------------------
    # METADADOS DO MODELO
    # -------------------------------------------------------------------------
    
    class Meta:
        """Configurações de metadados para o modelo Position."""
        verbose_name = _("Cargo")
        verbose_name_plural = _("Cargos")
        ordering = ['name']  # Ordenação alfabética por nome do cargo
    
    # -------------------------------------------------------------------------
    # MÉTODOS PÚBLICOS
    # -------------------------------------------------------------------------
    
    def __str__(self):
        """
        Representação em string do objeto Position.
        
        Utilizada em interfaces administrativas, dropdowns e logs para
        identificação rápida do cargo.
        
        Returns:
            str: Nome do cargo seguido do nível (se disponível).
                 Exemplos: "Analista de Sistemas - Pleno" ou apenas "Diretor"
        
        Example:
            >>> position.__str__()
            'Desenvolvedor - Sênior'
            >>> position_without_level.__str__()
            'Gerente Comercial'
        """
        # Se o nível estiver definido, retorna "Nome - Nível"
        # Caso contrário, retorna apenas o nome
        return f"{self.name} - {self.get_level_display()}" if self.level else self.name
    
    def clean(self):
        """
        Realiza validação personalizada dos dados do cargo.
        
        Este método é chamado pelo full_clean() e garante a consistência
        da faixa salarial, verificando se o salário mínimo não é maior
        que o salário máximo.
        
        Raises:
            ValidationError: Se min_wage for maior que max_wage (quando ambos
                            estiverem preenchidos).
        
        Note:
            A validação só é aplicada quando ambos os campos estão preenchidos,
            permitindo que cargos sem faixa salarial definida sejam salvos.
        """
        # Verifica consistência da faixa salarial
        if self.min_wage and self.max_wage and self.min_wage > self.max_wage:
            raise ValidationError(
                _('Salário mínimo não pode ser maior que o salário máximo.')
            )
    
    def save(self, *args, **kwargs):
        """
        Sobrescreve o método save para garantir validação antes da persistência.
        
        Executa a validação completa do modelo (clean_fields, clean, validate_constraints)
        antes de salvar no banco de dados, garantindo a integridade dos dados.
        
        Args:
            *args: Argumentos posicionais para o método save original.
            **kwargs: Argumentos nomeados para o método save original.
        
        Note:
            O full_clean() levanta ValidationError se a faixa salarial estiver
            inconsistente, impedindo a persistência de dados inválidos.
        """
        # Executa validação completa (incluindo clean()) antes de salvar
        self.full_clean()
        # Chama o método save da classe pai
        super().save(*args, **kwargs)
    
    # -------------------------------------------------------------------------
    # PROPRIEDADES (PROPERTIES)
    # -------------------------------------------------------------------------
    
    @property
    def salary_range(self):
        """
        Propriedade que retorna a faixa salarial formatada para exibição.
        
        Fornece uma representação amigável da faixa salarial do cargo,
        com formatação em moeda brasileira (R$).
        
        Returns:
            str: Faixa salarial formatada no padrão "R$ X.XXX,XX - R$ X.XXX,XX"
                 ou "Não definida" se a faixa não estiver configurada.
        
        Example:
            >>> position.salary_range
            'R$ 5.000,00 - R$ 7.500,00'
            >>> position_without_range.salary_range
            'Não definida'
        
        Note:
            A formatação utiliza a notação brasileira com vírgula para
            decimais e pontos para separadores de milhar.
        """
        # Verifica se ambos os valores da faixa salarial estão definidos
        if self.min_wage and self.max_wage:
            # Formata os valores no padrão de moeda brasileira
            # Exemplo: 5000.00 -> R$ 5.000,00
            return f"R$ {self.min_wage:,.2f} - R$ {self.max_wage:,.2f}"
        
        # Retorna mensagem padrão quando a faixa não está definida
        return "Não definida"