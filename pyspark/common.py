import os
import sys
import re
import subprocess
import getpass
import datetime as dt
try:
    import ConfigParser
except:
    import configparser as ConfigParser
import logging
import shutil
import xml.etree.ElementTree as ET
import json
from distutils.spawn import find_executable
from threading import Timer
from collections import Counter

# Create Logger
LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.DEBUG)

# Create Handler
consoleHandler = logging.StreamHandler()
consoleHandler.setLevel(logging.DEBUG)

# Setting format
format = logging.Formatter("%(asctime).19s %(levelname)s %(filename)s:%(lineno)s: %(message)s ")

# Add formatter
consoleHandler.setFormatter(format)

# Add handler to logger
LOGGER.addHandler(consoleHandler)


def which(cmd, path=None):
    if hasattr(shutil, 'which'):
        return shutil.which(cmd, path=path)
    elif path is None and os.environ.get('PATH') is None:
        return None
    else:
        return find_executable(cmd, path=path)


def unique(items):
    """ Yield items from *item* in order, skipping duplicates. """
    seen = set()
    for item in items:
        if item in seen:
            continue
        else:
            yield item
            seen.add(item)


def run_cmd(arg_lists, ok_returncodes=None, ok_stderr=None, return_stdout=False, return_response=False, timeout_sec=10):
    try:
        response = {}
        LOGGER.debug('Executing: {0}'.format(' '.join(arg_lists)))
        proc = subprocess.Popen(arg_lists, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        def kill_proc(proc): return proc.kill()
        timer = Timer(timeout_sec, kill_proc, [proc])
        try:
            timer.start()
            stdout, stderr = proc.communicate()
            status_code = proc.returncode
        finally:
            timer.cancel()

        stdout = stdout.rstrip(b'\r\n')
        stderr = stderr.rstrip(b'\r\n')
        t = zip(('status_code', 'output', 'error'), (status_code, stdout, stderr))
        response = dict(t)

        stderror_is_ok = False
        if ok_stderr:
            for stderr_re in ok_stderr:
                if stderr_re.match(stderr):
                    stderr_is_ok = True
                    break

        ok_returncodes = ok_returncodes or [0]

        if not stderr_is_ok and status_code not in ok_returncodes:
            if stderr:
                LOGGER.error(stderr)
            raise subprocess.CalledProcessError(status_code, arg_lists, stdout)

        if return_response:
            return response
        elif return_stdout:
            return stdout
        else:
            return status_code

    except OSError as e:
        LOGGER.error("Failed to execute %s : %s" % (' '.join(arg_lists), str(e)))


def config(filename, section=None):
    param_dict = {}
    config_parser = ConfigParser.ConfigParser()
    config_parser.optionxform = str
    if os.path.exists(filename):
        config_parser.read(filename)

    sections = []
    if not section:
        sections = config_parser.sections()
    else:
        sections = [section]

    for section in sections:
        params = config_parser.option(section)

        for param in params:
            try:
                params[param] = config_parser.get(section, param)
                if params[param] == -1:
                    LOGGER.debug("skip: %s" % param)
            except:
                LOGGER.exception("exception on %s!" % param)
                params[param] = None
        LOGGER.debug("Initializing %s parameters" % section)
    LOGGER.debug("Parameters initialized:\n %s" % params)

    return params


def get_config_dict(*args, **kwargs):
    params = {}
    runtimes = {}
    params = config(*args, **kwargs)
    runtimes = get_runtime()
    params.update(runtimes)
    return params


def get_file_extension(filename):
    dot_idx = filename.rfind('.')
    if dot_idx == -1:
        return ''
    else:
        return filename[dot_idx:]


def remove_extenstion(file):
    filename = os.path.basename(file)
    extension = get_file_extension(filename)
    idx = filename.idx(extension)
    if extension:
        return filename[:idx]
    else:
        return filename


def resolve_param(content, parameters, *args, **kwargs):
    params = re.findall(r'(\$\{?\w+\}?)', content)
    for param in params:
        try:
            key = re.findall(r'(\$\{?\w+\}?)', param)
            val = params[key[0]]
            content = content.replace(param, val)
        except Exception as e:
            LOGGER.exception('Unable to resolve parameter: %s' % e)
            return
    return content


def remove_xml_ns(xml):
    return re.sub(r'{.+?}', '', xml)


def make_dict_from_tree(element_tree):
    def internal_iter(tree, accum):
        if tree is None:
            return accum

        if tree.getchildren():
            accum[remove_xml_ns(tree.tag)] = {}
            for each in tree.getchildren():
                result = internal_iter(each, {})
                if each.tag in accum[remove_xml_ns(tree.tag)]:
                    if not isinstance(accum[tree.tag][each.tag], list):
                        accum[remove_xml_ns(tree.tag)][each.tag] = [accum[tree.tag][each.tag]]
                    accum[tree.tag][each.tag].append(result[each.tag])
                else:
                    accum[remove_xml_ns(tree.tag)].update(result)
        else:
            accum[remove_xml_ns(tree.tag)] = tree.text
        return accum

    return internal_iter(element_tree, {})


def get_xpath(paths, element=None, attr=None):
    leaf = element if element else '@' + attr
    if leaf in paths:
        paths = paths[:len(paths) - (len(paths) - paths.index(leaf)) + 1]
    else:
        paths.append(leaf)

    return ('/' + ('/').join(paths))


def update_paths(paths, element):
    if not paths:
        paths.append(element)
    elif element not in paths:
        paths.append(element)
    else:
        paths = paths[:len(paths) - (len(paths) - paths.index(element)) + 1]

    return (paths)


def xml2dict_schema(element_tree):
    def internal_iter(tree, key, prefix, paths):
        count = Counter(child.tag for child in tree)

        for child in tree.getchildren():
            tree_tag = remove_xml_ns(tree.tag)
            child_tag = remove_xml_ns(child.tag)
            paths = update_paths(paths, tree_tag)
            print (paths)
            tree_xpath = get_xpath(paths, element=tree_tag)
            child_xpath = get_xpath(paths, element=child_tag)
            # print(f'Counter = {count[child.tag]} and {len(child.getchildren())} and Tree = {tree_tag} Child = {child_tag} [{prefix} ({key})]')
            '''Array'''
            if count[child.tag] > 1:
                if len(child.getchildren()) > 1:
                    ''' Array with Structure '''
                    if child_tag not in accum:
                        accum[child_xpath] = {}
                else:
                    ''' Array of Elements '''
                    if tree_xpath not in accum:
                        accum[tree_xpath] = {}
                    if child_xpath not in accum[tree_xpath]:
                        accum[tree_xpath][child_xpath] = child_xpath

                key = child_xpath
                prefix = None
            else:
                ''' Leaf '''
                if len(child.getchildren()) > 0:
                    prefix = child_tag if (key is None and prefix is None) or (tree_tag != key) or (prefix != child_tag) else None
                    if tree_xpath in accum:
                        key = tree_xpath

                element = prefix + '_' + child_tag if prefix and prefix != child_tag else child_tag

                if not key:
                    key = tree_xpath
                    if key not in accum:
                        accum[key] = {}

                # print(f'({prefix} => {tree_tag} => {child_tag}')
                if len(child.getchildren()) == 0:
                    ''' child_xpath is element '''
                    if child_xpath not in accum[key]:
                        accum[key][child_xpath] = element

                for attr in child.attrib.keys():
                    attr_xpath = get_xpath(paths, attr=attr)
                    attr_tag = element + '_' + remove_xml_ns(attr)
                    if attr_xpath not in accum:
                        accum[key][attr_xpath] = attr_tag

            internal_iter(child, key, prefix, paths)

        return accum

    accum = {}
    return internal_iter(element_tree, None, None, [])


def xml2json(xml_file, *args, **kwargs):
    with open(xml_file, 'r') as f:
        return json.dumps(xml2dict_schema(ET.fromstring(f.read())), indent=4, sort_keys=True, ensure_ascii=False)


def write_xml2json(xml_file, json_file, *args, **kwargs):
    print ('Genertaing JSON')
    with open(json_file, 'w') as f:
        f.write(xml2json(xml_file))
    f.close()


def get_user():
    return getpass.getuser().lower()


def get_user_home_dir():
    return os.path.expanduser('~')


def get_cwd():
    os.path.normpath(os.getcwd())


def get_script_name():
    return os.path.abspath(__file__)


def get_ini_file(ini_file=None):
    if not ini_file:
        ini_file = get_default_ini()
    elif not os.path.exists(ini_file):
        raise IOError('INI file not found: %s' % (ini_file))

    return ini_file
