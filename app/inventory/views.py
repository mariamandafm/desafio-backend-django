from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.parsers import MultiPartParser
from core.models import AutoPart
from inventory import serializers
from .tasks import import_auto_parts_from_csv


class AutoPartView(ModelViewSet):
    """ViewSet for managing Auto Parts in the inventory."""
    serializer_class = serializers.AutoPartSerializer
    queryset = AutoPart.objects.all()

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [IsAdminUser]

        return [permission() for permission in permission_classes]


class AutoPartCSVUploadView(APIView):
    """View for uploading Auto Parts via CSV file."""
    permission_classes = [IsAdminUser]
    parser_classes = [MultiPartParser]

    def post(self, request):
        csv_file = request.FILES.get('file')

        if not csv_file:
            return Response({"error": "Nenhum arquivo fornecido."}, status=status.HTTP_400_BAD_REQUEST)

        if not csv_file.name.endswith('.csv'):
            return Response({"error": "Arquivo não é do tipo CSV."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            csv_content = csv_file.read().decode('utf-8')
        except UnicodeDecodeError:
            return Response(
                {"error": "Erro ao decodificar o arquivo. Use codificação UTF-8."},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {"error": f"Erro ao ler o arquivo: {e}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        import_auto_parts_from_csv.delay(csv_content)

        return Response({"message": "Arquivo recebido. A importação está sendo processada."},
                        status=status.HTTP_202_ACCEPTED)
