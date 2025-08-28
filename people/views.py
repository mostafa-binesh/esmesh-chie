from rest_framework import viewsets
from rest_framework.permissions import AllowAny
from .models import Person, CreditCard, PhoneNumber
from .serializers import PersonSerializer, CreditCardSerializer, PhoneNumberSerializer


class PersonViewSet(viewsets.ModelViewSet):
	queryset = Person.objects.all().order_by('id')
	serializer_class = PersonSerializer
	permission_classes = [AllowAny]


class CreditCardViewSet(viewsets.ModelViewSet):
	queryset = CreditCard.objects.all().order_by('id')
	serializer_class = CreditCardSerializer
	permission_classes = [AllowAny]


class PhoneNumberViewSet(viewsets.ModelViewSet):
	queryset = PhoneNumber.objects.all().order_by('id')
	serializer_class = PhoneNumberSerializer
	permission_classes = [AllowAny]