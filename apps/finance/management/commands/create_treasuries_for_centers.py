"""
Management command to create default treasuries for all existing centers.
Usage: python manage.py create_treasuries_for_centers
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from apps.core.models import Center
from apps.finance.models import Treasury


class Command(BaseCommand):
    help = 'Create default treasuries for all existing centers that don\'t have one'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force create treasury even if one already exists',
        )

    @transaction.atomic
    def handle(self, *args, **options):
        force = options.get('force', False)
        created_count = 0
        skipped_count = 0

        for center in Center.objects.all():
            if force:
                # Delete existing and recreate
                Treasury.objects.filter(center=center).delete()
                treasury = Treasury.objects.create(
                    center=center,
                    name='الخزينة الرئيسية',
                    initial_balance=0,
                    balance=0,
                )
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Created treasury for {center.name}')
                )
            else:
                # Get or create (skip if exists)
                treasury, was_created = Treasury.objects.get_or_create(
                    center=center,
                    defaults={
                        'name': 'الخزينة الرئيسية',
                        'initial_balance': 0,
                        'balance': 0,
                    }
                )
                if was_created:
                    created_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(f'✓ Created treasury for {center.name}')
                    )
                else:
                    skipped_count += 1
                    self.stdout.write(
                        self.style.WARNING(f'⊘ Treasury already exists for {center.name}')
                    )

        self.stdout.write(
            self.style.SUCCESS(
                f'\nSummary: {created_count} created, {skipped_count} skipped'
            )
        )
