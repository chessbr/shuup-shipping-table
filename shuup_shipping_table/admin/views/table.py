# -*- coding: utf-8 -*-
# This file is part of Shuup Shipping Table
#
# Copyright (c) 2016, Rockho Team. All rights reserved.
# Author: Christian Hess
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from shuup_shipping_table.admin.forms import ShippingTableFormPart, ShippingTableItemFormPart
from shuup_shipping_table.models import ShippingCarrier, ShippingTable

from django.core.urlresolvers import reverse_lazy
from django.db.transaction import atomic
from django.utils.translation import ugettext_lazy as _
from django.views.generic.edit import DeleteView

from shuup.admin.form_part import FormPartsViewMixin, SaveFormPartsMixin
from shuup.admin.toolbar import JavaScriptActionButton
from shuup.admin.utils.picotable import ChoicesFilter, Column, TextFilter
from shuup.admin.utils.views import CreateOrUpdateView, PicotableListView
from shuup.utils.i18n import get_locally_formatted_datetime


class TableListView(PicotableListView):
    model = ShippingTable
    default_columns = [
        Column("name", _("Name"), filter_config=TextFilter()),
        Column("identifier", _("Identifier"), filter_config=TextFilter()),
        Column("enabled", _("Enabled")),
        Column("start_date", _("Start Date"), display="format_start_date"),
        Column("end_date", _("End Date"), display="format_end_date"),
        Column("carrier", _("Carrier"), filter_config=ChoicesFilter(choices=ShippingCarrier.objects.all()))
    ]

    def format_start_date(self, instance, *args, **kwargs):
        if instance.start_date:
            return get_locally_formatted_datetime(instance.start_date)

    def format_end_date(self, instance, *args, **kwargs):
        if instance.end_date:
            return get_locally_formatted_datetime(instance.end_date)


class TableEditView(SaveFormPartsMixin, FormPartsViewMixin, CreateOrUpdateView):
    model = ShippingTable
    template_name = "shipping_table/admin/table_edit.jinja"
    context_object_name = "table"
    save_form_id = "shipping_table_form"
    base_form_part_classes = [
        ShippingTableFormPart,
        ShippingTableItemFormPart
    ]

    @atomic
    def form_valid(self, form):
        return self.save_form_parts(form)

    def get_toolbar(self):
        toolbar = super(TableEditView, self).get_toolbar()

        if self.object.pk:
            save_as_copy_button = JavaScriptActionButton(
                onclick="saveAsACopy()",
                text=_("Save as a copy"),
                icon="fa fa-clone",
            )
            toolbar.append(save_as_copy_button)

        return toolbar


class TableDeleteView(DeleteView):
    model = ShippingTable
    success_url = reverse_lazy("shuup_admin:shuup_shipping_table.table.list")
