from rest_framework.permissions import BasePermission

class IsAgent(BasePermission):
    def has_permission(self, request, view):
        # Why: agents should be in 'Agents' group managed by admin
        return request.user and request.user.is_authenticated and request.user.groups.filter(name='Agents').exists()

class IsAdminOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        # Admins (staff) have full control; others read-only
        if request.method in ['GET', 'HEAD', 'OPTIONS']:
            return True
        return request.user and request.user.is_staff
