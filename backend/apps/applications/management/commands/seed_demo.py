from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.applications.models import Application

User = get_user_model()


class Command(BaseCommand):
    help = 'Seed the database with demo data (applicant and reviewer users, sample applications)'

    def handle(self, *args, **options):
        # Create or get demo users
        alice, created = User.objects.get_or_create(
            username='alice',
            defaults={
                'email': 'alice@example.com',
                'first_name': 'Alice',
                'last_name': 'Developer',
            }
        )
        if created:
            alice.set_password('password123')
            alice.save()
            self.stdout.write(self.style.SUCCESS(f'Created user: {alice.username}'))
        else:
            self.stdout.write(f'User already exists: {alice.username}')

        bob, created = User.objects.get_or_create(
            username='bob',
            defaults={
                'email': 'bob@example.com',
                'first_name': 'Bob',
                'last_name': 'Reviewer',
                'is_staff': True,
            }
        )
        if created:
            bob.set_password('password123')
            bob.save()
            self.stdout.write(self.style.SUCCESS(f'Created user: {bob.username}'))
        else:
            self.stdout.write(f'User already exists: {bob.username}')

        # Create sample applications
        app1_data = {
            'owner': alice,
            'title': 'Project Alpha - ML Pipeline',
            'content': {
                'description': 'A machine learning pipeline for data processing and model training.',
                'technologies': ['Python', 'TensorFlow', 'Kubernetes'],
                'team_size': 5,
                'budget_usd': 50000,
            }
        }
        app1, created = Application.objects.get_or_create(
            owner=alice,
            title='Project Alpha - ML Pipeline',
            defaults=app1_data
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created application: {app1.title}'))
        else:
            self.stdout.write(f'Application already exists: {app1.title}')

        app2_data = {
            'owner': alice,
            'title': 'Project Beta - Web Portal',
            'content': {
                'description': 'A full-stack web portal for customer management.',
                'technologies': ['React', 'Django', 'PostgreSQL'],
                'team_size': 8,
                'budget_usd': 100000,
            }
        }
        app2, created = Application.objects.get_or_create(
            owner=alice,
            title='Project Beta - Web Portal',
            defaults=app2_data
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created application: {app2.title}'))
        else:
            self.stdout.write(f'Application already exists: {app2.title}')

        self.stdout.write(self.style.SUCCESS('\n✓ Demo data seeded successfully'))
        self.stdout.write('Users:')
        self.stdout.write(f'  - alice (applicant): password123')
        self.stdout.write(f'  - bob (reviewer): password123')
        self.stdout.write('Applications:')
        self.stdout.write(f'  - {app1.title}')
        self.stdout.write(f'  - {app2.title}')
