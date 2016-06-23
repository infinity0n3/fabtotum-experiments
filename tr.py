#!/bin/env python
# -*- coding: utf-8; -*-

"""
http://www.i18nguy.com/unicode/language-identifiers.html
https://pymotw.com/2/gettext/


xgettext -d tr -o tr.pot tr.py

mkdir -p locale/it_IT/LC_MESSAGES/
cp tr.pot locale/it_IT/LC_MESSAGES/tr.po
<edit> locale/it_IT/LC_MESSAGES/tr.po
msgfmt locale/it_IT/LC_MESSAGES/tr.po locale/it_IT/LC_MESSAGES/tr.mo

LANG=it_IT ./tr.py

"""

import gettext

# Set up message catalog access
#tr = gettext.translation('tr', 'locale', fallback=True, languages=['it_IT'])
tr = gettext.translation('tr', 'locale', fallback=True)
_ = tr.ugettext

print _("hello world")
