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

from karaage.datastores.software import base


class SoftwareDataStore(base.SoftwareDataStore):
    
    def create_software(self, software):
        pass

    def delete_software(self, software):
        pass

    def add_member(self, software, person):
        pass

    def remove_member(self, software, person):
        pass

    def get_members(self, software):
        pass

    def get_name(self, software):
        pass
