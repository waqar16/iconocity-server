from rest_framework import serializers
from app.models import Project

class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        exclude = ['created_at', 'updated_at']

class ProjectWithHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        exclude = ['created_at', 'updated_at']

    def save(self, **kwargs):
        # Get the instance if it exists
        instance = self.instance
        instance.save_with_historical_record()

class ProjectListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ['id', 'name']

class ProjectIconListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ['f_icons']

class ProjectIconAttributesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ['attributes']

class ProjectHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Project.history.model
        fields = ['history_id', 'name', 'f_icons', 'history_date', 'id']


class ProjectUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ['f_icons', 'attributes']

    def save(self, **kwargs):
        # Get the instance if it exists
        instance = self.instance
        instance.save_with_historical_record()