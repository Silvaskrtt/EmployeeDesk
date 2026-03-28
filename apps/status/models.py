import re
from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


# =============================================================================
# VALIDADORES PERSONALIZADOS
# =============================================================================

def validate_color_code(value):
    """
    Validador personalizado para códigos de cores em formato hexadecimal.
    
    Realiza validação do formato de cor, garantindo que seja um código
    hexadecimal válido de 6 dígitos, com ou sem o prefixo '#'.
    Utilizado pelo campo color_code do modelo Status.
    
    Args:
        value (str): Código de cor a ser validado. Pode estar nos formatos:
                     - '#FF0000' (com #)
                     - 'FF0000' (sem #)
    
    Raises:
        ValidationError: Quando o código não corresponde ao padrão hexadecimal
                         de 6 caracteres (0-9, A-F, a-f).
    
    Example:
        >>> validate_color_code('#FF0000')  # Válido (vermelho)
        >>> validate_color_code('00FF00')   # Válido (verde)
        >>> validate_color_code('#GGGGGG')  # Lança ValidationError
        >>> validate_color_code('FF')       # Lança ValidationError (menos de 6 dígitos)
    
    Note:
        A validação é case-insensitive, aceitando tanto letras maiúsculas
        quanto minúsculas no código hexadecimal.
    """
    if value:
        # Remove o prefixo '#' se presente para validação
        color = value.lstrip('#')
        
        # Verifica se o código contém exatamente 6 caracteres hexadecimais válidos
        # Padrão regex: ^[0-9A-Fa-f]{6}$ - 6 caracteres entre 0-9, A-F ou a-f
        if not re.match(r'^[0-9A-Fa-f]{6}$', color):
            raise ValidationError(
                _('Código de cor inválido. Use formato hexadecimal (ex: #FF0000)')
            )


# =============================================================================
# MODELO DE STATUS
# =============================================================================

class Status(models.Model):
    """
    Modelo que representa um status para funcionários ou entidades do sistema.
    
    Este modelo gerencia os diferentes estados que um funcionário pode assumir
    ao longo de seu ciclo na empresa (Ativo, Inativo, Férias, Licença, etc).
    Utiliza códigos de cores para identificação visual em interfaces de usuário.
    
    Attributes:
        name (CharField): Nome do status (único, ex: 'Ativo', 'Férias').
        description (CharField): Descrição detalhada do status (opcional).
        color_code (CharField): Código hexadecimal para cor de destaque (opcional).
        is_active (BooleanField): Indica se o status está disponível para uso.
        created_at (DateTimeField): Data/hora de criação do registro.
        updated_at (DateTimeField): Data/hora da última atualização.
    
    Meta:
        verbose_name: Nome singular para interface administrativa.
        verbose_name_plural: Nome plural para interface administrativa.
        ordering: Ordenação padrão por nome do status.
    
    Note:
        Status com is_active=False são mantidos no banco para histórico,
        mas não devem ser exibidos em seleções de novos registros.
    """
    
    # -------------------------------------------------------------------------
    # CAMPOS DO MODELO
    # -------------------------------------------------------------------------
    
    # Nome do status (ex: Ativo, Inativo, Férias, Licença Maternidade)
    # unique=True garante que não haja duplicidade de nomes
    name = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='Nome do Status'
    )
    
    # Descrição detalhada do status para auxiliar na compreensão
    # Campo opcional para evitar obrigatoriedade de preenchimento
    description = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name='Descrição'
    )
    
    # Código de cor em formato hexadecimal para identificação visual
    # Exemplos: '#FF0000' (vermelho), '#00FF00' (verde), '#0000FF' (azul)
    # Campo opcional com validação personalizada
    color_code = models.CharField(
        max_length=7,
        blank=True,
        null=True,
        validators=[validate_color_code],
        verbose_name='Código da Cor'
    )
    
    # Flag para controle de disponibilidade do status
    # Quando False, o status não deve ser oferecido como opção para novos registros
    # Mantém histórico de status descontinuados
    is_active = models.BooleanField(
        default=True,
        verbose_name='Status Ativo'
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
        """Configurações de metadados para o modelo Status."""
        verbose_name = _("Status")
        verbose_name_plural = _("Status")
        ordering = ['name']  # Ordenação alfabética por nome do status
    
    # -------------------------------------------------------------------------
    # MÉTODOS PÚBLICOS
    # -------------------------------------------------------------------------
    
    def __str__(self):
        """
        Representação em string do objeto Status.
        
        Utilizada em interfaces administrativas, dropdowns, selects e logs
        para identificação rápida do status.
        
        Returns:
            str: Nome do status.
        
        Example:
            >>> status.__str__()
            'Ativo'
            >>> Status.objects.get(name='Férias').__str__()
            'Férias'
        """
        return self.name
    
    def clean(self):
        """
        Realiza limpeza e normalização dos dados antes da validação completa.
        
        Este método é chamado pelo full_clean() e executa a normalização
        do campo color_code, garantindo que o código de cor seja armazenado
        consistentemente com o prefixo '#'.
        
        Note:
            - Se o código de cor for fornecido sem o prefixo '#', este método
              o adiciona automaticamente.
            - A validação do formato hexadecimal é realizada pelo validador
              personalizado validate_color_code, que é executado após este método.
            - Códigos de cor nulos ou vazios são ignorados (sem formatação).
        
        Example:
            >>> status = Status(color_code='FF0000')
            >>> status.clean()
            >>> status.color_code
            '#FF0000'
        """
        # Garante que o código de cor tenha o prefixo '#' se fornecido
        if self.color_code and not self.color_code.startswith('#'):
            self.color_code = f'#{self.color_code}'
    
    def save(self, *args, **kwargs):
        """
        Sobrescreve o método save para garantir validação antes da persistência.
        
        Executa a validação completa do modelo (clean_fields, clean, validate_constraints)
        antes de salvar no banco de dados, garantindo a integridade dos dados,
        especialmente do formato do código de cor.
        
        Args:
            *args: Argumentos posicionais para o método save original.
            **kwargs: Argumentos nomeados para o método save original.
        
        Note:
            O full_clean() levanta ValidationError se:
            - O código de cor não for um hexadecimal válido (via validate_color_code)
            - O campo name não for único
            - Qualquer outra validação de campo falhar
        
        Example:
            >>> status = Status(name='Férias', color_code='00FF00')
            >>> status.save()  # color_code será normalizado para '#00FF00'
        """
        # Executa validação completa (incluindo clean()) antes de salvar
        self.full_clean()
        # Chama o método save da classe pai
        super().save(*args, **kwargs)
    
    # -------------------------------------------------------------------------
    # PROPRIEDADES (PROPERTIES)
    # -------------------------------------------------------------------------
    
    @property
    def html_color(self):
        """
        Propriedade que retorna o código de cor para uso em HTML/CSS.
        
        Fornece um valor de cor seguro para utilização em interfaces web,
        com fallback para um cinza padrão (#CCCCCC) quando nenhuma cor
        está configurada.
        
        Returns:
            str: Código de cor no formato hexadecimal com prefixo '#'.
                 Retorna '#CCCCCC' (cinza médio) como cor padrão quando
                 o campo color_code está vazio ou nulo.
        
        Example:
            >>> status = Status(color_code='#FF0000')
            >>> status.html_color
            '#FF0000'
            >>> status_without_color = Status(color_code=None)
            >>> status_without_color.html_color
            '#CCCCCC'
        
        Note:
            Esta propriedade é útil para templates HTML onde a cor de fundo
            ou texto deve ser dinâmica baseada no status, garantindo que
            sempre haja um valor válido para o atributo style ou class CSS.
        """
        # Retorna o código de cor configurado ou um cinza padrão como fallback
        return self.color_code if self.color_code else '#CCCCCC'