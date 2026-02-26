import subprocess
from django.core.management.base import BaseCommand, CommandError

class Command(BaseCommand):
    help = 'Stops the background trackerjacker process and disables monitor mode.'

    def add_arguments(self, parser):
        parser.add_argument('interface', type=str, help='The monitor interface to stop (e.g., wlan1mon)')

    def handle(self, *args, **options):
        mon_iface = options['interface']

        try:
            kill_cmd = ['sudo', 'pkill', '-f', 'trackerjacker']
            subprocess.run(kill_cmd, check=True, capture_output=True)
            self.stdout.write(self.style.SUCCESS('Successfully stopped trackerjacker.'))
            
        except subprocess.CalledProcessError:
            self.stdout.write(self.style.NOTICE('No running trackerjacker process found. Moving on.'))

        try:
            airmon_cmd = ['sudo', 'airmon-ng', 'stop', mon_iface]
            subprocess.run(airmon_cmd, check=True, capture_output=True, text=True)
            self.stdout.write(self.style.SUCCESS(f'Monitor mode disabled. {mon_iface} network interface restored.'))
            
        except subprocess.CalledProcessError as e:
            self.stderr.write(self.style.ERROR(f'Failed to stop monitor mode: {e.stderr}'))
            raise CommandError('Encountered an error while trying to stop airmon-ng.')