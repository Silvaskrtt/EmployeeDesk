from django.db import models
from employee.models import Employee

class Department(models.Model):
    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name='Nome do Departamento'
    )
    
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name='Descrição'
    )
    
    manager = models.ForeignKey(
        Employee, 
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='managed_departments',
        verbose_name='Gestor'
    )
    
    active = models.BooleanField(
        default=True,
        verbose_name='Ativo'
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Criado em'
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Atualizado em'
    )
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = 'Departamento'
        verbose_name_plural = 'Departamentos'
        ordering = ['name']