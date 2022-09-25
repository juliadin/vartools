# (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = """
    name: merge
    author: Julia Brunenberg <julia@jjim.de>
    short_description: Find variables matching the patterns, sort and merge them recursively
    description:
      - Find variables matching the patterns, sort and merge them recursively
      - The matches for each regex will be sorted and added to a list.
      - The variable names in the list will be recursively combined in the resulting order
      - last value wins
    options:
      _terms:
        description: List of Python regex patterns to search for in variable names.
        required: True
      list_merge:
        description: Behavior to pass to combine() for merging lists. See combine filter
        required: False
        default: 'replace'
      recursive:
        description: Behavior to pass to combine() merging dicts recursive. See combine filter
        required: False
        default: True
      legacy:
        description: start with generating patterns for legacy depops scheme (d_*, a_*, g_* g[0-9]_*, h_*) for string
        required: False
        type: str
      default:
        description: start with generating patterns for legacy depops scheme (*_d[0-9]+_*, *_a[0-9]+_*, *_g[0-9]+_*, *_h[0-9]+_*) for string
        required: False
        type: str
"""

EXAMPLES = """
- name: Merge Variables that start with 'myval_'
  ansible.builtin.debug: msg="{{ lookup('juliadin.vartools.merge', '^myval_.+')[0] }}"

- name: Merge Variables that start with 'myval_', THEN merge in variables starting with myvaldev_
  ansible.builtin.debug: msg="{{ lookup('juliadin.vartools.merge', '^myval_.+', '^myvaldev_.+')[0] }}"

- name: Details about the merge of variables that start with 'myval_', THEN merge in variables starting with myvaldev_
  ansible.builtin.debug: msg="{{ lookup('juliadin.vartools.merge', '^myval_.+', '^myvaldev_.+')[1] }}"

"""

RETURN = """
_value:
  description:
    - List of:
    -  - Merged dictionary
    -  - Details about merge order
  type: list
"""

import re

from ansible.errors import AnsibleError
from ansible.module_utils._text import to_native
from ansible.module_utils.six import string_types
from ansible.plugins.lookup import LookupBase
from ansible.plugins.filter.core import combine


class LookupModule(LookupBase):

    def run(self, terms=[], variables=None, **kwargs):

        variables = getattr(self._templar, '_available_variables', {})
        h_variables = variables['hostvars'][variables['inventory_hostname']]

        if variables is None:
            raise AnsibleError('No variables available to search')

        list_merge = kwargs.pop('list_merge', 'replace')
        recursive = kwargs.pop('recursive', True)
        legacy = kwargs.pop('legacy', None)
        default = kwargs.pop('default', None)

        if kwargs:
            raise AnsibleError("'recursive' and 'list_merge' are the only valid keyword arguments")

        self.set_options(var_options=variables, direct=kwargs)

        legacy_patterns = []
        if legacy:
            for pattern in ['d_', 'd[0-9]+_', 'r_', 'r[0-9]+_', '', 'a_', 'a[0-9]+_', 'g_', 'g[0-9]+_', 'h_', 'h[0-9]+_']:
                legacy_patterns.append(r'^{}{}$'.format(pattern, legacy))

        default_patterns = []
        if default:
            for pattern in ['d', 'r', 'a', 'g', 'h']:
                default_patterns.append(r'^{}_{}((([0-9]+)?(_(\S+)?$|$))|$)'.format(default, pattern))

        names = []
        ret_names = {}
        variable_names = list(variables.keys())
        index = 0
        for term in legacy_patterns + default_patterns + terms:
            these_names = []
            debug_dict = {
                'regex': term,
                'names': []
            }
            if not isinstance(term, string_types):
                raise AnsibleError('Invalid setting identifier, "%s" is not a string, it is a %s' % (term, type(term)))

            try:
                name = re.compile(term)
            except Exception as e:
                raise AnsibleError('Unable to use "%s" as a search parameter: %s' % (term, to_native(e)))

            for varname in variable_names:
                if name.search(varname):
                    these_names.append(varname)

            names.extend(sorted(these_names))
            debug_dict['names'] = sorted(these_names)

            ret_names[index] = debug_dict

            index = index + 1

        values = [{}]
        for name in names:
            try:
                value = h_variables[name]
            except KeyError:
                try:
                    value = variables[name]
                except KeyError:
                    raise AnsibleError('Unable to find variable {}, it should be there though'.format(name))
            if isinstance(value, dict):
                values.append(self._templar.template(value, fail_on_undefined=True))

        return [combine(values, recursive=recursive, list_merge=list_merge), ret_names]
