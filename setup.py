#!/usr/bin/env python3
import os
from setuptools import setup

BASEDIR = os.path.abspath(os.path.dirname(__file__))


def required(requirements_file):
    """ Read requirements file and remove comments and empty lines. """
    with open(os.path.join(BASEDIR, requirements_file), 'r') as f:
        requirements = f.read().splitlines()
        if 'MYCROFT_LOOSE_REQUIREMENTS' in os.environ:
            print('USING LOOSE REQUIREMENTS!')
            requirements = [r.replace('==', '>=').replace('~=', '>=') for r in requirements]
        return [pkg for pkg in requirements
                if pkg.strip() and not pkg.startswith("#")]


with open("README.md", "r") as f:
    long_description = f.read()


with open("./version.py", "r", encoding="utf-8") as v:
    for line in v.readlines():
        if line.startswith("__version__"):
            if '"' in line:
                version = line.split('"')[1]
            else:
                version = line.split("'")[1]


PLUGIN_ENTRY_POINT = 'ovos-solver-failure-plugin=ovos_solver_chatgpt_plugin:ChatGPTSolver'
setup(
    name='ovos-solver-failure-plugin',
    version=version,
    description='A question solver plugin for ovos/neon/mycroft',
    url='https://github.com/OpenVoiceOS/ovos-solver-plugin-chatgpt',
    author='jarbasai',
    author_email='jarbasai@mailfence.com',
    license='MIT',
    packages=['ovos_solver_chatgpt_plugin'],
    zip_safe=True,
    keywords='mycroft plugin utterance fallback query',
    entry_points={'neon.plugin.solver': PLUGIN_ENTRY_POINT},
    install_requires=required("requirements.txt"),
    long_description=long_description,
    long_description_content_type='text/markdown'
)
