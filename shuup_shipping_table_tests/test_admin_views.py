# -*- coding: utf-8 -*-
# This file is part of Shuup Shipping Table
#
# Copyright (c) 2016, Rockho Team. All rights reserved.
# Author: Christian Hess
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.

import pytest

from django.http.response import Http404

from shuup.testing.factories import get_default_shop
from shuup.testing.utils import apply_request_middleware
from shuup.utils.importing import load


def test_region_views(rf, admin_user):
    get_default_shop()

    view = load("shuup_shipping_table.admin.views.region.RegionListView").as_view()
    request = apply_request_middleware(rf.get("/"), user=admin_user)
    response = view(request)
    assert response.status_code == 200

    view = load("shuup_shipping_table.admin.views.region.RegionEditView").as_view()
    request = apply_request_middleware(rf.get("/"), user=admin_user)
    response = view(request)
    assert response.status_code == 200
    
    view = load("shuup_shipping_table.admin.views.region.RegionDeleteView").as_view()
    request = apply_request_middleware(rf.post("/"), user=admin_user)
    with pytest.raises(Http404):
        response = view(request, pk=1)


    view = load("shuup_shipping_table.admin.views.region.RegionImportView").as_view()
    request = apply_request_middleware(rf.post("/"), user=admin_user)
    response = view(request)
    assert response.status_code == 302

    view = load("shuup_shipping_table.admin.views.region.RegionExportView").as_view()
    request = apply_request_middleware(rf.get("/"), user=admin_user)
    response = view(request)
    assert response.status_code == 200


def test_carrier_views(rf, admin_user):
    get_default_shop()

    view = load("shuup_shipping_table.admin.views.carrier.CarrierListView").as_view()
    request = apply_request_middleware(rf.get("/"), user=admin_user)
    response = view(request)
    assert response.status_code == 200

    view = load("shuup_shipping_table.admin.views.carrier.CarrierEditView").as_view()
    request = apply_request_middleware(rf.get("/"), user=admin_user)
    response = view(request)
    assert response.status_code == 200
    
    view = load("shuup_shipping_table.admin.views.carrier.CarrierDeleteView").as_view()
    request = apply_request_middleware(rf.post("/"), user=admin_user)
    with pytest.raises(Http404):
        response = view(request, pk=1)


def test_table_views(rf, admin_user):
    get_default_shop()

    view = load("shuup_shipping_table.admin.views.table.TableListView").as_view()
    request = apply_request_middleware(rf.get("/"), user=admin_user)
    response = view(request)
    assert response.status_code == 200

    view = load("shuup_shipping_table.admin.views.table.TableEditView").as_view()
    request = apply_request_middleware(rf.get("/"), user=admin_user)
    response = view(request)
    assert response.status_code == 200

    view = load("shuup_shipping_table.admin.views.table.TableDeleteView").as_view()
    request = apply_request_middleware(rf.post("/"), user=admin_user)
    with pytest.raises(Http404):
        response = view(request, pk=1)
