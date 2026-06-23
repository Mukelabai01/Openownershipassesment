"""Initial migration for audits app."""
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='AuditLog',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('application_id', models.UUIDField()),
                ('from_status', models.CharField(blank=True, max_length=32, null=True)),
                ('to_status', models.CharField(max_length=32)),
                ('comment', models.TextField(blank=True, null=True)),
                ('metadata', models.JSONField(blank=True, default=dict)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('actor', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='auth.user')),
            ],
        ),
        migrations.AddIndex(
            model_name='auditlog',
            index=models.Index(fields=['application_id', 'created_at'], name='audits_audi_applica_idx'),
        ),
    ]
