from django.core.management.commands.runserver import Command as BaseRunserverCommand


class Command(BaseRunserverCommand):
	"""Override default runserver port to 8005."""
	default_port = '8005'