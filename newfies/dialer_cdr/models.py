#
# Newfies-Dialer License
# http://www.newfies-dialer.org
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (C) 2011-2012 Star2Billing S.L.
#
# The Initial Developer of the Original Code is
# Arezqui Belaid <info@star2billing.com>
#

from django.db import models
from django.utils.translation import ugettext_lazy as _

from dialer_gateway.models import Gateway
from dialer_campaign.models import Campaign, CampaignSubscriber
from common.intermediate_model_base_class import Model
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from country_dialcode.models import Prefix
from uuid import uuid1
from datetime import datetime


CALLREQUEST_STATUS = (
    (1, u'PENDING'),
    (2, u'FAILURE'),
    (3, u'RETRY'),  # spawn for retry
    (4, u'SUCCESS'),
    (5, u'ABORT'),
    (6, u'PAUSE'),
    (7, u'PROCESS'),
    (8, u'IN-PROGRESS'),
)

CALLREQUEST_TYPE = (
    (1, _('ALLOW RETRY')),
    (2, _('CANNOT RETRY')),
    (3, _('RETRY DONE')),
)

LEG_TYPE = (
    (1, _('A-Leg')),
    (2, _('B-Leg')),
)

VOIPCALL_DISPOSITION = (
    ('ANSWER', u'ANSWER'),
    ('BUSY', u'BUSY'),
    ('NOANSWER', u'NOANSWER'),
    ('CANCEL', u'CANCEL'),
    ('CONGESTION', u'CONGESTION'),
    ('CHANUNAVAIL', u'CHANUNAVAIL'),
    ('DONTCALL', u'DONTCALL'),
    ('TORTURE', u'TORTURE'),
    ('INVALIDARGS', u'INVALIDARGS'),
    ('NOROUTE', u'NOROUTE'),
    ('FORBIDDEN', u'FORBIDDEN'),
)


class CallRequestManager(models.Manager):
    """CallRequest Manager"""

    def get_pending_callrequest(self):
        """Return all the pending callrequest based on call time and status"""
        kwargs = {}
        kwargs['status'] = 1
        tday = datetime.now()
        kwargs['call_time__lte'] = datetime(tday.year, tday.month,
            tday.day, tday.hour, tday.minute, tday.second, tday.microsecond)

        #return Callrequest.objects.all()
        return Callrequest.objects.filter(**kwargs)


def str_uuid1():
    return str(uuid1())


class Callrequest(Model):
    """This defines the call request, the dialer will read any new request
    and attempt to deliver the call.

    **Attributes**:

        * ``request_uuid`` - Unique id
        * ``call_time`` - Total call time
        * ``call_type`` - Call type
        * ``status`` - Call request status
        * ``callerid`` - Caller ID
        * ``last_attempt_time`` -
        * ``result`` --
        * ``timeout`` -
        * ``timelimit`` -
        * ``extra_dial_string`` -
        * ``phone_number`` -
        * ``parent_callrequest`` -
        * ``extra_data`` -
        * ``num_attempt`` -
        * ``hangup_cause`` -


    **Relationships**:

        * ``user`` - Foreign key relationship to the User model.\
        Each campaign assigned to a User

        * ``content_type`` - Defines the application \
        (``voip_app`` or ``survey``) \
        to use when the call is established on the A-Leg

        * ``object_id`` - Defines the object of content_type application

        * ``content_object`` - Used to define the VoIP App or the Survey with \
        generic ForeignKey

        * ``aleg_gateway`` - Foreign key relationship to the Gateway model.\
        Gateway to use to call the subscriber

        * ``campaign_subscriber`` - Foreign key relationship to\
        the CampaignSubscriber Model.

        * ``campaign`` - Foreign key relationship to the Campaign model.

    **Name of DB table**: dialer_callrequest
    """
    user = models.ForeignKey('auth.User')
    request_uuid = models.CharField(verbose_name=_("RequestUUID"),
                        default=str_uuid1(), db_index=True,
                        max_length=120, null=True, blank=True)
    aleg_uuid = models.CharField(max_length=120, help_text=_("A-Leg Call-ID"),
                        db_index=True, null=True, blank=True)
    call_time = models.DateTimeField(default=(lambda: datetime.now()))
    created_date = models.DateTimeField(auto_now_add=True, verbose_name='Date')
    updated_date = models.DateTimeField(auto_now=True)
    call_type = models.IntegerField(choices=CALLREQUEST_TYPE, default='1',
                verbose_name=_("Call Request Type"), blank=True, null=True)
    status = models.IntegerField(choices=CALLREQUEST_STATUS, default='1',
                blank=True, null=True, db_index=True,
                verbose_name=_('Status'))
    callerid = models.CharField(max_length=80, blank=True,
                verbose_name=_("CallerID"),
                help_text=_("CallerID used to call the A-Leg"))
    phone_number = models.CharField(max_length=80,
                verbose_name=_('Phone number'))
    timeout = models.IntegerField(blank=True, default=30,
                verbose_name=_('Time out'))
    timelimit = models.IntegerField(blank=True, default=3600,
                verbose_name=_('Time limit'))
    extra_dial_string = models.CharField(max_length=500, blank=True,
                verbose_name=_('Extra dial string'))

    campaign_subscriber = models.ForeignKey(CampaignSubscriber,
                null=True, blank=True,
                help_text=_("Campaign Subscriber related to this call request"))

    campaign = models.ForeignKey(Campaign, null=True, blank=True,
                help_text=_("Select Campaign"))
    aleg_gateway = models.ForeignKey(Gateway, null=True, blank=True,
                verbose_name="A-Leg Gateway",
                help_text=_("Select gateway to use to call the subscriber"))

    #used to define the Voice App or the Survey
    content_type = models.ForeignKey(ContentType, verbose_name=_("Type"))
    object_id = models.PositiveIntegerField(verbose_name=_("Application"))
    content_object = generic.GenericForeignKey('content_type', 'object_id')

    extra_data = models.CharField(max_length=120, blank=True,
                verbose_name=_("Extra Data"),
                help_text=_("Define the additional data to pass to the application"))

    num_attempt = models.IntegerField(default=0)
    last_attempt_time = models.DateTimeField(null=True, blank=True)
    result = models.CharField(max_length=180, blank=True)
    hangup_cause = models.CharField(max_length=80, blank=True)

    # if the call fails, create a new pending instance and link them
    parent_callrequest = models.ForeignKey('self', null=True, blank=True)

    objects = CallRequestManager()

    class Meta:
        db_table = u'dialer_callrequest'
        verbose_name = _("Call Request")
        verbose_name_plural = _("Call Requests")

    def __unicode__(self):
            return u"%s [%s]" % (self.id, self.request_uuid)


class VoIPCall(models.Model):
    """This gives information of all the calls made with
    the carrier charges and revenue of each call.

    **Attributes**:

        * ``callid`` - callid of the phonecall
        * ``callerid`` - CallerID used to call out
        * ``phone_number`` - Phone number contacted
        * ``dialcode`` - Dialcode of the phonenumber
        * ``starting_date`` - Starting date of the call
        * ``duration`` - Duration of the call
        * ``billsec`` -
        * ``progresssec`` -
        * ``answersec`` -
        * ``waitsec`` -
        * ``disposition`` - Disposition of the call
        * ``hangup_cause`` -
        * ``hangup_cause_q850`` -

    **Relationships**:

        * ``user`` - Foreign key relationship to the User model.
        * ``used_gateway`` - Foreign key relationship to the Gateway model.
        * ``callrequest`` - Foreign key relationship to the Callrequest model.

    **Name of DB table**: dialer_cdr
    """
    user = models.ForeignKey('auth.User', related_name='Call Sender')
    request_uuid = models.CharField(verbose_name=_("RequestUUID"),
                    default=str_uuid1(),
                    max_length=120, null=True, blank=True)
    used_gateway = models.ForeignKey(Gateway, null=True, blank=True,
                    verbose_name=_("Used gateway"))
    callrequest = models.ForeignKey(Callrequest, null=True, blank=True,
                    verbose_name=_("Callrequest"))
    callid = models.CharField(max_length=120, help_text=_("VoIP Call-ID"))
    callerid = models.CharField(max_length=120, verbose_name='CallerID')
    phone_number = models.CharField(max_length=120,  null=True, blank=True,
                    verbose_name=_("Phone number"),
                    help_text=_(u'The international number of the recipient, without the leading +'))

    dialcode = models.ForeignKey(Prefix, verbose_name=_("Destination"),
                    null=True, blank=True,
                    help_text=_("Select Prefix"))
    starting_date = models.DateTimeField(auto_now_add=True,
                    verbose_name=_("Starting date"),
                    db_index=True)
    duration = models.IntegerField(null=True, blank=True,
                    verbose_name=_("Duration"))
    billsec = models.IntegerField(null=True, blank=True,
                    verbose_name=_("Bill sec"))
    progresssec = models.IntegerField(null=True, blank=True,
                    verbose_name=_("Progress sec"))
    answersec = models.IntegerField(null=True, blank=True,
                    verbose_name=_("Answer sec"))
    waitsec = models.IntegerField(null=True, blank=True,
                    verbose_name=_("Wait sec"))
    disposition = models.CharField(choices=VOIPCALL_DISPOSITION,
                   max_length=40, null=True, blank=True,
                   verbose_name=_("Disposition"))
    hangup_cause = models.CharField(max_length=40, null=True, blank=True,
                    verbose_name=_("Hangup cause"))
    hangup_cause_q850 = models.CharField(max_length=10, null=True, blank=True)
    leg_type = models.SmallIntegerField(choices=LEG_TYPE, default=1,
                    verbose_name=_("Leg"),
                    null=True, blank=True)

    def destination_name(self):
        """Return Recipient dialcode"""
        if self.dialcode is None:
            return "0"
        else:
            return self.dialcode.name

    def min_duration(self):
        """Return duration in min & sec"""
        if self.duration:
            min = int(self.duration / 60)
            sec = int(self.duration % 60)
        else:
            min = 0
            sec = 0

        return "%02d" % min + ":" + "%02d" % sec

    class Meta:
        db_table = 'dialer_cdr'
        verbose_name = _("VoIP Call")
        verbose_name_plural = _("VoIP Call")

    def __unicode__(self):
            return u"%s" % self.callid
