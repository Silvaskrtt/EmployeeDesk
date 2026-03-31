"""
Módulo de gerenciamento de documentos.

Este módulo fornece a estrutura para armazenar e gerenciar documentos relacionados
aos funcionários da organização, incluindo contratos, certificados e demais arquivos.
"""

# Imports padrão da linguagem
import os

# Imports de terceiros
from django.conf import settings
from django.db import models
from django.core.exceptions import ValidationError


class Document(models.Model):
    """
    Modelo responsável pelo gerenciamento de documentos dos funcionários.

    Esta classe representa a entidade de documentos no sistema, armazenando
    informações como tipo, nome, caminho do arquivo e metadados relevantes.
    Segue o padrão de soft delete através do campo is_active e mantém
    auditoria completa com timestamps de criação e atualização.
    """

    # -------------------------------------------------------------------------
    #  CONSTANTES DA CLASSE
    # -------------------------------------------------------------------------

    class DocumentType(models.TextChoices):
        """
        Enumeração que define os tipos permitidos de documentos.

        Utiliza TextChoices do Django para garantir integridade dos dados
        e fornecer opções para selects no frontend. Centraliza os tipos
        disponíveis evitando strings mágicas no código.
        """
        CONTRACT = 'CONTRACT', 'Contrato'
        CERTIFICATE = 'CERTIFICATE', 'Certificado'
        IDENTITY = 'IDENTITY', 'Documento de Identidade'
        RESUME = 'RESUME', 'Currículo'
        MEDICAL = 'MEDICAL', 'Documento Médico'
        OTHER = 'OTHER', 'Outros'

    # -------------------------------------------------------------------------
    #  CAMPOS OBRIGATÓRIOS
    # -------------------------------------------------------------------------

    document_type = models.CharField(
        max_length=50,
        choices=DocumentType.choices,
        verbose_name='Tipo de Documento'
    )
    """Tipo do documento utilizando o enum DocumentType para validação."""

    name = models.CharField(
        max_length=200,
        verbose_name='Nome do Documento'
    )
    """Nome descritivo do documento para fácil identificação."""

    file_path = models.CharField(
        max_length=500,
        verbose_name='Caminho do Arquivo'
    )
    """
    Caminho absoluto ou relativo onde o arquivo físico está armazenado.
    Utiliza sistema de arquivos separado do banco de dados para melhor performance.
    """

    file_type = models.CharField(
        max_length=50,
        verbose_name='Tipo de Arquivo',
        help_text='Ex: PDF, DOC, JPEG'
    )
    """Extensão ou tipo MIME do arquivo para validações e renderização."""

    # -------------------------------------------------------------------------
    #  CAMPOS OPCIONAIS
    # -------------------------------------------------------------------------

    file_size = models.IntegerField(
        null=True,
        blank=True,
        verbose_name='Tamanho do Arquivo (bytes)'
    )
    """
    Tamanho do arquivo em bytes. Permite nulo para compatibilidade
    com migrações de dados existentes.
    """

    expiration_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='Data de Validade',
        help_text='Preencher se o documento tem validade'
    )
    """
    Data de validade do documento. Utilizado para documentos como certificados,
    licenças e contratos com prazo determinado.
    """

    is_active = models.BooleanField(
        default=True,
        verbose_name='Ativo',
        help_text='Documentos inativos não são considerados em validações'
    )
    """
    Flag de soft delete. Documentos marcados como inativos são mantidos
    no banco de dados mas excluídos das consultas padrão.
    """

    # -------------------------------------------------------------------------
    #  TIMESTAMPS DE AUDITORIA
    # -------------------------------------------------------------------------

    uploaded_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Data de Upload'
    )
    """Data e hora do upload do arquivo."""

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Criado em'
    )
    """Timestamp de criação do registro no banco de dados."""

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Atualizado em'
    )
    """Timestamp da última atualização do registro."""

    # -------------------------------------------------------------------------
    #  CHAVES ESTRANGEIRAS
    # -------------------------------------------------------------------------

    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='uploaded_documents',
        verbose_name='Enviado por'
    )
    """
    Usuário responsável pelo upload do documento.
    SET_NULL mantém o histórico mesmo se o usuário for removido.
    """

    employee = models.ForeignKey(
        'employee.Employee',
        on_delete=models.CASCADE,
        related_name='documents',
        verbose_name='Funcionário'
    )
    """
    Funcionário ao qual o documento pertence.
    CASCADE garante que documentos sejam removidos ao excluir o funcionário,
    mantendo a integridade referencial.
    """

    # -------------------------------------------------------------------------
    #  CONFIGURAÇÕES DO MODELO
    # -------------------------------------------------------------------------

    class Meta:
        """Configurações de metadados do modelo Document."""
        verbose_name = 'Documento'
        verbose_name_plural = 'Documentos'

        # Índices para otimização de consultas frequentes
        indexes = [
            models.Index(fields=['employee'], name='idx_document_employee'),
            models.Index(fields=['document_type'], name='idx_document_type'),
            models.Index(fields=['expiration_date'], name='idx_document_expiration'),
            models.Index(fields=['is_active'], name='idx_document_active'),
            models.Index(fields=['employee', 'is_active'], name='idx_document_employee_active'),
        ]

        # Ordenação padrão para listagens
        ordering = ['-uploaded_at', 'employee', 'document_type']

    # -------------------------------------------------------------------------
    #  MÉTODOS PÚBLICOS
    # -------------------------------------------------------------------------

    def __str__(self):
        """
        Representação em string do objeto.

        Returns:
            str: Nome do documento concatenado com o funcionário associado.
        """
        return f"{self.name} - {self.employee}"

    def clean(self):
        """
        Realiza validações adicionais no modelo antes da persistência.

        Este método é chamado pelo full_clean() e deve ser utilizado para
        validações que envolvem múltiplos campos ou regras de negócio
        complexas que não podem ser expressas apenas com constraints do banco.

        Raises:
            ValidationError: Quando alguma das validações não é satisfeita.
        """
        super().clean()

        # Validação 1: Limite de tamanho do arquivo (10MB)
        if self.file_size and self.file_size > 10 * 1024 * 1024:
            raise ValidationError({
                'file_size': 'Tamanho do arquivo não pode exceder 10MB'
            })

        # Validação 2: Data de expiração não pode ser passada
        if self.expiration_date and self.expiration_date < models.DateField().today():
            raise ValidationError({
                'expiration_date': 'Data de validade não pode ser anterior à data atual'
            })

        # Validação 3: Tipos de arquivo permitidos
        allowed_types = ['PDF', 'DOC', 'DOCX', 'JPG', 'JPEG', 'PNG']
        if self.file_type and self.file_type.upper() not in allowed_types:
            raise ValidationError({
                'file_type': f'Tipo de arquivo não permitido. Permitidos: {", ".join(allowed_types)}'
            })

    def save(self, *args, **kwargs):
        """
        Sobrescreve o método save para garantir validações antes da persistência.

        Garante que todas as validações definidas no método clean() sejam
        executadas antes de salvar o registro no banco de dados.
        """
        self.full_clean()
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """
        Sobrescreve o método delete para remover o arquivo físico do sistema.

        Remove o arquivo associado ao registro do sistema de arquivos antes
        de deletar o registro do banco de dados. Implementa tratamento de
        exceções para evitar falhas em caso de arquivo inexistente.
        """
        if self.file_path and os.path.exists(self.file_path):
            try:
                os.remove(self.file_path)
            except OSError:
                # TODO: Implementar logging adequado para monitoramento de erros
                # Importar logger e registrar o erro para análise posterior
                pass
        super().delete(*args, **kwargs)

    # -------------------------------------------------------------------------
    #  PROPRIEDADES COMPUTADAS
    # -------------------------------------------------------------------------

    @property
    def is_expired(self):
        """
        Verifica se o documento está expirado com base na data de validade.

        Returns:
            bool: True se o documento possui data de validade e esta é anterior
                  à data atual, False caso contrário.
        """
        if self.expiration_date:
            return self.expiration_date < models.DateField().today()
        return False

    @property
    def file_extension(self):
        """
        Extrai a extensão do arquivo a partir do caminho.

        Returns:
            str: Extensão do arquivo em minúsculo, incluindo o ponto.
        """
        return os.path.splitext(self.file_path)[1].lower()

    @property
    def formatted_file_size(self):
        """
        Retorna o tamanho do arquivo em formato legível para humanos.

        Converte bytes para a unidade mais adequada (B, KB, MB, GB, TB).

        Returns:
            str: Tamanho formatado com duas casas decimais e a unidade,
                 ou "Desconhecido" se o tamanho não estiver disponível.
        """
        if not self.file_size:
            return "Desconhecido"

        size = self.file_size
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.2f} {unit}"
            size /= 1024.0
        return f"{size:.2f} TB"

    # -------------------------------------------------------------------------
    #  MÉTODOS DE CLASSE (FACADES)
    # -------------------------------------------------------------------------

    @classmethod
    def get_active_documents(cls, employee=None):
        """
        Retorna todos os documentos ativos, opcionalmente filtrados por funcionário.

        Método de conveniência para consultas frequentes no sistema,
        encapsulando a lógica de filtro por is_active.

        Args:
            employee (Employee, optional): Funcionário para filtrar os documentos.

        Returns:
            QuerySet: QuerySet com documentos ativos, filtrados pelo funcionário
                      se fornecido.
        """
        queryset = cls.objects.filter(is_active=True)
        if employee:
            queryset = queryset.filter(employee=employee)
        return queryset

    @classmethod
    def get_expiring_soon(cls, days=30):
        """
        Retorna documentos que expiram nos próximos dias informados.

        Útil para sistemas de notificação e alertas sobre documentos
        que estão prestes a vencer.

        Args:
            days (int): Número de dias para considerar como "em breve".
                       Padrão é 30 dias.

        Returns:
            QuerySet: QuerySet ordenada por data de expiração contendo
                      documentos ativos que vencem no período informado.
        """
        from django.utils import timezone
        from datetime import timedelta

        today = timezone.now().date()
        expiring_date = today + timedelta(days=days)

        return cls.objects.filter(
            is_active=True,
            expiration_date__isnull=False,
            expiration_date__gte=today,
            expiration_date__lte=expiring_date
        ).order_by('expiration_date')