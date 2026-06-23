from django.conf import settings
from django.contrib.auth import authenticate, get_user_model
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.request import Request
from rest_framework_simplejwt.tokens import RefreshToken
import logging

from .serializers import UserSerializer

logger = logging.getLogger(__name__)


def _set_refresh_cookie(response: Response, token: str):
    # Cookie settings: Path should allow refresh endpoint to read it
    secure = not settings.DEBUG
    response.set_cookie(
        key='refresh',
        value=token,
        httponly=True,
        secure=secure,
        samesite='Lax',
        path='/'  # allow the cookie to be sent to the refresh endpoint
    )


class TokenObtainView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request: Request):
        username = request.data.get('username')
        password = request.data.get('password')
        user = authenticate(request, username=username, password=password)
        if not user:
            return Response({'detail': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)

        refresh = RefreshToken.for_user(user)
        access = str(refresh.access_token)

        data = {'access': access, 'user': UserSerializer(user).data}
        resp = Response(data, status=status.HTTP_200_OK)
        _set_refresh_cookie(resp, str(refresh))
        return resp


class TokenRefreshView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request: Request):
        # Try to get refresh token from cookie first, then from request body
        refresh_token = request.COOKIES.get('refresh') or request.data.get('refresh')
        if not refresh_token:
            return Response({'detail': 'Refresh token not found'}, status=status.HTTP_401_UNAUTHORIZED)
        try:
            token = RefreshToken(refresh_token)
            # Get the user_id from the token claims
            user_id = token.get('user_id')
            if not user_id:
                return Response({'detail': 'Invalid refresh token'}, status=status.HTTP_401_UNAUTHORIZED)
            
            # Get user from database
            User = get_user_model()
            user = User.objects.get(id=user_id)
            
            # rotate refresh token: create new refresh, send as cookie
            new_refresh = RefreshToken.for_user(user)
            access = str(new_refresh.access_token)

            data = {'access': access, 'user': UserSerializer(user).data}
            resp = Response(data, status=status.HTTP_200_OK)
            _set_refresh_cookie(resp, str(new_refresh))
            return resp
        except Exception as e:
            logger.error(f"Token refresh error: {e}", exc_info=True)
            return Response({'detail': 'Invalid refresh token'}, status=status.HTTP_401_UNAUTHORIZED)


class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request: Request):
        resp = Response({'detail': 'logged out'}, status=status.HTTP_200_OK)
        # unset cookie
        resp.delete_cookie('refresh', path='/')
        return resp


class MeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request: Request):
        return Response(UserSerializer(request.user).data)
