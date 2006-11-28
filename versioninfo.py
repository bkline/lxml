import os, sys, re

__LXML_VERSION = None

def version():
    global __LXML_VERSION
    if __LXML_VERSION is None:
        __LXML_VERSION = open(os.path.join(get_src_dir(), 'version.txt')).read().strip()
    return __LXML_VERSION

def branch_version():
    return version()[:3]

def svn_version():
    _version = version()
    src_dir = get_src_dir()

    revision = 0
    base_url = None
    urlre = re.compile('url="([^"]+)"')
    revre = re.compile('committed-rev="(\d+)"')

    for base, dirs, files in os.walk(src_dir):
        if '.svn' not in dirs:
            dirs[:] = []
            continue    # no sense walking uncontrolled subdirs
        dirs.remove('.svn')
        f = open(os.path.join(base, '.svn', 'entries'))
        data = f.read()
        f.close()

        if data.startswith('8'):
            data = map(str.splitlines, data.split('\n\x0c\n'))
            del data[0][0] # get rid of the '8'
            dirurl = data[0][3]
            localrev = max([int(d[9]) for d in data if len(d)>9 and d[9]])
        elif data.startswith('<?xml'):
            dirurl = urlre.search(data).group(1)    # get repository URL
            localrev = max([int(m.group(1)) for m in revre.finditer(data)])
        else:
            from warnings import warn
            warn("unrecognized .svn/entries format; skipping "+base)
            dirs[:] = []
            continue
        if base_url is None:
            base_url = dirurl+'/'   # save the root url
        elif not dirurl.startswith(base_url):
            dirs[:] = []
            continue    # not part of the same svn tree, skip it
        revision = max(revision, localrev)


    if revision:
        result = _version + '-' + str(revision)

    if 'dev' in _version:
        result = fix_alphabeta(result, 'dev')
    elif 'alpha' in _version:
        result = fix_alphabeta(result, 'alpha')
    if 'beta' in _version:
        result = fix_alphabeta(result, 'beta')

    return result

def dev_status():
    _version = version()
    if 'dev' in _version:
        return 'Development Status :: 3 - Alpha'
    elif 'alpha' in _version:
        return 'Development Status :: 3 - Alpha'
    elif 'beta' in _version:
        return 'Development Status :: 4 - Beta'
    else:
        return 'Development Status :: 5 - Production/Stable'

def changes():
    """Extract part of changelog pertaining to version.
    """
    _version = version()
    f = open(os.path.join(get_src_dir(), "CHANGES.txt"), 'r')
    lines = []
    for line in f:
        if line.startswith('====='):
            if len(lines) > 1:
                break
        if lines:
            lines.append(line)
        elif line.startswith(_version):
            lines.append(line)
    f.close()
    return ''.join(lines[:-1])

def create_version_h(svn_version):
    """Create lxml-version.h
    """
    version_h = open(
        os.path.join(get_src_dir(), 'src', 'lxml', 'lxml-version.h'),
        'w')
    version_h.write('''\
#ifndef LXML_VERSION_STRING
#define LXML_VERSION_STRING "%s"
#endif
''' % svn_version)
    version_h.close()

def get_src_dir():
    return os.path.join(os.getcwd(), os.path.dirname(sys.argv[0]))

def fix_alphabeta(version, alphabeta):
    if ('.' + alphabeta) in version:
        return version
    return version.replace(alphabeta, '.' + alphabeta)
