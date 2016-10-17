# -*- coding: utf-8 -*-
# This file is part of Shuup Shipping Table
#
# Copyright (c) 2016, Rockho Team. All rights reserved.
# Author: Christian Hess
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.

from shuup_shipping_table.models import (
    ShippingTable, ShippingTableByModeBehaviorComponent, ShippingTableItem,
    SpecificShippingTableBehaviorComponent
)

from django import forms
from django.forms.models import BaseModelFormSet
from django.utils.translation import ugettext_lazy as _

from shuup.admin.form_part import FormPart, TemplatedFormDef


class ShippingTableByModeBehaviorComponentForm(forms.ModelForm):
    class Meta:
        model = ShippingTableByModeBehaviorComponent
        exclude = ["identifier"]


class SpecificShippingTableBehaviorComponentForm(forms.ModelForm):
    class Meta:
        model = SpecificShippingTableBehaviorComponent
        exclude = ["identifier"]


class ShippingTableForm(forms.ModelForm):
    class Meta:
        model = ShippingTable
        exclude = ()


class ShippingTableItemForm(forms.ModelForm):
    class Meta:
        model = ShippingTableItem
        exclude = ()

    def __init__(self, **kwargs):
        self.table = kwargs.pop("table")
        super(ShippingTableItemForm, self).__init__(**kwargs)
        self.fields["table"].required = False

    def save(self, commit=True):
        self.instance.table = self.table
        super(ShippingTableItemForm, self).save(commit)


class ShippingtableItemFormSet(BaseModelFormSet):
    validate_min = False
    min_num = 0
    validate_max = False
    max_num = 1000
    absolute_max = 1000
    model = ShippingTableItem
    can_delete = True
    can_order = False
    extra = 30
    form_class = ShippingTableItemForm

    def __init__(self, *args, **kwargs):
        self.table = kwargs.pop("table")
        kwargs.pop("empty_permitted")  # this is unknown to formset
        super(ShippingtableItemFormSet, self).__init__(*args, **kwargs)

    def get_queryset(self):
        return ShippingTableItem.objects.filter(table=self.table).order_by('region', 'start_weight')

    def form(self, **kwargs):
        kwargs.setdefault("table", self.table)
        return self.form_class(**kwargs)


class ShippingTableFormPart(FormPart):
    priority = -1000  # Show this first, no matter what

    def get_form_defs(self):
        yield TemplatedFormDef(
            "base",
            ShippingTableForm,
            template_name="shipping_table/admin/_edit_table_form.jinja",
            required=True,
            kwargs={
                "instance": self.object
            }
        )

    def form_valid(self, form):
        self.object = form["base"].save()
        return self.object


class ShippingTableItemFormPart(FormPart):
    priority = -900

    def get_form_defs(self):
        yield TemplatedFormDef(
            "items",
            ShippingtableItemFormSet,
            template_name="shipping_table/admin/_edit_table_item_form.jinja",
            required=False,
            kwargs={'table': self.object}
        )

    def form_valid(self, form):
        if "items" in form.forms:
            form.forms["items"].save()
