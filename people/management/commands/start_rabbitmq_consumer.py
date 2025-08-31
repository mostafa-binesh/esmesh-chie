import os
import time
from django.core.management.base import BaseCommand
from people.tasks import start_rabbitmq_consumer

class Command(BaseCommand):
    help = 'Starts the RabbitMQ consumer for import processing'

    def handle(self, *args, **options):
        self.stdout.write('Starting RabbitMQ consumer...')
        self.stdout.write('Press Ctrl+C to exit')
        
        while True:
            try:
                start_rabbitmq_consumer()
            except KeyboardInterrupt:
                self.stdout.write('Consumer stopped by user')
                break
            except Exception as e:
                self.stdout.write(f'Error: {e}. Restarting in 5 seconds...')
                time.sleep(5)
