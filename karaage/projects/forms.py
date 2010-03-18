from django import forms
from django.contrib.admin.widgets import AdminDateWidget

import datetime
from andsome.middleware.threadlocals import get_current_user

from karaage.people.models import Institute, Person
from karaage.machines.models import MachineCategory
from karaage.requests.models import ProjectCreateRequest
from karaage.util.helpers import get_new_pid
from karaage.util import log_object

from models import Project


class ProjectForm(forms.ModelForm):
    name = forms.CharField(label='Project Title', widget=forms.TextInput(attrs={ 'size':60 }))
    description = forms.CharField(widget=forms.Textarea(attrs={'class':'vLargeTextField', 'rows':10, 'cols':40 }), required=False)
    institute = forms.ModelChoiceField(queryset=Institute.valid.all())
    additional_req = forms.CharField(widget=forms.Textarea(attrs={'class':'vLargeTextField', 'rows':10, 'cols':40 }), required=False)
    leader = forms.ModelChoiceField(queryset=Person.active.all())
    start_date = forms.DateField(widget=AdminDateWidget)
    end_date = forms.DateField(widget=AdminDateWidget, required=False)
    machine_categories = forms.ModelMultipleChoiceField(queryset=MachineCategory.objects.all(), widget=forms.CheckboxSelectMultiple())

    class Meta:
        model = Project
        fields = ('name', 'institute', 'leader', 'description', 'start_date', 'end_date', 'additional_req', 'machine_categories', 'machine_category')


class ProjectForm2(forms.Form):
    pid = forms.CharField(max_length=10, required=False, help_text="If left blank the next available pid will be used")
    name = forms.CharField(label='Project Title', widget=forms.TextInput(attrs={ 'size':60 }))
    description = forms.CharField(widget=forms.Textarea(attrs={'class':'vLargeTextField', 'rows':10, 'cols':40 }), required=False)
    institute = forms.ModelChoiceField(queryset=Institute.valid.all())
    additional_req = forms.CharField(widget=forms.Textarea(attrs={'class':'vLargeTextField', 'rows':10, 'cols':40 }), required=False)
    is_expertise = forms.BooleanField(required=False, help_text=u"Is this a current VPAC funded Expertise or Education Project?")
    leader = forms.ModelChoiceField(queryset=Person.active.all())
    start_date = forms.DateField(widget=AdminDateWidget)
    end_date = forms.DateField(widget=AdminDateWidget, required=False)
    machine_categories = forms.ModelMultipleChoiceField(queryset=MachineCategory.objects.all(), widget=forms.CheckboxSelectMultiple)
    
    def save(self, p=None):
        data = self.cleaned_data

        if p is None:
            p = Project()
            if data['pid']:
                p.pid = data['pid']
            else:
                p.pid = get_new_pid(data['institute'], data['is_expertise'])
            p.is_active = True
            p.is_approved = True
            p.date_approved = datetime.datetime.today()
            approver = get_current_user()
            p.approved_by = approver.get_profile()

            log_object(get_current_user(), p, 1, 'Created')
 
        else:
            log_object(get_current_user(), p, 2, 'Edited')
            
        p.name = data['name']
        p.description = data['description']
        p.institute = data['institute']
        p.additional_req = data['additional_req']
        p.is_expertise = data['is_expertise']
        p.leader = data['leader']
        p.start_date = data['start_date']
        p.end_date = data['end_date']
        p.machine_categories = data['machine_categories']
        p.save()

        return p
            
    def clean_pid(self):
        if self.cleaned_data.get('pid'):
            try:
                project = Project.objects.get(pk=self.cleaned_data['pid'])
            except:
                return self.cleaned_data['pid']
            raise forms.ValidationError(u'PID already exists')





class UserProjectForm(forms.Form):
    """
    This form is for people who have an account and want to start a new project
    or edit it
    """
    name = forms.CharField(label='Project Title', widget=forms.TextInput(attrs={ 'size':60 }))
    description = forms.CharField(widget=forms.Textarea(attrs={'class':'vLargeTextField', 'rows':10, 'cols':40 }))
    additional_req = forms.CharField(widget=forms.Textarea(attrs={'class':'vLargeTextField', 'rows':10, 'cols':40 }), required=False)
    is_expertise = forms.BooleanField(required=False, help_text=u"Is this a current VPAC funded Expertise or Education Project?")
    pid = forms.CharField(label="PIN", max_length=10, required=False, help_text="If yes, please provide Project Identification Number")
    needs_account = forms.BooleanField(required=False, label=u"Will you be working on this project yourself?")
    #machine_categories = forms.ModelMultipleChoiceField(queryset=MachineCategory.objects.all(), widget=forms.CheckboxSelectMultiple)
    institute = forms.ModelChoiceField(queryset=Institute.valid.all())

    def save(self, leader=None, p=None):
        data = self.cleaned_data

        if p is None:
            p = Project()
            p.pid = get_new_pid(data['institute'], data['is_expertise'])
            p.leader = leader
            p.institute = data['institute']
            p.machine_category=MachineCategory.objects.get_default()
            p.start_date = datetime.datetime.today()
            p.is_approved, p.is_active = False, False
            p.is_expertise = data['is_expertise']
            p.name = data['name']
            p.description = data['description']
            p.additional_req = data['additional_req']
            p.is_expertise = data['is_expertise']
            p.save()
            p.machine_categories.add(MachineCategory.objects.get_default())
            p.save()
            project_request = ProjectCreateRequest.objects.create(
                project=p,
                person=leader,
                needs_account=data['needs_account'],
            )

            log_object(get_current_user(), p, 1, 'Created')

            return project_request

        #edit
        p.name = data['name']
        p.description = data['description']
        p.additional_req = data['additional_req']
        p.is_expertise = data['is_expertise']
        p.save()

        log_object(get_current_user(), p, 2, 'Edited')

        return p


    def clean(self):
        data = self.cleaned_data

        if data.get('is_expertise') and data['pid'] == '':
                raise forms.ValidationError("Please provide your Expertise Grant project identifcation number")
            
        return data