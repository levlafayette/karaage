# Copyright 2007-2010 VPAC
#
# This file is part of Karaage.
#
# Karaage is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Karaage is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Karaage  If not, see <http://www.gnu.org/licenses/>.

from django.conf import settings

REQUIRED_USER_ATTRS = [
    'uid', 'givenName', 'sn', 'cn', 'telephoneNumber', 'mail', 'o', 'userPassword',
    'shadowLastChange', 'shadowMax', 'shadowWarning', 'objectClass',
    ]
OPTIONAL_USER_ATTRS = [
    'loginShell', 'homeDirectory', 'uidNumber', 'gidNumber', 'gecos', 'title',
]

DEFAULT_USER_ATTRS = {
    'shadowLastChange': '13600',
    'shadowMax': '99999',
    'shadowWarning': '10',
    'objectClass': settings.USER_OBJECTCLASS,
}

PASSWORD_ATTRS = [
    'userPassword',
    ]


def get_next_uid(data):
    if 'posixAccount' in data['objectClass']:
        from placard.client import LDAPClient
        conn = LDAPClient()
        uidNumber = conn.get_new_uid()
        return str(uidNumber)
    else:
        return ''


def get_gid(data):
    if 'posixAccount' in data['objectClass']:
        return data['person'].institute.gid
    return ''

GENERATED_USER_ATTRS = {
    'uidNumber': get_next_uid,
    'gidNumber': get_gid,
    'gecos': lambda x: 'posixAccount' in x['objectClass'] and '%s %s (%s)' % (str(x['givenName']), str(x['sn']), str(x['o'])) or '',
    'cn': lambda x: '%s %s' % (str(x['givenName']), str(x['sn'])),
    'homeDirectory': lambda x: 'posixAccount' in x['objectClass'] and '/home/%s' % x['uid'] or '',
    'loginShell': lambda x: 'posixAccount' in x['objectClass'] and settings.DEFAULT_SHELL or '',
}


REQUIRED_GROUP_ATTRS = [
    'cn', 'objectClass', 'gidNumber',
    ]

OPTIONAL_GROUP_ATTRS = [
    
]
#GENERATED METHODS
# Must take one argument which is a dictionary of the currently resolved attributes (attributes are resolved in the order above)


def get_next_gid(data):
    from placard.client import LDAPClient
    conn = LDAPClient()
    gid = conn.get_next_gid()
    return [str(gid)]

DEFAULT_GROUP_ATTRS = {
    'objectClass': ['posixGroup', 'top'],
    }


GENERATED_GROUP_ATTRS = {
    'gidNumber': get_next_gid,
}

execfile("/etc/karaage/ldap_attrs.py")
