# -*- coding: utf-8 -*-
"""Ansible AutoDoc module."""
from __future__ import division, print_function, absolute_import

from pathlib import Path
from pathlib import PurePath
import os
import pickle
from docutils import nodes
from docutils.parsers import rst
from docutils.parsers.rst import Directive
from sphinx.util.logging import SphinxLoggerAdapter

from loguru import logger

from ruamel.yaml import YAML

from .i18n import texts

logger.add(SphinxLoggerAdapter)
logger.critical('this is the ansible autodoc extension')

def is_same_mtime(path1, path2):
    """Check for an exact match for modification time in two paths.

    :param str path1: The first path to check.
    :param str path2: The second path to check.
    """
    ret_value = False
    mtime1 = os.stat(path1).st_mtime
    mtime2 = os.stat(path2).st_mtime
    ret_value = mtime1 == mtime2
    return ret_value


def basename(path):
    """Return the filename of a path.

    :str path:
    """
    filename = PurePath(path)
    logger.debug(filename)
    return filename

class Task():
    """Define Task objects."""

    role_name = None
    def __init__(self, filename, name, args, role_name=None):
        self.filename = filename
        self.name = name
        self.args = args
        if role_name:
            self.role_name = role_name
            logger.debug(role_name)

    def __str__(self):
        return f'{self.filename}, {self.name}, {self.role_name}'

    def make_arg_simple(self, key, value):
        """Return a simplified argument."""
        name = nodes.field_name(text=key)
        body = nodes.field_body()
        body.append(nodes.emphasis(text=value))
        field = nodes.field()
        field += [name, body]
        return field

    def make_list_representation(self, value):
        """Return a representation of a list."""
        bl = nodes.bullet_list()
        if isinstance(value, list):
            for v in value:
                body = nodes.literal(text=v)
                bl.append(nodes.list_item('', body))
        elif isinstance(value, dict):
            for k,v in value.items():
                body = nodes.literal(text=f'{k}={v}')
                bl.append(nodes.list_item('', body))
        return bl

    def make_arg_complex(self, key, value):
        """Return a complex argument."""
        bl = self.make_list_representation(value)
        name = nodes.field_name(text=key)
        body = nodes.field_body()
        body.append(bl)
        field = nodes.field()
        field += [name, body]
        return field

    def make_node(self, lang='en'):
        """Create a document object model node."""
        arg_map = texts[lang]["arg_map"]
        task_title = texts[lang]["task_title"]
        logger.debug(task_title)
        module_title = texts[lang]["module_title"]

        module_args = {}

        # Search task definition for modules and associated arguments.
        for key, value in self.args.items():
            if key not in arg_map.keys():
                module_args[key] = value

        # Create task node (using type: admonition)
        item = nodes.admonition()
        title = nodes.title(text=self.name)
        item.append(title)

        # Add modules and arguments to task node
        for module, args in module_args.items():
            field_list = nodes.field_list() # wrap module header in field_list
            field_list.append(self.make_arg_simple(module_title, module))
            item.append(field_list)
            if isinstance(args, str):
                item.append(nodes.literal_block(text=args))
            else:
                item.append(self.make_list_representation(args))

        # Handle non-module task parameters.
        field_list = nodes.field_list()
        for arg, txt in arg_map.items():
            if not txt:  # skip name etc...
                continue
            if arg not in self.args:
                continue
            value = self.args[arg]  # value of that task arg
            if isinstance(value, list) or isinstance(value, dict):
                field_list.append(self.make_arg_complex(txt, value))
            else:
                field_list.append(self.make_arg_simple(txt, value))

        item.append(field_list)

        return item

class AutodocCache(object):
    """Define AutodocCache objects."""
    _cache = {}
    yml = YAML(typ='rt')

    def parse_include(self, filename, include, role_name=None):
        """Parse an included file."""
        if role_name:
            include_file = Path(f'roles/{role_name}/tasks/{include}')
            logger.debug(include_file)
        else:
            include_file = Path(include)
            logger.info(include_file)

        with include_file.open('r', encoding='utf-8') as if_fh:
            for task in self.yml.load_all(if_fh):
                self.parse_task(filename, task, role_name)

    def parse_role(self, filename, role):
        """Parse a role."""
        ret_value = None

        role_path = Path(f'roles/{role}/tasks/{filename}')

        with role_path.open('r', encoding='utf-8') as rp_fh:
            for task in self.yml.load(rp_fh):
                self.parse_task(filename, task, role['role'])
        return ret_value

    def parse_task(self, filename, task, role_name=None):
        """Parse a task."""
        if 'include' in task:
            self.parse_include(filename, task['include'], role_name)
            return
        if 'name' not in task:
            return
        t = Task(filename, task['name'], task, role_name)
        self._cache[filename].append(t)

    def parse_play(self, filename, play):
        """Parse a play."""
        if 'tasks' in play:
            for task in play['tasks']:
                self.parse_task(filename, task)
        if 'roles' in play:
            for role in play['roles']:
                self.parse_role(filename, role)

    def walk(self, filename, role=None):
        """Walk a directory for files."""
        file_path = Path(filename)
        assert role is None
        if filename not in self._cache:
            # use list because there might be same task name
            self._cache[filename] = []

        with file_path.open('r', encoding='utf-8') as fp_fh:
            for play in self.yml.load_all(fp_fh):
                self.parse_play(filename, play)

    def get(self, filename, taskname, role_name=None):
        """Get a task."""
        if filename not in self._cache:
            return None
        for t in self._cache[filename]:
            if t.name == taskname:
                if role_name and t.role_name != role_name:
                    continue
                return t
        return None

    def parse(self, basedir, filename):
        """Parse a file name object."""
        cachename = str(Path(f'{basedir}/{filename}'))
        if is_same_mtime(filename, cachename):
            self._cache = pickle.load(open(cachename, 'rb'))
        else:
            self.walk(filename)
            with open(cachename, 'wb') as f:
                pickle.dump(self._cache, f)
            mtime = os.stat(filename).st_mtime
            os.utime(cachename, (mtime, mtime))

class AnsibleTaskDirective(Directive):
    """Define AnsibleTaskDirective objects."""
    directive_name = "ansibletask"

    _cache = AutodocCache()

    has_content = True
    option_spec = {
        'playbook': rst.directives.unchanged_required,
        'role': rst.directives.unchanged,
    }
    task = False

    def run(self):
        self.assert_has_content()
        dir_env = self.state.document.settings.env
        ret_value = []
        role = None

        if 'playbook' not in self.options:
            msg = 'playbook option is required '
            self.state_machine.reporter.warning(msg, line=self.lineno)

        # basedir = dir_env.doctreedir
        filename = self.options['playbook']
        # self._cache.parse(basedir, filename)

        if 'role' in self.options:
            role = self.options['role']
        else:
            role = 'none'

        taskname = "".join(self.content)
        self.task = self._cache.get(filename, taskname, role)
        if not self.task:
            msg = f'filename: {filename}, taskname: {taskname} is not found'
            self.state_machine.reporter.warning(msg, line=self.lineno)
            ret_value = []

        lang = dir_env.config.language
        if not lang:
            lang = 'en'

        if self.task:
            ret_value = [self.task.make_node(lang)]

        return ret_value
