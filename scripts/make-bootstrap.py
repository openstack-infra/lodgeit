#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    Lodgeit Bootstrap Creation Script
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Creates a bootstrap script for LodgeIt
"""
from virtualenv import create_bootstrap_script


EXTRA_TEXT = """
import os

def after_install(options, home_dir):
    easy_install('Jinja2', home_dir)
    easy_install('Werkzeug', home_dir)
    easy_install('Pygments', home_dir)
    easy_install('SQLAlchemy==0.6', home_dir)
    easy_install('simplejson', home_dir)
    easy_install('Babel', home_dir)
    easy_install('PIL', home_dir)


def easy_install(package, home_dir, optional_args=None):
    optional_args = optional_args or []
    cmd = [os.path.join(home_dir, 'bin', 'easy_install')]
    cmd.extend(optional_args)
    # update the environment
    cmd.append('-U')
    cmd.append(package)
    call_subprocess(cmd)
"""

if __name__ == '__main__':
    print create_bootstrap_script(EXTRA_TEXT)
