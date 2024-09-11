# decorators.py
from django.shortcuts import redirect
# my own decorator for liogin required
def login_required(view_func):
    def _wrapped_view(request, *args, **kwargs):
        if 'uid' not in request.session:
            return redirect('login')
        return view_func(request, *args, **kwargs)
    return _wrapped_view
