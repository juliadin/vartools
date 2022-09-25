# Ansible Collection - juliadin.vartools

## Motivation

When using ansible for continuous system management, I often found myself using cascaded combines to layer information in my platform:

- provide sane defaults in the role
- set infrastructure specific defaults in `group_vars/all`
- set specific settings per location, group, purpose of system on `group_vars/<groupname>`
- set host overrides in `host_vars/<hostname>`
 
This works very well when using primitive data types but when using dicts, since the `hash_behaviour=merge` is no longer to be used, I found a lot of this in my roles:

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

## Lookups and limitations

using a lookup means I have to return a list. That makes the [0] after the lookup necessary to get the merged result.

The lookup always returns 2 items:

0. The merged result. Even if no variable matches, this is at least the empty dict `{}` so using it without the default filter should be safe.
0. Information about the merged items as a list. Each item contains:
   - a dict with the item `regex`, containing the regex that was tried and 
   - the item `names`, containing a list with all the variable names that were matched and merged.

## Patterns explained:
  - **d** - is intended for sane role defaults that are not environment specific
  - **r** - is intended for roles that include the role using the variable. Example: I would expect `debian_repos_pins_r000_qemu_from_testing` to appear in role `kvm` as a default when it includes the `debian_repo` role. Careful: these are only available while including!
  - **a** - is intended to be set in `group_vars/all` as environment specific defaults
  - **g** - is intended for `group_vars/<group>` to override/extend values
  - **h** - is intended for `host_vars/<hostname>` to set host specific overrides

The legacy pattern catches the name itself for backwards compatibility.

Examples for the `default` patterns I recommend:
  - `<rolename>_<var>_d000_role_defaults`
  - `<rolename>_<var>_a000_group_all`
  - `<rolename>_<var>_g500_<group>_allow_testing_repo_on_dev`
  - `<rolename>_<var>_h500`

use numbers to irder 

### Legacy patterns:

- "^d_apache_vhosts$"
- "^d[0-9]+_apache_vhosts$"
- "^r_apache_vhosts$"
- "^r[0-9]+_apache_vhosts$"
- "^apache_vhosts$"
- "^a_apache_vhosts$"
- "^a[0-9]+_apache_vhosts$"
- "^g_apache_vhosts$"
- "^g[0-9]+_apache_vhosts$"
- "^h_apache_vhosts$"
- "^h[0-9]+_apache_vhosts$"

### Default patterns:

- "^apache_vhosts_d_\\S+$"
- "^apache_vhosts_d[0-9]+_\\S+$"
- "^apache_vhosts_r_\\S+$"
- "^apache_vhosts_r[0-9]+_\\S+$"
- "^apache_vhosts_a_\\S+$"
- "^apache_vhosts_a[0-9]+_\\S+$"
- "^apache_vhosts_g_\\S+$"
- "^apache_vhosts_g[0-9]+_\\S+$"
- "^apache_vhosts_h_\\S+$"
- "^apache_vhosts_h[0-9]+_\\S+$"

Additional regexes can be provided as positional arguments.

### Precedence

last merge wins:
1. merged matches for legacy patterns in order
1. merged matches for default patterns in order
1. merged matches for positional argument regexes in order

