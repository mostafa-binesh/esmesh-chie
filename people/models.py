from django.db import models
from django.core.validators import RegexValidator


class Source(models.TextChoices):
	UNKNOWN = 'UNKNOWN', 'Unknown'
	MELLI = 'MELLI', 'Melli'
	SADERAT = 'SADERAT', 'Saderat'
	MELLAT = 'MELLAT', 'Mellat'


class Person(models.Model):
	first_name = models.CharField(max_length=150, blank=True)
	last_name = models.CharField(max_length=150, blank=True, null=True)
	national_code = models.CharField(
		max_length=10,
		help_text='10-digit national identification code',
		validators=[RegexValidator(r'^\d{10}$', 'National code must be 10 digits')]
	)
	birthdate = models.DateField(null=True, blank=True)
	source = models.CharField(max_length=32, choices=Source.choices, default=Source.UNKNOWN)

	class Meta:
		constraints = [
			models.UniqueConstraint(fields=['national_code', 'source'], name='uniq_person_national_code_source')
		]
		indexes = [
			models.Index(fields=['national_code', 'source'], name='idx_person_natcode_source')
		]

	def __str__(self) -> str:
		return f"{self.first_name} {self.last_name}".strip() or f"Person {self.pk}"


class CreditCard(models.Model):
	card_number = models.CharField(
		max_length=16,
		validators=[RegexValidator(r'^\d{16}$', 'Card number must be 16 digits')]
	)
	person = models.ForeignKey(
		Person,
		on_delete=models.CASCADE,
		related_name='credit_cards'
	)
	source = models.CharField(max_length=32, choices=Source.choices, default=Source.UNKNOWN)

	class Meta:
		constraints = [
			models.UniqueConstraint(fields=['card_number', 'source'], name='uniq_creditcard_number_source')
		]
		indexes = [
			models.Index(fields=['card_number', 'source'], name='idx_creditcard_number_source')
		]

	def __str__(self) -> str:
		return f'Card ending with {self.card_number[-4:]}'


class PhoneNumber(models.Model):
	number = models.CharField(
		max_length=15,
		validators=[RegexValidator(r'^\+?1?\d{9,15}$', 'Enter a valid phone number')]
	)
	person = models.ForeignKey(
		Person,
		on_delete=models.CASCADE,
		related_name='phone_numbers'
	)
	source = models.CharField(max_length=32, choices=Source.choices, default=Source.UNKNOWN)

	class Meta:
		constraints = [
			models.UniqueConstraint(
				fields=['number', 'person', 'source'], 
				name='uniq_phonenumber_number_person_source'
			)
		]
		indexes = [
			models.Index(fields=['number', 'person', 'source'], name='idx_phone_num_per_src')
		]

	def __str__(self) -> str:
		return self.number


class ImportJobStatus(models.TextChoices):
    PENDING = 'PENDING', 'Pending'
    PROCESSING = 'PROCESSING', 'Processing'
    COMPLETED = 'COMPLETED', 'Completed'
    FAILED = 'FAILED', 'Failed'


class ImportJob(models.Model):
    source = models.CharField(max_length=32, choices=Source.choices)
    file_path = models.CharField(max_length=500)
    status = models.CharField(
        max_length=20, 
        choices=ImportJobStatus.choices, 
        default=ImportJobStatus.PENDING
    )
    total_chunks = models.IntegerField(default=0)
    processed_chunks = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    error_message = models.TextField(blank=True, null=True)

    def progress_percentage(self):
        if self.total_chunks > 0:
            return round((self.processed_chunks / self.total_chunks) * 100)
        return 0

    def __str__(self):
        return f"ImportJob {self.id} - {self.source} - {self.status}"
