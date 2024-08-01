"""Ansible AutoDoc module initializer."""
from .ansibleautodoc import AnsibleTaskDirective

def setup(app):
    """Set up the Sphinx extension."""
    classes = [
        AnsibleTaskDirective,
    ]
    for directive_class in classes:
        app.add_directive(directive_class.directive_name, directive_class)
