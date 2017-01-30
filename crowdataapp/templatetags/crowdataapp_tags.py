from django.core.context_processors import csrf
from django import template
from django.conf import settings
from django.template.loader import get_template
from crowdataapp import models
import json

from forms_builder.forms.forms import FormForForm

register = template.Library()

class BuiltFormNode(template.Node):

    def __init__(self, name, value):
        self.name = name
        self.value = value

    def render(self, context):
        request = context["request"]
        post = getattr(request, "POST", None)
        form = template.Variable(self.value).resolve(context) # TODO catch VariableDoesNotExist Error: Admin: Define form in given DOcumentSet (users shouldn;t be allowed to enter site if this is not set)
        t = get_template("forms/includes/built_form.html")
        context["form"] = form
        form_args = (form, context, post or None)
        form_for_form = FormForForm(*form_args)

        # kind of a hack
        # add the 'data-verify' attribute if the field is marked
        # as a verifiable field
        for field in form_for_form.form_fields.filter(verify=True):
            form_for_form.fields[field.slug].widget.attrs['data-verify'] = True


        for field_ in form_for_form.form_fields:
            form_for_form.fields[field_.slug].widget.attrs['group'] = field_.group
            form_for_form.fields[field_.slug].group = field_.group

        context["form_for_form"] = form_for_form
        return t.render(context)


@register.tag
def render_form(parser, token):
    """
    render_form takes one argument in one of the following formats:

    {% render_build_form form_instance %}

    """
    try:
        _, arg = token.split_contents()
        arg = "form=" + arg

        name, value = arg.split("=", 1)
        print arg, value
    except ValueError:
        raise template.TemplateSyntaxError(render_form.__doc__)

    return BuiltFormNode(name, value)

@register.simple_tag(takes_context=True)
def pending_document_count_for_user(context, document_set):
    user = context['request'].user
    return document_set.get_pending_documents_count_for_user(user)

@register.simple_tag(takes_context=True)
def render_ranking(context, ranking_definition):
    t = get_template('ranking.html')
    context['ranking'] = ranking_definition

    r = t.render(context)
    return r

@register.simple_tag(takes_context=True)
def render_ranking_all(context, ranking_definition, search_term):
    t = get_template('ranking_all.html')
    context['ranking'] = ranking_definition
    context['ranking_calculate_all'] = ranking_definition.calculate_all(search_term)

    r = t.render(context)
    return r

@register.simple_tag
def index_in_ranking(page, counter, cant_per_page ):
   return int(page)*cant_per_page-cant_per_page+counter

@register.simple_tag(takes_context=True)
def call_to_action(context, document_set):
    t = get_template("call_to_action.html")
    context["document_set"] = document_set

    return t.render(context)

@register.simple_tag(takes_context=True)
def documents_verified(context, document_set):
    t = get_template("documents_verified.html")
    context["document_set"] = document_set

    return t.render(context)

@register.simple_tag(takes_context=True)
def list_ranking_user(context, users_ranking, profile = None):
    t = get_template("list_ranking_user.html")
    context["users_ranking"] = users_ranking
    context["profile"] = profile
    return t.render(context)


@register.filter_function
def order_by(queryset, args):
    args = [x.strip() for x in args.split(',')]
    return queryset.order_by(*args)


@register.filter('get_value_from_dict')
def get_value_from_dict(dict_data, key):
    """
    usage example {{ your_dict|get_value_from_dict:your_key }}
    """
    if key:
        return dict_data.get(key)

@register.filter_function
def get_setting(name, default):
    return getattr(settings, name, default)

@register.filter_function
def dictvalue(the_dict, key):
   # Try to fetch from the dict, and if it's not found return None
   return the_dict.get(key, None)

@register.filter_function
def getattribute(the_object, attribute_name):
   # Try to fetch from the object, and if it's not found return None.
   return getattr(the_object, attribute_name, None)