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

from django.test import TestCase
from django.test.client import Client
from django.core import mail
from django.core.urlresolvers import reverse
from django.core.management import call_command
from django.contrib.auth.models import User
from django.conf import settings

import datetime
from time import sleep
from placard.server import slapd
from placard.client import LDAPClient
from placard import exceptions as placard_exceptions

from karaage.people.models import Person, Institute
from karaage.projects.models import Project
from karaage.machines.models import UserAccount, MachineCategory, Machine
from karaage.test_data.initial_ldap_data import test_ldif

class UserAccountTestCase(TestCase):

    def setUp(self):
        global server
        server = slapd.Slapd()
        server.set_port(38911)
        server.start()
        base = server.get_dn_suffix()
        server.ldapadd("\n".join(test_ldif)+"\n")
        call_command('loaddata', 'karaage_data', **{'verbosity': 0})
        self.server = server
        form_data = {
            'title' : 'Mr',
            'first_name': 'Sam',
            'last_name': 'Morrison2',
            'position': 'Sys Admin',
            'institute': 1,
            'department': 'eddf',
            'email': 'sam@vpac.org',
            'country': 'AU',
            'telephone': '4444444',
            'username': 'samtest2',
            'password1': 'Exaiquouxei0',
            'password2': 'Exaiquouxei0',
            'needs_account': False,
            }
        self.client.login(username='kgsuper', password='aq12ws')
        response = self.client.post(reverse('kg_add_user'), form_data)
        self.failUnlessEqual(response.status_code, 302)


    def tearDown(self):
        self.server.stop()

    def test_add_useraccount(self):

        response = self.client.get(reverse('kg_add_useraccount', args=['samtest2']))
        self.failUnlessEqual(response.status_code, 200)
        
        form_data = {
            'machine_category': 1,
            'default_project': 'TestProject1',
            }
            
        response = self.client.post(reverse('kg_add_useraccount', args=['samtest2']), form_data)
        self.failUnlessEqual(response.status_code, 302)
        person = Person.objects.get(user__username="samtest2")
        lcon = LDAPClient()
        luser = lcon.get_user('uid=samtest2')
        self.assertEqual(luser.objectClass, settings.ACCOUNT_OBJECTCLASS)
        self.assertTrue(person.has_account(MachineCategory.objects.get(pk=1)))

    def test_fail_add_useraccounts_username(self):
        form_data = {
            'machine_category': 1,
            'default_project': 'TestProject1',
            }          
        response = self.client.post(reverse('kg_add_useraccount', args=['samtest2']), form_data)
        self.failUnlessEqual(response.status_code, 302)
        
        response = self.client.post(reverse('kg_add_useraccount', args=['samtest2']), form_data)
        self.assertContains(response, "Username already in use")


    def test_fail_add_useraccounts_project(self):
        form_data = {
            'machine_category': 1,
            'default_project': 'TestProject1',
            }          
        response = self.client.post(reverse('kg_add_useraccount', args=['samtest2']), form_data)
        self.failUnlessEqual(response.status_code, 302)

        form_data = {
            'machine_category': 2,
            'default_project': 'TestProject1',
            }

        response = self.client.post(reverse('kg_add_useraccount', args=['samtest2']), form_data)
        self.assertContains(response, "Default project not in machine category")


    def test_lock_unlock_account(self):
        response = self.client.get(reverse('kg_add_useraccount', args=['samtest2']))
        self.failUnlessEqual(response.status_code, 200)
        
        form_data = {
            'username': 'samtest2',
            'machine_category': 1,
            'default_project': 'TestProject1',
            }
            
        response = self.client.post(reverse('kg_add_useraccount', args=['samtest2']), form_data)
        self.failUnlessEqual(response.status_code, 302)
        person = Person.objects.get(user__username='samtest2')
        ua = person.get_user_account(MachineCategory.objects.get(pk=1))
        
        self.failUnlessEqual(person.is_locked(), False)
        self.failUnlessEqual(ua.loginShell(), '/bin/bash')

        response = self.client.get(reverse('kg_lock_user', args=['samtest2']))
        self.failUnlessEqual(person.is_locked(), True)
        self.failUnlessEqual(ua.loginShell(), settings.LOCKED_SHELL)

        response = self.client.get(reverse('kg_unlock_user', args=['samtest2']))
        self.failUnlessEqual(person.is_locked(), False)
        self.failUnlessEqual(ua.loginShell(), '/bin/bash')


class MachineTestCase(TestCase):

    def setUp(self):
        global server
        server = slapd.Slapd()
        server.set_port(38911)
        server.start()
        base = server.get_dn_suffix()
        server.ldapadd("\n".join(test_ldif)+"\n")
        call_command('loaddata', 'karaage_data', **{'verbosity': 0})

        self.server = server
        today = datetime.datetime.now()
        # 10cpus
        mach1 = Machine.objects.get(pk=1)
        mach1.start_date = today - datetime.timedelta(days=80)
        mach1.save()
        # 40 cpus
        mach2 = Machine.objects.get(pk=2)
        mach2.start_date = today - datetime.timedelta(days=100)
        mach2.end_date = today - datetime.timedelta(days=20)
        mach2.save()
        # 8000 cpus
        mach3 = Machine.objects.get(pk=3)
        mach3.start_date = today - datetime.timedelta(days=30)
        mach3.save()

    def tearDown(self):
        self.server.stop()

    def do_availablity_test(self, start, end, mc, expected_time, expected_cpu):
        from karaage.util.helpers import get_available_time
        available_time, avg_cpus = get_available_time(start.date(), end.date(), mc)
        self.failUnlessEqual(avg_cpus, expected_cpu)
        self.failUnlessEqual(available_time, expected_time)
        
    def test_available_time(self):
        from karaage.util.helpers import get_available_time
        mc1 = MachineCategory.objects.get(pk=1)
        mc2 = MachineCategory.objects.get(pk=2)
        for machine in Machine.objects.all():
            machine.category = mc1
            machine.save()
            
        day = 60*60*24
        today = datetime.datetime.now()
        
        end = today - datetime.timedelta(days=20)
        start = today - datetime.timedelta(days=30)
        self.do_availablity_test(start, end, mc1, 8050*day*11, 8050)
        
        start = today - datetime.timedelta(days=99)
        end = today - datetime.timedelta(days=90)
        self.do_availablity_test(start, end, mc1, 40*day*10, 40)

        start = today - datetime.timedelta(days=85)
        end = today - datetime.timedelta(days=76)
        self.do_availablity_test(start, end, mc1, 45*day*10, 45)

        start = today - datetime.timedelta(days=35)
        end = today - datetime.timedelta(days=16)
        self.do_availablity_test(start, end, mc1, 6042*day*20, 6042)

        start = today - datetime.timedelta(days=20)
        end = today - datetime.timedelta(days=20)
        self.do_availablity_test(start, end, mc1, 8050*day, 8050)
