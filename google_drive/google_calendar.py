""" Google Calendar XBlock implementation """
# -*- coding: utf-8 -*-
#

# Imports ###########################################################
from __future__ import absolute_import
import logging

from django import utils
from xblock.core import XBlock
from xblock.fields import Integer, Scope, String
from xblock.fragment import Fragment
from xblockutils.publish_event import PublishEventMixin
from xblockutils.resources import ResourceLoader
import copy
LOG = logging.getLogger(__name__)
RESOURCE_LOADER = ResourceLoader(__name__)

# Constants ###########################################################
DEFAULT_CALENDAR_ID = "edx.org_lom804qe3ttspplj1bgeu1l3ak@group.calendar.google.com"
DEFAULT_CALENDAR_URL = (
    'https://www.google.com/calendar/embed?mode=Month&src={}&showCalendars=0&hl=en-us'.format(DEFAULT_CALENDAR_ID))
CALENDAR_TEMPLATE = "/templates/html/google_calendar.html"
CALENDAR_EDIT_TEMPLATE = "/templates/html/google_calendar_edit.html"


def _(text):
    """
    Dummy ugettext.
    """
    return text


# Classes ###########################################################
@XBlock.needs("i18n")  # pylint: disable=too-many-ancestors
class GoogleCalendarBlock(XBlock, PublishEventMixin):
    """
    XBlock providing a google calendar view for a specific calendar
    """


    display_name = String(
        display_name=_("Display Name"),
        help=_("This name appears in the horizontal navigation at the top of the page."),
        scope=Scope.settings,
        default=_("Google Calendar")
    )
    calendar_id = String(
        display_name=_("Public Calendar ID"),
        help=_(
            "Google provides an ID for publicly available calendars. In the Google Calendar, "
            "open Settings and copy the ID from the Calendar Address section into this field."
        ),
        scope=Scope.settings,
        default=DEFAULT_CALENDAR_ID
    )
    default_view = Integer(
        display_name=_("Default View"),
        help=_("The calendar view that students see by default. A student can change this view."),
        scope=Scope.settings,
        default=1
    )
    views = [[0, _('Week')], [1, _('Month')], [2, _('Agenda')]]

    org_views = copy.deepcopy(views)
    skip_flag = False
    # Context argument is specified for xblocks, but we are not using herein
    def student_view(self, context):  # pylint: disable=unused-argument
        """
        Player view, displayed to the student
        """
        self.init_emulation()
        fragment = Fragment()
        fragment.add_content(RESOURCE_LOADER.render_django_template(
            CALENDAR_TEMPLATE,
            context={
                "mode": self.org_views[self.default_view][1],
                "src": self.calendar_id,
                "title": self.display_name,
                "language": utils.translation.get_language(),
            },
            i18n_service=self.runtime.service(self, "i18n"),
        ))
        fragment.add_css(RESOURCE_LOADER.load_unicode('public/css/google_calendar.css'))
        fragment.add_javascript(RESOURCE_LOADER.load_unicode('public/js/google_calendar.js'))

        fragment.initialize_js('GoogleCalendarBlock')

        return fragment

    # Context argument is specified for xblocks, but we are not using herein
    def studio_view(self, context):  # pylint: disable=unused-argument
        """
        Editing view in Studio
        """

        fragment = Fragment()
        # Need to access protected members of fields to get their default value
        default_name = self.fields['display_name']._default  # pylint: disable=protected-access,unsubscriptable-object
        fragment.add_content(RESOURCE_LOADER.render_django_template(
            CALENDAR_EDIT_TEMPLATE,
            context={
                'self': self,
                'defaultName': default_name,
                'defaultID': self.fields['calendar_id']._default  # pylint: disable=protected-access,unsubscriptable-object
            },
            i18n_service=self.runtime.service(self, "i18n"),
        ))
        fragment.add_javascript(RESOURCE_LOADER.load_unicode('public/js/google_calendar_edit.js'))
        fragment.add_css(RESOURCE_LOADER.load_unicode('public/css/google_edit.css'))

        fragment.initialize_js('GoogleCalendarEditBlock')

        return fragment

    # suffix argument is specified for xblocks, but we are not using herein
    @XBlock.json_handler
    def studio_submit(self, submissions, suffix=''):  # pylint: disable=unused-argument
        """
        Change the settings for this XBlock given by the Studio user
        """
        if not isinstance(submissions, dict):
            LOG.error("submissions object from Studio is not a dict - %r", submissions)
            return {
                'result': 'error'
            }

        if 'display_name' in submissions:
            self.display_name = submissions['display_name']
        if 'calendar_id' in submissions:
            self.calendar_id = submissions['calendar_id']
        if 'default_view' in submissions:
            self.default_view = submissions['default_view']

        return {
            'result': 'success',
        }

    @staticmethod
    def workbench_scenarios():
        """
        A canned scenario for display in the workbench.
        """
        return [("Google Calendar scenario", "<vertical_demo><google-calendar/></vertical_demo>")]

    def init_emulation(self):
        """
        Emulation of init function, for translation purpose.
        """
        if not self.skip_flag:
            _ = self.runtime.service(self, "i18n").ugettext
            for i, el in enumerate(self.views):
                el[1] = _(el[1])
            #     self.display_name = _(self.display_name)
            self.fields['display_name']._default = _(self.fields['display_name']._default)
            self.skip_flag = True