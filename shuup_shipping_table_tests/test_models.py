# -*- coding: utf-8 -*-
# This file is part of Shuup Shipping Table
#
# Copyright (c) 2016, Rockho Team. All rights reserved.
# Author: Christian Hess
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.

from __future__ import unicode_literals

from datetime import timedelta
from decimal import Decimal

import pytest
from shuup_shipping_table.models import (
    AddressShippingRegion, CountryShippingRegion, FetchTableMode, PostalCodeRangeShippingRegion,
    ShippingCarrier, ShippingTable, ShippingTableByModeBehaviorComponent, ShippingTableItem,
    SpecificShippingTableBehaviorComponent, KG_TO_G
)
from shuup_tests.front.test_checkout_flow import fill_address_inputs
from shuup_tests.utils import SmartClient
from shuup_tests.utils.basketish_order_source import BasketishOrderSource

from shuup.core.defaults.order_statuses import create_default_order_statuses
from shuup.core.models._contacts import get_person_contact
from shuup.core.models._order_lines import OrderLineType
from shuup.core.models._orders import Order, PaymentStatus
from shuup.core.models._product_shops import ShopProduct
from shuup.core.models._service_shipping import CustomCarrier
from shuup.testing.factories import (
    get_address, get_default_product, get_default_shop, get_default_supplier, get_default_tax_class,
    get_payment_method
)
from shuup.testing.mock_population import populate_if_required
from shuup.testing.soup_utils import extract_form_fields
from shuup.xtheme._theme import set_current_theme

from django.core.urlresolvers import reverse
from django.utils.timezone import now


def get_custom_carrier_service():
    carrier = CustomCarrier.objects.create(name="Carrier Service")

    service = carrier.create_service(
        'shipping-table',
        shop=get_default_shop(),
        enabled=True,
        tax_class=get_default_tax_class(),
        name="SHIPPING TABLE"
    )

    return service


def create_test_data():
    # Carriers
    carrier1 = ShippingCarrier.objects.create(name="Carrier 1", enabled=True)
    carrier1.shops.add(get_default_shop())

    carrier2 = ShippingCarrier.objects.create(name="Carrier 2", enabled=True)
    carrier2.shops.add(get_default_shop())


    # Regions
    region1 = PostalCodeRangeShippingRegion.objects.create(name="Region PCR 1",
                                                           priority=1,
                                                           start_postal_code=89060000,
                                                           end_postal_code=89070000,
                                                           country="BR")
    region2 = PostalCodeRangeShippingRegion.objects.create(name="Region PCR 2",
                                                           priority=1,
                                                           start_postal_code=89040000,
                                                           end_postal_code=89050000,
                                                           country="BR")
    region3 = PostalCodeRangeShippingRegion.objects.create(name="Region PCR 3",
                                                           priority=1,
                                                           start_postal_code=89060001,
                                                           end_postal_code=89060005,
                                                           country="BR")

    region4 = CountryShippingRegion.objects.create(name="Region Country CA",
                                                   priority=1,
                                                   country='CAN')
    region5 = CountryShippingRegion.objects.create(name="Region Country US",
                                                   priority=1,
                                                   country='US')
    region_br = CountryShippingRegion.objects.create(name="Region Country BR",
                                                     priority=1,
                                                     country='BR')

    excluded_postal_code = PostalCodeRangeShippingRegion.objects.create(name="Prohibited Postal Code",
                                                                        priority=99,
                                                                        start_postal_code=89060100,
                                                                        end_postal_code=89060100,
                                                                        country="BR")

    region6 = PostalCodeRangeShippingRegion.objects.create(name="Region PCR 6",
                                                           priority=1,
                                                           start_postal_code=99090001,
                                                           end_postal_code=99090002,
                                                           country="BR")
    region7 = PostalCodeRangeShippingRegion.objects.create(name="Region PCR 7",
                                                           priority=99,
                                                           start_postal_code=99090001,
                                                           end_postal_code=99090002,
                                                           country="BR")

    # Tables
    table1 = ShippingTable.objects.create(identifier="table-1",
                                          name="Table 1",
                                          carrier=carrier1,
                                          start_date=now()-timedelta(days=1),
                                          end_date=now()+timedelta(days=1))
    table1.shops.add(get_default_shop())
    table1.excluded_regions.add(region3)
    table1.excluded_regions.add(excluded_postal_code)

    ShippingTableItem.objects.create(table=table1,
                                     region=region1,
                                     start_weight=0,
                                     end_weight=1,
                                     price=1,
                                     delivery_time=8)
    ShippingTableItem.objects.create(table=table1,
                                     region=region1,
                                     start_weight=1.01,
                                     end_weight=5,
                                     price=2,
                                     delivery_time=8)
    ShippingTableItem.objects.create(table=table1,
                                     region=region2,
                                     start_weight=0,
                                     end_weight=10,
                                     price=20,
                                     delivery_time=74)
    ShippingTableItem.objects.create(table=table1,
                                     region=region2,
                                     start_weight=10,
                                     end_weight=200,
                                     price=100,
                                     delivery_time=85)
    ShippingTableItem.objects.create(table=table1,
                                     region=region6,
                                     start_weight=0,
                                     end_weight=100,
                                     price=1,
                                     delivery_time=1)
    ShippingTableItem.objects.create(table=table1,
                                     region=region7,
                                     start_weight=0,
                                     end_weight=100,
                                     price=999,
                                     delivery_time=999)


    table2 = ShippingTable.objects.create(identifier="table-2",
                                          name="Table 2",
                                          carrier=carrier2,
                                          start_date=now()-timedelta(days=1),
                                          end_date=now()+timedelta(days=1))
    table2.shops.add(get_default_shop())
    table2.excluded_regions.add(excluded_postal_code)

    ShippingTableItem.objects.create(table=table2,
                                     region=region1,
                                     start_weight=0,
                                     end_weight=1,
                                     price=9,
                                     delivery_time=2)
    ShippingTableItem.objects.create(table=table2,
                                     region=region1,
                                     start_weight=1.0,
                                     end_weight=5,
                                     price=14,
                                     delivery_time=2)
    ShippingTableItem.objects.create(table=table2,
                                     region=region2,
                                     start_weight=0,
                                     end_weight=10,
                                     price=50,
                                     delivery_time=23)
    ShippingTableItem.objects.create(table=table2,
                                     region=region2,
                                     start_weight=10,
                                     end_weight=20,
                                     price=530,
                                     delivery_time=26)


    table3 = ShippingTable.objects.create(identifier="table-3",
                                          name="Table 3",
                                          carrier=carrier1,
                                          start_date=now()-timedelta(days=1),
                                          end_date=now()+timedelta(days=1))
    table3.shops.add(get_default_shop())

    ShippingTableItem.objects.create(table=table3,
                                     region=region4,
                                     start_weight=0,
                                     end_weight=10,
                                     price=9,
                                     delivery_time=2)
    ShippingTableItem.objects.create(table=table3,
                                     region=region4,
                                     start_weight=10,
                                     end_weight=20,
                                     price=14,
                                     delivery_time=2)
    ShippingTableItem.objects.create(table=table3,
                                     region=region5,
                                     start_weight=0,
                                     end_weight=10,
                                     price=9,
                                     delivery_time=2)
    ShippingTableItem.objects.create(table=table3,
                                     region=region5,
                                     start_weight=20,
                                     end_weight=50,
                                     price=14,
                                     delivery_time=2)


    # catch all BRA shipping items - no matter what
    table4 = ShippingTable.objects.create(identifier="table-4",
                                          name="Table 4 - A expired table",
                                          carrier=carrier2,
                                          start_date=now()-timedelta(days=20),
                                          end_date=now()-timedelta(days=19))
    table4.shops.add(get_default_shop())
    ShippingTableItem.objects.create(table=table4,
                                     region=region_br,
                                     start_weight=0,
                                     end_weight=1000,
                                     price=0.01,
                                     delivery_time=1)

    # catch all BRA shipping items - no matter what
    table5 = ShippingTable.objects.create(identifier="table-5",
                                          name="Table 5 - A disabled table",
                                          carrier=carrier2,
                                          start_date=now()-timedelta(days=20),
                                          end_date=now()+timedelta(days=19),
                                          enabled=False)
    table5.shops.add(get_default_shop())
    ShippingTableItem.objects.create(table=table5,
                                     region=region_br,
                                     start_weight=0,
                                     end_weight=1000,
                                     price=0.01,
                                     delivery_time=1)

    # catch all BRA shipping items - no matter what
    table6 = ShippingTable.objects.create(identifier="table-6",
                                          name="Table 5 - A table without shop",
                                          carrier=carrier1,
                                          start_date=now()-timedelta(days=20),
                                          end_date=now()+timedelta(days=19))
    ShippingTableItem.objects.create(table=table6,
                                     region=region_br,
                                     start_weight=0,
                                     end_weight=1000,
                                     price=0.01,
                                     delivery_time=1)

def get_source(admin_user, service):
    contact = get_person_contact(admin_user)
    source = BasketishOrderSource(get_default_shop())

    billing_address = get_address()
    shipping_address = get_address(name="My House", country='BR')

    source.billing_address = billing_address
    source.shipping_address = shipping_address
    source.customer = contact

    source.shipping_method = service.carrier
    source.payment_method = get_payment_method(name="neat", price=4)

    return source


@pytest.mark.django_db
def test_lowest_price_table1_behavior(admin_user):
    create_test_data()

    service = get_custom_carrier_service()
    component = ShippingTableByModeBehaviorComponent.objects.create(
        mode=FetchTableMode.LOWEST_PRICE
    )
    service.behavior_components.add(component)
    source = get_source(admin_user, service)

    source.add_line(
        type=OrderLineType.PRODUCT,
        product=get_default_product(),
        supplier=get_default_supplier(),
        quantity=1,
        base_unit_price=source.create_price(10),
        weight=Decimal("0.2")
    )

    # By postal code range
    source.shipping_address.postal_code = "89060201"

    table_item = component.get_first_available_item(source)
    assert table_item.price == Decimal(1)
    assert table_item.delivery_time == 8
    costs = list(component.get_costs(service, source))
    assert len(costs) == 1
    assert costs[0].price.value == table_item.price
    delivery_time = component.get_delivery_time(service, source)
    assert delivery_time.min_duration.days == table_item.delivery_time


    # only the carrier2 can be used
    component.carriers.add(ShippingCarrier.objects.get(name="Carrier 2"))

    table_item = component.get_first_available_item(source)
    assert table_item.price == Decimal(9)
    assert table_item.delivery_time == 2
    costs = list(component.get_costs(service, source))
    assert len(costs) == 1
    assert costs[0].price.value == table_item.price
    delivery_time = component.get_delivery_time(service, source)
    assert delivery_time.min_duration.days == table_item.delivery_time
    # clear carriers filter
    component.carriers.all().delete()


    # test priority
    source.shipping_address.postal_code = "99090001"

    table_item = component.get_first_available_item(source)
    assert table_item.price == Decimal(999)
    assert table_item.delivery_time == 999
    costs = list(component.get_costs(service, source))
    assert len(costs) == 1
    assert costs[0].price.value == table_item.price
    delivery_time = component.get_delivery_time(service, source)
    assert delivery_time.min_duration.days == table_item.delivery_time

    # configure additioal price
    component.add_price = Decimal(23.4)
    component.add_delivery_time_days = 9
    component.save()

    table_item = component.get_first_available_item(source)
    assert table_item.price == Decimal(999)
    assert table_item.delivery_time == 999
    costs = list(component.get_costs(service, source))
    assert len(costs) == 1
    assert costs[0].price.value == table_item.price + component.add_price
    delivery_time = component.get_delivery_time(service, source)
    assert delivery_time.min_duration.days == table_item.delivery_time + component.add_delivery_time_days


@pytest.mark.django_db
def test_lowest_time_table1_behavior(admin_user):
    create_test_data()

    service = get_custom_carrier_service()
    component = ShippingTableByModeBehaviorComponent.objects.create(
        mode=FetchTableMode.LOWEST_DELIVERY_TIME
    )
    service.behavior_components.add(component)
    source = get_source(admin_user, service)

    source.add_line(
        type=OrderLineType.PRODUCT,
        product=get_default_product(),
        supplier=get_default_supplier(),
        quantity=1,
        base_unit_price=source.create_price(10),
        weight=Decimal("0.2")
    )

    # by postal code range
    source.shipping_address.postal_code = "89060201"

    table_item = component.get_first_available_item(source)
    assert table_item.price == Decimal(9)
    assert table_item.delivery_time == 2
    costs = list(component.get_costs(service, source))
    assert len(costs) == 1
    assert costs[0].price.value == table_item.price
    delivery_time = component.get_delivery_time(service, source)
    assert delivery_time.min_duration.days == table_item.delivery_time


    # now only the table1 must be used to calculate prices/time
    component.tables.add(ShippingTable.objects.get(identifier='table-1'))


    table_item = component.get_first_available_item(source)
    assert table_item.price == Decimal(1)
    assert table_item.delivery_time == 8
    costs = list(component.get_costs(service, source))
    assert len(costs) == 1
    assert costs[0].price.value == table_item.price
    delivery_time = component.get_delivery_time(service, source)
    assert delivery_time.min_duration.days == table_item.delivery_time


@pytest.mark.django_db
def test_no_table_region_not_found_behavior(admin_user):
    create_test_data()

    service = get_custom_carrier_service()
    component = ShippingTableByModeBehaviorComponent.objects.create(
        mode=FetchTableMode.LOWEST_DELIVERY_TIME
    )
    service.behavior_components.add(component)
    source = get_source(admin_user, service)

    source.add_line(
        type=OrderLineType.PRODUCT,
        product=get_default_product(),
        supplier=get_default_supplier(),
        quantity=1,
        base_unit_price=source.create_price(10),
        weight=Decimal("0.2")
    )

    # by postal code range
    source.shipping_address.postal_code = "89090001"
    source.shipping_address.country = "AR"

    table_item = component.get_first_available_item(source)
    assert table_item is None
    errors = list(component.get_unavailability_reasons(service, source))
    assert len(errors) == 1

    # excluded postal code
    source.shipping_address.postal_code = "89060100"
    source.shipping_address.country = "BR"

    table_item = component.get_first_available_item(source)
    assert table_item is None
    errors = list(component.get_unavailability_reasons(service, source))
    assert len(errors) == 1


@pytest.mark.django_db
def test_lowest_time_table3_behavior(admin_user):
    create_test_data()

    service = get_custom_carrier_service()
    component = ShippingTableByModeBehaviorComponent.objects.create(
        mode=FetchTableMode.LOWEST_DELIVERY_TIME
    )
    service.behavior_components.add(component)
    source = get_source(admin_user, service)

    source.add_line(
        type=OrderLineType.PRODUCT,
        product=get_default_product(),
        supplier=get_default_supplier(),
        quantity=1,
        base_unit_price=source.create_price(10),
        weight=Decimal("0.2")
    )

    # No postal code, just country
    source.shipping_address.postal_code = ""
    source.shipping_address.country = "US"

    table_item = component.get_first_available_item(source)
    assert table_item.price == Decimal(9)
    assert table_item.delivery_time == 2

    errors = list(component.get_unavailability_reasons(service, source))
    assert len(errors) == 0

    costs = list(component.get_costs(service, source))
    assert len(costs) == 1
    assert costs[0].price.value == table_item.price

    delivery_time = component.get_delivery_time(service, source)
    assert delivery_time.min_duration.days == table_item.delivery_time


@pytest.mark.django_db
def test_specific_table1_behavior(admin_user):
    create_test_data()

    service = get_custom_carrier_service()
    component = SpecificShippingTableBehaviorComponent.objects.create(
        table=ShippingTable.objects.get(identifier='table-1')
    )
    service.behavior_components.add(component)
    source = get_source(admin_user, service)

    source.add_line(
        type=OrderLineType.PRODUCT,
        product=get_default_product(),
        supplier=get_default_supplier(),
        quantity=1,
        base_unit_price=source.create_price(10),
        weight=Decimal("0.2")
    )

    # By postal code range
    source.shipping_address.postal_code = "89060201"

    table_item = component.get_first_available_item(source)
    assert table_item.price == Decimal(1)
    assert table_item.delivery_time == 8
    costs = list(component.get_costs(service, source))
    assert len(costs) == 1
    assert costs[0].price.value == table_item.price

    delivery_time = component.get_delivery_time(service, source)
    assert delivery_time.min_duration.days == table_item.delivery_time


    # test priority
    source.shipping_address.postal_code = "99090001"
    table_item = component.get_first_available_item(source)
    assert table_item.price == Decimal(999)
    assert table_item.delivery_time == 999
    costs = list(component.get_costs(service, source))
    assert len(costs) == 1
    assert costs[0].price.value == table_item.price

    delivery_time = component.get_delivery_time(service, source)
    assert delivery_time.min_duration.days == table_item.delivery_time


@pytest.mark.django_db
def test_checkout(admin_user):
    get_default_shop()
    set_current_theme('shuup.themes.classic_gray')
    create_default_order_statuses()
    populate_if_required()
    create_test_data()

    default_product = get_default_product()
    sp = ShopProduct.objects.get(product=default_product, shop=get_default_shop())
    sp.default_price = get_default_shop().create_price(Decimal(10.0))
    sp.save()

    service = get_custom_carrier_service()
    component = SpecificShippingTableBehaviorComponent.objects.create(
        table=ShippingTable.objects.get(identifier='table-1')
    )
    service.behavior_components.add(component)

    c = SmartClient()

    basket_path = reverse("shuup:basket")
    add_to_basket_resp = c.post(basket_path, data={
        "command": "add",
        "product_id": default_product.pk,
        "quantity": 1,
        "supplier": get_default_supplier().pk
    })
    assert add_to_basket_resp.status_code < 400

    shipping_method = service
    payment_method = get_payment_method(name="neat", price=4)

    # Resolve paths
    addresses_path = reverse("shuup:checkout", kwargs={"phase": "addresses"})
    methods_path = reverse("shuup:checkout", kwargs={"phase": "methods"})
    confirm_path = reverse("shuup:checkout", kwargs={"phase": "confirm"})

    # Phase: Addresses
    addresses_soup = c.soup(addresses_path)
    inputs = fill_address_inputs(addresses_soup, with_company=False)

    inputs['shipping-postal_code'] = "89060201"
    inputs['shipping-country'] = "BR"

    response = c.post(addresses_path, data=inputs)

    assert response.status_code == 302, "Address phase should redirect forth"
    assert response.url.endswith(methods_path)

    # Phase: Methods
    assert Order.objects.filter(payment_method=payment_method).count() == 0
    response = c.post(
        methods_path,
        data={
            "payment_method": payment_method.pk,
            "shipping_method": shipping_method.pk
        }
    )

    assert response.status_code == 302, "Methods phase should redirect forth"
    assert response.url.endswith(confirm_path)
    response = c.get(confirm_path)
    assert response.status_code == 200

    # Phase: Confirm
    assert Order.objects.count() == 0
    confirm_soup = c.soup(confirm_path)
    response = c.post(confirm_path, data=extract_form_fields(confirm_soup))
    assert response.status_code == 302, "Confirm should redirect forth"

    assert Order.objects.count() == 1
    order = Order.objects.filter(payment_method=payment_method).first()
    assert order.payment_status == PaymentStatus.NOT_PAID


@pytest.mark.django_db
def test_postal_code_range_region(admin_user):
    service = get_custom_carrier_service()
    component = ShippingTableByModeBehaviorComponent.objects.create(
        mode=FetchTableMode.LOWEST_DELIVERY_TIME
    )
    service.behavior_components.add(component)
    source = get_source(admin_user, service)

    source.add_line(
        type=OrderLineType.PRODUCT,
        product=get_default_product(),
        supplier=get_default_supplier(),
        quantity=1,
        base_unit_price=source.create_price(10),
        weight=Decimal("0.2")
    )

    region = PostalCodeRangeShippingRegion(start_postal_code=998000,
                                           end_postal_code=998999,
                                           country="BR")
    source.shipping_address.country = "BR"
    source.shipping_address.postal_code = "823131"
    assert region.is_compatible_with(source) is False
    source.shipping_address.postal_code = "998001"
    assert region.is_compatible_with(source)
    source.shipping_address.country = "US"
    assert region.is_compatible_with(source) is False


@pytest.mark.django_db
def test_country_region(admin_user):
    service = get_custom_carrier_service()
    component = ShippingTableByModeBehaviorComponent.objects.create(
        mode=FetchTableMode.LOWEST_DELIVERY_TIME
    )
    service.behavior_components.add(component)
    source = get_source(admin_user, service)

    source.add_line(
        type=OrderLineType.PRODUCT,
        product=get_default_product(),
        supplier=get_default_supplier(),
        quantity=1,
        base_unit_price=source.create_price(10),
        weight=Decimal("0.2")
    )

    region = CountryShippingRegion(country="BR")
    source.shipping_address.country = "US"
    assert region.is_compatible_with(source) is False
    source.shipping_address.country = "BR"
    assert region.is_compatible_with(source)


@pytest.mark.django_db
def test_address_region(admin_user):
    service = get_custom_carrier_service()
    component = ShippingTableByModeBehaviorComponent.objects.create(
        mode=FetchTableMode.LOWEST_DELIVERY_TIME
    )
    service.behavior_components.add(component)
    source = get_source(admin_user, service)

    source.add_line(
        type=OrderLineType.PRODUCT,
        product=get_default_product(),
        supplier=get_default_supplier(),
        quantity=1,
        base_unit_price=source.create_price(10),
        weight=Decimal("0.2")
    )

    # match region country
    region = AddressShippingRegion(country="BR")
    source.shipping_address.country = "BR"
    assert region.is_compatible_with(source)

    # does not match anymore
    region.region = "SC"
    source.shipping_address.region = "PR"
    assert region.is_compatible_with(source) is False

    # match region
    source.shipping_address.region = "SC"
    assert region.is_compatible_with(source)

    # check city
    source.shipping_address.city = "Plumenau"
    region.city = "Indaiaba"
    assert region.is_compatible_with(source) is False
    region.city = "Plumenau"
    assert region.is_compatible_with(source)

    # check street1
    source.shipping_address.street1 = "R test"
    region.street1 = "T tosta"
    assert region.is_compatible_with(source) is False
    region.street1 = "R test"
    assert region.is_compatible_with(source)

    # check street2
    source.shipping_address.street2 = "R test"
    region.street2 = "T tosta"
    assert region.is_compatible_with(source) is False
    region.street2 = "R test"
    assert region.is_compatible_with(source)

    # check street3
    source.shipping_address.street3 = "R test"
    region.street3 = "T tosta"
    assert region.is_compatible_with(source) is False
    region.street3 = "R test"
    assert region.is_compatible_with(source)

    # clean all attrs
    region.region = ""
    region.city = ""
    region.street1 = ""
    region.street1 = ""
    region.street1 = ""

    # match only street3
    source.shipping_address.street3 = "R test"
    region.street3 = "T tosta"
    assert region.is_compatible_with(source) is False
    region.street3 = "R test"
    assert region.is_compatible_with(source)

    # match several cities
    region.street = ""
    region.city = "sao paulo, santos, curitiba"
    assert region.is_compatible_with(source) is False
    source.shipping_address.city = "santos"
    assert region.is_compatible_with(source)

    # match several regions
    region.region = "sp, rj, pr"
    assert region.is_compatible_with(source) is False
    source.shipping_address.region = "sp"
    assert region.is_compatible_with(source)

    # match several street1
    region.street1 = "st1, st2, st3"
    assert region.is_compatible_with(source) is False
    source.shipping_address.street1 = "st3"
    assert region.is_compatible_with(source)

    # match several street2
    region.street2 = "st4, st5, st6"
    assert region.is_compatible_with(source) is False
    source.shipping_address.street2 = "st4"
    assert region.is_compatible_with(source)

    # match several street3
    region.street3 = "st7, st8, st9"
    assert region.is_compatible_with(source) is False
    source.shipping_address.street3 = "st9"
    assert region.is_compatible_with(source)


@pytest.mark.django_db
def test_shipping_table_behavior(admin_user):
    service = get_custom_carrier_service()
    component = ShippingTableByModeBehaviorComponent.objects.create(
        mode=FetchTableMode.LOWEST_DELIVERY_TIME
    )
    service.behavior_components.add(component)
    source = get_source(admin_user, service)

    PRODUCT_WEIGHT = Decimal(700.0)  # in grams
    PRODUCT_WIDTH = Decimal(340)
    PRODUCT_DEPTH = Decimal(320)
    PRODUCT_HEIGHT = Decimal(180)

    product = get_default_product()
    product.gross_weight = PRODUCT_WEIGHT
    product.width = PRODUCT_WIDTH
    product.depth = PRODUCT_DEPTH
    product.height = PRODUCT_HEIGHT
    product.save()

    source.add_line(
        type=OrderLineType.PRODUCT,
        product=product,
        supplier=get_default_supplier(),
        quantity=1,
        base_unit_price=source.create_price(10),
    )

    assert abs((component.get_source_weight(source) * KG_TO_G) - PRODUCT_WEIGHT) < Decimal(0.0001)

    # configure cubic usage
    component.use_cubic_weight = True
    component.cubic_weight_factor = Decimal(6000.0)
    component.cubic_weight_exemption = Decimal(3.000)
    component.save()

    # not using cubic weight because of weight exemption
    assert abs((component.get_source_weight(source) * KG_TO_G) - PRODUCT_WEIGHT) < Decimal(0.0001)

    source.add_line(
        type=OrderLineType.PRODUCT,
        product=product,
        supplier=get_default_supplier(),
        quantity=7,
        base_unit_price=source.create_price(10),
    )

    cubic_weight = (PRODUCT_WIDTH * PRODUCT_DEPTH * (PRODUCT_HEIGHT * 8)) / component.cubic_weight_factor
    assert abs((component.get_source_weight(source) * KG_TO_G) - cubic_weight) < Decimal(0.0001)

    # set constraints
    component.max_package_width = Decimal(1000)
    component.max_package_height = Decimal(1000)
    component.max_package_length = Decimal(1000)
    component.max_package_edges_sum = Decimal(2000)
    component.max_package_weight = Decimal(10)
    component.save()

    cubic_weight = (PRODUCT_WIDTH * PRODUCT_DEPTH * (PRODUCT_HEIGHT * 8)) / component.cubic_weight_factor
    assert abs((component.get_source_weight(source) * KG_TO_G) - cubic_weight) < Decimal(0.0001)
