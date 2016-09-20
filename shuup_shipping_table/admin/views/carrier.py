# -*- coding: utf-8 -*-
# This file is part of Shuup Shipping Table
#
# Copyright (c) 2016, Rockho Team. All rights reserved.
# Author: Christian Hess
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from shuup_shipping_table.models import ShippingCarrier

from django import forms
from django.core.urlresolvers import reverse_lazy
from django.utils.translation import ugettext_lazy as _
from django.views.generic.edit import DeleteView

from shuup.admin.utils.picotable import Column, TextFilter
from shuup.admin.utils.views import CreateOrUpdateView, PicotableListView


class CarrierListView(PicotableListView):
    model = ShippingCarrier
    default_columns = [
        Column("name", _("Name"), filter_config=TextFilter()),
        Column("enabled", _("Enabled")),
        Column("shops", _("Shops"))
    ]


class ShippingCarrierForm(forms.ModelForm):
    class Meta:
        model = ShippingCarrier
        exclude = ()


class CarrierEditView(CreateOrUpdateView):
    model = ShippingCarrier
    form_class = ShippingCarrierForm
    template_name = "shipping_table/admin/carrier_edit.jinja"
    context_object_name = "carrier"


class CarrierDeleteView(DeleteView):
    model = ShippingCarrier
    success_url = reverse_lazy("shuup_admin:shuup_shipping_table.carrier.list")
