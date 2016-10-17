# -*- coding: utf-8 -*-
# This file is part of Shuup Shipping Table
#
# Copyright (c) 2016, Rockho Team. All rights reserved.
# Author: Christian Hess
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from shuup_shipping_table.models import ShippingCarrier, ShippingRegion, ShippingTable

from django.utils.translation import ugettext_lazy as _

from shuup.admin.base import AdminModule, MenuEntry
from shuup.admin.utils.permissions import get_default_model_permissions
from shuup.admin.utils.urls import admin_url, derive_model_url, get_edit_and_list_urls


class ShippingTableAdminModule(AdminModule):
    category = _("ShippingTable")
    model = None
    name = _("Shipping Table")
    url_prefix = None
    view_template = None
    name_template = None
    menu_entry_url = None
    url_name_prefix = None
    icon = None

    def get_urls(self):
        permissions = self.get_required_permissions()
        return [
            admin_url(
                "%s/(?P<pk>\d+)/delete/$" % self.url_prefix,
                self.view_template % "Delete",
                name=self.name_template % "delete",
                permissions=permissions
            )
        ] + get_edit_and_list_urls(
            url_prefix=self.url_prefix,
            view_template=self.view_template,
            name_template=self.name_template,
            permissions=permissions
        )

    def get_menu_entries(self, request):
        return [
            MenuEntry(
                text=self.name,
                url=self.menu_entry_url,
                icon=self.icon,
                category=self.category
            )
        ]

    def get_required_permissions(self):
        return get_default_model_permissions(self.model)

    def get_model_url(self, obj, kind):
        return derive_model_url(self.model, self.url_name_prefix, obj, kind)

    def get_menu_category_icons(self):
        return {self.category: "fa fa-table", self.name: self.icon}


class ShippingTableModule(ShippingTableAdminModule):
    name = _("Shipping tables")
    model = ShippingTable

    icon = "fa fa-table"
    breadcrumbs_menu_entry = MenuEntry(name, url="shuup_admin:shipping_table.list")
    url_name_prefix = "shuup_admin:shipping_table"
    url_prefix = "^shipping_table/table"
    view_template = "shuup_shipping_table.admin.views.table.Table%sView"
    name_template = "shipping_table.%s"
    menu_entry_url = "shuup_admin:shipping_table.list"


class ShippingCarrierModule(ShippingTableAdminModule):
    name = _("Carriers")
    model = ShippingCarrier

    icon = "fa fa-truck"
    breadcrumbs_menu_entry = MenuEntry(name, url="shuup_admin:shipping_carrier.list")
    url_name_prefix = "shuup_admin:shipping_carrier"
    url_prefix = "^shipping_table/carrier"
    view_template = "shuup_shipping_table.admin.views.carrier.Carrier%sView"
    name_template = "shipping_carrier.%s"
    menu_entry_url = "shuup_admin:shipping_carrier.list"


class ShippingRegionModule(ShippingTableAdminModule):
    name = _("Regions")
    model = ShippingRegion

    icon = "fa fa-map-marker"
    breadcrumbs_menu_entry = MenuEntry(name, url="shuup_admin:shipping_region.list")
    url_name_prefix = "shuup_admin:shipping_region"
    url_prefix = "^shipping_table/region"
    view_template = "shuup_shipping_table.admin.views.region.Region%sView"
    name_template = "shipping_region.%s"
    menu_entry_url = "shuup_admin:shipping_region.list"

    def get_urls(self):
        urls = super(ShippingRegionModule, self).get_urls()
        urls = urls + [
            admin_url(
                "%s/import/$" % self.url_prefix,
                self.view_template % "Import",
                name=self.name_template % "import",
                permissions=self.get_required_permissions()
            ),
            admin_url(
                "%s/export/$" % self.url_prefix,
                self.view_template % "Export",
                name=self.name_template % "export",
                permissions=self.get_required_permissions()
            )
        ]
        return urls
