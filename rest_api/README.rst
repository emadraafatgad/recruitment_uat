Support email (UTC+2): avs3.ua@gmail.com

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

OVERVIEW
========

This module provide professional RESTful API (json) access to Odoo models with OAuth2 authentication (very simplified) and optional Redis token store.

The module has a **predefined** (and statically customizable) **schema** of response Odoo fields for 'Read one', 'Read all' and 'Create one' methods. Also there is an ability to **dynamically exclude or include** fetching fields. This allow **not** to fetch unnecessary fields (like a **heavy** image/binary fields or technical garbage fields) in **each request** or not to compose the list of desired fields in each request. Also that schemas can be used as a quick and clear model **reference guide** for your developers (backend, client side, etc.). See "Example #3" below.

The schema of the response fields can have a **tree-like** structure with **any** level of **nesting**. So **you can read an object at once with absolutely all its inner data (including its lines with all inner data) in just one http request.** Therefore you don't need to make a two (or much more) requests to get one object (if would so, the possible interruptions or lags between that requests can be fatal to the integrity of your data). See "Example #1" below.

The schema of the request fields can have a **tree-like** structure with one (and more in some cases) level of **nesting**. So **you can easily update (or create) an object at once with all its lines (including all their data) in just one http request.** See "Example #2" below.

This module has a **high-load** ready feature: it uses a mechanism which allow to cope with intensive and concurrent reading and writing the same Odoo records.

The previous features improves the integrity of your data, enhance the reliability of data processing and also reduce the size and complexity of code on your REST client side. These requirements are often necessary in **professional development**.

Also this module allow to fetch any PDF report from Odoo.

This module works with standard and custom Odoo models. Also, it works with both Community and Enterprise Odoo Edition.

The author of this module do not manipulate its price and don't cheat with itself purchasing.

Available models (the list is easily extensible):
    - account.invoice
    - account.invoice.line
    - product.template
    - report (only to fetching existing reports)
    - res.partner
    - sale.order
    - sale.order.line

**The procedure of adding any Odoo model is simple and not required of writing new code.** It's described below.

Each model has the following methods:
    - Read all (with optional filters, offset, limit, order, exclude_fields, include_fields)
    - Read one (with optional exclude_fields, include_fields)
    - Create one (with optional static default values)
    - Update one
    - Delete one
    - Call any method of Odoo model, including workflow manipulations (till the Odoo v10)

Also the 'Call any method' feature allow to execute a standard model's methods, like:
    - copy()
    - check_access_rights()
    - check_access_rule()
    - fields_get()
    - etc.

Authentication consists of three methods:
    - Login in Odoo (using three params: dbname, Odoo user, password) and get access and refresh token
    - Refresh access token
    - Delete access token from token store

'Access token' and 'Refresh token' have a certain lifetimes (statically customizable).

Thanks to Redis token store (disabled by default), your REST sessions are not drops after the server reboot.

This module requires sending 'Access token' inside the request header. All other parameters of any requests should be sent as json payload inside the request body or through the URL arguments (or simultaneously, with body priority).

|

**Example #1: 'sale.order - Read one' - response json**::

    {
        "date_order": "2016-06-02 18:41:42",
        "name": "SO001",
        "partner_id": {
            "city": "City 1",
            "id": 6,
            "name": "Customer 1"
        },
        "order_line": [
            {
                "name": "Product 1",
                "price_unit": 111,
                "product_uom_qty": 11,
                "price_subtotal": 1221,
                "product_id": {
                    "barcode": "2400000032632",
                    "name": "Product 1",
                    "type": "consu",
                    "attribute_line_ids": [
                        {
                            "display_name": "Attribute 1",
                            "id": 1
                        },
                        {
                            "display_name": "Attribute 2",
                            "id": 2
                        }
                    ],
                    "categ_id": {
                        "id": 1,
                        "name": "All"
                    },
                    "id": 2
                },
                "id": 1,
                "tax_id": [
                    {
                        "id": 6,
                        "name": "ITAX X"
                    },
                    {
                        "id": 7,
                        "name": "Tax 15.00%"
                    }
                ]
            },
            {
                "name": "Product 2",
                "price_unit": 222,
                "product_uom_qty": 22,
                "price_subtotal": 4884,
                "product_id": {
                    "barcode": null,
                    "name": "Product 2",
                    "type": "consu",
                    "attribute_line_ids": [],
                    "categ_id": {
                        "id": 1,
                        "name": "All"
                    },
                    "id": 3
                },
                "id": 2,
                "tax_id": [
                    {
                        "id": 7,
                        "name": "Tax 15.00%"
                    }
                ]
            }
        ],
        "amount_tax": 915.75,
        "state": "manual",
        "user_id": {
            "id": 1,
            "name": "Admin"
        },
        "create_date": "2016-06-02 18:42:48",
        "payment_term_id": {
            "id": 2,
            "name": "15 Days"
        },
        "id": 1,
        "amount_total": 7020.75
    }


The fields in this (static) schema are very **easy to add or delete, without writing or deleting code.** The dynamically included fields can not have a tree-like structure.


**Example #2: 'res.partner - Update one' - request json**::

    {
        # simple fields (non relational):
        'name':         'TEST Name~~',
        'street':       'TEST Street~~',
        'street2':      'TEST Street2~~',
        'city':         'TEST City~~',
        'zip':          '123~~',
        'phone':        '+123456789~~',
        'email':        'a@b.com~~',
        # many2one fields (existing 'id', not dictionary of new record!):
        'state_id':     6,
        'country_id':   14,
        # one2many fields (list of dictionaries of records):
        'bank_ids': [
            {                                   # this record will be updated (because 'id' is specified)
                'id':           56,
                'acc_number':   'acc_number 1~~',
                'bank_bic':     'bank_bic 1~~',
            },
            {                                   # this record will be removed (because 'id' is specified and record is empty)
                'id':           57,
            },
            {                                   # this record will be created (because 'id' is not specified but record is not empty)
                'acc_number':   'acc_number 4',
                'bank_bic':     'bank_bic 4',
            },
        ],
        # many2many fields (list of dictionaries of existing 'ids'):
        'category_id': [  # field's values will be replaced by this 'ids'
            {'id': 3},
            {'id': 4},
        ],
    }


~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

DETAILED DESCRIPTION
====================
|

**Full list of REST resources**::

    (route)                           (method)    (action)

       (authentication):

    /api/auth/get_tokens                POST    - Login in Odoo and get access and refresh token
    /api/auth/refresh_token             POST    - Refresh access token
    /api/auth/delete_tokens             POST    - Delete access token from token store

       (models):

    /api/<model>                        GET     - Read all (with optional filters, offset, limit, order, exclude_fields, include_fields)
    /api/<model>/<id>                   GET     - Read one (with optional exclude_fields, include_fields)
    /api/<model>                        POST    - Create one
    /api/<model>/<id>                   PUT     - Update one
    /api/<model>/<id>                   DELETE  - Delete one
    /api/<model>/<id>/<method>          PUT     - Call method (with optional parameters)

    * models - Only models which are added in REST API (the procedure is described below).
    The models available out of the box: account.invoice, account.invoice.line, product.template, res.partner, sale.order, sale.order.line.

       (reports):

    /api/report/get_pdf                 PUT     - Call method (with parameters)


The detailed description of IN/OUT data for each REST resource (HTTP-headers, data, error codes, etc.) presents in the files '/controllers/model__TEMPLATE.py' and '/controllers/auth.py'.

|

**The procedure of adding any Odoo model in REST API:**

1. Clone and rename the template file "/controllers/model__TEMPLATE.py" - replace the word "TEMPLATE" by "your_model_name".
For example::
    "model__TEMPLATE.py" >> "model__res_partner.py"

2. In that file, replace all substrings "model.name" and "model_name" by substrings "your.model.name" and "your_model_name" respectively. (Of course, use an IDE or text editor for this).
For example::
    "model.name" >> "res.partner"
    "model_name" >> "res_partner"

3. (most important) Fill the three schemas of response Odoo fields for "Read one", "Read all" and "Create one" methods in that file in three variables - "OUT__your_model_name__read_one__JSON", "OUT__your_model_name__read_all__JSON" and "OUT__your_model_name__create_one__JSON".
Here is the syntax of the schema (also you can see the working schema in Example #3 below)::

    (
        # (The order of fields of different types can be arbitrary)
        # simple fields (non relational):
        'simple_field_1',
        'simple_field_2',
        ...
        # many2one fields:
        
        'many2one_field_1',     # will return just 'id'
        OR
        ('many2one_field_1', (  # will return dictionary of inner fields
            'inner_field_1',
            'inner_field_2',
            ...
        )),
        
        'many2one_field_2',
        OR
        ('many2one_field_2', (
            'inner_field_1',
            'inner_field_2',
            ...
        )),
        
        ...
        # one2many fields:
        ('one2many_field_1', [(
            'inner_field_1',
            'inner_field_2',
            ...
        )]),
        ('one2many_field_2', [(
            'inner_field_1',
            'inner_field_2',
            ...
        )]),
        ...
        # many2many fields:
        ('many2many_field_1', [(
            'inner_field_1',
            'inner_field_2',
            ...
        )]),
        ('many2many_field_2', [(
            'inner_field_1',
            'inner_field_2',
            ...
        )]),
        ...
    )

There can be any level of nesting of inner fields.

If you'll want to add or remove some Odoo field in REST API in the future, you'll need just add or remove/comment out a field in this schema.

4. If necessary (but not mandatory), change the values of some variables which are labeled by tag "# editable" in that file.
There are such variables::
    - successful response codes in all methods;
    - default values in "Create one" method;
    - etc.

5. Add one import line of your new file in the file '/controllers/resources.py'.
For example::
    import model__your_model_name

6. Restart Odoo server.

|

**More examples of the request and response fields:**

|

**Example #3: 'sale.order - Read one' - response fields schema**::

    (
        # (The order of fields of different types can be arbitrary)
        # simple fields (non relational):
        'id',
        'name',
        'date_order',
        'create_date',
        'amount_tax',
        'amount_total',
        'state',
        # many2one fields:
        ('partner_id', (
            'id',
            'name',
            'city',
        )),
        ('user_id', (
            'id',
            'name',
        )),
        ('payment_term_id', (
            'id',
            'name',
        )),
        # one2many fields:
        ('order_line', [(
            'id',
            ('product_id', (  # many2one
                'id',
                'name',
                'type',
                'barcode',
                ('categ_id', (  # many2one
                    'id',
                    'name',
                )),
                ('attribute_line_ids', [(  # one2many
                    'id',
                    'display_name',
                )]),
            )),
            'name',
            'product_uom_qty',
            'price_unit',
            ('tax_id', [(  # many2many
                'id',
                'name',
            )]),
            'price_subtotal',
        )]),
    )


**Example #4: 'res.partner - Read all' - response json**::

    {
        "count": 11,
        "results": [
            {
                "id": 3,
                "name": "Admin"
            },
            {
                "id": 6,
                "name": "Customer 1"
            },
            {
                "id": 8,
                "name": "Customer Restapi"
            },
            
            ...
            
        ]
    }


**Example #5: 'res.partner - Create one' - request json**::

    {
        # simple fields (non relational):
        'name':         'TEST Name',
        'street':       'TEST Street',
        'street2':      'TEST Street2',
        'city':         'TEST City',
        'zip':          '123',
        'phone':        '+123456789',
        'email':        'a@b.com',
        # many2one fields (existing 'id', not dictionary of new record!):
        'state_id':     10,
        'country_id':   235,
        # one2many fields (list of dictionaries of new records):
        'bank_ids': [
            {
                'acc_number':   'acc_number 1',
                'bank_bic':     'bank_bic 1',
            },
            {
                'acc_number':   'acc_number 2',
                'bank_bic':     'bank_bic 2',
            },
            {
                'acc_number':   'acc_number 3',
                'bank_bic':     'bank_bic 3',
            },
        ],
        # many2many fields (list of dictionaries of existing 'ids'):
        'category_id': [
            {'id': 1},
            {'id': 2},
        ],
    }


Other examples it can see in the existing different models files like '/controllers/model__xxxxxxxxxx.py'.

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

INSTALLATION TIPS
=================
|

It would be good to install a 'simplejson' Python package (to avoid rare unusual unicode issues with latest 3.x or obsolete Python versions).

**This module requires the 'db_name' and 'dbfilter' Odoo config parameters (or command line options) with only one database (without aliases)!**::
    
    (config parameters)
    db_name = your_db_name
    dbfilter = your_db_name
    
    (or command line options)
    --database=your_db_name --db-filter=your_db_name

**After the installation (or updating) of this module it need to restart Odoo server!**

This module adds the following 'System Parameters' in Odoo:
    - rest_api.access_token_expires_in (600 seconds)
    - rest_api.refresh_token_expires_in (7200 seconds)
    - rest_api.use_redis_token_store (False)
    - rest_api.redis_host (localhost)
    - rest_api.redis_port (6379)
    - rest_api.redis_db (0)
    - rest_api.redis_password (None)

If you want to use the Redis token store, you should set the Odoo system parameter "rest_api.use_redis_token_store = True", and also you need to install, (optional) setup and run 'Redis' server, something like this::
    
        (choose your package manager)
    $ sudo apt install redis-server python3-redis
    $ sudo apt-get install redis-server python3-redis
    $ sudo yum install redis python3-redis
    $ sudo dnf install redis python3-redis
        (run)
    $ redis-server

And then restart Odoo server.

Useful 'Redis' links:

    - https://pypi.python.org/pypi/redis
    - http://redis.io/topics/quickstart

|

**To test REST resources can be used 'curl', like this**::

    (Linux syntax)

    1. Login in Odoo and get access and refresh token:
    curl -v -i -k -H "Content-Type: text/html"   http://localhost:8069/api/auth/get_tokens   -X POST   -d '{"db":"testdb12", "username":"admin", "password":"admin"}'

    2. Refresh access token:
    curl -v -i -k -H "Content-Type: text/html"   http://localhost:8069/api/auth/refresh_token   -X POST   -d '{"refresh_token":"XXXXXXXXXXXXXXXXX"}'

    3. Delete access token from token store:
    curl -v -i -k -H "Content-Type: text/html"   http://localhost:8069/api/auth/delete_tokens   -X POST   -d '{"refresh_token":"XXXXXXXXXXXXXXXXX"}'

    4. res.partner - Read all (without filters):
    curl -v -i -k -H "Content-Type: text/html"   http://localhost:8069/api/res.partner   -X GET   -H "Access-Token: XXXXXXXXXXXXXXXXX"

    5. res.partner - Read all (with two filters):
    curl -v -i -k -H "Content-Type: text/html"   http://localhost:8069/api/res.partner   -X GET   -H "Access-Token: XXXXXXXXXXXXXXXXX"   -d '{"filters": "[(\"name\", \"like\", \"ompany\"), (\"id\", \"<=\", 50)]"}'

    6. res.partner - Read one:
    curl -v -i -k -H "Content-Type: text/html"   http://localhost:8069/api/res.partner/3   -X GET   -H "Access-Token: XXXXXXXXXXXXXXXXX"

    7. res.partner - Create one:
    curl -v -i -k -H "Content-Type: text/html"   http://localhost:8069/api/res.partner   -X POST   -H "Access-Token: XXXXXXXXXXXXXXXXX"   -d '{"name": "TEST Name", "street": "TEST Street", "city": "TEST City"}'

    8. res.partner - Update one:
    curl -v -i -k -H "Content-Type: text/html"   http://localhost:8069/api/res.partner/2361   -X PUT   -H "Access-Token: XXXXXXXXXXXXXXXXX"   -d '{"name": "TEST Name~~", "street": "TEST Street~~", "city": "TEST City~~"}'

    9. res.partner - Delete one:
    curl -v -i -k -H "Content-Type: text/html"   http://localhost:8069/api/res.partner/2361   -X DELETE   -H "Access-Token: XXXXXXXXXXXXXXXXX"

    10. res.partner - Call method 'address_get' (without parameters):
    curl -v -i -k -H "Content-Type: text/html"   http://localhost:8069/api/res.partner/2361/address_get   -X PUT   -H "Access-Token: XXXXXXXXXXXXXXXXX"

    11. res.partner - Call method '_email_send' (with parameters):
    curl -v -i -k -H "Content-Type: text/html"   http://localhost:8069/api/res.partner/2361/_email_send   -X PUT   -H "Access-Token: XXXXXXXXXXXXXXXXX"   -d '{"email_from": "test@test.com", "subject": "TEST Subject", "body": "TEST Body"}'

    12. report - Call method 'get_pdf' (with parameters):
    curl -v -i -k -H "Content-Type: text/html"   http://localhost:8069/api/report/get_pdf   -X PUT   -H "Access-Token: XXXXXXXXXXXXXXXXX"   -d '{"report_name": "account.report_invoice", "ids": [3]}'


There are also some files in Python for examples and testing purpose:
    - /rest_api/tests/test__Auth_GetTokens.py
    - /rest_api/tests/test__Create__OrderInvoice_.py
    - /rest_api/tests/test__Create__product.template.py
    - /rest_api/tests/test__Create__res.partner.py
    - /rest_api/tests/test__CreateWithAttributes__product.template.py
    - /rest_api/tests/test__CreateWithVendors__product.template.py
    - /rest_api/tests/test__get_pdf__report.py
    - /rest_api/tests/test__ReadAllWithFiltersInURL__res.partner.py
    - /rest_api/tests/test__ReadAllWithFiltersOffsetLimitOrder__res.partner.py
    - /rest_api/tests/test__Update__res.partner.py
    - /rest_api/tests/test__UpdateWithVendors__product.template.py


CHANGELOG
=========
|

version 1.7 (2018-12-02):
    - added the ability to send parameters of all requests through the URL arguments (GET requests already had this feature before)

version 1.6 (2018-08-26):
    - added the ability to **not use the Redis** token store, from now on, this is the **default** behavior. Also added the 'rest_api' prefix in the system parameters created by this module.

version 1.5 (2018-03-10):
    - added the ability to dynamically exclude or include fetching fields

version 1.4 (2017-12-10):
    - added the ability to send parameters of GET requests through the URL arguments

version 1.3 (2017-10-25):
    - added the ability to fetch any PDF report from Odoo

version 1.2 (2017-02-08):
    - added the ability to customize response Odoo fields returned by 'Create one' method (see changes in file "/controllers/model__TEMPLATE.py")

version 1.1 (2017-01-03):
    - added **call any method** of Odoo model (including workflow manipulations)

version 1.0 (2016-06-25):
    - initial release (for Odoo v8/9)

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The support consists of **free lifetime** bug-fixing and keeping the actuality of this module's code according with all stable and old (since v8) Odoo versions.

Support email (UTC+2): avs3.ua@gmail.com
