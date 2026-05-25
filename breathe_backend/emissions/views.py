import csv
import json
import datetime
from decimal import Decimal, InvalidOperation
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from .models import Tenant, DataSource, EmissionRecord
from .serializers import EmissionRecordSerializer, ApprovalSerializer

def parse_date(date_str):
    if not date_str:
        return None
    try:
        # Try DD.MM.YYYY (SAP common)
        return datetime.datetime.strptime(date_str, '%d.%m.%Y').date()
    except ValueError:
        pass
    try:
        # Try YYYY-MM-DD
        return datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        pass
    try:
        # Try ISO format
        return datetime.datetime.fromisoformat(date_str.replace("Z", "+00:00")).date()
    except ValueError:
        return None

class EmissionRecordViewSet(viewsets.ModelViewSet):
    queryset = EmissionRecord.objects.all().order_by('-source__upload_date', '-id')
    serializer_class = EmissionRecordSerializer

    @action(detail=False, methods=['post'])
    def upload(self, request):
        tenant_id = request.data.get('tenant_id')
        source_type = request.data.get('source_type')
        uploaded_file = request.FILES.get('file')

        if not tenant_id or not source_type or not uploaded_file:
            return Response({"error": "Missing tenant_id, source_type, or file"}, status=status.HTTP_400_BAD_REQUEST)

        tenant, _ = Tenant.objects.get_or_create(id=tenant_id, defaults={'name': 'Default Tenant'})
        
        data_source = DataSource.objects.create(
            tenant=tenant,
            source_type=source_type,
            file_name=uploaded_file.name
        )

        records_created = 0

        try:
            if source_type == 'SAP_FLAT_FILE':
                decoded_file = uploaded_file.read().decode('utf-8').splitlines()
                reader = csv.DictReader(decoded_file, delimiter=',')
                if not reader.fieldnames:
                    reader = csv.DictReader(decoded_file, delimiter='\t') # fallback to TSV
                
                for row in reader:
                    validation_errors = []
                    
                    # Mapping SAP fields
                    raw_date = row.get('BUDAT')
                    parsed_date = parse_date(raw_date) if raw_date else None
                    if not parsed_date:
                        validation_errors.append("Invalid or missing date (BUDAT)")

                    raw_qty = row.get('MENGE')
                    qty = None
                    try:
                        qty = Decimal(raw_qty) if raw_qty else None
                    except InvalidOperation:
                        validation_errors.append(f"Invalid quantity: {raw_qty}")

                    unit = row.get('MEINS')
                    if not unit:
                        validation_errors.append("Missing unit (MEINS)")
                    
                    plant = row.get('WERKS')
                    if not plant:
                        validation_errors.append("Missing plant code (WERKS)")
                    elif plant not in ['1000', '2000']:
                        validation_errors.append(f"Unknown plant code: {plant}")

                    EmissionRecord.objects.create(
                        tenant=tenant,
                        source=data_source,
                        category='SCOPE_1',
                        original_payload=row,
                        start_date=parsed_date,
                        quantity=qty,
                        unit=unit,
                        validation_errors=validation_errors
                    )
                    records_created += 1

            elif source_type == 'UTILITY_CSV':
                decoded_file = uploaded_file.read().decode('utf-8').splitlines()
                reader = csv.DictReader(decoded_file)
                for row in reader:
                    validation_errors = []
                    
                    start_date = parse_date(row.get('Billing Period Start'))
                    end_date = parse_date(row.get('Billing Period End'))
                    
                    if not start_date or not end_date:
                        validation_errors.append("Missing or invalid billing period dates")
                        
                    raw_qty = row.get('Total Usage (kWh)')
                    qty = None
                    try:
                        qty = Decimal(raw_qty) if raw_qty else None
                    except InvalidOperation:
                        validation_errors.append(f"Invalid usage quantity: {raw_qty}")
                        
                    unit = 'kWh' # Implied by header

                    EmissionRecord.objects.create(
                        tenant=tenant,
                        source=data_source,
                        category='SCOPE_2',
                        original_payload=row,
                        start_date=start_date,
                        end_date=end_date,
                        quantity=qty,
                        unit=unit,
                        validation_errors=validation_errors
                    )
                    records_created += 1

            elif source_type == 'CONCUR_JSON':
                data = json.load(uploaded_file)
                segments = data.get('Segments', [])
                if not isinstance(segments, list):
                    segments = [data] # Fallback if single dict
                    
                for seg in segments:
                    validation_errors = []
                    seg_type = seg.get('SegmentType', 'Unknown')
                    
                    # Using overall trip date as fallback if segment date is missing
                    date_str = seg.get('StartDate') or data.get('StartDate')
                    start_date = parse_date(date_str)
                    
                    qty = None
                    unit = None
                    
                    if seg_type == 'Air':
                        dist = seg.get('Distance')
                        if not dist:
                            validation_errors.append("Distance missing, estimation required based on airport codes")
                        else:
                            try:
                                qty = Decimal(dist)
                                unit = 'km'
                            except InvalidOperation:
                                validation_errors.append(f"Invalid distance: {dist}")
                                
                    elif seg_type == 'Hotel':
                        nights = seg.get('Nights')
                        if not nights:
                            validation_errors.append("Missing number of nights")
                        else:
                            try:
                                qty = Decimal(nights)
                                unit = 'nights'
                            except InvalidOperation:
                                validation_errors.append(f"Invalid nights: {nights}")

                    EmissionRecord.objects.create(
                        tenant=tenant,
                        source=data_source,
                        category='SCOPE_3',
                        original_payload=seg,
                        start_date=start_date,
                        quantity=qty,
                        unit=unit,
                        validation_errors=validation_errors
                    )
                    records_created += 1
            else:
                return Response({"error": "Unknown source type"}, status=status.HTTP_400_BAD_REQUEST)

            data_source.status = 'COMPLETED'
            data_source.save()
            return Response({"message": f"Successfully parsed {records_created} records"}, status=status.HTTP_200_OK)

        except Exception as e:
            data_source.status = 'FAILED'
            data_source.save()
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        record = self.get_object()
        serializer = ApprovalSerializer(data=request.data)
        if serializer.is_valid():
            new_status = serializer.validated_data['status']
            new_quantity = serializer.validated_data.get('quantity')
            new_unit = serializer.validated_data.get('unit')
            
            audit_entry = {
                "timestamp": timezone.now().isoformat(),
                "action": f"Status changed to {new_status}"
            }
            
            if new_quantity is not None and new_quantity != record.quantity:
                audit_entry["quantity_changed"] = f"{record.quantity} -> {new_quantity}"
                record.quantity = new_quantity
                
            if new_unit and new_unit != record.unit:
                audit_entry["unit_changed"] = f"{record.unit} -> {new_unit}"
                record.unit = new_unit
                
            record.status = new_status
            
            audit_trail = list(record.audit_trail)
            audit_trail.append(audit_entry)
            record.audit_trail = audit_trail
            record.save()
            
            return Response(EmissionRecordSerializer(record).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
