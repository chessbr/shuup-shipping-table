# -*- coding: utf-8 -*-
# This file is part of Shuup Shipping Table
#
# Copyright (c) 2016, Rockho Team. All rights reserved.
# Author: Christian Hess
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.

from shuup_shipping_table.forms import (
    ShippingTableCountryRegionForm, ShippingTablePostalCodeRegionForm
)


def test_forms():
    ShippingTablePostalCodeRegionForm()
    ShippingTableCountryRegionForm()
