# coding: utf-8
import urllib, json, csv, itertools
import django.http
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
from models import DocumentSet, Document

from crowdataapp import models, forms

@render_to('document_set_index.html')
def document_set_index(request):
    # TODO clean
    # stats = get_stats() # TODO clean if not needed
    # total = get_total() # TODO clean if not needed

    #widget_categories_stats = get_stats_by_cat()
    # liberated_amounts = dict(get_amounts_by_cat())

    try:
      document_set = models.DocumentSet.objects.filter(published=True).order_by('-created_at')[0]
      entries_count = document_set.get_entries_count()
      stats = { 'volunteers_count': entries_count,
                'all_declarations_count': document_set.documents.count(),
                'liberated_declarations': document_set.get_verified_documents().count(),
                 # time spent estimate: 12mins each entry
                'time_spent_minutes': entries_count * 12,
                }
      stats['progress_percent'] = int(100 * stats['liberated_declarations'] / stats['all_declarations_count'])

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

def get_stats():
    """ Get all documents that have an entry with canon """

    q = """
       SELECT SUM(FT.final_amount) AS total
       , FT.category
       FROM (
       SELECT DOC.DOC_ID
       , MAX(Vals.amount) AS final_amount -- In case different values are present
       , Cats.category
       FROM (
          SELECT D.id AS DOC_ID
          FROM crowdataapp_document D
          WHERE D.verified is TRUE
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
          SELECT category
          ,entry_id
          FROM (
              SELECT row_number() OVER(
                 PARTITION BY
                 DSFI2.entry_id
                 ORDER BY
                 DSFI2.id) AS Row
                 ,DSFI2.value AS category
                 ,DSFI2.entry_id
              FROM crowdataapp_DocumentSetFieldEntry DSFI2
              WHERE DSFI2.field_id = 66
          ) A
       WHERE Row = 1 -- get the first category only in case of disagreement
       ) Cats
       ON DFSE.id = cats.entry_id
       GROUP BY DOC.DOC_ID
       , Cats.category
       ) FT
       GROUP BY FT.category
       ORDER BY SUM(FT.final_amount) DESC
       LIMIT 4
       """

    cursor = connection.cursor()
    cursor.execute(q)
    return cursor.fetchall()

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
    args = (form, request_context, request.POST or None)

    form_for_form = forms.DocumentSetFormForForm(*args)

    if request.method == 'POST':
        if not form_for_form.is_valid():
            form_invalid.send(sender=request, form=form_for_form)
            return HttpResponseBadRequest(json.dumps(form_for_form.errors), content_type='application/json')
        else:
            entry = form_for_form.save()
            form_valid.send(sender=request, form=form_for_form, entry=entry, document_id=request.session['document_id_for_entry'])
            return HttpResponse('')
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
def transcription_new(request, document_set, filename=None, category=None):
    doc_set = get_object_or_404(models.DocumentSet, slug=document_set)
    document = None
    if request.GET.get('document_id') is not None and request.user.is_staff:

        document = get_object_or_404(models.Document, pk=request.GET.get('document_id'),
                                 document_set=doc_set)
    elif filename is not None: # TODO document name shouldn't be used as filename
        filename = filename + ".pdf"
        document = get_object_or_404(models.Document,
                                     name=filename)
    elif category is not None:
        candidates = doc_set.get_pending_documents_by_category(category=category).exclude(form_entries__user=request.user)

        if candidates.count() == 0:
            # TODO Redirect to a message page: "you've gone through all the documents in this project!"
            return render_to_response('no_more_documents.html',
                                      { 'document_set': doc_set },
                                      context_instance=RequestContext(request))

        document = candidates.order_by('?')[0]
    else:
        candidates = doc_set.get_pending_documents().exclude(form_entries__user=request.user)

        if candidates.count() == 0:
            # TODO Redirect to a message page: "you've gone through all the documents in this project!"
            return render_to_response('no_more_documents.html',
                                      { 'document_set': doc_set },
                                      context_instance=RequestContext(request))

        document = candidates.order_by('?')[0]

    # save the candidate document in the session, for later use
    # in signals.create_entry
    request.session['document_id_for_entry'] = document.id

    return render(request,
                  'transcription_new.html',
                  {
                      'document': document,
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
    import datetime
    feedback_model = models.Feedback()

    if request.method == 'POST':
        print request.POST
        feedback_form = forms.FeedbackForm(request.POST, instance=feedback_model)
        if feedback_form.is_valid():
            feedback_form.save()


    else:
        feedback_form = forms.FeedbackForm()

    return {
        'feedback_form': feedback_form
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


