from rest_framework import serializers
from .models import Application


class ApplicationListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Application
        fields = ['id', 'title', 'status', 'owner_id', 'created_at', 'updated_at']
        read_only_fields = ['id', 'status', 'owner_id', 'created_at', 'updated_at']


class ApplicationDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Application
        fields = ['id', 'title', 'content', 'status', 'owner_id', 'created_at', 'updated_at']
        read_only_fields = ['id', 'status', 'owner_id', 'created_at', 'updated_at']

    def validate(self, attrs):
        request = self.context.get('request')
        if not request or not hasattr(request, 'user'):
            return attrs

        if self.instance is not None:
            if self.instance.status != Application.Status.DRAFT:
                raise serializers.ValidationError('Application may only be edited while in DRAFT state')
            if self.instance.owner_id != request.user.id:
                raise serializers.ValidationError('Only the owner may edit the draft')

        return attrs


class ApplicationCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Application
        fields = ['id', 'title', 'content']
        read_only_fields = ['id']

    def create(self, validated_data):
        request = self.context.get('request')
        owner = getattr(request, 'user', None)
        return Application.objects.create(owner=owner, **validated_data)
