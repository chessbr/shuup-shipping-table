# -*- coding: utf-8 -*-
# This file is part of Shuup Shipping Table
#
# Copyright (c) 2016, Rockho Team. All rights reserved.
# Author: Christian Hess
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.

import setuptools
from babel.messages import frontend as babel

NAME = 'shuup-shipping-table'
VERSION = '1.0.0'
DESCRIPTION = 'A shipping method add-on for Shuup based on price tables by region'
AUTHOR = 'Rockho Team'
AUTHOR_EMAIL = 'rockho@rockho.com.br'
URL = 'http://www.rockho.com.br/'
LICENSE = 'AGPL-3.0'

EXCLUDED_PACKAGES = [
    'shuup_shipping_table_tests', 'shuup_shipping_table_tests.*',
]

REQUIRES = [

]

if __name__ == '__main__':
    setuptools.setup(
        name=NAME,
        version=VERSION,
        description=DESCRIPTION,
        url=URL,
        author=AUTHOR,
        author_email=AUTHOR_EMAIL,
        license=LICENSE,
        packages=["shuup_shipping_table"],
        include_package_data=True,
        install_requires=REQUIRES,
        entry_points={"shuup.addon": "shuup_shipping_table=shuup_shipping_table"},
        cmdclass={'compile_catalog': babel.compile_catalog,
                  'extract_messages': babel.extract_messages,
                  'init_catalog': babel.init_catalog,
                  'update_catalog': babel.update_catalog},
        message_extractors={
            'shuup_shipping_table': [
                ('**.py', 'python', None),
                ('**/templates/**.html', 'jinja2', None),
                ('**/templates/**.jinja', 'jinja2', None)
            ],
        }
    )
