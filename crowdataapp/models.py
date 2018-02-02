from collections import defaultdict
from crowdataapp.middleware import get_current_user
from itertools import ifilter
from datetime import datetime

from django.db import models, connection
from django.utils.translation import ugettext, ugettext_lazy as _
from django.contrib.auth.models import User
from django.conf import settings
from django.core.urlresolvers import reverse
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Count
from django.http import Http404
from django.shortcuts import get_object_or_404

from django_extensions.db import fields as django_extensions_fields
from django_countries import CountryField
import forms_builder
import forms_builder.forms.fields
import forms_builder.forms.models
import logging
import re

DEFAULT_TEMPLATE_JS = """// Javascript function to insert the document into the DOM.
// Receives the URL of the document as its only parameter.
// Must be called insertDocument
// JQuery is available
// resulting element should be inserted into div#document-viewer-container
function insertDocument(document_url) {
}
"""

# some mokeypatching, I don't want every field type to be available in forms
#from forms_builder.forms import fields

ALLOWED_FIELD_TYPES = (
    forms_builder.forms.fields.TEXT,
    forms_builder.forms.fields.TEXTAREA,
    forms_builder.forms.fields.CHECKBOX,
    forms_builder.forms.fields.CHECKBOX_MULTIPLE,
    forms_builder.forms.fields.SELECT,
    forms_builder.forms.fields.SELECT_MULTIPLE,
    forms_builder.forms.fields.DATE,
    forms_builder.forms.fields.DATE_TIME,
    forms_builder.forms.fields.HIDDEN,
    forms_builder.forms.fields.NUMBER,
    forms_builder.forms.fields.URL,
)

forms_builder.forms.models.Field._meta.local_fields[3]._choices \
    = filter(lambda i: i[0] in ALLOWED_FIELD_TYPES,
             forms_builder.forms.fields.NAMES)

class UserProfile(models.Model):
    user = models.ForeignKey(User, unique=True)
    name = models.CharField(_('Your Name'), max_length='128', null=False, blank=False)
    country = CountryField(_('Your country'), null=True)
    show_in_leaderboard = models.BooleanField(_("Appear in the leaderboards"),
                                              default=True,
                                              help_text=_("If checked, you will appear in CrowData's leaderboards"))

class CrowManager(models.Manager):
    def get_or_none(self, **kwargs):
        try:
            return self.get(**kwargs)
        except ObjectDoesNotExist:
            return None

    def get_or_404(self, *args, **kwargs):
        try:
            return self.get(*args, **kwargs)
        except self.model.DoesNotExist:
            raise Http404('No %s matches the given query.' % self.model._meta.object_name)

class DocumentSetManager(CrowManager):
    def get_query_set(self):
        u = get_current_user() # from LocalUserMiddleware
        rv = super(DocumentSetManager, self).get_query_set()

        # only get published if we got a User and is not staff/superuser
        if (u is not None) and (not u.is_staff) and (not u.is_superuser):
            rv = rv.filter(published=True)

        return rv

class DocumentSet(models.Model):

    objects = DocumentSetManager()

    name = models.CharField(_('Document set name'), max_length='128',)

    description = models.TextField(null=True,
                                   blank=True,
                                   help_text=_('Description for this Document Set'))

    header_image = models.URLField(null=True,
                                   blank=True,
                                   help_text=_('Header Image URL'))

    slug = django_extensions_fields.AutoSlugField(populate_from=('name'))

    tosum_field = models.ForeignKey("DocumentSetFormField",
                                        related_name='tosum_fields',
                                        null=True, blank=True,
                                        verbose_name='Field to sum on',
                                        help_text=_("Field from the form to sum total on. This will be displayed in the document set's homepage."))

    entries_threshold = models.IntegerField(default=3,
                                            null=False,
                                            help_text=_('Minimum number of coincidental answers for a field before marking it as valid'))

    head_html = models.TextField(default='<!-- <script> or <link rel="stylesheet"> tags go here -->',
                                 null=True,
                                 help_text=_('HTML to be inserted in the <head> element in this page'))

    published = models.BooleanField(_('Published'),
                                    default=True,
                                    help_text=_('Is this Document Set published to non-admins?'))

    created_at = models.DateTimeField(auto_now_add = True)
    updated_at = models.DateTimeField(auto_now = True)

    class Meta:
        verbose_name = _('Document Set')
        verbose_name_plural = _('Document Sets')

    def __unicode__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('crowdataapp.views.document_set_view',
                       args=[self.slug])

    def admin_links(self):
        kw = {"args": (self.id,)}
        links = [
            (_("Export all answers to CSV"), reverse("admin:document_set_answers_csv", **kw)),
            (_("Export all answers to JSON"), reverse("document_set_statements_json", **kw)),
            (_("Export all politicians to JSON"), reverse("politicians_json")),
            (_("Import asset declarations"), reverse("admin:kmonitor_import_asset_declarations", **kw)),
            (_("Add Documents to this document set"), reverse("admin:document_set_add_documents", **kw)),
            (_("Update Canons to this document set"), reverse("admin:document_set_update_canons", **kw))
        ]
        for i, (text, url) in enumerate(links):
            links[i] = "<a href='%s'>%s</a>" % (url, ugettext(text))
        return "<br>".join(links)
    admin_links.allow_tags = True
    admin_links.short_description = ""

    def field_names(self):
        """Used for column names in CSV export of
        :class:`DocumentUserFormEntry`
        """

        entry_time_name = forms_builder.forms.models.FormEntry._meta.get_field('entry_time').verbose_name.title()
        document_title_name = Document._meta.get_field('name').verbose_name.title()
        document_url_name = Document._meta.get_field('url').verbose_name.title()

        form = self.form.all()[0]
        return ['user'] \
            + [document_title_name, document_url_name] \
            + [f.label
               for f in form.fields.all()] \
            + [entry_time_name]

    def get_pending_documents(self):
        return self.documents.filter(verified=False)

    def get_pending_documents_by_category(self, category):
        return self.documents.filter(verified=False, category=category)

    def get_pending_documents_with_entries(self):
        return self.documents.filter(verified=False)

    def get_entries_count(self):
        return DocumentSetFormEntry.objects.filter(document__document_set=self).count()

    def get_pending_documents_count_for_user(self, user):
        return self.get_pending_documents().exclude(form_entries__user=user).count()

    def get_pending_documents_for_user(self, user):
        return self.get_pending_documents().exclude(form_entries__user=user)

    def get_verified_documents_count_for_user(self, user):
        return self.documents.filter(verified=True, form_entries__user=user).count()

    def get_verified_documents_for_user(self, user):
        return self.documents.filter(verified=True, form_entries__user=user).distinct()

    def get_verified_documents(self):
        return self.documents.filter(verified=True)

    def get_reviewed_documents_count_for_user(self, user):
        return self.documents.filter(form_entries__user=user).count()

    def leaderboard(self):
        """ Returns a queryset of the biggest contributors (User) to this DocumentSet """
        return User.objects.filter(documentsetformentry__form__document_set=self).annotate(num_entries=Count('documentsetformentry')).order_by('-num_entries')

    def userboard(self, user):
       """ Returns a queryset of the contributors (User) around user to this DocumentSet """
       reviewed_documents = self.get_reviewed_documents_count_for_user(user)
       count = self.leaderboard().filter(num_entries__gte = reviewed_documents).count()
       count_top = count -3 if count -3 >= 0 else 0
       user_top  = self.leaderboard().filter(num_entries__gte = reviewed_documents)[count_top:]
       user_down = self.leaderboard().filter(num_entries__lte = reviewed_documents).exclude(pk=user)[:3]
       result    = [user_top, user_down]
       return [item for sublist in result for item in sublist]

    def amount_on_field(self):
        """ Sums the total on verified field on the amount """

        query = """ SELECT SUM(field_entry.value::DOUBLE PRECISION)
                    FROM crowdataapp_documentsetfieldentry field_entry
                    INNER JOIN crowdataapp_documentsetformentry form_entry ON form_entry.id = field_entry.entry_id
                    INNER JOIN crowdataapp_document document ON document.id = form_entry.document_id
                    WHERE document.document_set_id = %d
                    AND field_entry.verified = TRUE
                    AND field_entry.field_id = %d""" % ( self.id, self.tosum_field.id)

        cursor = connection.cursor()
        cursor.execute(query)

        amount = cursor.fetchall()[0][0]

        return amount

class DocumentSetForm(forms_builder.forms.models.AbstractForm):
    document_set = models.ForeignKey(DocumentSet, unique=True, related_name='form')
    #document_set = models.OneToOneField(DocumentSet, parent_link=True)

    @models.permalink
    def get_absolute_url(self):
        return ('crowdata_form_detail', (), { 'slug': self.slug })

class DocumentSetFormFieldManager(models.Manager):
    """
    Only show visible fields when displaying actual form..
    """
    def visible(self):
        return self.filter(visible=True).order_by('order')

class DocumentSetFormField(forms_builder.forms.models.AbstractField):
    autocomplete = models.BooleanField(_("Autocomplete"),
        help_text=_("If checked, this text field will have autocompletion"))
    form = models.ForeignKey(DocumentSetForm, related_name="fields")
    order = models.IntegerField(_("Order"), null=True, blank=True)
    group = models.CharField(_("Group"),max_length= 200 ,
    help_text=_("If checked, this text field will have autocompletion"))
    verify = models.BooleanField(_("Verify"), default=True)
    objects = DocumentSetFormFieldManager()

    def save(self, *args, **kwargs):
        if self.order is None:
            self.order = self.form.fields.count()
        super(DocumentSetFormField, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        fields_after = self.form.fields.filter(order__gte=self.order)
        fields_after.update(order=models.F("order") - 1)
        DocumentSetFieldEntry.objects.filter(field_id=self.id).delete()
        super(DocumentSetFormField, self).delete(*args, **kwargs)

class DocumentSetFormEntry(forms_builder.forms.models.AbstractFormEntry):
    """ A :class:`forms_builder.forms.models.AbstractFormEntry` plus
    foreign keys to the :class:`User` and filled the form and the
    :class:`Document` it belongs to
    """

    form = models.ForeignKey("DocumentSetForm", related_name='entries')
    document = models.ForeignKey('Document', related_name='form_entries', blank=True, null=True)
    user = models.ForeignKey(User, blank=True, null=True)

    def to_dict(self):
        form_fields = dict([(f.id, f.label)
                            for f in self.form.fields.all()])
        entry_time_name = forms_builder.forms.models.FormEntry._meta.get_field('entry_time').verbose_name.title()

        rv = dict()
        rv['user'] = str(self.user.pk)
        rv['username'] = self.user.get_username()
        rv[Document._meta.get_field('name').verbose_name.title()] = self.document.name
        rv[Document._meta.get_field('url').verbose_name.title()] = self.document.url

        for field_entry in self.fields.all():
            rv['answer_' + form_fields[field_entry.field_id] + '_verified'] = field_entry.verified
            rv['answer_' + form_fields[field_entry.field_id]] = field_entry.value

        rv[entry_time_name] = self.entry_time

        return rv

    def get_answer_for_field(self, field):
        answer_qs = self.fields.filter(field_id=field.pk)
        try:
            answer_for_field = answer_qs[0]
        except IndexError: # there is no answer for this field
            msg = "Haven't received value for field {0}. Check if your form isn't missing this field.".format(field.slug)
            if settings.DEBUG:
                raise IndexError(msg + " On production server this will be only logged.")

            logging.getLogger('crowdata.crowdataapp.views.input').error(msg)
            return None

        if answer_for_field.canonical_label is None:
          return answer_for_field.value
        else:
          return answer_for_field.canonical_label.value

    def force_verify(self):
        """ set this entire entry as verified, overriding the normal rules
            (intended for marking admin' entries as verified) """

        for field in self.fields.all():
            if DocumentSetFormField.objects.get(pk=field.field_id).verify:
              # mark field entry as verified
              field.verified = True
              for other_field in self.fields.filter(field_id=field.pk).exclude(pk=field.pk):
                  self.verified = (field.value == other_field.value)
                  other_field.save()
              field.save()

        self.document.verified = True
        self.document.save()

    def __str__(self):
        return str(self.document) + ' ' + str(self.user)

class DocumentSetFieldEntry(forms_builder.forms.models.AbstractFieldEntry):
    entry = models.ForeignKey("DocumentSetFormEntry", related_name="fields")
    verified = models.BooleanField(default=False, null=False)
    canonical_label = models.ForeignKey("CanonicalFieldEntryLabel", related_name="fields", null=True)
    group = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add = True, null=True)
    updated_at = models.DateTimeField(auto_now = True, null=True)

    def assigned_canonical_value(self):
      if self.canonical_label is None:
        return ''
      else:
        return self.canonical_label.value

    def get_canonical_value(self):
      order_similarity = "similarity(unaccent(lower(value)), unaccent(lower('%s')))" % self.value.replace("'","''")
      similarity = "similarity(unaccent(lower(value)), unaccent(lower('%s'))) > 0.34" % self.value.replace("'","''")

      # Get all the canons
      best_canons = CanonicalFieldEntryLabel \
                            .objects.filter(value__similar=self.value,
                                            form_field_id=self.field_id) \
                            .extra(select={
                                'distance': similarity,
                                'order_distance': order_similarity
                            }) \
                            .order_by('-order_distance')

      if len(best_canons) == 0:
        best_canonical_label = CanonicalFieldEntryLabel(value=self.value, document_set= self.entry.document.document_set, form_field_id=self.field_id)
        best_canonical_label.save()
      else:
        best_canonical_label = best_canons[0]

      return best_canonical_label

    # I'm only using this method to force the setting of the canon
    def save_without_setting_canon(self, *args, **kwargs):
      """ when the field is saved we need to look for the canonical form
      """
      super(DocumentSetFieldEntry, self).save(*args, **kwargs)


    def save(self, *args, **kwargs):
      """ when the field is saved we need to look for the canonical form
      """
      if DocumentSetFormField.objects.get(pk=self.field_id).autocomplete:
        self.canonical_label = self.get_canonical_value()

      super(DocumentSetFieldEntry, self).save(*args, **kwargs)


class DocumentSetRankingDefinition(models.Model):
    """ the definition of a ranking (leaderboard of sorts) for a DocumentSet """

    GROUPING_FUNCTIONS = (
        ('AVG', _('Average')),
        ('COUNT', _('Count')),
        ('SUM', _('Sum')),
    )

    SUBQUERY_LABEL = """
    SELECT distinct(document.id) AS document_id,
          coalesce(canonical_label.value, field_entry.value) AS value,
          canonical_label.id as canonical_label_id
    FROM crowdataapp_documentsetfieldentry field_entry
    LEFT OUTER JOIN crowdataapp_canonicalfieldentrylabel canonical_label ON canonical_label.id = field_entry.canonical_label_id
    INNER JOIN crowdataapp_documentsetformentry form_entry ON form_entry.id = field_entry.entry_id
    INNER JOIN crowdataapp_document document ON document.id = form_entry.document_id
    WHERE document.document_set_id = %(document_set_id)d
      AND field_entry.verified = TRUE
      AND field_entry.field_id = %(label_field_id)d
    """

    SUBQUERY_MAGNITUDE = """
    SELECT distinct(document.id) AS document_id,
          cast(field_entry.value AS double PRECISION) AS value
     FROM crowdataapp_documentsetfieldentry field_entry
     INNER JOIN crowdataapp_documentsetformentry form_entry ON form_entry.id = field_entry.entry_id
     INNER JOIN crowdataapp_document document ON document.id = form_entry.document_id
     WHERE document.document_set_id = %(document_set_id)d
       AND field_entry.verified = TRUE
       AND field_entry.field_id = %(magnitude_field_id)d
    """

    name = models.CharField(_('Ranking title'), max_length=256, editable=True, null=False)
    document_set = models.ForeignKey(DocumentSet, related_name='rankings')
    label_field = models.ForeignKey(DocumentSetFormField, related_name='label_fields')
    magnitude_field = models.ForeignKey(DocumentSetFormField,
                                        related_name='magnitude_fields',
                                        null=True, blank=True)

    amount_rows_on_home = models.IntegerField(default=10,
                                            null=True,
                                            help_text=_('Cantidad de filas a mostrar en el home page.'))

    grouping_function = models.CharField(_('Grouping Function'),
                                         max_length=10,
                                         choices=GROUPING_FUNCTIONS,
                                         default='SUM')
    sort_order = models.BooleanField(_('Sort order'),
                                     default=False,
                                     help_text=_('Ascending if checked, descending otherwise'))

    def _ranking_query(self, search_term=None, limit=None, offset=0):
        if limit is None:
            limit = 10000000

        # ToDo : WHERE label.value LIKE %(search_term)s
        q = None
        if self.grouping_function == 'COUNT':
            q = """ SELECT label.value, COUNT(label.value), label.canonical_label_id
                    FROM (%s) label
                    GROUP BY label.value, label.canonical_label_id
                    ORDER BY COUNT(label.value) %s
                    LIMIT %d OFFSET %d """ % (self.SUBQUERY_LABEL,
                                              'ASC' if self.sort_order else 'DESC',
                                              limit,
                                              offset)

            q = q % { 'document_set_id': self.document_set.id, 'label_field_id': self.label_field.id }
        elif self.grouping_function == 'SUM':
            q = """ SELECT label.value, SUM(magnitude.value), label.canonical_label_id
                    FROM (%s) label
                    INNER JOIN (%s) magnitude
                      ON magnitude.document_id = label.document_id
                    GROUP BY label.value, label.canonical_label_id
                    ORDER BY SUM(magnitude.value) %s
                    LIMIT %d OFFSET %d """ % (self.SUBQUERY_LABEL,
                                              self.SUBQUERY_MAGNITUDE,
                                              'ASC' if self.sort_order else 'DESC',
                                              limit,
                                              offset)

            q = q % { 'document_set_id': self.document_set.id,
                      'label_field_id': self.label_field.id,
                      'magnitude_field_id': self.magnitude_field_id }

        elif self.grouping_function == 'AVG':
            q = """ SELECT label.value, AVG(magnitude.value), label.canonical_label_id
                    FROM (%s) label
                    INNER JOIN (%s) magnitude
                      ON magnitude.document_id = label.document_id
                    GROUP BY label.value, label.canonical_label_id
                    ORDER BY AVG(magnitude.value) %s
                    LIMIT %d OFFSET %d """ % (self.SUBQUERY_LABEL,
                                              self.SUBQUERY_MAGNITUDE,
                                              'ASC' if self.sort_order else 'DESC',
                                              limit,
                                              offset)

            q = q % { 'document_set_id': self.document_set.id,
                      'label_field_id': self.label_field.id,
                      'magnitude_field_id': self.magnitude_field_id}
            #ToDo, filter on 'search_term': "'%" + search_term.encode('utf-8') + "%'"

        return q

    def calculate(self):
        cursor = connection.cursor()
        cursor.execute(self._ranking_query(limit=self.amount_rows_on_home))
        return cursor.fetchall()

    def calculate_all(self, search_term):
        cursor = connection.cursor()
        cursor.execute(self._ranking_query(search_term))
        return cursor.fetchall()


class Document(models.Model):
    name = models.CharField(_('Document title'), max_length=256, editable=True, null=True)
    category = models.CharField(_('Document category'), max_length=256, editable=True, null=True)
    politician = models.ForeignKey("Politician",  related_name='declarations',
                                        null=True, blank=True,)
    url = models.URLField(_('Document URL'), max_length='512', editable=True)
    document_set = models.ForeignKey(DocumentSet, related_name='documents')
    verified = models.BooleanField(_('Verified'),
                                   help_text=_('Is this document verified?'))

    opened_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add = True)
    updated_at = models.DateTimeField(_('Modified'), auto_now = True)


    entries_threshold_override = models.IntegerField(null=True,
                                                     blank=True,
                                                     help_text=_('Minimum number of coincidental answers for a field before marking it as valid. Overrides the default value set in the Document Set this Document belongs to'))

    _form_field_cache = {}

    def __unicode__(self):
        return "%s (%s)" % (self.name, self.url) if self.name else self.url

    def get_absolute_url(self):
        return "%s?document_id=%s" % (reverse('crowdataapp.views.transcription_new',
                                              kwargs={'document_set': self.document_set.slug}),
                                      self.pk)

    def entries_threshold(self):
        if self.entries_threshold_override is None:
            return self.document_set.entries_threshold
        else:
            return self.entries_threshold_override

    def is_verified_by_staff(self):
      """ The document is verified because there is a staff/superuser that revised."""
      form_entries = self.form_entries.all().distinct('user')
      for f in form_entries:
        if f.user.is_staff or f.user.is_superuser:
          return self.verified

      return False

    def is_revised_by_staff(self):
      """ The document has somebody from staff that revised it. """

      form_entries = self.form_entries.all().distinct('user')
      for f in form_entries:
        if f.user.is_staff or f.user.is_superuser:
          return True

      return False

    def verified_answers(self, any_fields=False):
        """ get a dict of verified answers (entries) for this Document
              { <DocumentSetFormField>: <value>, ... }
        """
        if not self.verified and not any_fields:
            return {}

        # oneliner: [a for a in DocumentSetFieldEntry.objects.filter(entry__document=document, verified=True).order_by('field_id').distinct().values('field__label', 'value')]

        verified_answers = {}
        for entry in DocumentSetFieldEntry.objects \
                .filter(verified=True, entry__document=self) \
                .prefetch_related('canonical_label'):

            value = entry.value

            if entry.field_id not in self._form_field_cache:
                self._form_field_cache[entry.field_id] = DocumentSetFormField.objects.get(id=entry.field_id)

            verified_answers.update({self._form_field_cache[entry.field_id]: value})

        return verified_answers

    def force_verify(self):
        form_entries = self.form_entries.all().distinct('user')
        for f in form_entries:
          if f.user.is_staff or f.user.is_superuser:
            f.force_verify()
            return


    def verify(self):
        # almost direct port from ProPublica's Transcribable.
        # Thanks @ashaw! :)

        entries = self.form_entries.all().distinct('user')
        field_to_verify = self.document_set.form.all()[0].fields.filter(verify=True)

        aggregate = defaultdict(dict)
        for field in field_to_verify:
            aggregate[field] = defaultdict(lambda: 0)

        # Maps how many answers were given of each type
        for entry in entries:
            for field in field_to_verify:
                answer = entry.get_answer_for_field(field)
                if answer == None:
                    answer = '' # also map empties
                aggregate[field][answer] += 1

        choosen = {}
        choosen_count = {}

        for field, answers in aggregate.items():
            for answer, answer_ct in answers.items():
                # number of identical entries is higher or equal to `entries_threshold'`
                if answer_ct >= self.entries_threshold() and answer_ct > choosen_count.get(field, 0):
                    choosen[field] = answer
                    choosen_count[field] = answer_ct # count maximum occurences

        if len(choosen):
            # verified fields can change, mark all document's field entries as unverified
            DocumentSetFieldEntry.objects.filter(entry__document=self).update(verified=False)

            # mark verified field entries
            for field, answer in choosen.iteritems():
                DocumentSetFieldEntry.objects.filter(entry__document=self, field_id=field.id, value=answer).update(verified=True)


        # if all fields has been verified
        if len(choosen.keys()) == len(field_to_verify):
            # verify the document
            self.verified = True
            self.updated_at = datetime.today()

        else:
            self.verified = False # mark whole document as not verified

        self.save()


    def unverify(self):
        DocumentSetFieldEntry.objects.filter(entry__in=self.form_entries.all()) \
                                     .update(verified=False)
        self.verified = False
        self.save()

    def has_entry_for_user(self, user):
        form_entries_for_user = self.form_entries.filter(user=user)
        return form_entries_for_user

    def kmonitor_extract_filled_date(self):
        # template = 'http://www.parlament.hu/internet/cplsql/ogy_vagyonpub.vagyon_kiir_egys?P_FNEV=/{year}/{id}_j0{date}k.pdf&p_cont=application/pdf'
        m = re.search('_j0(\d{6})k', self.url)
        if not m:
            raise Exception("Could not parse url: " + self.url)

        return m.group(1)

    class Meta:
        verbose_name = _('Document')
        verbose_name_plural = _('Documents')


# This is the model that will save the canonical value of a string.
# For example for a DocumentSetFormField 'Adjudicatario' will save the canonical
# form ('Honorable Senado de la nacion') of the value ('honorable senado').
class CanonicalFieldEntryLabel(models.Model):
  value = models.CharField(_('Canonical value'), max_length=2000, editable=True, null=True)
  form_field = models.ForeignKey(DocumentSetFormField, related_name='form_field')
  document_set = models.ForeignKey(DocumentSet, related_name='canonical_values', null=True)

  def get_verified_documents(self, document_set):
    """ Get all documents that have an entry with canon """

    q = """
    SELECT distinct(document.id) AS document_id, document.name as document_name
    FROM crowdataapp_documentsetfieldentry field_entry

    LEFT OUTER JOIN crowdataapp_canonicalfieldentrylabel canonical_label ON canonical_label.id = field_entry.canonical_label_id
    INNER JOIN crowdataapp_documentsetformentry form_entry ON form_entry.id = field_entry.entry_id
    INNER JOIN crowdataapp_document document ON document.id = form_entry.document_id

    WHERE document.document_set_id = %d
      AND field_entry.verified = TRUE
      AND canonical_label.id = %d
    """ % (document_set.id, self.id)

    cursor = connection.cursor()
    cursor.execute(q)
    return cursor.fetchall()

  def has_entries(self):
    return (len(self.fields.all()) != 0)

  def reassign_entries_to(self, new_canon):
    for entry in self.fields.all():
      entry.canonical_label = new_canon
      entry.save_without_setting_canon()

class Feedback(models.Model):
    feedback_text = models.CharField(max_length=10000)
    # document_id = models.IntegerField(max_length=20)
    timestamp = models.DateTimeField(auto_now_add=True)
    document = models.ForeignKey(Document)


# K-Monitor-specific models
class Politician(models.Model):
    objects = CrowManager()

    name = models.CharField(_('Full name'), max_length='128',)

    """
    Used in most of the urls of parliamentary website
    """
    parliamentary_id = models.CharField(_('Parliamentary website ID'), max_length='24',)
    image_url = models.URLField(_('Image URL'), max_length='256',)
    party = models.ForeignKey("Party",  related_name='members',
                                        null=True, blank=True,
                                        verbose_name='Current MPs party',)
    parldata_id = models.CharField(_('External ParlData API ID'), max_length='64',)

    # Audit timestamps
    created_at = models.DateTimeField(auto_now_add = True)
    updated_at = models.DateTimeField(auto_now = True)

    def create_asset_declaration_url(self, year):
        template = 'http://www.parlament.hu/internet/cplsql/ogy_vagyonpub.vagyon_kiir_egys?P_FNEV=/{year}/{prefix}{id}_j0{date}k.pdf&p_cont=application/pdf'
        # other link; working, but longer
        # template = 'http://www.parlament.hu/aktiv-kepviseloi-nevsor?p_p_id=pairproxy_WAR_pairproxyportlet_INSTANCE_9xd2Wc9jP4z8&p_p_lifecycle=2&p_p_state=normal&p_p_mode=view&p_p_cacheability=cacheLevelPage&p_p_col_id=column-1&p_p_col_count=1&_pairproxy_WAR_pairproxyportlet_INSTANCE_9xd2Wc9jP4z8_pairAction=%2Finternet%2Fcplsql%2Fogy_vagyonpub.vagyon_kiir_egys%3FP_FNEV%3D%2F2015%2Fv050_j0151231k.pdf%26p_cont%3Dapplication%2Fpdf'

        from datetime import date, timedelta
        date_filled = date(int(year) + 1, 1, 1) - timedelta(days=1) # last day of the year

        prefix = ''
        if year == 2017:
            prefix = '0419'

        return (template.format(id=self.parliamentary_id,
                                prefix=prefix,
                                date=date_filled.strftime('%y%m%d'),
                                year=year), date_filled)

    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name = _('Politician')
        verbose_name_plural = _('Politicians')

class Party(models.Model):
    name = models.CharField(_('Full name'), max_length='128',)
    short_name = models.CharField(_('Short name'), max_length='128',)
    parldata_id = models.CharField(_('External ParlData API ID'), max_length='64',)

    # Audit timestamps
    created_at = models.DateTimeField(auto_now_add = True)
    updated_at = models.DateTimeField(auto_now = True)

    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name = _('Political Party')
        verbose_name_plural = _('Political Parties')
