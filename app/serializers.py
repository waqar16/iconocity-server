from rest_framework import serializers
from app.models import Project

class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        exclude = ['created_at', 'updated_at']

class ProjectListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ['id', 'name']

class ProjectIconListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ['f_icons']