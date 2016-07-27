# -*- coding: utf-8 -*-
# This file is part of Shuup Shipping Table
#
# Copyright (c) 2016, Rockho Team. All rights reserved.
# Author: Christian Hess
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from shuup_shipping_table.models import ShippingRegion

from django import forms
from django.contrib import messages
from django.core import serializers
from django.core.urlresolvers import reverse, reverse_lazy
from django.http import StreamingHttpResponse
from django.http.response import HttpResponseRedirect
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ungettext_lazy as _p
from django.views.generic.base import View
from django.views.generic.edit import DeleteView

from shuup.admin.forms._base import ShuupAdminForm
from shuup.admin.modules.service_providers.views._edit import _FormInfoMap
from shuup.admin.toolbar import JavaScriptActionButton
from shuup.admin.utils.picotable import Column, TextFilter
from shuup.admin.utils.views import CreateOrUpdateView, PicotableListView
from shuup.apps.provides import get_provide_objects


class RegionListView(PicotableListView):
    model = ShippingRegion
    template_name = "shipping_table/admin/region_list.jinja"
    columns = [
        Column("name", _("Name"), filter_config=TextFilter()),
        Column("type", _(u"Type"), display="get_type_display", sortable=False),
    ]

    def get_type_display(self, instance):
        return instance._meta.verbose_name.capitalize()

    def get_toolbar(self):
        toolbar = super(RegionListView, self).get_toolbar()

        toolbar.append(JavaScriptActionButton(text=_("Import from JSON"),
                                              icon="fa fa-cloud-upload",
                                              onclick="importFromJSON()",
                                              extra_css_class="btn-info"))

        toolbar.append(JavaScriptActionButton(text=_("Download as JSON"),
                                              icon="fa fa-cloud-download",
                                              onclick="downloadAsJSON()",
                                              extra_css_class="btn-info"))

        return toolbar


class ShippingRegionForm(ShuupAdminForm):
    class Meta:
        model = ShippingRegion
        exclude = ()


class RegionDeleteView(DeleteView):
    model = ShippingRegion
    success_url = reverse_lazy("shuup_admin:shuup_shipping_table.region.list")


class RegionEditView(CreateOrUpdateView):
    model = ShippingRegion
    form_class = ShippingRegionForm
    template_name = "shipping_table/admin/region_edit.jinja"
    context_object_name = "region"
    form_provide_key = "shipping_table_region_form"

    def get_form(self, form_class=None):
        form_classes = list(get_provide_objects(self.form_provide_key))
        form_infos = _FormInfoMap(form_classes)
        if self.object and self.object.pk:
            return self._get_concrete_form(form_infos)
        else:
            return self._get_type_choice_form(form_infos)

    def _get_concrete_form(self, form_infos):
        form_info = form_infos.get_by_object(self.object)
        self.form_class = form_info.form_class
        return self. _get_form(form_infos, form_info, type_enabled=False)

    def _get_type_choice_form(self, form_infos):
        selected_type = self.request.GET.get("type")
        form_info = form_infos.get_by_choice_value(selected_type)
        if not form_info:
            form_info = list(form_infos.values())[0]
        self.form_class = form_info.form_class
        self.object = form_info.model()
        return self. _get_form(form_infos, form_info, type_enabled=True)

    def _get_form(self, form_infos, selected, type_enabled):
        form = self.form_class(**self.get_form_kwargs())
        type_field = forms.ChoiceField(
            choices=form_infos.get_type_choices(),
            label=_("Type"),
            required=type_enabled,
            initial=selected.choice_value,
        )
        if not type_enabled:
            type_field.widget.attrs['disabled'] = True
        form.fields["type"] = type_field
        return form

    def get_success_url(self):
        return reverse("shuup_admin:shuup_shipping_table.region.list")


class RegionImportView(View):

    def post(self, request, **kwargs):

        if request.FILES.get('json_file'):

            obj_count = 0
            for deserialized_object in serializers.deserialize("json", request.FILES['json_file']):
                deserialized_object.save()
                obj_count = obj_count + 1

            messages.info(request, _p("Imported {0} regions", "Imported {0} regions", obj_count).format(obj_count))
        else:
            messages.error(request, _("Missing JSON file"))

        return HttpResponseRedirect(reverse("shuup_admin:shuup_shipping_table.region.list"))


class RegionExportView(View):

    def get(self, request, **kwargs):
        # FIXME: this is serializing objects without translated fields
        from shuup_shipping_table.models import ShippingRegionTranslation
        data = serializers.serialize(
            'json', list(ShippingRegion.objects.all()) + list(ShippingRegionTranslation.objects.all())
        )
        response = StreamingHttpResponse(data, content_type="text/json")
        response['Content-Disposition'] = 'attachment; filename="shipping_regions.json"'
        return response
