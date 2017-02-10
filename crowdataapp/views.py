# coding: utf-8
import urllib, json, csv, itertools
import django.http
import json
from django.conf import settings
from django.shortcuts import get_object_or_404, redirect, render_to_response, render
from django.utils.translation import ugettext, ugettext_lazy as _
from django.core.urlresolvers import resolve, reverse
from django.db.models import Count
from django.db.models.signals import post_save
from django.template import RequestContext
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseForbidden, HttpResponseBadRequest
from django.contrib import auth
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.db import models, connection
from datetime import datetime
from annoying.decorators import render_to
from forms_builder.forms.signals import form_valid, form_invalid
import logging
from models import DocumentSet, Document
import re

from crowdataapp import models, forms

@render_to('document_set_index.html')
def document_set_index(request):
    # TODO clean
    # total = get_total() # TODO clean if not needed

    #widget_categories_stats = get_stats_by_cat()
    # liberated_amounts = dict(get_amounts_by_cat())

    try:
      document_set = models.DocumentSet.objects.filter(published=True).order_by('-created_at')[0]
      stats = _get_stats(document_set)

    except IndexError:
      document_set = None
      stats = {}

    return { 'document_set': document_set,
             #'header_title': _('Choose one of this project'),
             'stats': stats,
             #'liberated_amounts':liberated_amounts,
             #'total':total ,
             #'alimentos':widget_categories_stats,
            # 'alimentos_verified_docs': widget_categories_stats,
            # 'widget_cat_stats': get_stats_by_cat()
             }

def _get_stats(document_set):
    entries_count = document_set.get_entries_count()
    stats = { 'volunteers_count': 124 + entries_count,
                'all_declarations_count': document_set.documents.count(),
                'liberated_declarations': document_set.get_verified_documents().count(),
                'liberated_declarations_since_iceage': 397 + document_set.get_verified_documents().count(),
                 # time spent estimate: 16 minutes each entry
                'time_spent_hours': 99 + (entries_count * 16) / 60,
                }
    stats['progress_percent'] = int(100 * stats['liberated_declarations'] / stats['all_declarations_count'])

    return  stats

def get_stats_by_cat():
    q = """
    SELECT a.category,
    COUNT (a.*) as number_of_docs
    , b.number_of_verified_docs
    FROM crowdataapp_document a
    LEFT OUTER JOIN (
     SELECT category
         , COUNT (*) as number_of_verified_docs
     FROM crowdataapp_document
     WHERE verified=true
     GROUP BY category
    ) as b
    ON a.category = b.category
    GROUP BY a.category, b.number_of_verified_docs
    """

    cursor = connection.cursor()
    cursor.execute(q)
    return cursor.fetchall()

    return cursor.fetchall()

def get_amounts_by_cat():
    q = """
         SELECT FT.category as selected_cat, SUM(FT.final_amount) AS total
     FROM (
       SELECT DOC.DOC_ID,
              Cats.category,
              MAX(Vals.amount) AS final_amount -- In case different values are present
       FROM (
          SELECT D.id AS DOC_ID
          FROM crowdataapp_document D
          --WHERE D.verified is TRUE
           ) DOC
       INNER JOIN crowdataapp_DocumentSetFormEntry DFSE
           ON DOC.doc_id= DFSE.document_id
       INNER JOIN (
          SELECT DSFI1.value::NUMERIC as amount
              ,DSFI1.entry_id
          FROM crowdataapp_DocumentSetFieldEntry DSFI1
          WHERE DSFI1.field_id = 88
          AND DSFI1.verified is TRUE
          ) Vals
           ON DFSE.id = Vals.entry_id
       INNER JOIN (
          SELECT DSFI2.value as category
              ,DSFI2.entry_id
          FROM crowdataapp_DocumentSetFieldEntry DSFI2
          WHERE DSFI2.field_id = 66
          --AND DSFI2.verified is TRUE
          ) Cats
       ON DFSE.id = Cats.entry_id
       GROUP BY DOC.DOC_ID
            , Cats.category
       ) FT
        GROUP BY FT.category
      """

    cursor = connection.cursor()
    cursor.execute(q)
    return cursor.fetchall()

    return cursor.fetchall()

def get_total():

    q = """
     SELECT SUM(FT.final_amount) AS total
       FROM (
       SELECT DOC.DOC_ID
       , MAX(Vals.amount) AS final_amount -- In case different values are present
       FROM (
          SELECT D.id AS DOC_ID
          FROM crowdataapp_document D
          --WHERE D.verified is TRUE
       ) DOC
       INNER JOIN crowdataapp_DocumentSetFormEntry DFSE
       ON DOC.doc_id= DFSE.document_id
       INNER JOIN (
          SELECT DSFI1.value::NUMERIC as amount
          ,DSFI1.entry_id
          FROM crowdataapp_DocumentSetFieldEntry DSFI1
          WHERE DSFI1.field_id = 88
          AND DSFI1.verified is TRUE
       ) Vals
       ON DFSE.id = Vals.entry_id

       GROUP BY DOC.DOC_ID
       ) FT
    """
    cursor = connection.cursor()
    cursor.execute(q)
    return cursor.fetchall()

@render_to('document_set_landing.html')
def document_set_view(request, document_set):
    document_set = get_object_or_404(models.DocumentSet,
                                     slug=document_set)
    return {
        'document_set': document_set,
    }

def form_detail(request, slug, template="forms/form_detail.html"):
    form = get_object_or_404(models.DocumentSetForm, slug=slug)
    request_context = RequestContext(request)
    post = request.POST.copy() or None
    packed_multiples = {}


    # pack dates from multiple fields (professionaly it should be done by form widgets)
    def getelem(arr, i, default):
        return arr[i] if len(arr) > i else default

    packed_dates = {}
    for k in post.keys():
        if "-year" in k or "-month" in k or "-day" in k:
            keytemplate = k.replace('-year', '-DATEPART').replace('-month', '-DATEPART').replace('-day', '-DATEPART')

            years = post.getlist(keytemplate.replace('-DATEPART', '-year'))
            months = post.getlist(keytemplate.replace('-DATEPART', '-month'))
            days = post.getlist(keytemplate.replace('-DATEPART', '-day'))

            dates = []
            if len(years) and years[0]:
                for i in range(len(years)):
                    dates.append('{:0>2}-{:0>2}-{:0>2}'.format(getelem(years,i,''), getelem(months,i,'').replace('choose',''), getelem(days,i,'')))

            packed_dates[keytemplate.replace('-DATEPART', '_date')] = dates

    # insert packed values in dictionary
    for key, dates in packed_dates.iteritems():
        if '[]' in key:
            post.setlist(key, dates)
        else:
            if len(dates):
                post[key] = dates[0]
            else:
                post[key] = ''

    # remove old unpacked entries
    [post.pop(key.replace('_date', '-year'), None) for key in packed_dates.keys()]
    [post.pop(key.replace('_date', '-month'), None) for key in packed_dates.keys()]
    [post.pop(key.replace('_date', '-day'), None) for key in packed_dates.keys()]



    # pack multiple fields in JSON
    pop_me = []
    nested_multiline = {}
    for k in post.keys():
        # if it is multivalued
        if len(k) > 2 and k[-2:] == '[]':
            values = post.getlist(k)
            for i in range(len(values)):
                if values[i] == 'choose': # hack to get multivalued selects # TODO strip also if we have in future non-multivalue selects
                    values[i] = ''

            if values == [u'']:
                values = []

            k = k[:-2]
            packed_multiples[k] = json.dumps(values, ensure_ascii=False)

            # detect nested multilines
            m = re.search(r"^([\w\-_]+)\[(\d+)\]$", k)
            if m:
                nested_multiline[m.group(1)] = ''
                pop_me.append(k + '[]')
    [post.pop(k,None) for k in pop_me]

    for k in nested_multiline.keys():
        i = 0
        list_of_lists = []
        while True:
            jarr = packed_multiples.pop(k + '[' + str(i) + ']', None)
            if jarr == None:
                break

            jarr = json.loads(jarr)
            list_of_lists.append(jarr)
            i += 1

        packed_multiples[k] = json.dumps(list_of_lists, ensure_ascii=True)

    # insert packed values in dictionary
    post.update(packed_multiples)

    # remove old unpacked entries
    [post.pop(key + '[]', None) for key in packed_multiples.keys()]

    # check if we forgot to map any form field in DB
    unmapped_by_design = getattr(settings, 'UNMAPPED_FORM_FIELDS', [])
    unmapped_by_design += ['csrfmiddlewaretoken']
    unmapped_by_accident = []

    dbfields = [f['slug'] for f in models.DocumentSetFormField.objects.filter(form__slug=slug).values('slug')]
    for fieldname in post.keys():
        if not fieldname in dbfields and not fieldname in unmapped_by_design and not fieldname[:2] == '__':
            unmapped_by_accident.append(fieldname)

    if len(unmapped_by_accident):
        msg = 'Form fields {} are not mapped in the database.'.format(unmapped_by_accident)
        if getattr(settings, 'DEBUG', False):
            raise IndexError(msg + " On production server this will be only logged.")
        else:
            logging.getLogger('crowdata.crowdataapp.views.input').error(msg)

    args = (form, request_context, post)
    form_for_form = forms.DocumentSetFormForForm(*args)
    doc_id = post.get('__document_id')

    if request.method == 'POST':
        if not form_for_form.is_valid():
            form_invalid.send(sender=request, form=form_for_form)
            return HttpResponseBadRequest(json.dumps(form_for_form.errors), content_type='application/json')
        else:
            entry = form_for_form.save()
            form_valid.send(sender=request, form=form_for_form, entry=entry, document_id=doc_id, staff_force_verification=request.POST.get('staff_force_verification', None))

            return HttpResponseRedirect(reverse('feedback', kwargs={'document_id':doc_id}))

    return render_to_response(template, { 'form': form }, request_context)

def show_document(request, document_set,document_id):
  document_set = get_object_or_404(models.DocumentSet, slug=document_set)
  document = get_object_or_404(models.Document, id=int(document_id))

  return render(request,
                'show_document.html',
                {
                    'document': document,
                    'document_set': document_set,
                    'head_html': document.document_set.head_html
                })

@render_to('document_set_ranking.html')
def ranking_all(request, document_set, ranking_id):
    document_set = get_object_or_404(models.DocumentSet,
                                slug=document_set)

    ranking = get_object_or_404(models.DocumentSetRankingDefinition,
                              pk=ranking_id)
    return {
            'document_set': document_set,
            'ranking': ranking,
            'page': request.GET.get('page', '1'),
            'search_term': request.REQUEST.get('search'),
            }

@login_required
@render_to('liberate_mp.html')
def liberate_mp(request, document_set_slug):
    doc_set = DocumentSet.objects.get_or_404(slug=document_set_slug)

    candidates = doc_set.get_pending_documents().exclude(form_entries__user=request.user)
    if candidates.count() == 0:
        # TODO Redirect to a message page: "you've gone through all the documents in this project!"
        return render_to_response('no_more_documents.html',
                                  { 'document_set': doc_set },
                                  context_instance=RequestContext(request))

    document = candidates.order_by('?')[0]

    return {'document': document,
            'document_set': doc_set,
            'mp': document.politician,
            }


@login_required
def transcription_new(request, document_set, doc_id=None, category=None):
    doc_set = get_object_or_404(models.DocumentSet, slug=document_set)
    document = None
    if doc_id:
        document = get_object_or_404(models.Document, pk=doc_id,
                                 document_set=doc_set)
    elif category is not None:
        candidates = doc_set.get_pending_documents_by_category(category=category).exclude(form_entries__user=request.user)

        if candidates.count() == 0:
            # TODO Redirect to a message page: "you've gone through all the documents in this project!"
            return render_to_response('no_more_documents.html',
                                      { 'document_set': doc_set },
                                      context_instance=RequestContext(request))

        document = candidates.order_by('+opened_count','?')[0]
    else:
        candidates = doc_set.get_pending_documents().exclude(form_entries__user=request.user)

        if candidates.count() == 0:
            # TODO Redirect to a message page: "you've gone through all the documents in this project!"
            return render_to_response('no_more_documents.html',
                                      { 'document_set': doc_set },
                                      context_instance=RequestContext(request))

        document = candidates.order_by('+opened_count','?')[0]

    document.opened_count += 1
    document.save() # TODO can incrment and save can be done in one step?

    return render(request,
                  'transcription_new.html',
                  {
                      'document': document,
                      'mp': document.politician,
                      'head_html': document.document_set.head_html,
                      'pending_documents_count': doc_set.get_pending_documents_count_for_user(request.user),
                      'verified_documents_count': doc_set.get_verified_documents_count_for_user(request.user),
                      'reviewed_documents_count': doc_set.get_reviewed_documents_count_for_user(request.user)
                  })

def autocomplete_field(request, document_set, field_name):
    document_set = get_object_or_404(models.DocumentSet, slug=document_set)
    field = document_set.form.all()[0].fields.get(slug=field_name)

    q = request.REQUEST.get('q')
    if q is not None:
        verified_entries = models.DocumentSetFieldEntry.objects\
            .order_by('value') \
            .filter(field_id=field.pk, verified=True) \
            .extra(
                where=['unaccent(value) ilike %s'], params=["%%%s%%" % q]
            ) \
            .prefetch_related('canonical_label')
    else:
        verified_entries = models.DocumentSetFieldEntry.objects\
            .order_by('value') \
            .filter(field_id=field.pk, verified=True)

    return HttpResponse(json.dumps(map(lambda e: {'value': e.canonical_label.value if e.canonical_label is not None else e.value,
                                                  'tokens': e.value.split(' ') },
                                       verified_entries)),
                        content_type='application/json')

@render_to('login_page.html')
def login(request):
    return login_anonymously(request)
    # next_page = request.REQUEST.get(auth.REDIRECT_FIELD_NAME, reverse('document_set_index'))
    #
    # if request.user.is_authenticated():
    #     return HttpResponseRedirect(next_page)
    #
    # request.session['redirect_after_login'] = next_page
    #
    # user = auth.authenticate(request=request)
    # if user is not None:
    #     auth.login(request, user)
    #     return HttpResponseRedirect(reverse('after_login'))
    # else:
    #     return { }

@render_to('feedback.html')
def feedback(request, document_id):
    feedback_model = models.Feedback()
    document_set = Document.objects.get(pk=document_id).document_set
    feedback_sent = False

    if request.method == 'POST':
        print request.POST
        feedback_form = forms.FeedbackForm(request.POST, instance=feedback_model)
        if feedback_form.is_valid():
            feedback_form.save()
            feedback_sent = True

    else:
        feedback_form = forms.FeedbackForm()

    return {
        'feedback_form': feedback_form,
        'document_set_slug': document_set.slug,
        'stats': _get_stats(document_set),
        'feedback_sent': feedback_sent,
    }

@render_to('login_anonymously.html')
def login_anonymously(request):


    next_page = request.REQUEST.get(auth.REDIRECT_FIELD_NAME, reverse('document_set_index'))

    user = auth.authenticate(request=request)
    request.session['redirect_after_login'] = next_page
    if user is not None:

        auth.login(request, user)
        return HttpResponseRedirect(reverse('after_login'))
    else:
        from django.contrib.auth.models import User
        from django.contrib.auth import authenticate, login

        username = randomword(5)
        password = randomword(5)

        created_user = User.objects.create_user(username, '', password, first_name=username, last_name=username)

        user = authenticate(username=username, password=password)
        auth.login(request, user)
        return HttpResponseRedirect(reverse('after_login'))

import random, string

def randomword(length):
   return ''.join(random.choice(string.lowercase) for i in range(length))

def logout(request):
    auth.logout(request)
    return HttpResponseRedirect(reverse('document_set_index'))

@login_required
def after_login(request):
    if 'redirect_after_login' in request.session:
        redir = request.session['redirect_after_login']
        del request.session['redirect_after_login']
        return redirect(redir)

    return redirect(reverse('document_set_index'))

@render_to('edit_profile.html')
@login_required
def edit_profile(request):
    """ Profile Edit """
    try:
        profile = models.UserProfile.objects.get(user=request.user)
    except models.UserProfile.DoesNotExist:
        profile = None

    if request.method == 'POST':
        form = forms.UserProfileForm(data=request.POST, instance=profile)
        if form.is_valid():
            profile = form.save(commit=False)
            profile.user = request.user
            profile.save()
            if 'redirect_after_login' in request.session:
                redir = request.session['redirect_after_login']
                del request.session['redirect_after_login']
                return redirect(redir)
            else:
                return redirect(reverse('edit_profile'))
    else:
        form = forms.UserProfileForm(instance=profile)

    return {
        'profile_form': form
    }

@render_to('shutdown.html')
def on_shutdown(request, document_set):
    document_set = get_object_or_404(models.DocumentSet,slug=document_set)
    return {
        'document_set': document_set
        }

@render_to('show_profile.html')
def user_profile(request, document_set, username):
    """ Show User Profile """
    document_set = get_object_or_404(models.DocumentSet, slug=document_set)
    user = get_object_or_404(models.User, username=username)

    try:
      profile = models.UserProfile.objects.get(user=user)
    except models.UserProfile.DoesNotExist:
          profile = models.UserProfile(user=user, name=user.get_full_name())
          profile.save()

    return {
      'document_set' : document_set,
      'profile': profile,
      'full_name' : profile.user.get_full_name(),
      'verified_documents_count': document_set.get_verified_documents_count_for_user(profile.user),
      'verified_documents' : document_set.get_verified_documents_for_user(profile.user),
      'pending_documents_count' : document_set.get_pending_documents_count_for_user(profile.user),
      'pending_documents' : document_set.get_pending_documents_for_user(profile.user),
      'users_ranking_list' : document_set.userboard(profile.user.pk),
      'page': request.GET.get('page', '1'),
      'search_term': request.REQUEST.get('search'),
    }
@render_to("users_all.html")
def users_all(request, document_set):
    """ Show all ranking of Users """
    document_set = get_object_or_404(models.DocumentSet, slug=document_set)

    return {
            'document_set': document_set,
            'users_list':document_set.leaderboard(),
            'page': request.GET.get('page', '1'),
            'search_term': request.REQUEST.get('search'),
            }

@render_to("documents_by_entry_value.html")
def documents_by_entry_value(request, document_set, field_id, canon_id):
    """ Show all documents that have a field value in the field_id"""

    canon = get_object_or_404(models.CanonicalFieldEntryLabel, pk=canon_id)
    document_set = get_object_or_404(models.DocumentSet, slug=document_set)

    documents = canon.get_verified_documents(document_set)

    return {
            'entry_value': canon.value,
            'field_name': models.DocumentSetFormField.objects.get(pk=field_id).label,
            'documents': documents,
            'document_set': document_set,
    }

def f4(seq):
       # order preserving
       noDupes = []
       [noDupes.append(i) for i in seq if not noDupes.count(i)]
       return noDupes

def convert(entries):
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

def politicians_json(self):
    politicians = [{
        '_id': {
            'km_id': p.id,
            'parliamentary_id': p.parliamentary_id
        },
        'name': {
            'value': p.name
        }
                   } for p in models.Politician.objects.all()]

    return HttpResponse(json.dumps(politicians), content_type="application/json")

def statements_json(request, document_set_id, document_id=None):
    statements = []
    if document_id:
        docs = models.Document.objects.select_related('politician').filter(verified=True, document_set__id=document_set_id, id=document_id)
    else:
        docs = models.Document.objects.select_related('politician').filter(verified=True, document_set__id=document_set_id)

    for doc in docs:
        ds = {
            "name": doc.politician.name,
            'familyMembers': [],
            'residentialProperties': []
        }

        vfs = {}
        for k, value in doc.verified_answers().iteritems():
            if value and (value[0] == '{' or value[0] == '['):
                value = json.loads(value)
            vfs[k.slug] = value

        # =============================
        # FAMILY
        # =============================

        if vfs.get('spouse', None):
            ds['familyMembers'].append({
                'status': 'Házas-/élettárs',
                'name': vfs['spouse']
            })

        if vfs.get('children',[]):
            for c in vfs['children']:
                if c:
                    ds['familyMembers'].append({
                        'status': 'gyermek',
                        'name': c
                    })

        # =============================
        # RESIDENTIAL PROPERTIES
        # =============================

        residentialProperties_fields = [
            'location',
            'area',
            'area_unit',
            'area_unit_other',
            'cultivation_checkbox1',
            'cultivation_checkbox2',
            'cultivation_checkbox3',
            'cultivation_other',
            'building_nature1',
            'building_nature2',
            'building_nature3',
            'building_nature_other',
            'building_area',
            'building_area_unit',
            'building_area_unit_other',
            'legal_designation1',
            'legal_designation2',
            'legal_designation3',
            'legal_designation_other',
            'legal_status1',
            'legal_status2',
            'legal_status3',
            'legal_status_other',
            'ownership_ratio1',
            'ownership_ratio2',
            'ownership_ratio_percent',
            'acquisition1',
            'acquisition_date',
            'property_category',
        ]
        residentialProperties_count = reduce(
            lambda len1, len2: max(len1,len2),
            [len(vfs.get(fld, [])) for fld in residentialProperties_fields])

        def elemat(arr, i, default=None):
            if i < len(arr):
                v = arr[i]
                if v == '' or v == u'':
                    v = None
                return v

            else:
                return default

        for i in range(residentialProperties_count):
            prop = {}

            # RATIO
            ratio1 = elemat(vfs['ownership_ratio1'], i)
            ratio2 = elemat(vfs['ownership_ratio2'], i)
            ratiop = elemat(vfs['ownership_ratio_percent'], i)
            ratio = None
            if ratiop:
                complex = re.match('^(\d+)[/](\d+)$', ratiop)
                if complex:
                    ratiop = 100 * int(complex.group(1)) / int(complex.group(2))
                else:
                    ratio = int(ratiop)

            elif ratio1 and ratio2:
                ratio = 100 * int(ratio1) / int(ratio2)

            # AREA
            area = elemat(vfs['area'], i)
            area_unit = elemat(vfs['area_unit'], i)
            if area_unit == 'egyeb':
                area_unit = elemat(vfs['area_unit_other'], i)

            building_area = elemat(vfs['building_area'], i)
            building_area_unit = elemat(vfs['building_area_unit'], i)
            if building_area_unit == 'egyeb':
                area_unit = elemat(vfs['building_area_unit_other'], i)

            if building_area and building_area_unit:
                building_area += building_area_unit
            if area and area_unit:
                area += area_unit

            def aggregate_checkboxes(i, prefix, options, other):
                value = []
                for k, v in options.iteritems():
                    if elemat(vfs[prefix + k], i):
                        value.append(v)

                if other:
                    key = other if type(other) == str else prefix + '_other'
                    v = elemat(vfs[key], i)
                    if v:
                        value.append(v)

                if value:
                    value = u', '.join(value)
                else:
                    value = None
                return  value

            # CHECK BOXES
            # TODO this should be transformed while saving the data and supported in widgets
            legalNature = aggregate_checkboxes(i, 'legal_designation', {
                '1': u'családi ház',
                '2': u'társasház',
                '3': u'garázs'
            }, True)

            cultivation = aggregate_checkboxes(i, 'cultivation_checkbox', {
                '1': u'belterület/művelés alól kivett',
                '2': u'külterület',
                '3': u'lakás/lakóház'
            }, 'cultivation_other')

            building_nature = aggregate_checkboxes(i, 'building_nature', {
                '1': u'garázs',
                '2': u'lakóház',
                '3': u'üdülő/nyaraló'
            }, True)

            legal_status = aggregate_checkboxes(i, 'legal_status', {
                '1': u'tulajdonos',
                '2': u'haszonélvező',
                '3': u'bérlő'
            }, True)

            acquisitions = []
            acq_type = elemat(vfs['acquisition1'], i, [])
            acq_date = elemat(vfs['acquisition_date'], i, [])
            for j in range(max(len(acq_type), len(acq_date))):
                d = elemat(acq_date, j)
                if d:
                    d = d.replace('-', '. ') # "2002. 06. 20." format
                acquisitions.append({
                    'type': elemat(acq_type, j),
                    'acquiredAt': d,
                })

            ds['residentialProperties'].append({
                "function": 'howtomapit?', # TODO how to map it?
                "category": elemat(vfs.get('property_category',[]), i),
                "legalNature": legalNature,
                'legalStatus': legal_status, # TODO EXTRA FIELD
                'cultivation': cultivation,
                "area": area,
                'buildingNature': building_nature,
                "buildingArea": building_area, # TODO EXTRA FIELD
                "place": elemat(vfs['location'], i), # TODO
                "ownership": ratio,
                "acquisitions": acquisitions, # TODO these are multiple fields
                #"acquisition": None,
                #"acquiredAt": elemat(vfs['acquisition_date'], i, "NONE") + "2002. 06. 20."
            })

        # TODO how to map lands?
        # 		"lands": [
			# {
			# 	"function": "",
			# 	"area": "",
			# 	"place": "",
			# 	"legalStatus": "",
			# 	"acquisition": "",
			# 	"acquiredAt": ""
			# }
        # ],

        # TODO vehicles not mapped - Nyilatkozott-e valamilyen nagy értékű ingóságról (járművek, műtárgyak)?
        # 		"vehicles": [
			# {
			# 	"type": "",
			# 	"make": "",
			# 	"acquisition": "",
			# 	"acquiredAt": "1994"
			# }

        # =============================
        # SAVINGS
        # =============================

        # TODO how to map
        # "claims": [
			# {
			# 	"type": "",
			# 	"amount": ""
			# }
        # ],

        savings = []

        # Értékpapír vagy egyéb befektetés - Securities or other investments
        icount = reduce(
            lambda len1, len2: max(len1,len2),
            [len(vfs.get(fld, [])) for fld in ['inv_name', 'inv_value', 'inv_curr', 'inv_curr_other']])

        for i in range(icount):
            iname = elemat(vfs['inv_name'], i)
            ivalue = elemat(vfs['inv_value'], i)
            icurr = elemat(vfs['inv_curr'], i)
            icurrother = elemat(vfs['inv_curr_other'], i)

            if icurr == u'egyéb':
                icurr = icurrother

            if ivalue and icurr:
                ivalue += icurr

            if iname or ivalue:
                savings.append({
                    '_type': 'investments',
                    'type': iname,
                    'amount': ivalue,
                })

        # Takarék - savings
        icount = reduce(
            lambda len1, len2: max(len1,len2),
            [len(vfs.get(fld, [])) for fld in ['sec_name', 'sec_value', 'sec_curr', 'sec_curr_other']])

        for i in range(icount):
            iname = elemat(vfs['sec_name'], i)
            ivalue = elemat(vfs['sec_value'], i)
            icurr = elemat(vfs['sec_curr'], i)
            icurrother = elemat(vfs['sec_curr_other'], i)

            if icurr == u'egyéb':
                icurr = icurrother

            if ivalue and icurr:
                ivalue += icurr

            if iname or ivalue:
                savings.append({
                    '_type': 'savings',
                    'type': iname,
                    'amount': ivalue,
                })

        # Készpénz - cash
        icount = reduce(
            lambda len1, len2: max(len1,len2),
            [len(vfs.get(fld, [])) for fld in ['cash', 'cash_curr', 'cash_curr_other']])

        for i in range(icount):
            ivalue = elemat(vfs['cash'], i)
            icurr = elemat(vfs['cash_curr'], i)
            icurrother = elemat(vfs['cash_curr_other'], i)

            if icurr == u'egyéb':
                icurr = icurrother

            if ivalue and icurr:
                ivalue += icurr

            if iname or ivalue:
                savings.append({
                    '_type': 'cash',
                    'amount': ivalue,
                })

        # Pénzintézeti számlakövetelés vagy más pénzkövetelés - Financial Institutions account receivables or other financial assets
        icount = reduce(
            lambda len1, len2: max(len1,len2),
            [len(vfs.get(fld, [])) for fld in ['obligation_type', 'obligation_value', 'obligation_curr', 'obligation_curr_other']]) # TODO

        for i in range(icount):
            iname = elemat(vfs['obligation_type'], i)
            ivalue = elemat(vfs['obligation_value'], i)
            icurr = elemat(vfs['obligation_curr'], i)
            icurrother = elemat(vfs['obligation_curr_other'], i)

            if icurr == u'egyéb':
                icurr = icurrother

            if ivalue and icurr:
                ivalue += icurr

            if iname or ivalue:
                savings.append({
                    '_type': 'obligation',
                    'type': iname,
                    'amount': ivalue,
                })

        ds['savings'] = savings

        # =============================
        # DEBTS - Nyilatkozik-e tartozásokról?
        # =============================

        allowances = []
        icount = reduce(
            lambda len1, len2: max(len1,len2),
            [len(vfs.get(fld, [])) for fld in ['debt_type', 'debt_desc', 'debt_value', 'debt_curr', 'debt_curr_other']])

        for i in range(icount):
            iname = elemat(vfs['debt_type'], i)
            idesc = elemat(vfs['debt_desc'], i)
            ivalue = elemat(vfs['debt_value'], i)
            icurr = elemat(vfs['debt_curr'], i)
            icurrother = elemat(vfs['debt_curr_other'], i)

            if icurr == u'egyéb':
                icurr = icurrother

            if ivalue and icurr:
                ivalue += icurr

            if iname or ivalue or idesc:
                allowances.append({
                    'type': iname,
                    'amount': ivalue,
                    'notes': idesc
                })

        ds['debits'] = allowances

        # =============================
        # INCOME - Nyilatkozik-e egyéb jövedelmeiről (Jövedelemnyilatkozat)?
        # =============================

        allowances = []
        icount = reduce(
            lambda len1, len2: max(len1,len2),
            [len(vfs.get(fld, [])) for fld in ['profession', 'employer', 'active', 'income', 'income_curr', 'income_curr_other', 'regularity']])

        for i in range(icount):
            iprofession = elemat(vfs['profession'], i)

            ivalue = elemat(vfs['income'], i)
            icurr = elemat(vfs['income_curr'], i)
            icurrother = elemat(vfs['income_curr_other'], i)

            if icurr == u'egyéb':
                icurr = icurrother

            if ivalue and icurr:
                ivalue += icurr

            active = elemat(vfs['active'], i)
            if type(active) == str:
                active = bool(active)

            if iprofession or ivalue:
                allowances.append({
                    'job': iprofession,
                    'workplace': elemat(vfs['employer'], i),
                    'isActive': active,
                    'amount': ivalue, # TODO EXTRA monthly amount divided in two fields
                    'regularity': elemat(vfs['regularity'], i),
                })

        ds['incomes'] = allowances

        # =============================
        # ALLOWANCES - Nyilatkozik-e bármilyen juttatásról, ajándékról, támogatásról?
        # =============================

        allowances = []

        # Benefits - Juttatás
        icount = reduce(
            lambda len1, len2: max(len1,len2),
            [len(vfs.get(fld, [])) for fld in ['benefit_date', 'benefit_name', 'benefit_value', 'benefit_curr']])

        for i in range(icount):
            iname = elemat(vfs['benefit_name'], i)
            ivalue = elemat(vfs['benefit_value'], i)
            icurr = elemat(vfs['benefit_curr'], i)
            idate = elemat(vfs['benefit_date'], i) or None

            if ivalue and icurr:
                ivalue += icurr

            if iname or ivalue:
                allowances.append({
                    '_type': 'benefit-juttatas',
                    'name': iname,
                    'receivedAt': idate,
                    'worth': ivalue,
                })

        # Present - Ajándék
        icount = reduce(
            lambda len1, len2: max(len1,len2),
            [len(vfs.get(fld, [])) for fld in ['present_date', 'present_name', 'present_value', 'present_currency']])

        for i in range(icount):
            iname = elemat(vfs['present_name'], i)
            ivalue = elemat(vfs['present_value'], i)
            icurr = elemat(vfs['present_currency'], i)
            idate = elemat(vfs['present_date'], i) or None

            if ivalue and icurr:
                ivalue += icurr

            if iname or ivalue:
                allowances.append({
                    '_type': 'present-ajandek',
                    'name': iname,
                    'receivedAt': idate,
                    'worth': ivalue,
                })

        # Subsidies - Támogatások
        icount = reduce(
            lambda len1, len2: max(len1,len2),
            [len(vfs.get(fld, [])) for fld in ['subs_reci', 'subs_legal', 'subs_date', 'subs_provider', 'subs_purpose', 'subs_value', 'subs_curr', 'subs_curr_other']])

        for i in range(icount):
            ireci = elemat(vfs['subs_reci'], i)
            ilegal = elemat(vfs['subs_legal'], i)
            idate = elemat(vfs['subs_date'], i) or None
            iprovider = elemat(vfs['subs_provider'], i)
            ipurpose = elemat(vfs['subs_purpose'], i)
            ivalue = elemat(vfs['subs_value'], i)
            icurr = elemat(vfs['present_currency'], i)
            icurrother = elemat(vfs['income_curr_other'], i)

            if icurr == u'egyéb':
                icurr = icurrother

            if ivalue and icurr:
                ivalue += icurr

            if ireci or ivalue or ilegal or iprovider or ipurpose:
                allowances.append({
                    '_type': 'subsidy-tamogatasok',
                    'recipient': ireci,
                    'legal': ilegal,
                    'provider': iprovider,
                    'purpose': ipurpose,
                    'receivedAt': idate,
                    'worth': ivalue,
                })


        ds['allowances'] = allowances

        # Date filled
        ds['date'] = doc.kmonitor_extract_filled_date()

        # TODO Nyilatkozik-e gazdasági érdekeltségekről? not mapped

        st = {
            "_id": {
                "Document.id": doc.id,
                "Document.url": doc.url,
                "self": request.build_absolute_uri(reverse('document_set_statements_json', kwargs={'document_set_id':document_set_id, 'document_id':doc.id}))
            },
            "officer": {
                "$ref": "officers",
                "$id": {
                    "km_id": doc.politician_id
                },
                "name": doc.politician.name,
                "parliamentary_id": doc.politician.parliamentary_id
            },
            "year": {
                "$numberLong": "2016"
            },
            "dataSheet": ds,
        }

        statements.append(st)

    if document_id:
        statements = statements[0]

    return HttpResponse(json.dumps(statements, indent=2), content_type="application/json")

def answers_view( request, document_set_id):

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

    document_set = get_object_or_404(models.DocumentSet,pk=document_set_id)
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

    unique_keys_list =  f4(list_of_dictionary_keys)

    # print unique_keys_list
    final_converted_document = []
    for key in unique_keys_list:
        unique_document_entries = []
        for entry in dictionary:
            if(entry['Document Url'] == key):
                unique_document_entries.append(entry)
        final_converted_document.append(convert(unique_document_entries))
    # converted_doc = self.convert(dictionary)

    # print final_converted_document

    for entry in final_converted_document:
       writer.writerow(_encode_dict_for_csv(entry))
    return response


