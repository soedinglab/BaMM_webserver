from django.conf import settings
from .forms import JobForm


def get_valid_form(post, files, user):
    form = JobForm(post, files)
    args = {}
    valid = False
    if not form.is_valid():
        args['form'] = JobForm()
        args['type'] = "OK"
        args['message'] = "OK"
        return form, valid, args
    max_size = settings.MAX_UPLOAD_SIZE if user.is_authenticated() else settings.MAX_UPLOAD_SIZE_ANONYMOUS
    print("FORM IS VALID")
    # Test if data maximum size is not reached
    content = form.cleaned_data['Input_Sequences']
    if content._size > int(max_size):
        args['form'] = JobForm()
        args['type'] = "FileSize"
        args['message'] = max_size
        return form, valid, args
    valid = True
    return form, valid, args
