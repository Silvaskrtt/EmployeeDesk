from django.conf import settings
from django.db import models
from django.core.exceptions import ValidationError
import os

class Document(models.Model):
    """
    Documentos de funcionários
    Gerencia arquivos como contratos, certificados, etc.
    """
    
    # Tipos de documento pré-definidos (boa prática)
    class DocumentType(models.TextChoices):
        CONTRACT = 'CONTRACT', 'Contrato'
        CERTIFICATE = 'CERTIFICATE', 'Certificado'
        IDENTITY = 'IDENTITY', 'Documento de Identidade'
        RESUME = 'RESUME', 'Currículo'
        MEDICAL = 'MEDICAL', 'Documento Médico'
        OTHER = 'OTHER', 'Outros'
    
    # Campos obrigatórios
    document_type = models.CharField(
        max_length=50,
        choices=DocumentType.choices,
        verbose_name='Tipo de Documento'
    )
    
    name = models.CharField(
        max_length=200,
        verbose_name='Nome do Documento'
    )
    
    file_path = models.CharField(
        max_length=500,
        verbose_name='Caminho do Arquivo'
    )
    
    file_type = models.CharField(
        max_length=50,
        verbose_name='Tipo de Arquivo',
        help_text='Ex: PDF, DOC, JPEG'
    )
    
    # Campos opcionais
    file_size = models.IntegerField(
        null=True,
        blank=True,
        verbose_name='Tamanho do Arquivo (bytes)'
    )
    
    expiration_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='Data de Validade',
        help_text='Preencher se o documento tem validade'
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name='Ativo',
        help_text='Documentos inativos não são considerados em validações'
    )
    
    # Timestamps de auditoria
    uploaded_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Data de Upload'
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Criado em'
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Atualizado em'
    )
    
    # Chaves estrangeiras - CORRIGIDAS
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='uploaded_documents',
        verbose_name='Enviado por'
    )
    
    employee = models.ForeignKey(
        'employee.Employee',
        on_delete=models.CASCADE,
        related_name='documents',
        verbose_name='Funcionário'
    )
    
    class Meta:
        verbose_name = 'Documento'
        verbose_name_plural = 'Documentos'
        
        indexes = [
            models.Index(fields=['employee'], name='idx_document_employee'),
            models.Index(fields=['document_type'], name='idx_document_type'),
            models.Index(fields=['expiration_date'], name='idx_document_expiration'),
            # Índices adicionais para otimização
            models.Index(fields=['is_active'], name='idx_document_active'),
            models.Index(fields=['employee', 'is_active'], name='idx_document_employee_active'),
        ]
        
        # Ordenação padrão
        ordering = ['-uploaded_at', 'employee', 'document_type']
    
    def __str__(self):
        return f"{self.name} - {self.employee}"
    
    def clean(self):
        """Validações adicionais"""
        super().clean()
        
        # 1. Validação de tamanho de arquivo (exemplo: limite 10MB)
        if self.file_size and self.file_size > 10 * 1024 * 1024:  # 10MB
            raise ValidationError({
                'file_size': 'Tamanho do arquivo não pode exceder 10MB'
            })
        
        # 2. Validação de data de expiração
        if self.expiration_date and self.expiration_date < models.DateField().today():
            raise ValidationError({
                'expiration_date': 'Data de validade não pode ser anterior à data atual'
            })
        
        # 3. Validação de tipo de arquivo (lista permitida)
        allowed_types = ['PDF', 'DOC', 'DOCX', 'JPG', 'JPEG', 'PNG']
        if self.file_type and self.file_type.upper() not in allowed_types:
            raise ValidationError({
                'file_type': f'Tipo de arquivo não permitido. Permitidos: {", ".join(allowed_types)}'
            })
    
    def save(self, *args, **kwargs):
        self.full_clean()  # Executa validações antes de salvar
        super().save(*args, **kwargs)
    
    def delete(self, *args, **kwargs):
        """
        Remove o arquivo físico ao deletar o registro
        """
        if self.file_path and os.path.exists(self.file_path):
            try:
                os.remove(self.file_path)
            except OSError:
                pass  # Log de erro seria ideal aqui
        super().delete(*args, **kwargs)
    
    @property
    def is_expired(self):
        """Verifica se o documento está expirado"""
        if self.expiration_date:
            return self.expiration_date < models.DateField().today()
        return False
    
    @property
    def file_extension(self):
        """Retorna a extensão do arquivo"""
        return os.path.splitext(self.file_path)[1].lower()
    
    @property
    def formatted_file_size(self):
        """Retorna o tamanho do arquivo formatado"""
        if not self.file_size:
            return "Desconhecido"
        
        for unit in ['B', 'KB', 'MB', 'GB']:
            if self.file_size < 1024.0:
                return f"{self.file_size:.2f} {unit}"
            self.file_size /= 1024.0
        return f"{self.file_size:.2f} TB"
    
    @classmethod
    def get_active_documents(cls, employee=None):
        """Retorna documentos ativos"""
        queryset = cls.objects.filter(is_active=True)
        if employee:
            queryset = queryset.filter(employee=employee)
        return queryset
    
    @classmethod
    def get_expiring_soon(cls, days=30):
        """Retorna documentos que expiram em breve"""
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