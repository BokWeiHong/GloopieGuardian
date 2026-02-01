from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
import os
from datetime import timedelta
from django.utils import timezone
import requests
from kismet.parser import import_kismet_file

class Command(BaseCommand):
    help = 'Import a Kismet sqlite DB into Django models. Usage: python manage.py import_kismet /path/to/kismet.db'

    def add_arguments(self, parser):
        parser.add_argument('db_path', type=str, help='Path to the Kismet sqlite DB file')

    def handle(self, *args, **options):
        db_path = options['db_path']
        if not os.path.isfile(db_path):
            raise CommandError(f"DB file not found: {db_path}")

        self.stdout.write(self.style.NOTICE(f"Importing {db_path} ..."))
        try:
            import_kismet_file(db_path)
        except Exception as e:
            raise CommandError(f"Import failed: {e}")
        self.stdout.write(self.style.SUCCESS("Import completed successfully."))
