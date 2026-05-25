import uuid
from django.db import models

class Tenant(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class DataSource(models.Model):
    SOURCE_TYPES = (
        ('SAP_FLAT_FILE', 'SAP Flat File'),
        ('UTILITY_CSV', 'Utility CSV'),
        ('CONCUR_JSON', 'Concur JSON'),
    )
    STATUS_CHOICES = (
        ('PROCESSING', 'Processing'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
    )
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    source_type = models.CharField(max_length=50, choices=SOURCE_TYPES)
    upload_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PROCESSING')
    file_name = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.source_type} - {self.file_name}"

class EmissionRecord(models.Model):
    CATEGORY_CHOICES = (
        ('SCOPE_1', 'Scope 1'),
        ('SCOPE_2', 'Scope 2'),
        ('SCOPE_3', 'Scope 3'),
    )
    STATUS_CHOICES = (
        ('PENDING_REVIEW', 'Pending Review'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    )
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    source = models.ForeignKey(DataSource, on_delete=models.CASCADE)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    
    # Store the exact row parsed for source-of-truth
    original_payload = models.JSONField(default=dict)
    
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    
    quantity = models.DecimalField(max_digits=15, decimal_places=4, null=True, blank=True)
    unit = models.CharField(max_length=50, null=True, blank=True)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING_REVIEW')
    validation_errors = models.JSONField(default=list, blank=True)
    audit_trail = models.JSONField(default=list, blank=True)

    def __str__(self):
        return f"{self.category} - {self.quantity} {self.unit} ({self.status})"
