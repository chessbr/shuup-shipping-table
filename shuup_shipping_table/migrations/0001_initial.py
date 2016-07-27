# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import shuup_shipping_table.models
import parler.models
import shuup.core.fields
import enumfields.fields
import django_countries.fields
from decimal import Decimal


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('shuup', '0002_rounding'),
    ]

    operations = [
        migrations.CreateModel(
            name='ShippingCarrier',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, serialize=False, auto_created=True)),
                ('name', models.CharField(verbose_name='name', max_length=40)),
                ('enabled', models.BooleanField(verbose_name='enabled', default=True)),
                ('shops', models.ManyToManyField(verbose_name='shops', related_name='shop_shipping_carriers', help_text='Select the shops which can use this carrier. Blank means no shop!', blank=True, to='shuup.Shop')),
            ],
            options={
                'verbose_name': 'shipping carrier',
                'verbose_name_plural': 'shipping carriers',
            },
        ),
        migrations.CreateModel(
            name='ShippingRegion',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, serialize=False, auto_created=True)),
                ('priority', models.IntegerField(verbose_name='priority', help_text='A higher number means this region is most important than other with a lower priority', default=0)),
            ],
            options={
                'verbose_name': 'shipping region',
                'verbose_name_plural': 'shipping regions',
            },
            bases=(parler.models.TranslatableModelMixin, models.Model),
        ),
        migrations.CreateModel(
            name='ShippingRegionTranslation',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, serialize=False, auto_created=True)),
                ('language_code', models.CharField(verbose_name='Language', max_length=15, db_index=True)),
                ('name', models.CharField(verbose_name='name', max_length=100)),
                ('description', models.CharField(verbose_name='description', max_length=120, blank=True)),
            ],
            options={
                'db_table': 'shuup_shipping_table_shippingregion_translation',
                'managed': True,
                'verbose_name': 'shipping region Translation',
                'db_tablespace': '',
                'default_permissions': (),
            },
        ),
        migrations.CreateModel(
            name='ShippingTable',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, serialize=False, auto_created=True)),
                ('identifier', models.SlugField(verbose_name='identifier', help_text='A slug identifier, e.g my-table-id-3218321', unique=True)),
                ('name', models.CharField(verbose_name='name', max_length=40)),
                ('enabled', models.BooleanField(verbose_name='enabled', default=True)),
                ('start_date', models.DateTimeField(verbose_name='start date', null=True, blank=True)),
                ('end_date', models.DateTimeField(verbose_name='end date', null=True, blank=True)),
                ('carrier', models.ForeignKey(verbose_name='carrier', to='shuup_shipping_table.ShippingCarrier')),
            ],
            options={
                'verbose_name': 'shipping table',
                'verbose_name_plural': 'shipping tables',
            },
        ),
        migrations.CreateModel(
            name='ShippingTableByModeBehaviorComponent',
            fields=[
                ('servicebehaviorcomponent_ptr', models.OneToOneField(to='shuup.ServiceBehaviorComponent', auto_created=True, serialize=False, primary_key=True, parent_link=True)),
                ('add_delivery_time_days', models.PositiveSmallIntegerField(verbose_name='additional delivery time', help_text='Extra number of days to add.', default=0)),
                ('add_price', shuup.core.fields.MoneyValueField(verbose_name='additional price', help_text='Extra amount to add.', default=Decimal('0'), max_digits=36, decimal_places=9)),
                ('mode', enumfields.fields.EnumIntegerField(verbose_name='mode', help_text='Select the mode which will be used to fetch a shipping table.', enum=shuup_shipping_table.models.FetchTableMode)),
                ('carriers', models.ManyToManyField(verbose_name='carriers filter', to='shuup_shipping_table.ShippingCarrier', help_text='Only selected carriers will be used to calculate shipping. Blank means all carriers.', blank=True)),
                ('tables', models.ManyToManyField(verbose_name='tables filter', to='shuup_shipping_table.ShippingTable', help_text='Only selected tables will be used to calculate shipping. Blank means all available tables.', blank=True)),
            ],
            options={
                'abstract': False,
            },
            bases=('shuup.servicebehaviorcomponent',),
        ),
        migrations.CreateModel(
            name='ShippingTableItem',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, serialize=False, auto_created=True)),
                ('start_weight', shuup.core.fields.MeasurementField(verbose_name='start weight (g)', unit='g', default=0, max_digits=36, decimal_places=9)),
                ('end_weight', shuup.core.fields.MeasurementField(verbose_name='end weight (g)', unit='g', default=0, max_digits=36, decimal_places=9)),
                ('price', shuup.core.fields.MoneyValueField(verbose_name='price', max_digits=36, decimal_places=9)),
                ('delivery_time', models.PositiveSmallIntegerField(verbose_name='delivery time (days)')),
            ],
            options={
                'verbose_name': 'shipping price table',
                'verbose_name_plural': 'shipping price tables',
            },
        ),
        migrations.CreateModel(
            name='SpecificShippingTableBehaviorComponent',
            fields=[
                ('servicebehaviorcomponent_ptr', models.OneToOneField(to='shuup.ServiceBehaviorComponent', auto_created=True, serialize=False, primary_key=True, parent_link=True)),
                ('add_delivery_time_days', models.PositiveSmallIntegerField(verbose_name='additional delivery time', help_text='Extra number of days to add.', default=0)),
                ('add_price', shuup.core.fields.MoneyValueField(verbose_name='additional price', help_text='Extra amount to add.', default=Decimal('0'), max_digits=36, decimal_places=9)),
                ('table', models.ForeignKey(to='shuup_shipping_table.ShippingTable', help_text='Select the table to fetch the price and delivery time.', verbose_name='table')),
            ],
            options={
                'abstract': False,
            },
            bases=('shuup.servicebehaviorcomponent',),
        ),
        migrations.CreateModel(
            name='CountryShippingRegion',
            fields=[
                ('shippingregion_ptr', models.OneToOneField(to='shuup_shipping_table.ShippingRegion', auto_created=True, serialize=False, primary_key=True, parent_link=True)),
                ('country', django_countries.fields.CountryField(verbose_name='country', max_length=2, unique=True)),
            ],
            options={
                'verbose_name': 'shipping region by country',
                'verbose_name_plural': 'shipping regions by country',
            },
            bases=('shuup_shipping_table.shippingregion',),
        ),
        migrations.CreateModel(
            name='PostalCodeRangeShippingRegion',
            fields=[
                ('shippingregion_ptr', models.OneToOneField(to='shuup_shipping_table.ShippingRegion', auto_created=True, serialize=False, primary_key=True, parent_link=True)),
                ('country', django_countries.fields.CountryField(verbose_name='country', max_length=2)),
                ('start_postal_code', models.PositiveIntegerField(verbose_name='starting postal code')),
                ('end_postal_code', models.PositiveIntegerField(verbose_name='ending postal code')),
            ],
            options={
                'verbose_name': 'shipping region by postal code range',
                'ordering': ('priority', 'start_postal_code'),
                'verbose_name_plural': 'shipping regions by postal code range',
            },
            bases=('shuup_shipping_table.shippingregion',),
        ),
        migrations.AddField(
            model_name='shippingtableitem',
            name='region',
            field=models.ForeignKey(verbose_name='region', to='shuup_shipping_table.ShippingRegion'),
        ),
        migrations.AddField(
            model_name='shippingtableitem',
            name='table',
            field=models.ForeignKey(verbose_name='table', to='shuup_shipping_table.ShippingTable'),
        ),
        migrations.AddField(
            model_name='shippingtable',
            name='excluded_regions',
            field=models.ManyToManyField(verbose_name='excluded regions', to='shuup_shipping_table.ShippingRegion', help_text='Selected regions will be excluded from this table', blank=True),
        ),
        migrations.AddField(
            model_name='shippingtable',
            name='shops',
            field=models.ManyToManyField(verbose_name='shops', related_name='shop_shipping_tables', help_text='Select the shops which can use this table. Blank means no shop!', blank=True, to='shuup.Shop'),
        ),
        migrations.AddField(
            model_name='shippingregiontranslation',
            name='master',
            field=models.ForeignKey(to='shuup_shipping_table.ShippingRegion', related_name='base_translations', null=True, editable=False),
        ),
        migrations.AddField(
            model_name='shippingregion',
            name='polymorphic_ctype',
            field=models.ForeignKey(to='contenttypes.ContentType', related_name='polymorphic_shuup_shipping_table.shippingregion_set+', null=True, editable=False),
        ),
        migrations.AlterUniqueTogether(
            name='shippingregiontranslation',
            unique_together=set([('language_code', 'master')]),
        ),
    ]
