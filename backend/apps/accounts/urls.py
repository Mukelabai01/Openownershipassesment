from django.urls import path
from .views import TokenObtainView, TokenRefreshView, LogoutView, MeView

urlpatterns = [
    path('token/', TokenObtainView.as_view(), name='token_obtain'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('me/', MeView.as_view(), name='me'),
]
