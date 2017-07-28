"""
Custom Decorators
"""

from django.contrib.auth.decorators import login_required


def is_activated(f):
    """
    A decorator to allow only logged in and activated accounts to enter
    """

    @login_required(login_url='/')
    def wrapper(*args, **kwargs):

        if(args[0].user.profile.activated):
            return f(*args, **kwargs)
        return redirect('inout:activate')

    return wrapper
