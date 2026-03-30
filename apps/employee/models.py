from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

# Importação de modelos relacionados de outros aplicativos
from accounts.models import User
from status.models import Status
from address.models import Address


# =============================================================================
# VALIDADORES PERSONALIZADOS
# =============================================================================

def validate_cpf(value):
    """
    Validador personalizado para documentos CPF.
    
    Realiza validação completa do CPF incluindo:
    - Remoção de caracteres não numéricos
    - Verificação de quantidade de dígitos (11)
    - Validação contra CPFs com todos dígitos iguais
    - Cálculo e validação dos dígitos verificadores
    
    Args:
        value (str): Valor do CPF a ser validado, podendo conter máscaras
                     como pontos e hífen.
    
    Raises:
        ValidationError: Quando o CPF não atende aos critérios de validação
                         (quantidade incorreta de dígitos, todos iguais ou
                         dígitos verificadores inválidos).
    
    Example:
        >>> validate_cpf('123.456.789-09')  # Válido
        >>> validate_cpf('111.111.111-11')  # Lança ValidationError (todos iguais)
        >>> validate_cpf('123.456.789-00')  # Lança ValidationError (dígitos inválidos)
    """
    # Remove caracteres não numéricos (pontos, hífen, espaços)
    cpf = ''.join(filter(str.isdigit, value))
    
    # Verifica se possui exatamente 11 dígitos (CPF válido)
    if len(cpf) != 11:
        raise ValidationError('CPF deve ter 11 dígitos')
    
    # Verifica se todos os dígitos são iguais (ex: 111.111.111-11)
    # Estes CPFs são considerados inválidos pela Receita Federal
    if cpf == cpf[0] * 11:
        raise ValidationError('CPF inválido')
    
    # Validação dos dígitos verificadores (9º e 10º dígitos)
    # Algoritmo oficial de validação de CPF
    for i in range(9, 11):
        # Calcula a soma ponderada dos dígitos anteriores
        value = sum((int(cpf[num]) * ((i+1) - num) for num in range(0, i)))
        # Calcula o dígito verificador esperado
        digit = ((value * 10) % 11) % 10
        # Compara com o dígito informado
        if digit != int(cpf[i]):
            raise ValidationError('CPF inválido')


# =============================================================================
# MODELO DE FUNCIONÁRIO
# =============================================================================

class Employee(models.Model):
    """
    Modelo que representa um funcionário no sistema.
    
    Este modelo centraliza todas as informações relacionadas a um funcionário,
    incluindo dados pessoais, profissionais, vínculo com usuário do sistema,
    cargo, status e endereço. Utiliza relacionamentos com outros modelos
    para garantir integridade referencial e reuso de dados.
    
    Attributes:
        user (OneToOneField): Relacionamento com o modelo User do sistema.
        first_name (CharField): Primeiro nome do funcionário.
        last_name (CharField): Sobrenome do funcionário.
        cpf (CharField): CPF do funcionário (único e validado).
        personal_email (EmailField): E-mail pessoal (único).
        email (EmailField): E-mail corporativo (único).
        birth_date (DateField): Data de nascimento.
        hire_date (DateField): Data de admissão.
        wage (DecimalField): Salário do funcionário.
        emergency_contact (CharField): Nome do contato de emergência.
        emergency_phone (CharField): Telefone do contato de emergência.
        resignation_date (DateField): Data de demissão (se aplicável).
        status (ForeignKey): Status atual do funcionário (ativo/inativo).
        position (ForeignKey): Cargo ocupado pelo funcionário.
        address (ForeignKey): Endereço do funcionário.
        created_at (DateTimeField): Data/hora de criação do registro.
        updated_at (DateTimeField): Data/hora da última atualização.
    
    Meta:
        verbose_name: Nome singular para interface administrativa.
        verbose_name_plural: Nome plural para interface administrativa.
        ordering: Ordenação padrão por nome e sobrenome.
    
    Note:
        Os campos user, status, position e address utilizam on_delete=models.PROTECT
        para evitar exclusão acidental de registros relacionados.
    """
    
    # -------------------------------------------------------------------------
    # RELACIONAMENTOS
    # -------------------------------------------------------------------------
    
    # Relacionamento um-para-um com o modelo User do sistema
    # PROTECT: Impede exclusão do User se houver Employee associado
    # related_name='employee': Permite acessar o employee via user.employee
    user = models.OneToOneField(
        User,
        on_delete=models.PROTECT,
        related_name='employee'
    )
    
    # -------------------------------------------------------------------------
    # DADOS PESSOAIS
    # -------------------------------------------------------------------------
    
    # Nome do funcionário (primeiro nome e sobrenome separados)
    first_name = models.CharField(
        max_length=150,
        verbose_name='Primeiro Nome'
    )
    last_name = models.CharField(
        max_length=150,
        verbose_name='Sobrenome'
    )
    
    # CPF com validação personalizada e unicidade garantida
    cpf = models.CharField(
        'CPF',
        max_length=14,
        unique=True,
        validators=[validate_cpf]
    )
    
    # E-mails pessoal e corporativo (ambos únicos)
    personal_email = models.EmailField(
        'E-mail Pessoal',
        unique=True
    )
    email = models.EmailField(
        'E-mail Corporativo',
        unique=True
    )
    
    # Datas importantes com help text para orientar o usuário
    birth_date = models.DateField(
        help_text="Formato: DD/MM/AAAA",
        verbose_name='Data de Nascimento'
    )
    hire_date = models.DateField(
        help_text="Formato: DD/MM/AAAA",
        verbose_name='Data de Admissão'
    )
    
    # -------------------------------------------------------------------------
    # DADOS PROFISSIONAIS E CONTRATUAIS
    # -------------------------------------------------------------------------
    
    # Salário com 2 casas decimais e até 10 dígitos no total
    wage = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Salário'
    )
    
    # Contato de emergência (campos opcionais)
    emergency_contact = models.CharField(
        blank=True,
        null=True,
        max_length=150,
        verbose_name='Contato de Emergência'
    )
    emergency_phone = models.CharField(
        blank=True,
        null=True,
        max_length=20,
        verbose_name='Telefone de Emergência'
    )
    
    # Data de desligamento (opcional, presente apenas se funcionário foi desligado)
    resignation_date = models.DateField(
        blank=True,
        null=True,
        help_text="Formato: DD/MM/AAAA",
        verbose_name='Data de Desligamento'
    )
    
    # -------------------------------------------------------------------------
    # CHAVES ESTRANGEIRAS (RELACIONAMENTOS EXTERNOS)
    # -------------------------------------------------------------------------
    
    # Status do funcionário (Ativo, Inativo, etc)
    # PROTECT: Impede exclusão de Status em uso
    status = models.ForeignKey(
        Status,
        on_delete=models.PROTECT,
        verbose_name='Status'
    )
    
    # Obs.: ForeignKey usando strings para evitar a dependência circular entre os modelos. 
    # Cargo ocupado pelo funcionário
    # PROTECT: Impede exclusão de Position em uso
    position = models.ForeignKey(
        'position.Position',
        on_delete=models.PROTECT,
        verbose_name='Cargo'
    )
    
    # Endereço do funcionário
    # PROTECT: Impede exclusão de Address em uso
    address = models.ForeignKey(
        Address,
        on_delete=models.PROTECT,
        verbose_name='Endereço'
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
    # METADADOS DO MODELO
    # -------------------------------------------------------------------------
    
    class Meta:
        """Configurações de metadados para o modelo Employee."""
        verbose_name = _("Funcionário")
        verbose_name_plural = _("Funcionários")
        ordering = ['first_name', 'last_name']  # Ordenação alfabética por nome
    
    # -------------------------------------------------------------------------
    # MÉTODOS PÚBLICOS
    # -------------------------------------------------------------------------
    
    def __str__(self):
        """
        Representação em string do objeto Employee.
        
        Utilizada em interfaces administrativas, debug e logs para
        identificação rápida do funcionário.
        
        Returns:
            str: Nome completo do funcionário.
        
        Example:
            >>> employee.__str__()
            'João Silva'
        """
        return f"{self.first_name} {self.last_name}"
    
    def clean(self):
        """
        Realiza limpeza e formatação dos dados antes da validação completa.
        
        Este método é chamado pelo full_clean() e executa a normalização
        do campo CPF, aplicando a máscara padrão (XXX.XXX.XXX-XX) quando
        o valor contém exatamente 11 dígitos numéricos.
        
        Note:
            Este método é executado automaticamente durante o full_clean()
            que é chamado no save().
        """
        if self.cpf:
            # Remove caracteres não numéricos para normalização
            cpf_clean = ''.join(filter(str.isdigit, self.cpf))
            # Aplica máscara apenas se houver 11 dígitos
            if len(cpf_clean) == 11:
                self.cpf = f'{cpf_clean[:3]}.{cpf_clean[3:6]}.{cpf_clean[6:9]}-{cpf_clean[9:]}'
    
    def save(self, *args, **kwargs):
        """
        Sobrescreve o método save para garantir validação antes da persistência.
        
        Executa a validação completa do modelo (clean_fields, clean, validate_constraints)
        antes de salvar no banco de dados, garantindo a integridade dos dados.
        
        Args:
            *args: Argumentos posicionais para o método save original.
            **kwargs: Argumentos nomeados para o método save original.
        
        Note:
            O full_clean() levanta ValidationError se algum campo estiver inválido,
            impedindo a persistência de dados inconsistentes.
        """
        # Executa validação completa (incluindo clean()) antes de salvar
        self.full_clean()
        # Chama o método save da classe pai
        super().save(*args, **kwargs)
    
    def toggle_status(self):
        """
        Alterna o status do funcionário entre Ativo e Inativo.
        
        Este método busca os objetos Status com nomes 'Ativo' e 'Inativo'
        e alterna o status atual do funcionário entre eles. É útil para
        ações de desligamento e reativação de funcionários.
        
        Returns:
            str: Nome do novo status após a alteração.
        
        Raises:
            ValidationError: Se os status 'Ativo' ou 'Inativo' não forem
                            encontrados no banco de dados.
        
        Example:
            >>> employee.status.name  # 'Ativo'
            >>> employee.toggle_status()
            'Inativo'
            >>> employee.status.name  # 'Inativo'
        
        Note:
            Este método realiza o save() automaticamente após a alteração.
        """
        # Importação local para evitar importação circular
        from status.models import Status
        
        try:
            # Busca os status necessários no banco de dados
            ativo = Status.objects.get(name='Ativo')
            inativo = Status.objects.get(name='Inativo')
        except Status.DoesNotExist:
            raise ValidationError('Status "Ativo" ou "Inativo" não encontrados.')
        
        # Alterna entre Ativo e Inativo
        if self.status == ativo:
            self.status = inativo
        else:
            self.status = ativo
        
        # Persiste a alteração no banco de dados
        self.save()
        return self.status.name
    
    # -------------------------------------------------------------------------
    # PROPRIEDADES (PROPERTIES)
    # -------------------------------------------------------------------------
    
    @property
    def full_name(self):
        """
        Propriedade que retorna o nome completo do funcionário.
        
        Fornece uma forma conveniente de acessar o nome completo
        concatenando primeiro nome e sobrenome.
        
        Returns:
            str: Nome completo no formato "Primeiro Nome Sobrenome".
        
        Example:
            >>> employee.full_name
            'Maria Santos'
        """
        return f"{self.first_name} {self.last_name}"
    
    @property
    def is_active(self):
        """
        Propriedade que verifica se o funcionário está ativo.
        
        Determina o status ativo baseado em duas condições:
        1. O status.name deve ser 'ATIVO' (case insensitive)
        2. Não deve haver data de desligamento preenchida
        
        Returns:
            bool: True se o funcionário está ativo, False caso contrário.
        
        Example:
            >>> employee.is_active
            True
        """
        return self.status.name.upper() == 'ATIVO' and self.resignation_date is None