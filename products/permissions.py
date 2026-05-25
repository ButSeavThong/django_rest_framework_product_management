# products/permissions.py
#
# RESPONSIBILITY:
#   Defines who is allowed to do what after they are authenticated.
#   Authentication = who you are
#   Permission    = what you can do
#
#   You can use these classes on individual views to control access.


from rest_framework.permissions import BasePermission


class IsWSO2Authenticated(BasePermission):
    """
    Allows access only to requests that have a valid WSO2 JWT token.

    This is the basic permission — user just needs to be authenticated.
    Use this on views that any logged-in user can access.
    """

    message = 'A valid WSO2 access token is required.'

    def has_permission(self, request, view):
        # request.user is set by our WSO2Authentication class
        # request.auth contains the decoded JWT payload
        return bool(request.user and request.auth)


class IsWSO2AdminUser(BasePermission):
    """
    Allows access only to WSO2 users who have the 'admin' role.

    WSO2 can include user roles in the JWT token.
    This permission checks for that role.

    To enable roles in tokens:
    WSO2 Console → Applications → Your App
    → User Attributes → Add 'roles' claim
    """

    message = 'Admin role required.'

    def has_permission(self, request, view):
        if not request.auth:
            return False

        # WSO2 puts roles in the token under different claims
        # depending on your configuration — check your actual token
        roles = request.auth.get('roles', [])

        # Handle both string and list formats
        if isinstance(roles, str):
            roles = [roles]

        return 'admin' in roles