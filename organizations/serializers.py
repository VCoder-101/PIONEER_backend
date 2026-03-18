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
    organizationStatus = serializers.CharField(source='organization_status', read_only=True)
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
    countServices = serializers.SerializerMethodField()
    summaryPrice = serializers.SerializerMethodField()

    class Meta:
        model = Organization
        fields = [
            'id', 'name', 'shortName', 'organizationStatus', 'organizationDateApproved',
            'owner', 'owner_email', 'city', 'address', 'phone', 'email', 
            'description', 'is_active', 'created_at', 'organizationType',
            'orgOgrn', 'orgInn', 'orgKpp', 'wheelDiameters', 'countServices', 'summaryPrice'
        ]
        read_only_fields = ['id', 'owner', 'created_at', 'organizationStatus', 'organizationDateApproved', 'countServices', 'summaryPrice']
    
    def get_countServices(self, obj):
        """Вычисляет количество активных услуг организации"""
        return obj.services.filter(is_active=True).count()
    
    def get_summaryPrice(self, obj):
        """Вычисляет суммарную стоимость всех активных услуг организации"""
        from django.db.models import Sum
        total = obj.services.filter(is_active=True).aggregate(total=Sum('price'))['total']
        return str(total) if total else "0.00"
    
    def validate_name(self, value):
        """
        Проверяет уникальность названия организации.
        При обновлении исключает текущую организацию из проверки.
        """
        # Нормализуем название (убираем лишние пробелы, приводим к нижнему регистру для сравнения)
        normalized_name = value.strip()
        
        # Проверяем существование организации с таким названием
        queryset = Organization.objects.filter(name__iexact=normalized_name)
        
        # При обновлении исключаем текущую организацию
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)
        
        if queryset.exists():
            raise serializers.ValidationError(
                f"Организация с названием '{normalized_name}' уже существует. Пожалуйста, выберите другое название."
            )
        
        return normalized_name
    
    def validate_short_name(self, value):
        """
        Проверяет уникальность короткого названия организации (если указано).
        """
        if not value or not value.strip():
            return value
        
        normalized_short_name = value.strip()
        
        # Проверяем существование организации с таким коротким названием
        queryset = Organization.objects.filter(short_name__iexact=normalized_short_name)
        
        # При обновлении исключаем текущую организацию
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)
        
        if queryset.exists():
            raise serializers.ValidationError(
                f"Организация с коротким названием '{normalized_short_name}' уже существует. Пожалуйста, выберите другое название."
            )
        
        return normalized_short_name
