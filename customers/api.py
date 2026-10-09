from rest_framework import permissions, serializers, viewsets
from rest_framework.routers import DefaultRouter

from .models import Note, Record
from .views import search_records, visible_records


class NoteSerializer(serializers.ModelSerializer):
    author = serializers.CharField(source='author.username', read_only=True, default=None)

    class Meta:
        model = Note
        fields = ('id', 'body', 'author', 'created_at')


class RecordSerializer(serializers.ModelSerializer):
    # read_only fields are shown in responses but ignored if a client sends them
    owner = serializers.CharField(source='owner.username', read_only=True, default=None)
    notes = NoteSerializer(many=True, read_only=True)
    # The model stores email as a CharField; this adds proper email validation, like AddRecordForm does
    email = serializers.EmailField(max_length=100)

    class Meta:
        model = Record
        fields = (
            'id', 'first_name', 'last_name', 'email', 'phone',
            'address', 'city', 'state', 'zipcode', 'status',
            'owner', 'created_at', 'notes',
        )

class RecordViewSet(viewsets.ModelViewSet):
    """
    list:     GET    /api/customers/?q=<search>&status=<lead|active|inactive>
    create:   POST   /api/customers/
    retrieve: GET    /api/customers/<id>/
    update:   PUT    /api/customers/<id>/   (PATCH for partial updates)
    destroy:  DELETE /api/customers/<id>/
    """
    serializer_class = RecordSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Same rules as the website: users only reach the customers they own
        records = search_records(visible_records(self.request.user), self.request.query_params.get('q', '').strip())
        status = self.request.query_params.get('status')
        if status in Record.Status.values:
            records = records.filter(status=status)
        return records.select_related('owner').prefetch_related('notes__author').order_by('-created_at', '-pk')

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


router = DefaultRouter()
router.register('customers', RecordViewSet, basename='api-customer')
