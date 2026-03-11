from rest_framework import serializers
from .models import Organization, City


class CitySerializer(serializers.ModelSerializer):
    class Meta:
        model = City
        fields = ['id', 'name', 'region', 'country', 'is_active', 'created_at']
        read_only_fields = ['id', 'created_at']


class OrganizationSerializer(serializers.ModelSerializer):
    owner_email = serializers.EmailField(source='owner.email', read_only=True)
    shortName = serializers.CharField(source='short_name')
    organizationStatus = serializers.CharField(source='organization_status')
    organizationDateApproved = serializers.DateTimeField(
        source='organization_date_approved', 
        format='%d/%m/%Y',
        read_only=True
    )
    organizationType = serializers.CharField(source='organization_type')
    orgOgrn = serializers.CharField(source='org_ogrn')
    orgInn = serializers.CharField(source='org_inn')
    orgKpp = serializers.CharField(source='org_kpp')
    wheelDiameters = serializers.JSONField(source='wheel_diameters', required=False)
    countServices = serializers.IntegerField(source='count_services', read_only=True)
    summaryPrice = serializers.DecimalField(
        source='summary_price', 
        max_digits=10, 
        decimal_places=2, 
        read_only=True
    )

    class Meta:
        model = Organization
        fields = [
            'id', 'name', 'shortName', 'organizationStatus', 'organizationDateApproved',
            'owner', 'owner_email', 'city', 'address', 'phone', 'email', 
            'description', 'is_active', 'created_at', 'organizationType',
            'orgOgrn', 'orgInn', 'orgKpp', 'wheelDiameters', 'countServices', 'summaryPrice'
        ]
        read_only_fields = ['id', 'created_at', 'organizationDateApproved', 'countServices', 'summaryPrice']
