import six
from django.core.exceptions import FieldDoesNotExist
from django.forms.models import modelform_factory
from django.db.models.query_utils import Q
from django.db import models


class FormFilter:
    form = None

    def __init__(self, request, form=None):
        if form:
            self.form = form
        self.request = request
        self.form_instance = self.form(request.GET)
        for key in self.form_instance.fields:
            self.form_instance.fields[key].required = False
        self.form_instance.is_valid()
        self.form_instance._errors = {}

    def get_cleaned_fields(self):
        values = {}
        for value in self.form_instance.cleaned_data:
            rq_value = self.request.GET.get(value, '')
            if value and rq_value:
                values[value] = self.form_instance.cleaned_data[value]
        return values

    def render(self):
        return self.form_instance

    def get_filter(self, queryset):
        clean_value = self.get_cleaned_fields()
        if clean_value:
            sfilter = None
            for rq in clean_value:  # relation query model  (rq)
                try:  
                    if (len (clean_value[rq])):
                         for rqo in clean_value[rq]:   # relation query object model  (rqo)
                                if sfilter is None:
                                    sfilter = Q(**{rq: rqo})
                                else:
                                     sfilter |= Q(**{rq: rqo})             
                    if sfilter is not None:
                            queryset = queryset.filter(sfilter)    
                except ValueError:
                    pass
                except TypeError: # When model hasn't relationship with rq (model) name
                    pass    
        return queryset

    def get_params(self, exclude=[]):
        params = []
        for value in self.form_instance.cleaned_data:
            if value in exclude:
                continue
            rq_value = self.request.GET.get(value, '')
            if rq_value:
                data = self.form_instance.cleaned_data[value]
                if isinstance(data, models.base.Model):
                    data = str(data.pk)
                params.append("%s=%s" %
                              (value, str(data)))
        return params


def get_filters(model, list_filter, request):
    fields = []
    forms = []
    for field in list_filter:
        if type(field) in [six.string_types, six.text_type, six.binary_type]:
            # this is a model field
            try:
                model._meta.get_field(field)
                fields.append(field)
            except FieldDoesNotExist:
                pass
        else:
            forms.append(field(request))

    if fields:
        form = modelform_factory(model, fields=fields)
        forms.insert(0, FormFilter(request, form=form))

    return forms
