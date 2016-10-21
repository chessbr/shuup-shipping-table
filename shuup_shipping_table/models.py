# -*- coding: utf-8 -*-
# This file is part of Shuup Shipping Table
#
# Copyright (c) 2016, Rockho Team. All rights reserved.
# Author: Christian Hess
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.

from __future__ import unicode_literals

import logging
from datetime import timedelta
from decimal import Decimal

from enumfields import Enum, EnumIntegerField
from parler.fields import TranslatedField
from parler.models import TranslatedFields

from shuup_order_packager.algorithms import SimplePackager
from shuup_order_packager.constraints import (
    SimplePackageDimensionConstraint, WeightPackageConstraint
)

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.utils.encoding import python_2_unicode_compatible
from django.utils.timezone import now
from django.utils.translation import ugettext_lazy as _
from django_countries.fields import CountryField

from shuup.core.fields import MeasurementField, MoneyValueField
from shuup.core.models._base import PolymorphicTranslatableShuupModel
from shuup.core.models._service_base import ServiceBehaviorComponent, ServiceCost
from shuup.core.models._shops import Shop
from shuup.utils.dates import DurationRange

logger = logging.getLogger(__name__)

G_TO_KG = Decimal(0.001)
KG_TO_G = Decimal(1000)


class FetchTableMode(Enum):
    LOWEST_PRICE = 0
    LOWEST_DELIVERY_TIME = 1

    class Labels:
        LOWEST_PRICE = _('Lowest price')
        LOWEST_DELIVERY_TIME = _('Lowest delivery time')


class ShippingTableBehaviorComponent(ServiceBehaviorComponent):
    add_delivery_time_days = models.PositiveSmallIntegerField(verbose_name=_("additional delivery time"),
                                                              default=0,
                                                              help_text=_("Extra number of days to add."))

    add_price = MoneyValueField(verbose_name=_("additional price"),
                                default=Decimal(),
                                help_text=_("Extra amount to add."))

    use_cubic_weight = models.BooleanField(verbose_name=_("Use Cubic Weight"),
                                           default=False,
                                           help_text=_("Enable this to calculate the cubic weight and use "
                                                       "the heaviest measurement (real weight or cubic weight)."))

    cubic_weight_factor = models.DecimalField(verbose_name=_("Cubic Weight Factor (cm³)"),
                                              decimal_places=2, max_digits=10,
                                              default=Decimal(6000),
                                              help_text=_("Google it if you don't know what you're doing."))

    cubic_weight_exemption = MeasurementField(unit="kg",
                                              verbose_name=_("Cubic Weight exemption value (kg)"),
                                              decimal_places=3, max_digits=8,
                                              default=Decimal(),
                                              help_text=_("The Cubic Weight will be considered if the "
                                                          "sum of all products real weights "
                                                          "is higher then this value."))

    max_package_width = MeasurementField(unit="mm",
                                         verbose_name=_("Max package width (mm)"),
                                         decimal_places=2, max_digits=7,
                                         default=Decimal(),
                                         help_text=_("This is only used for Cubic Weight method "
                                                     "since the order/basket will be splitted into packages "
                                                     "for volume calculation."))

    max_package_height = MeasurementField(unit="mm",
                                          verbose_name=_("Max package height (mm)"),
                                          decimal_places=2, max_digits=7,
                                          default=Decimal(),
                                          help_text=_("This is only used for Cubic Weight method "
                                                      "since the order/basket will be splitted into packages "
                                                      "for volume calculation."))

    max_package_length = MeasurementField(unit="mm",
                                          verbose_name=_("Max package length (mm)"),
                                          decimal_places=2, max_digits=7,
                                          default=Decimal(),
                                          help_text=_("This is only used for Cubic Weight method "
                                                      "since the order/basket will be splitted into packages "
                                                      "for volume calculation."))

    max_package_edges_sum = MeasurementField(unit="mm",
                                             verbose_name=_("Max package edge sum (mm)"),
                                             decimal_places=2, max_digits=7,
                                             default=Decimal(),
                                             help_text=_("The max sum of width, height and length of the package. "
                                                         "This is only used for Cubic Weight method "
                                                         "since the order/basket will be splitted into packages "
                                                         "for volume calculation."))

    max_package_weight = MeasurementField(unit="kg",
                                          verbose_name=_("Max package weight (kg)"),
                                          decimal_places=3, max_digits=8,
                                          default=Decimal(),
                                          help_text=_("This is only used for Cubic Weight method "
                                                      "since the order/basket will be splitted into packages "
                                                      "for volume calculation."))

    class Meta:
        abstract = True

    def get_source_weight(self, source):
        """
        Calculates the source weight (in kg) based on behavior component configuration.
        """
        weight = source.total_gross_weight * G_TO_KG  # transform g in kg

        if self.use_cubic_weight and weight > self.cubic_weight_exemption:
            # create the packager
            packager = SimplePackager()

            # add the constraints, if configured
            if self.max_package_height and self.max_package_length and \
                    self.max_package_width and self.max_package_edges_sum:

                packager.add_constraint(SimplePackageDimensionConstraint(
                    self.max_package_width,
                    self.max_package_length,
                    self.max_package_height,
                    self.max_package_edges_sum
                ))

            if self.max_package_weight:
                packager.add_constraint(WeightPackageConstraint(self.max_package_weight * KG_TO_G))

            # split products into packages
            packages = packager.pack_source(source)

            # check if some package was created
            if packages:
                total_weight = 0

                for package in packages:

                    if package.weight > self.cubic_weight_exemption:
                        total_weight = total_weight + (package.volume / self.cubic_weight_factor * G_TO_KG)
                    else:
                        total_weight = total_weight + package.weight * G_TO_KG

                weight = total_weight

        return weight

    def get_available_table_items(self, source):
        """
        Fetches the available table items
        """
        now_dt = now()
        weight = self.get_source_weight(source)

        # 1) source total weight must be in a range
        # 2) enabled tables
        # 3) enabled table carriers
        # 4) valid shops
        # 5) valid date range tables
        # 6) order by priority
        # 7) distinct rows

        qs = ShippingTableItem.objects.select_related('table').filter(
            end_weight__gte=weight,
            start_weight__lte=weight,
            table__enabled=True,
            table__carrier__enabled=True,
            table__shops__in=[source.shop]
        ).filter(
            Q(Q(table__start_date__lte=now_dt) | Q(table__start_date=None)),
            Q(Q(table__end_date__gte=now_dt) | Q(table__end_date=None))
        ).order_by('-region__priority').distinct()

        return qs

    def get_first_available_item(self, source):
        table_items = self.get_available_table_items(source)

        for table_item in table_items:
            # check if the table exclude region is compatible
            # with the source.. if True, check next one
            invalid_region = False
            for excluded_region in table_item.table.excluded_regions.all():
                if excluded_region.is_compatible_with(source):
                    invalid_region = True
                    break
            if invalid_region:
                continue

            # a valid table item was found! get out of here
            if table_item.region.is_compatible_with(source):
                return table_item

    def get_unavailability_reasons(self, service, source):
        table_item = self.get_first_available_item(source)

        if not table_item:
            return [ValidationError(_("No table found"))]
        return ()

    def get_costs(self, service, source):
        table_item = self.get_first_available_item(source)

        if table_item:
            return [ServiceCost(source.create_price(table_item.price + self.add_price))]

        return ()

    def get_delivery_time(self, service, source):
        table_item = self.get_first_available_item(source)

        if table_item:
            return DurationRange(
                timedelta(days=(table_item.delivery_time + self.add_delivery_time_days))
            )

        return None


class ShippingTableByModeBehaviorComponent(ShippingTableBehaviorComponent):
    name = _("Shipping Table: custom fetch mode")
    help_text = _("Fetches the price and delivery time using a custom mode.")

    mode = EnumIntegerField(FetchTableMode,
                            verbose_name=_('mode'),
                            help_text=_("Select the mode which will be used "
                                        "to fetch a shipping table."))

    tables = models.ManyToManyField('ShippingTable',
                                    verbose_name=_("tables filter"),
                                    blank=True,
                                    help_text=_("Only selected tables will be used "
                                                "to calculate shipping. "
                                                "Blank means all available tables."))

    carriers = models.ManyToManyField('ShippingCarrier',
                                      verbose_name=_("carriers filter"),
                                      blank=True,
                                      help_text=_("Only selected carriers will be used "
                                                  "to calculate shipping. "
                                                  "Blank means all carriers."))

    def get_available_table_items(self, source):
        """
        Add extra filtering
        """

        table_items = super(
            ShippingTableByModeBehaviorComponent, self
        ).get_available_table_items(source)

        if self.tables.exists():
            table_items = table_items.filter(
                table__in=self.tables.all()
            )

        if self.carriers.exists():
            table_items = table_items.filter(
                table__carrier__in=self.carriers.all()
            )

        if self.mode == FetchTableMode.LOWEST_PRICE:
            table_items = table_items.order_by('-region__priority', 'price')
        elif self.mode == FetchTableMode.LOWEST_DELIVERY_TIME:
            table_items = table_items.order_by('-region__priority', 'delivery_time')

        return table_items


class SpecificShippingTableBehaviorComponent(ShippingTableBehaviorComponent):
    name = _("Shipping Table: specific table")
    help_text = _("Fetches the price and delivery time from a specific shipping table")

    table = models.ForeignKey('ShippingTable',
                              verbose_name=_("table"),
                              help_text=_("Select the table to fetch the price and delivery time."))

    def get_available_table_items(self, source):
        """ Add extra filtering """

        qs = super(
            SpecificShippingTableBehaviorComponent, self
        ).get_available_table_items(source).filter(
            table=self.table
        ).order_by('-region__priority', 'price')

        return qs


@python_2_unicode_compatible
class ShippingCarrier(models.Model):
    name = models.CharField(verbose_name=_("name"), max_length=40)
    enabled = models.BooleanField(verbose_name=_("enabled"), default=True)
    shops = models.ManyToManyField(Shop, blank=True,
                                   related_name="shop_shipping_carriers",
                                   verbose_name=_("shops"),
                                   help_text=_("Select the shops which can use this carrier. "
                                               "Blank means no shop!"))

    class Meta:
        verbose_name = _("shipping carrier")
        verbose_name_plural = _("shipping carriers")

    def __str__(self):
        return self.name


@python_2_unicode_compatible
class ShippingRegion(PolymorphicTranslatableShuupModel):
    name = TranslatedField(any_language=True)
    description = TranslatedField()
    priority = models.IntegerField(verbose_name=_("priority"),
                                   default=0,
                                   help_text=_("A higher number means this region is most "
                                               "important than other with a lower priority"))

    base_translations = TranslatedFields(
        name=models.CharField(max_length=100, verbose_name=_("name")),
        description=models.CharField(max_length=120, blank=True, verbose_name=_("description"))
    )

    class Meta:
        verbose_name = _("shipping region")
        verbose_name_plural = _("shipping regions")

    def __str__(self):
        return self.name

    def is_compatible_with(self, source):
        """
        Returns true if this region is compatible for given source.

        This method should especially check the source's delivery address
        and return if this region is compatible

        :type source: shuup.core.order_creator.OrderSource
        :rtype: bool
        :return: whether this region is available for a source
        """
        return False


@python_2_unicode_compatible
class PostalCodeRangeShippingRegion(ShippingRegion):
    country = CountryField(verbose_name=_("country"))
    start_postal_code = models.PositiveIntegerField(verbose_name=_("starting postal code"))
    end_postal_code = models.PositiveIntegerField(verbose_name=_("ending postal code"))

    class Meta:
        verbose_name = _("shipping region by postal code range")
        verbose_name_plural = _("shipping regions by postal code range")
        ordering = ('priority', 'start_postal_code')

    def is_compatible_with(self, source):
        if not source.shipping_address or not source.shipping_address.postal_code or \
                source.shipping_address.country != self.country:
            return False

        try:
            postal_code_int = int("".join([d for d in source.shipping_address.postal_code if d.isdigit()]))
            return (self.start_postal_code <= postal_code_int <= self.end_postal_code)
        except ValueError:
            return False

    def __str__(self):
        return self.name


@python_2_unicode_compatible
class CountryShippingRegion(ShippingRegion):
    country = CountryField(verbose_name=_("country"), unique=True)

    class Meta:
        verbose_name = _("shipping region by country")
        verbose_name_plural = _("shipping regions by country")

    def is_compatible_with(self, source):
        if not source.shipping_address or not source.shipping_address.country:
            return False
        return source.shipping_address.country == self.country

    def __str__(self):
        return self.name


@python_2_unicode_compatible
class AddressShippingRegion(ShippingRegion):
    country = CountryField(verbose_name=_("country"))

    region = models.TextField(verbose_name=_('region'),
                              blank=True, null=True,
                              help_text=_("use comma-separated values to match several names"))

    city = models.TextField(verbose_name=_('city'),
                            blank=True, null=True,
                            help_text=_("use comma-separated values to match several names"))

    street1 = models.TextField(verbose_name=_('street (1)'),
                               blank=True, null=True,
                               help_text=_("use comma-separated values to match several names"))

    street2 = models.TextField(verbose_name=_('street (2)'),
                               blank=True, null=True,
                               help_text=_("use comma-separated values to match several names"))

    street3 = models.TextField(verbose_name=_('street (3)'),
                               blank=True, null=True,
                               help_text=_("use comma-separated values to match several names"))

    class Meta:
        verbose_name = _("shipping region by address")
        verbose_name_plural = _("shipping regions by address")

    def is_compatible_with(self, source):
        if not source.shipping_address or not source.shipping_address.country or \
                source.shipping_address.country != self.country:
            return False

        attrs_check = ('region', 'city', 'street1', 'street2', 'street3')

        # address attributes to check, those configured must match
        for attr_name in attrs_check:
            attr_value = getattr(self, attr_name, None)

            if attr_value:
                if not getattr(source.shipping_address, attr_name, None):
                    return False

                # split, transform to upper and strip
                values = [v.upper().strip() for v in attr_value.split(",")]
                addr_value = getattr(source.shipping_address, attr_name).upper().strip()

                if addr_value not in values:
                    return False

        return True

    def __str__(self):
        return self.name


@python_2_unicode_compatible
class ShippingTable(models.Model):
    identifier = models.SlugField(unique=True,
                                  verbose_name=_("identifier"),
                                  help_text=_("A slug identifier, e.g my-table-id-3218321"))
    name = models.CharField(verbose_name=_("name"), max_length=40)
    enabled = models.BooleanField(verbose_name=_("enabled"), default=True)
    carrier = models.ForeignKey(ShippingCarrier, verbose_name=_("carrier"))
    excluded_regions = models.ManyToManyField(ShippingRegion, blank=True,
                                              verbose_name=_("excluded regions"),
                                              help_text=_("Selected regions will be excluded "
                                                          "from this table"))
    start_date = models.DateTimeField(verbose_name=_("start date"), null=True, blank=True)
    end_date = models.DateTimeField(verbose_name=_("end date"), null=True, blank=True)
    shops = models.ManyToManyField(Shop, blank=True,
                                   related_name="shop_shipping_tables",
                                   verbose_name=_("shops"),
                                   help_text=_("Select the shops which can use this table. "
                                               "Blank means no shop!"))

    class Meta:
        verbose_name = _("shipping table")
        verbose_name_plural = _("shipping tables")

    def __str__(self):
        return self.name


@python_2_unicode_compatible
class ShippingTableItem(models.Model):
    table = models.ForeignKey(ShippingTable, verbose_name=_("table"))
    region = models.ForeignKey(ShippingRegion, verbose_name=_("region"))

    start_weight = MeasurementField(unit="g", verbose_name=_('start weight (g)'))
    end_weight = MeasurementField(unit="g", verbose_name=_('end weight (g)'))

    price = MoneyValueField(verbose_name=_("price"))
    delivery_time = models.PositiveSmallIntegerField(verbose_name=_("delivery time (days)"))

    class Meta:
        verbose_name = _("shipping price table")
        verbose_name_plural = _("shipping price tables")

    def __str__(self):
        return "ID {0} {1} {2} - {3}->{4}: {5}-{6}".format(self.id,
                                                           self.table,
                                                           self.region,
                                                           self.start_weight,
                                                           self.end_weight,
                                                           self.price,
                                                           self.delivery_time)
