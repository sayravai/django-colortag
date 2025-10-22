from collections.abc import Iterable
from itertools import chain
from typing import (
    Callable,
    Optional,
)

from django.forms import widgets
from django.utils.encoding import force_str
from django.utils.translation import gettext_lazy as _


def get_colortag_attrs(colortag, options):
    attrs = {
        'data-tagid': colortag.id,
        'data-tagslug': colortag.slug,
        'data-background': '{}'.format(colortag.color),
    }
    if not options.get('no_tooltip') and colortag.description:
        attrs.update({
            'data-bs-toggle': 'tooltip',
            'data-bs-trigger': options.get('tooltip_trigger', 'hover'),
            'data-bs-placement': options.get('tooltip_placement', 'top'),
            'title': colortag.description,
        })
    return attrs


def get_colortag_classes(colortag, options):
    cls = set(('colortag',))
    cls.add('colortag-dark' if colortag.font_white else 'colortag-light')
    if colortag.is_pinned:
        cls.add('pinned')
    if options.get('active'):
        cls.add('colortag-active')
    if options.get('button'):
        cls.add('btn')
    if options.get('label'):
        cls.update(('label', 'label-{}'.format(options.get('size', 'xs'))))
    if options.get('class'):
        cls.update(options['class'].split(' '))
    return cls


class ColortagMixIn:
    option_inherits_attrs = False
    class_name = 'colortag'

    def __init__(self, attrs=None, choices=()):
        super().__init__(attrs=attrs, choices=choices)
        if 'class' in self.attrs:
            self.attrs['class'] += ' ' + self.class_name
        else:
            self.attrs['class'] = self.class_name


class ColortagSelectMultiple(ColortagMixIn, widgets.CheckboxSelectMultiple):
    class_name = 'colortag-choice'

    def create_option(self, name, value, label, selected, index, subindex=None, attrs=None,
            colortag_instance=None):
        # colortag_instance is a new parameter that is not used in the super class method.
        # The overridden optgroups method uses this method.
        option = super().create_option(name, value, label, selected, index, subindex=subindex, attrs=attrs)
        if colortag_instance is None:
            return option
        # Add custom attributes to the option (one checkbox) that are based on
        # the corresponding ColorTag instance.
        opts = { 'button': True }
        attrs = option['attrs']
        attrs.update(get_colortag_attrs(colortag_instance, opts))
        attrs['data-class'] = ' '.join(get_colortag_classes(colortag_instance, opts))
        return option

    def optgroups(self, name, value, attrs=None):
        """Return a list of optgroups for this widget."""
        # Copied from https://github.com/django/django/blob/stable/1.11.x/django/forms/widgets.py#L570
        # (Django 1.11 django.forms.widgets.ChoiceWidget method optgroups)
        # and then slightly modified so that self.choices includes
        # model instances in addition to the HTML input values and labels.
        # Model instances in self.choices originate from the field ColortagChoiceField.
        groups = []
        has_selected = False

        for index, (option_value, option_label, colortag_instance) in enumerate(chain(self.choices)):
            if option_value is None:
                option_value = ''

            subgroup = []
            if isinstance(option_label, (list, tuple)):
                group_name = option_value
                subindex = 0
                choices = option_label
            else:
                group_name = None
                subindex = None
                choices = [(option_value, option_label)]
            groups.append((group_name, subgroup, index))

            for subvalue, sublabel in choices:
                selected = (
                    force_str(subvalue) in value and
                    (has_selected is False or self.allow_multiple_selected)
                )
                if selected is True and has_selected is False:
                    has_selected = True
                subgroup.append(self.create_option(
                    name, subvalue, sublabel, selected, index,
                    subindex=subindex, attrs=attrs,
                    colortag_instance=colortag_instance,
                ))
                if subindex is not None:
                    subindex += 1
        return groups


class ColortagIncludeExcludeWidget(ColortagMixIn, widgets.RadioSelect):
    class_name = 'colortag-inc-exc'
    template_name = "django_colortag/widgets/inc_exc_group.html"
    option_template_name = "django_colortag/widgets/inc_exc_option.html"

    def __init__(self,
                 attrs: Optional[dict[str, object]] = None,
                 tag: Optional["ColorTag"] = None,
                ) -> None:
        assert tag, "The choice must be defined"
        opts = { 'button': True }
        if attrs == None:
            attrs = {}
        attrs.update(get_colortag_attrs(tag, opts))
        attrs['style'] = f"--colortag-color: {tag.color};"
        attrs['data-class'] = ' '.join(get_colortag_classes(tag, opts))
        choices = [
            ('', tag.name),
            ('I' + str(tag.pk), tag.name),
            ('E' + str(tag.pk), tag.name),
        ]
        super().__init__(attrs, choices)

    def create_option(self,
                      name: str,
                      value: Optional[str],
                      label: str,
                      selected: bool,
                      index: int,
                      subindex: Optional[int] = None,
                      attrs: Optional[dict[str, object]] = None,
                      ) -> dict[str, object]:
        option = super().create_option(
            name, value, label, selected, index, subindex=subindex, attrs=attrs
        )
        id = attrs['id']
        if not value:
            add_class = "inactive"
            id += '_?'
        elif  value[0] == 'I':
            add_class = "include active"
            id += '_i'
        elif value[0] == "E":
            add_class = "exclude active"
            id += '_e'
        if 'data-class' in attrs:
            add_class += " " + attrs['data-class']
        if 'class' in option['attrs']:
            option['attrs']['class'] += " " + add_class
        else:
            option['attrs']['class'] = add_class
        if 'id' not in option['attrs']:
            option['attrs']['id'] = id
        return option


class ColortagIEMultiWidget(widgets.MultiWidget):
    template_name = "django_colortag/widgets/colortag_multiwidget.html"
    class_name = 'colortag-ie-group'

    def __init__(self,
                 attrs: Optional[dict[str, object]] = None,
                 choices: Optional[Iterable["ColorTag"]] = None,
                ) -> None:
        widgets = {
            c.slug: ColortagIncludeExcludeWidget(attrs, c) for c in choices
        } if choices else []
        super().__init__(widgets, attrs)
        if 'class' in self.attrs:
            self.attrs['class'] += ' ' + self.class_name
        else:
            self.attrs['class'] = self.class_name

    def set_subwidgets(self, choices: Iterable["ColorTag"]) -> None:
        self.widgets = [ColortagIncludeExcludeWidget(tag=c) for c in choices]
        self.widgets_names = ['_%s' % c.slug for c in choices]

    def get_context(self,
                    name: str,
                    value: Iterable,
                    attrs: Optional[dict[str, object]],
                    ) -> dict[str, object]:
        context = widgets.Widget.get_context(self, name, value, attrs)
        if self.is_localized:
            for widget in self.widgets:
                widget.is_localized = self.is_localized
        # value is a list/tuple of values, each corresponding to a widget
        # in self.widgets.
        if not isinstance(value, (list, tuple)):
            value = self.decompress(value)

        final_attrs = context["widget"]["attrs"]
        input_type = final_attrs.pop("type", None)
        id_ = context["widget"]["attrs"].get("id")
        subwidgets = []
        for i, (widget_name, widget) in enumerate(
            zip(self.widgets_names, self.widgets)
        ):
            if input_type is not None:
                widget.input_type = input_type
            widget_name = name + widget_name
            try:
                widget_value = value[i]
            except IndexError:
                widget_value = None
            widget_attrs = widget.attrs
            if id_:
                widget_attrs["id"] = "%s_%s" % (id_, i)
            subwidgets.append(
                widget.get_context(widget_name, widget_value, widget_attrs)["widget"]
            )
        context["widget"]["subwidgets"] = subwidgets
        return context

    def decompress(self, value):
        if value == None:
            return [None for w in self.widgets]
        return value


class AndOrWidget(widgets.CheckboxInput):
    template_name = "django_colortag/widgets/colortag_andor.html"

    def __init__(self,
                 attrs: Optional[dict[str, object]] = None,
                 check_test: Optional[Callable[[object], bool]] = None,
                 ) -> None:
        add_classes = "btn-group btn-group-sm and-or"
        if not attrs:
            attrs = {
                "class": add_classes,
            }
        elif not attrs.get("class"):
            attrs["class"] = add_classes
        else:
            attrs["class"] += " " + add_classes
        attrs.setdefault('or', {
            'data-bs-toggle': 'tooltip',
            'title': _("Show a result if it has ANY of the selected tags."),
        })
        attrs.setdefault('and', {
            'data-bs-toggle': 'tooltip',
            'title': _("Show a result only if it has ALL of the selected tags."),
        })
        super().__init__(attrs, check_test)

    def get_context(self,
                    name: str,
                    value: object,
                    attrs: Optional[dict[str, object]],
                    ) -> dict[str, object]:
        context = super().get_context(name, value, attrs)
        return context


class ColortagIEAndOrWidget(widgets.MultiWidget):

    def __init__(self,
                 attrs: Optional[dict[str, object]] = None,
                 choices: Optional[Iterable["ColorTag"]] = None,
                 ) -> None:
        if not attrs:
            attrs = {}
        helptext = attrs.pop('helptext', {
            'title': _("Colortag filter"),
            'content': _(
                "<p>You can filter results based on whether they are tagged with specified colortags.<br>" +
                "Click on a tag button once if you wish to find results that <b>include</b> that tag. " +
                "(The button will become colored and display the icon <span class='glyphicon glyphicon-check'></span>.)<br>" +
                "If you wish to <b>exclude</b> results that have the tag, click on the button another time. " +
                "(The button will become outlined with the tag color and display the icon <span class='glyphicon glyphicon-remove'></span>.)<br>" +
                "If you click on a button one more time, it will return to the default state (gray) and will not be considered in the filtering.<br>" +
                "You can also <i>right click</i> the tag buttons to toggle the state in the opposite direction.</p>" +
                "<p> You can use the OR/AND selection to determine if you wish the include-tags to be joined with an OR or an AND operator. " +
                "This defines whether a result should appear if it has <b>any</b> of the tags or if it must have <b>all</b> of the selected tags." +
                "<br>However, the OR/AND selection <b>does not apply</b> to the tags to be <b>excluded</b>: " +
                "If a result has <i>any</i> of the tags to be excluded, it will not appear in the search results." +
                "</p>"
            ),
        })
        or_tooltip = attrs.pop('or-tooltip', (
            _("Show a result if it has ANY of the selected tags.") +
            _("<br>(If a result has any of the tags to be excluded, it will not appear.)")
        ))
        and_tooltip = attrs.pop('and-tooltip', (
            _("Show a result only if it has ALL of the selected tags.") +
            _("<br>(If a result has any of the tags to be excluded, it will not appear.)")
        ))
        widgets = {
            'use_and': AndOrWidget({
                'helptext': helptext,
                'or': {
                    'data-bs-toggle': 'tooltip',
                    'data-html': "true",
                    'title': or_tooltip,
                },
                'and': {
                    'data-bs-toggle': 'tooltip',
                    'data-html': "true",
                    'title': and_tooltip,
                },
            }),
            '': ColortagIEMultiWidget(attrs, choices)
        }
        super().__init__(widgets, attrs)

    def set_subwidgets(self, choices):
        self.widgets[1].set_subwidgets(choices)

    def decompress(self, value):
        if value == None:
            return [None, None]
        return value
