from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Task
from .serializers import TaskSerializer


class TaskViewSet(viewsets.ModelViewSet):
    """
    CRUD for the signed-in user's tasks only.

    Query params on the list endpoint:
      status    = all | pending | completed
      priority  = low | medium | high
      search    = text matched against the title
      ordering  = due_date (default, ascending) | -due_date
    """

    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = Task.objects.filter(user=self.request.user)
        params = self.request.query_params

        status = params.get("status")
        if status in Task.Status.values:
            qs = qs.filter(status=status)

        priority = params.get("priority")
        if priority in Task.Priority.values:
            qs = qs.filter(priority=priority)

        search = (params.get("search") or "").strip()
        if search:
            qs = qs.filter(title__icontains=search)

        ordering = params.get("ordering")
        if ordering == "-due_date":
            qs = qs.order_by("-due_date", "-id")
        else:
            qs = qs.order_by("due_date", "id")
        return qs

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=["post"])
    def complete(self, request, pk=None):
        task = self.get_object()
        task.status = Task.Status.COMPLETED
        task.save(update_fields=["status", "updated_at"])
        return Response(self.get_serializer(task).data)
