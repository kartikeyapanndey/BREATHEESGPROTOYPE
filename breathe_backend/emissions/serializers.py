from rest_framework import serializers
from .models import Tenant, DataSource, EmissionRecord

class TenantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tenant
        fields = '__all__'

class DataSourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = DataSource
        fields = '__all__'

class EmissionRecordSerializer(serializers.ModelSerializer):
    source_type = serializers.CharField(source='source.source_type', read_only=True)
    file_name = serializers.CharField(source='source.file_name', read_only=True)
    upload_date = serializers.DateTimeField(source='source.upload_date', read_only=True)

    class Meta:
        model = EmissionRecord
        fields = '__all__'

class ApprovalSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=['APPROVED', 'REJECTED'])
    quantity = serializers.DecimalField(max_digits=15, decimal_places=4, required=False)
    unit = serializers.CharField(max_length=50, required=False)
