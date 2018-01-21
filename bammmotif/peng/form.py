from django.conf import settings
from bammmotif.forms import PredictionExampleForm
from django import forms
from bammmotif.models import PengJob_deprecated, Peng, JobInfo


class PengFormMeta(forms.ModelForm):

    class Meta:
        model = Peng
        fields = (
            'fasta_file', 'bg_sequences',
            'pattern_length', 'zscore_threshold', 'count_threshold', 'bg_model_order',
            'strand', 'objective_function', 'no_em'

        )

    def __init__(self, *args, **kwargs):
        super(PengFormMeta, self).__init__(*args, **kwargs)
        for field in self.fields:
            help_text = self.fields[field].help_text
            self.fields[field].help_text = None
            if help_text != '':
                self.fields[field].widget.attrs.update({'class': 'has-popover',
                                                        'data-content': help_text,
                                                        'data-placement': 'right',
                                                        'data-container': 'body'})

class PengExampleFormMeta(forms.ModelForm):

    class Meta:
        model = Peng
        fields = (
            'bg_sequences',
            'pattern_length', 'zscore_threshold', 'count_threshold', 'bg_model_order',
            'strand', 'objective_function', 'no_em'
        )

    def __init__(self, *args, **kwargs):
        super(PengExampleFormMeta, self).__init__(*args, **kwargs)
        for field in self.fields:
            help_text = self.fields[field].help_text
            self.fields[field].help_text = None
            if help_text != '':
                self.fields[field].widget.attrs.update({'class': 'has-popover',
                                                        'data-content': help_text,
                                                        'data-placement': 'right',
                                                        'data-container': 'body'})


class PengForm(forms.ModelForm):

    class Meta:
        model = PengJob_deprecated
        # fields = tuple(ShootPengModule().options.keys()) + ('job_name',)
        fields = (
            'fasta_file', 'bg_sequences',
            'pattern_length', 'zscore_threshold', 'count_threshold', 'bg_model_order',
            'strand', 'objective_function', 'no_em', 'job_name'
        )

    def __init__(self, *args, **kwargs):
        super(PengForm, self).__init__(*args, **kwargs)
        for field in self.fields:
            help_text = self.fields[field].help_text
            self.fields[field].help_text = None
            if help_text != '':
                self.fields[field].widget.attrs.update({'class': 'has-popover',
                                                        'data-content': help_text,
                                                        'data-placement': 'right',
                                                        'data-container': 'body'})

class PengExampleForm(forms.ModelForm):

    class Meta:
        model = PengJob_deprecated
        fields = (
            'bg_sequences',
            'pattern_length', 'zscore_threshold', 'count_threshold', 'bg_model_order',
            'strand', 'objective_function', 'enrich_pseudocount_factor', 'no_em',
            'em_saturation_threshold', 'em_threshold', 'em_max_iterations', 'no_merging',
            'bit_factor_threshold', 'use_default_pwm', 'pwm_pseudo_counts',
            'silent', 'job_name'
        )

    def __init__(self, *args, **kwargs):
        super(PengExampleForm, self).__init__(*args, **kwargs)
        for field in self.fields:
            help_text = self.fields[field].help_text
            self.fields[field].help_text = None
            if help_text != '':
                self.fields[field].widget.attrs.update({'class': 'has-popover',
                                                        'data-content': help_text,
                                                        'data-placement': 'right',
                                                        'data-container': 'body'})

class JobInfoForm(forms.ModelForm):
    class Meta:
        model = JobInfo
        fields = ('job_name',)

    def __init__(self, *args, **kwargs):
        super(JobInfoForm, self).__init__(*args, **kwargs)
        for field in self.fields:
            help_text = self.fields[field].help_text
            self.fields[field].help_text = None
            if help_text != '':
                self.fields[field].widget.attrs.update({'class': 'has-popover',
                                                        'data-content': help_text,
                                                        'data-placement': 'right',
                                                        'data-container': 'body'})



def get_valid_peng_form(post, files, user, mode):
    print("post", post, "files", files)
    args = {}
    valid = False
    if mode == 'example':
        valid = True
        args['form'] = PengExampleFormMeta()
        return PengExampleFormMeta(post, files), valid, args
    #print("get valid peng form")
    #print(post.__dir__())
    #print("files:")
    #print(files)
    form = PengForm(post, files)
    if not form.is_valid():
        print("get_valid_peng_form second if")
        args['form'] = PengForm()
        args['type'] = "OK"
        args['message'] = "OK"
        return form, valid, args
    max_size = settings.MAX_UPLOAD_SIZE if user.is_authenticated else settings.MAX_UPLOAD_SIZE_ANONYMOUS
    print("FORM IS VALID")
    # Test if data maximum size is not reached
    content = form.cleaned_data['fasta_file']
    if content._size > int(max_size):
        print("get_valid_peng_form third if")
        args['form'] = PengForm()
        args['type'] = "FileSize"
        args['message'] = max_size
        return form, valid, args
    valid = True
    return form, valid, args

def get_valid_peng_form_meta(post, files, user, mode):
    print("post", post, "files", files)
    args = {}
    valid = False
    if mode == 'example':
        valid = True
        args['form'] = PengExampleFormMeta()
        return PengExampleFormMeta(post, files), valid, args
    form = PengFormMeta(post, files)
    if not form.is_valid():
        print("get_valid_peng_form_meta second if")
        args['form'] = PengFormMeta()
        args['type'] = "OK"
        args['message'] = "OK"
        return form, valid, args
    max_size = settings.MAX_UPLOAD_SIZE if user.is_authenticated else settings.MAX_UPLOAD_SIZE_ANONYMOUS
    print("FORM IS VALID")
    # Test if data maximum size is not reached
    content = form.cleaned_data['fasta_file']
    if content._size > int(max_size):
        print("get_valid_peng_form third if")
        args['form'] = PengForm()
        args['type'] = "FileSize"
        args['message'] = max_size
        return form, valid, args
    valid = True
    return form, valid, args
