# -*- coding: utf-8 -*-
# This file is part of Shuup Shipping Table
#
# Copyright (c) 2016, Rockho Team. All rights reserved.
# Author: Christian Hess
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.

from shuup.apps import AppConfig


class ShuupShippingTableAppConfig(AppConfig):
    name = __name__
    verbose_name = "Shuup Shipping Table"
    label = "shuup_shipping_table"
    provides = {
        "admin_module": [
            "shuup_shipping_table.admin:ShippingTableModule",
            "shuup_shipping_table.admin:ShippingCarrierModule",
            "shuup_shipping_table.admin:ShippingRegionModule",
        ],
        "shipping_table_region_form": [
            "shuup_shipping_table.forms:ShippingTablePostalCodeRegionForm",
            "shuup_shipping_table.forms:ShippingTableCountryRegionForm",
        ],
        "service_behavior_component_form": [
            "shuup_shipping_table.admin.forms:ShippingTableByModeBehaviorComponentForm",
            "shuup_shipping_table.admin.forms:SpecificShippingTableBehaviorComponentForm",
        ]
    }

default_app_config = __name__ + ".ShuupShippingTableAppConfig"

__version__ = "1.0.0"
