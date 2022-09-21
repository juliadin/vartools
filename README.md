# Ansible Collection - juliadin.vartools

## Motivation

When using ansible for continuous system management, I often found myself using cascaded combines to layer information in my platform:

- provide sane defaults in the role
- set infrastructure specifig defaults in `group_vars/all`
- set specific settings per location, group, purpose of system on `group_vars/<groupname>`
- set host overrides in `host_vars/<hostname>`
 
This works very well when using primirive data types but when using dicts, since the `hash_behaviour=merge` is no longer to be used, I found a lot of this in my roles:

    - name: Merge variables from global, host, group
      ansible.builtin.set_fact:
        apache_vhosts: "{{
                          d_apache_vhosts | default({}) |
                    combine(apache_vhosts | default({}), recursive=True) |
                  combine(a_apache_vhosts | default({}), recursive=True) |
                  combine(g_apache_vhosts | default({}), recursive=True) |
                  combine(h_apache_vhosts | default({}), recursive=True)
                  }}"

This is - while very explicit - tedious and each new layer requires modification of the role. I didn't like that.

Unaware of any easy solutions for this, I tried automating this. The lookup plugin provided can collect variables based on regex patterns or two predfined naming schemes (legacy / default) and output the result ready to be used in any jinja templated variable - in set_fact for example, to simulate something akin to hash_behaviour=merge on a per-variable-basis:

    - name: Merge variables from global, host, group
      ansible.builtin.set_fact:
        apache: "{{ lookup( 'juliadin.vartools.merge', legacy='apache_vhosts', default='apache_vhosts')[0] }}"

Which replaces the above set_fact by

- looking for variables matching the following patterns
- sorting the matches for each pattern alphabetically
- merging all found variables in the resulting order

Legacy patterns:

- "^d_apache_vhosts$"
- "^d[0-9]+_apache_vhosts$"
- "^apache_vhosts$"
- "^a_apache_vhosts$"
- "^a[0-9]+_apache_vhosts$"
- "^g_apache_vhosts$"
- "^g[0-9]+_apache_vhosts$"
- "^h_apache_vhosts$"
- "^h[0-9]+_apache_vhosts$"

Default patterns:

- "^apache_vhosts_d_\\S+$"
- "^apache_vhosts_d[0-9]+_\\S+$"
- "^apache_vhosts_a_\\S+$"
- "^apache_vhosts_a[0-9]+_\\S+$"
- "^apache_vhosts_g_\\S+$"
- "^apache_vhosts_g[0-9]+_\\S+$"
- "^apache_vhosts_h_\\S+$"
- "^apache_vhosts_h[0-9]+_\\S+$"

Additional regexes can be provided as positional arguments.

Precedence is as follows (last wins):

1. merged matches for legacy patterns in order
1. merged matches for default patterns in order
1. merged matches for positional argument regexes in order

