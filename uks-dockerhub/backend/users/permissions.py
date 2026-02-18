from functools import wraps
from django.http import HttpResponseForbidden

def role_required(role):
	def decorator(view_func):
		@wraps(view_func)
		def _wrapped_view(request, *args, **kwargs):
			if not request.user.is_authenticated:
				return HttpResponseForbidden("You must be logged in.")
			if getattr(request.user, 'role', None) != role:
				return HttpResponseForbidden("You do not have permission to access this page.")
			return view_func(request, *args, **kwargs)
		return _wrapped_view
	return decorator

def admin_required(view_func):
	return role_required('admin')(view_func)

def superadmin_required(view_func):
	return role_required('superadmin')(view_func)
