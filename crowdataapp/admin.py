# coding: utf-8
import csv, sys, re, json, itertools
from datetime import datetime
import django.db.models
import django.http
from django.utils.translation import ugettext, ugettext_lazy as _
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User, Group
from django.utils.safestring import mark_safe
from django.db.models import Count
from django.db import transaction
from django.conf.urls import patterns, url
from django.shortcuts import get_object_or_404, render_to_response, redirect
from django.template import RequestContext
from django.core.urlresolvers import reverse
from django.contrib import messages
from django.forms import TextInput
from django.views.decorators.csrf import csrf_exempt
from django.contrib.contenttypes.models import ContentType
from django.http import HttpResponseRedirect

from models import DocumentSetFieldEntry, DocumentSetForm, DocumentSetFormField

from django_ace import AceWidget
from nested_inlines.admin import NestedModelAdmin,NestedTabularInline, NestedStackedInline
import forms_builder

from crowdataapp import models

class DocumentSetFormFieldAdmin(NestedTabularInline):
    model = models.DocumentSetFormField
    extra = 0

class DocumentSetFormInline(NestedStackedInline):
    fields = ("title", "intro", "button_text")
    model = models.DocumentSetForm
    inlines = [DocumentSetFormFieldAdmin]
    show_url = False

class CanonicalFieldEntryLabel(NestedTabularInline):
    model = models.CanonicalFieldEntryLabel
    fields = ('value', 'form_field')
    initial = 1

class DocumentSetRankingDefinitionInline(NestedTabularInline):
    fields = ('name', 'label_field', 'magnitude_field', 'amount_rows_on_home', 'grouping_function', 'sort_order')
    model = models.DocumentSetRankingDefinition
    max_num = 2

    LABEL_TYPES = (
        forms_builder.forms.fields.TEXT,
        forms_builder.forms.fields.SELECT,
        forms_builder.forms.fields.RADIO_MULTIPLE,
    )

    MAGNITUDE_TYPES = (
        forms_builder.forms.fields.NUMBER,
    )

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        # this sucks
        document_set_id = int(re.search('documentset/(\d+)', request.path).groups()[0])
        document_set = models.DocumentSet.objects.get(pk=document_set_id)
        qs = models.DocumentSetFormField.objects.filter(form__document_set=document_set)

        if db_field.name == 'label_field':
            # get fields from this document_set form that can only act as labels
            kwargs["queryset"] = qs.filter(field_type__in=self.LABEL_TYPES, verify=True)
        elif db_field.name == 'magnitude_field':
            # get fields from this document_set form that can only act as magnitudes
            kwargs["queryset"] = qs.filter(field_type__in=self.MAGNITUDE_TYPES, verify=True)
        return super(DocumentSetRankingDefinitionInline, self) \
            .formfield_for_foreignkey(db_field, request, **kwargs)

class CanonicalFieldEntryLabelAdmin(NestedModelAdmin):
    class Media:
        css = {
            'all': ('admin/css/document_set_admin.css',
                    '/static/django_ace/widget.css')
        }
        js = ('admin/js/document_set_admin.js',
              'django_ace/ace/ace.js',
              'django_ace/widget.js'
        )

    # class ClusterForm(forms_builder.forms.forms.FormForForm):
    #     _selected_action = forms.CharField(widget=forms.MultipleHiddenInput)
    #     canon = forms.ModelChoiceField(KeyWord.objects)

    list_display = ('value', 'form_field', 'document_set')
    search_fields = ['value']
    actions = ['cluster_canons_action']

    def cluster_canons_action(self, request, queryset):
        selected = request.POST.getlist(admin.ACTION_CHECKBOX_NAME)
        #ct = ContentType.objects.get_for_model(queryset.model)
        #return HttpResponseRedirect("/cluster/?ct=%s&ids=%s" % (ct.pk, ",".join(selected)))
        return HttpResponseRedirect("/admin/crowdataapp/canonicalfieldentrylabel/cluster/?ids=%s" % ",".join(selected))
    cluster_canons_action.short_description = _('Cluster several canons into only one of them.')

    def get_urls(self):
        urls = super(CanonicalFieldEntryLabelAdmin, self).get_urls()

        extra_urls = patterns('',
                              url('^cluster/$',
                                  self.admin_site.admin_view(self.cluster_canons),
                                  name="cluster_canons"),
                                  )
        return extra_urls + urls


    def cluster_canons(self, request):

      if request.GET.get('ids') is None:

        the_canon_id = int(request.POST['canon'])
        the_canon = models.CanonicalFieldEntryLabel.objects.get(pk=the_canon_id)

        canon_ids = [int(i) for i in request.POST['ids'].split(',')]
        canon_ids.remove(the_canon_id)

        canons_to_cluster = models.CanonicalFieldEntryLabel.objects.filter(id__in=canon_ids)

        # Asign all entries to the canon
        # Remove the empty canons
        for canon in canons_to_cluster:
          canon.reassign_entries_to(the_canon)
          if not canon.has_entries():
            canon.delete()

        # cluster the canons
        return redirect(reverse('admin:crowdataapp_canonicalfieldentrylabel_changelist'))
      else:
        canon_ids = [int(i) for i in request.GET['ids'].split(',')]
        canons_to_cluster = models.CanonicalFieldEntryLabel.objects.filter(id__in=canon_ids)

        # Check that all the canons to cluster have the same form-field
        canons_with_the_same_form_field = canons_to_cluster.filter(form_field=canons_to_cluster[0].form_field)
        if (len(canons_with_the_same_form_field) == len(canons_to_cluster)):
          return render_to_response('admin/cluster_canons.html',
                                 {
                                  'canon_ids': request.GET['ids'],
                                  'canons': canons_to_cluster,
                                  'current_app': self.admin_site.name
                                 },
                                 RequestContext(request))
        else:
          return redirect(reverse('admin:crowdataapp_canonicalfieldentrylabel_changelist'))


class DocumentSetAdmin(NestedModelAdmin):

    class Media:
        css = {
            'all': ('admin/css/document_set_admin.css',
                    '/static/django_ace/widget.css')
        }
        js = ('admin/js/document_set_admin.js',
              'django_ace/ace/ace.js',
              'django_ace/widget.js'
        )

    list_display = ('name', 'published', 'document_count', 'admin_links')

    fieldsets = (
        (_('Document Set Description'), {
            'fields': ('name', 'description', 'header_image', 'tosum_field', 'published')
        }),
        (_('Document Set Behaviour'), {
            'fields': ('entries_threshold', 'head_html')
        })
    )
    inlines = ()

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if (re.search('documentset/(\d+)', request.path)):
          document_set_id = int(re.search('documentset/(\d+)', request.path).groups()[0])
          document_set = models.DocumentSet.objects.get(pk=document_set_id)
          qs = models.DocumentSetFormField.objects.filter(form__document_set=document_set)

          if db_field.name == 'tosum_field':
              kwargs["queryset"] = qs.filter(field_type__in={ forms_builder.forms.fields.NUMBER }, verify=True)
        return super(DocumentSetAdmin, self) \
            .formfield_for_foreignkey(db_field, request, **kwargs)

    def change_view(self, request, object_id, form_url='', extra_context=None):
        self.inlines = (DocumentSetFormInline, DocumentSetRankingDefinitionInline)
        return super(DocumentSetAdmin, self).change_view(request, object_id)

    def add_view(self, request, form_url='', extra_context=None):
        self.inlines = (DocumentSetFormInline,)
        return super(DocumentSetAdmin, self).add_view(request)

    def get_urls(self):
        urls = super(DocumentSetAdmin, self).get_urls()

        extra_urls = patterns('',
                              url('^(?P<document_set_id>\d+)/answers/$',
                                  self.admin_site.admin_view(self.answers_view),
                                  name="document_set_answers_csv"),
                              url('^(?P<document_set_id>\d+)/add_documents/$',
                                  self.admin_site.admin_view(self.add_documents_view),
                                  name='document_set_add_documents'),
                              url('^(?P<document_set_id>\d+)/update_canons/$',
                                  self.admin_site.admin_view(self.update_canons_view),
                                  name='document_set_update_canons'),
                              url('^(?P<document_set_id>\d+)/reverify_documents/$',
                                self.admin_site.admin_view(self.reverify_documents_view),
                                  name='document_set_reverify_documents'),

                              # k-monitor specific urls
                              url('^(?P<document_set_id>\d+)/kmonitor_import_asset_declarations$',
                                  self.admin_site.admin_view(self.kmonitor_import_asset_declarations),
                                  name='kmonitor_import_asset_declarations')
                             )

        return extra_urls + urls

    def add_documents_view(self, request, document_set_id):
        """ add a bunch of documents to
         a DocumentSet by uploading a CSV """
        document_set = get_object_or_404(self.model, pk=document_set_id)
        if request.FILES.get('csv_file'):
            # got a CSV, process, check and create
            csvreader = csv.reader(request.FILES.get('csv_file'))

            header_row = csvreader.next()
            if [h.strip() for h in header_row] != ['document_title', 'document_url']:
                messages.error(request,
                               _('Header cells must be document_title and document_url'))


            count = 0
            try:
                with transaction.commit_on_success():
                    for row in csvreader:
                        document_set.documents.create(name=row[0].strip(),
                                                      url=row[1].strip())
                        count += 1
            except:
                messages.error(request,
                               _('Could not create documents'))

                return redirect(reverse('admin:document_set_add_documents',
                                        args=(document_set_id,)))

            messages.info(request,
                          _('Successfully created %(count)d documents') % { 'count': count })

            return redirect(reverse('admin:crowdataapp_documentset_changelist'))

        else:
            return render_to_response('admin/document_set_add_documents.html',
                                      {
                                          'document_set': document_set,
                                          'current_app': self.admin_site.name,
                                      },
                                      RequestContext(request))

    def kmonitor_import_asset_declarations(self, request, document_set_id):
        from crowdataapp.scrapers.kmonitor import asset_declarations
        # TODO catch requests.exceptions.ConnectionError

        document_set = get_object_or_404(self.model, pk=document_set_id)
        if request.method == 'POST' and request.REQUEST['chamber'] and int(request.REQUEST['year']):
            year = int(request.REQUEST['year'])
            chamber_id = request.REQUEST['chamber']

            report = asset_declarations.import_declarations(document_set, chamber_id, year)

            return render_to_response('admin/kmonitor_import_asset_declarations_report.html',
                                      {
                                          'document_set': document_set,
                                          'current_app': self.admin_site.name,
                                          'report': report
                                      },
                                      RequestContext(request))

        else:
            return render_to_response('admin/kmonitor_import_asset_declarations.html',
                                      {
                                          'document_set': document_set,
                                          'current_app': self.admin_site.name,
                                          'chambers': asset_declarations.get_chambers()
                                      },
                                      RequestContext(request))

    def update_canons_view(self, request, document_set_id):
      """Update canons for the document set"""

      def _encode_dict_for_csv(d):
          rv = {}
          for k,v in d.items():
              k = k.encode('utf8') if type(k) == unicode else k
              if type(v) == datetime:
                  rv[k] = v.strftime('%Y-%m-%d %H:%M')
              elif type(v) == unicode:
                  rv[k] = v.encode('utf8')
              elif type(v) == bool:
                  rv[k] = 'true' if v else 'false'
              else:
                  rv[k] = v

          return rv

      response = django.http.HttpResponse(mimetype="text/csv")

      writer = csv.DictWriter(response, fieldnames=['entry_id', 'entry_value', 'entry_canonical_value'],extrasaction='ignore')
      writer.writeheader()

      for entry in models.DocumentSetFieldEntry.objects.all():
        if models.DocumentSetFormField.objects.get(pk=entry.field_id).autocomplete:
          try:
            entry.canonical_label = entry.get_canonical_value()
            entry.save()
            mensaje = entry.canonical_label.value
          except Exception, e:
            mensaje = "Failed %s" % e
          writer.writerow(_encode_dict_for_csv({'entry_id': entry.id, 'entry_value': entry.value, 'entry_canonical_value': mensaje}))

      return response

    def reverify_documents_view(self, request, document_set_id):
      """Reverify all the documents for document set"""
      pass

    def answers_view(self, request, document_set_id):

        def _encode_dict_for_csv(d):
            rv = {}
            for k,v in d.items():
                k = k.encode('utf8') if type(k) == unicode else k
                if type(v) == datetime:
                    rv[k] = v.strftime('%Y-%m-%d %H:%M')
                elif type(v) == unicode:
                    rv[k] = v.encode('utf8')
                elif type(v) == bool:
                    rv[k] = 'true' if v else 'false'
                else:
                    rv[k] = v
            return rv

        def partition(items, predicate=bool):
            a, b = itertools.tee((predicate(item), item) for item in items)
            return ((item for pred, item in a if not pred),
                    (item for pred, item in b if pred))

        document_set = get_object_or_404(self.model,pk=document_set_id)
        response = django.http.HttpResponse(mimetype="text/csv")
        # las_documents = document_set.documents.get(verified=1)
        # print las_documents
        entries = models.DocumentSetFormEntry \
                        .objects \
                        .filter(document__in=document_set.documents.all())

        if len(entries) == 0:
            return django.http.HttpResponse('No document inputs found.')

        answer_field, non_answer_field = partition([u.encode('utf8') for u in entries[0].to_dict().keys()],
                                                   lambda fn: not fn.startswith('answer_'))

        writer = csv.DictWriter(response, fieldnames=sorted(non_answer_field) + sorted(answer_field),extrasaction='ignore')

        writer.writeheader()

        # for entry in entries:
        #     writer.writerow(_encode_dict_for_csv(entry.to_dict()))

        dictionary = []

        for entry in entries:
            dictionary.append(entry.to_dict())

        list_of_dictionary_keys = []
        for elem in dictionary:
            list_of_dictionary_keys.append(elem['Document Url'])

        unique_keys_list =  self.f4(list_of_dictionary_keys)

        # print unique_keys_list
        final_converted_document = []
        for key in unique_keys_list:
            unique_document_entries = []
            for entry in dictionary:
                if(entry['Document Url'] == key):
                    unique_document_entries.append(entry)
            final_converted_document.append(self.convert(unique_document_entries))
        # converted_doc = self.convert(dictionary)

        # print final_converted_document

        for entry in final_converted_document:
           writer.writerow(_encode_dict_for_csv(entry))
        return response


    def f4(self,seq):
       # order preserving
       noDupes = []
       [noDupes.append(i) for i in seq if not noDupes.count(i)]
       return noDupes
    def document_count(self, obj):
        l = '<a href="%s?document_set__id=%s">%s</a>' % (reverse("admin:crowdataapp_document_changelist"),
                                                           obj.pk,
                                                           obj.documents.count())
        return mark_safe(l)

    def convert(self, entries):
        #!/usr/local/bin/python3.1
        import datetime
        import sys    # sys.setdefaultencoding is cancelled by site.py
        reload(sys)   # to re-enable sys.setdefaultencoding()
        sys.setdefaultencoding('utf-8')

        def distinct(l):
          checked = []
          for item in l:
              if str(item) not in checked:
                  checked.append(str(item))
          return checked

        # Load in verified entries

        keys = list(entries[0].keys())
        unifiedDict = {}

        for key in keys:
           # print(key)
           values = [entry[key] for entry in entries if key in entry]
           values = '|'.join(distinct(values))
           unifiedDict[key] = values

        return unifiedDict

class DocumentSetFormEntryInline(admin.TabularInline):
    fields = ('user_link', 'answers', 'entry_time', 'document_link')
    readonly_fields = ('user_link', 'answers', 'entry_time', 'document_link')
    ordering = ('document',)
    list_select_related = True
    model = models.DocumentSetFormEntry
    extra = 0

    def answers(self, obj):
        field_template = "<li><input type=\"checkbox\" data-change-url=\"%s\" data-field-entry=\"%d\" data-document=\"%d\" data-entry-value=\"%s\" %s><span class=\"%s\">%s</span>: <strong>%s</strong> - <em>%s</em></li>"
        rv = '<ul>'
        form_fields = {f.id: f for f in obj.form.fields.order_by('id').all()}

        for e in obj.fields.order_by('field_id').all():
            f = form_fields[e.field_id]
            rv += field_template % (reverse('admin:document_set_field_entry_change', args=(obj.document.pk, e.pk,)),
                                         e.pk,
                                         obj.document.pk,
                                         e.value,
                                         'checked' if e.verified else '',
                                         'verify' if f.verify else '',
                                         f.slug,
                                         e.value,
                                         e.assigned_canonical_value())
        rv += '</ul>'

        return mark_safe(rv)


    def user_link(self, obj):
        url = reverse('admin:auth_user_change', args=(obj.user.id,))
        return mark_safe('<a href="%s">%s</a>' % (url, obj.user.get_full_name()))

    def document_link(self, obj):
        url = reverse('admin:crowdataapp_document_change', args=(obj.document.id,))
        return mark_safe('<a href="%s">%s</a>' % (url, obj.document.name))

    def document_set_link(self, obj):
        url = reverse('admin:crowdataapp_documentset_change', args=(obj.document.document_set.id,))
        return mark_safe('<a href="%s">%s</a>' % (url, obj.document.document_set.name))


class DocumentAdmin(admin.ModelAdmin):
    class Media:
        css = {
            'all': ('admin/css/document_admin.css', )
        }
        js = ('admin/js/jquery-2.0.3.min.js', 'admin/js/nested.js', 'admin/js/document_admin.js',)

    fields = ('name', 'url', 'document_set', 'opened_count', 'politician', 'verified')
    readonly_fields = ('verified', 'verified_fields', 'document_set', 'opened_count')

    actions = ['verify_document']
    list_display = ('id', 'name', 'verified', 'entries_count', 'opened_count', 'document_set', 'updated_at')
    list_filter = ('document_set__name', 'verified')
    search_fields = ['form_entries__fields__value', 'name']

    def change_view(self, request, object_id, form_url='', extra_context=None):
        doc = models.Document.objects.get(pk=object_id)
        dbfields = models.DocumentSetFormField.objects.filter(form__document_set__id=doc.document_set_id)

        fields = []
        for f in dbfields:
            answers = DocumentSetFieldEntry.objects.filter(field_id=f.id, entry__document=doc).select_related(
                'entry__user__username').order_by('value').values('value', 'verified', 'entry__user__username')
            verified = None
            if answers:
                verified = reduce(lambda x,y: x or y, map(lambda a: a['value'] if a['verified'] else None, answers))

            verified_status = True
            if verified is None:
                verified_status = False
                verified = ''

            fields.append({
                'slug': f.slug,
                'answers': answers,
                'verified': verified_status,
                'verified_answer': verified
            })
        fields.sort(key=lambda a: a['verified'])

        extra_context = extra_context or {}
        extra_context['fields'] = fields
        return super(DocumentAdmin, self).change_view(request, object_id, form_url, extra_context=extra_context)

    def save_model(self, request, obj, form, change):
        # check to save verified fields
        verified_answers = {f.slug: a for f, a in obj.verified_answers(True).iteritems()}
        fields = {f.slug: f for f in DocumentSetFormField.objects.all()}

        # get moderator's entry
        (moderator_entry, me_created) = obj.form_entries.prefetch_related('fields').get_or_create(user=request.user,
                                                                                                  document=obj,
                                                         defaults={'form': DocumentSetForm.objects.all()[0],
                                                                   'entry_time': datetime.now()})

        updated_any = False
        for fldname, value in form.data.iteritems():
            if not fldname.startswith('_verified_') or not value:
                continue
            fldname = fldname[10:]

            # option 1 - field is already verified with that value -> do nothing
            if verified_answers.has_key(fldname) and value == verified_answers.get(fldname):
                continue

            # option 2 - admin has chosen one of the fields as verified
            # option 3 - or admin has entered new value
            (fldentry, fe_created) = moderator_entry.fields.get_or_create(field_id=fields[fldname].id)
            fldentry.value = value
            fldentry.verified = True
            fldentry.save()
            updated_any = True

        if updated_any:
            moderator_entry.save()

        super(DocumentAdmin, self).save_model(request, obj, form, change)

    def queryset(self, request):
        return models.Document.objects.annotate(entries_count=Count('form_entries'))

    def get_urls(self):
        urls = super(DocumentAdmin, self).get_urls()
        my_urls = patterns('',
                           url('^(?P<document>\d+)/document_set_field_entry/(?P<document_set_field_entry>\d+)/$',
                               self.admin_site.admin_view(self.field_entry_set),
                               name='document_set_field_entry_change')
        )
        return my_urls + urls

    def verified_fields(self, document):
        if not document.verified:
            return ''

        return mark_safe('<div class="keep-margin"><ul>' + ''.join(['<li><b>'+ f.slug +'</b>: ' +answer + '</li>' for f, answer in document.verified_answers().iteritems()]) + '</ul></div>')

    def field_entry_set(self, request, document, document_set_field_entry):
        """ Set verify status for form field entries """
        if request.method != 'POST':
            return django.http.HttpResponseBadRequest()

        document = get_object_or_404(models.Document, pk=document)
        this_field_entry = get_object_or_404(models.DocumentSetFieldEntry, pk=document_set_field_entry)

        # get all answers for the same document that match with this one
        coincidental_field_entries = models.DocumentSetFieldEntry.objects.filter(field_id=this_field_entry.field_id,
                                                                                 value=this_field_entry.value,
                                                                                 entry__document=this_field_entry.entry.document)

        # set the verified state for all the matching answers
        for fe in coincidental_field_entries:
            fe.verified = (request.POST['verified'] == 'true')
            fe.save()

        # if there are verified answers for every field that's marked as 'verify'
        # set this Document as verified
        verified_fields = models.DocumentSetFormField \
                                .objects \
                                .filter(pk__in=set(map(lambda fe: fe.field_id,
                                                       models.DocumentSetFieldEntry.objects.filter(entry__document=this_field_entry.entry.document,
                                                                                                   verified=True))),
                                        verify=True,
                                        form=this_field_entry.entry.form)

        document.verified = (len(verified_fields) == len(models.DocumentSetFormField.objects.filter(verify=True,
                                                                                                    form=this_field_entry.entry.form)))

        document.save()

        return django.http.HttpResponse(json.dumps(map(lambda fe: fe.pk,
                                                       coincidental_field_entries)),
                                                   content_type="application/json")


    def document_set_link(self, obj):
        # crowdataapp_documentset_change
        change_url = reverse('admin:crowdataapp_documentset_change', args=(obj.document_set.id,))
        return mark_safe('<a href="%s">%s</a>' % (change_url, obj.document_set.name))
    document_set_link.short_description = _('Document Set')

    def entries_count(self, doc):
        return doc.entries_count
    entries_count.admin_order_field = 'entries_count'

    # Verify the documents by admin or without admin
    def verify_document(self, request, queryset):
      for doc in queryset:
        if doc.is_revised_by_staff():
          doc.force_verify()
        else:
          doc.verify()
    verify_document.short_description = _('Re-verify selected documents.')

class CrowDataUserAdmin(UserAdmin):

    class Media:
        css = {
            'all': ('admin/css/user_admin.css', )
        }
        js = ('admin/js/jquery-2.0.3.min.js',
              'admin/js/nested.js',
              'admin/js/user_admin.js',
              'admin/js/document_admin.js',)


    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'email')}),
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser')}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    inlines = [DocumentSetFormEntryInline]

    readonly_fields = ('last_login', 'date_joined', )

class FeedbackAdmin(NestedModelAdmin):
    fields = ('feedback_text', 'timestamp')
    list_display = ('document_link', 'id',  'timestamp', 'feedback_text')
    list_display_links = ('document_link', 'id',  'timestamp', 'feedback_text')
    readonly_fields = ('feedback_text', 'timestamp')
    ordering = ('timestamp',)
    list_select_related = True
    model = models.Feedback
    extra = 0

    # inlines = [DocumentSetFormEntryInline]

    def get_urls(self):
        urls = super(FeedbackAdmin, self).get_urls()
        extra_urls = patterns('/admin/',
                              url('^export_feedback/$',
                                  self.admin_site.admin_view(self.export_feedback_view),
                                  name='export_feedback'),
                             )
        return extra_urls + urls
    def export_feedback_view(self):

        return render_to_response('admin/export_feedback.html')

    def document_link(self, obj):
        url = reverse('admin:crowdataapp_document_change', args=(obj.document.id,))
        return mark_safe('<a href="%s">%s</a>' % (url, obj.document.name))

admin.site.register(models.DocumentSetFormEntry)

admin.site.register(models.DocumentSet, DocumentSetAdmin)
admin.site.register(models.Document, DocumentAdmin)
admin.site.unregister(forms_builder.forms.models.Form)

admin.site.register(models.Feedback, FeedbackAdmin)

admin.site.register(models.CanonicalFieldEntryLabel, CanonicalFieldEntryLabelAdmin)

admin.site.register(models.Politician)
admin.site.register(models.Party)

admin.site.unregister(User)
admin.site.register(User, CrowDataUserAdmin)

from django.contrib.sites.models import Site
admin.site.unregister(Site)
admin.site.unregister(Group)
