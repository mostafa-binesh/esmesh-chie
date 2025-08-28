from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PersonViewSet, CreditCardViewSet, PhoneNumberViewSet

router = DefaultRouter()
router.register(r'users', PersonViewSet, basename='person')
router.register(r'credit-cards', CreditCardViewSet, basename='creditcard')
router.register(r'phone-numbers', PhoneNumberViewSet, basename='phonenumber')

urlpatterns = [
	path('', include(router.urls)),
]