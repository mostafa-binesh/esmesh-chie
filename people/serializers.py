from rest_framework import serializers
from .models import Person, CreditCard, PhoneNumber, Source


class PersonSerializer(serializers.ModelSerializer):
	source = serializers.ChoiceField(choices=Source.choices, default=Source.UNKNOWN)

	class Meta:
		model = Person
		fields = ['id', 'national_code', 'first_name', 'last_name', 'birthdate', 'source']


class CreditCardSerializer(serializers.ModelSerializer):
	person_id = serializers.PrimaryKeyRelatedField(source='person', queryset=Person.objects.all())
	source = serializers.ChoiceField(choices=Source.choices, default=Source.UNKNOWN)

	class Meta:
		model = CreditCard
		fields = ['id', 'card_number', 'person_id', 'source']


class PhoneNumberSerializer(serializers.ModelSerializer):
	person_id = serializers.PrimaryKeyRelatedField(source='person', queryset=Person.objects.all())
	source = serializers.ChoiceField(choices=Source.choices, default=Source.UNKNOWN)

	class Meta:
		model = PhoneNumber
		fields = ['number', 'person_id', 'source']