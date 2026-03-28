from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError  # Import adicionado para referência correta

# =============================================================================
# VALIDADORES PERSONALIZADOS
# =============================================================================

def validate_zip_code(value):
    """
    Validador personalizado para campos de CEP.
    
    Realiza a validação do formato do CEP, garantindo que contenha exatamente
    8 dígitos numéricos. Este validador é utilizado pelo campo zip_code do
    modelo Address.
    
    Args:
        value (str): Valor do CEP a ser validado, podendo conter máscaras
                     como hífen ou espaços.
    
    Raises:
        ValidationError: Quando o CEP não possui exatamente 8 dígitos numéricos.
    
    Example:
        >>> validate_zip_code('12345-678')  # Válido
        >>> validate_zip_code('1234')       # Lança ValidationError
    """
    if value:
        # Remove caracteres não numéricos para validação da quantidade de dígitos
        cep = ''.join(filter(str.isdigit, value))
        if len(cep) != 8:
            raise ValidationError('CEP deve ter 8 dígitos')


# =============================================================================
# MODELO DE ENDEREÇO
# =============================================================================

class Address(models.Model):
    """
    Modelo que representa um endereço no sistema.
    
    Este modelo armazena informações completas de endereçamento, incluindo
    CEP, país, estado, cidade, bairro, logradouro, número e complemento.
    Utiliza campos de auditoria (created_at e updated_at) para rastreamento
    de alterações.
    
    Attributes:
        zip_code (CharField): CEP do endereço, aceita máscara e é validado
                              pelo validador personalizado.
        country (CharField): País do endereço, com valor padrão 'Brasil'.
        state (CharField): Estado/UF do endereço.
        city (CharField): Cidade do endereço.
        neighborhood (CharField): Bairro do endereço.
        street (CharField): Logradouro (rua, avenida, etc).
        number (CharField): Número do imóvel.
        complement (CharField): Complemento do endereço (apto, bloco, etc).
        created_at (DateTimeField): Data/hora de criação do registro.
        updated_at (DateTimeField): Data/hora da última atualização.
    
    Meta:
        verbose_name: Nome singular para interface administrativa.
        verbose_name_plural: Nome plural para interface administrativa.
        ordering: Ordenação padrão por país, estado e cidade.
    """
    
    # -------------------------------------------------------------------------
    # CAMPOS DO MODELO
    # -------------------------------------------------------------------------
    
    # CEP com validação personalizada e suporte a máscara
    zip_code = models.CharField(
        max_length=10,
        blank=True,
        null=True,
        validators=[validate_zip_code],
        verbose_name='CEP'
    )
    
    # País com valor padrão Brasil para otimizar cadastros nacionais
    country = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        default='Brasil',
        verbose_name='País'
    )
    
    # Campo obrigatório para estado
    state = models.CharField(
        max_length=100,
        verbose_name='Estado'
    )
    
    # Campo obrigatório para cidade
    city = models.CharField(
        max_length=100,
        verbose_name='Cidade'
    )
    
    # Campo obrigatório para bairro
    neighborhood = models.CharField(
        max_length=100,
        verbose_name='Bairro'
    )
    
    # Campo obrigatório para logradouro
    street = models.CharField(
        max_length=200,
        verbose_name='Logradouro'
    )
    
    # Campo obrigatório para número
    number = models.CharField(
        max_length=20,
        verbose_name='Número'
    )
    
    # Complemento opcional para informações adicionais
    complement = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name='Complemento'
    )
    
    # Campos de auditoria automáticos
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Criado em'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Atualizado em'
    )
    
    # -------------------------------------------------------------------------
    # METADADOS DO MODELO
    # -------------------------------------------------------------------------
    
    class Meta:
        """Configurações de metadados para o modelo Address."""
        verbose_name = _("Endereço")
        verbose_name_plural = _("Endereços")
        ordering = ['country', 'state', 'city']  # Ordenação geográfica
    
    # -------------------------------------------------------------------------
    # MÉTODOS PÚBLICOS
    # -------------------------------------------------------------------------
    
    def __str__(self):
        """
        Representação em string do objeto Address.
        
        Utilizada em interfaces administrativas e debug, retorna uma
        representação resumida do endereço.
        
        Returns:
            str: String no formato "Logradouro, Número - Cidade/Estado"
        """
        return f"{self.street}, {self.number} - {self.city}/{self.state}"
    
    def clean(self):
        """
        Realiza limpeza e validação dos dados antes da validação completa.
        
        Este método é chamado pelo full_clean() e executa a normalização
        do campo zip_code, aplicando a máscara padrão de CEP (xxxxx-xxx)
        quando o valor contém exatamente 8 dígitos numéricos.
        
        Note:
            Este método é executado automaticamente durante o full_clean()
            que é chamado no save().
        """
        if self.zip_code:
            # Remove caracteres não numéricos para normalização
            cep_clean = ''.join(filter(str.isdigit, self.zip_code))
            # Aplica máscara apenas se houver 8 dígitos
            if len(cep_clean) == 8:
                self.zip_code = f'{cep_clean[:5]}-{cep_clean[5:]}'
    
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
        # Executa validação completa antes de salvar
        self.full_clean()
        # Chama o método save da classe pai
        super().save(*args, **kwargs)
    
    @property
    def full_address(self):
        """
        Propriedade que retorna o endereço completo formatado.
        
        Fornece uma representação concatenada dos principais campos do endereço,
        útil para exibição em templates e APIs.
        
        Returns:
            str: Endereço formatado como "Logradouro, Número - Cidade/Estado"
        
        Example:
            >>> address.full_address
            'Rua das Flores, 123 - São Paulo/SP'
        """
        return f"{self.street}, {self.number} - {self.city}/{self.state}"