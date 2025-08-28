from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator


# Create your models here.
class User(AbstractUser):
    # Custom username field with new validators
    username_validator = RegexValidator(r'^[\w.@+\-\_\s]+$',
                                        'Enter a valid username. This value may contain only letters, numbers, and @/./+/-/_ characters.')

    username = models.CharField(
        max_length=150,
        unique=True,
        help_text='Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.',
        validators=[username_validator],
        error_messages={
            'unique': "A user with that username already exists.",
        },
    )

    @property
    def full_name(self):
        return f'{self.first_name} {self.last_name}'
