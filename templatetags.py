"""
Module which contains Custom Template Tags or Filters.

Notes:
    - Make sure to set the variable TEMPLATE_TAGS_FILTERS_MODULE in settings.py

Example:
    # tags.py
    from duck.template import TemplateTag, TemplateFilter

    def mytag(arg1):
        # do some stuff here
        return "some data"

    def myfilter(data):
        # do some stuff here
        return data

    TAGS = [
        TemplateTag("name_here", mytag, takes_context=False)  # takes_context defaults to False
    ]

    FILTERS = [
        TemplateFilter("name_here", myfilter)
    ]
"""

TAGS = [
    # Your tags here
]

FILTERS = [
    # Your filters here
]
