"""Generate a limited CSP Report-Only draft from explicit source lists."""
import argparse
import json
from pathlib import Path
import re

ORDER = ('default-src', 'script-src', 'style-src', 'img-src', 'connect-src', 'font-src', 'object-src', 'base-uri', 'frame-ancestors')
ORIGIN = re.compile(r'https://[a-z0-9](?:[a-z0-9-]*[a-z0-9])?(?:\.[a-z0-9](?:[a-z0-9-]*[a-z0-9])?)*(?::[1-9][0-9]{0,4})?')


def build(config):
    if type(config) is not dict or not config or set(config) - set(ORDER):
        raise ValueError('provide a nonempty object using only supported directives')
    if 'default-src' not in config:
        raise ValueError('default-src must be explicit')
    parts = []
    for name in ORDER:
        if name not in config:
            continue
        sources = config[name]
        if type(sources) is not list or not 1 <= len(sources) <= 20:
            raise ValueError(f'{name}: provide 1–20 sources')
        for source in sources:
            if type(source) is not str or len(source) > 255:
                raise ValueError(f'{name}: invalid source')
            if source not in ("'self'", "'none'"):
                if not ORIGIN.fullmatch(source):
                    raise ValueError(f'{name}: only self, none or lowercase HTTPS origins are supported')
                if ':' in source[8:] and int(source.rsplit(':', 1)[1]) > 65535:
                    raise ValueError(f'{name}: invalid port')
        if "'none'" in sources and len(sources) != 1:
            raise ValueError(f'{name}: none must appear alone')
        if len(set(sources)) != len(sources):
            raise ValueError(f'{name}: duplicate sources')
        parts.append(name + ' ' + ' '.join(sorted(sources)))
    return 'Content-Security-Policy-Report-Only: ' + '; '.join(parts)


def unique(pairs):
    obj = {}
    for k, v in pairs:
        if k in obj:
            raise ValueError('duplicate JSON key')
        obj[k] = v
    return obj


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('file', type=Path)
    a = p.parse_args()
    try:
        with a.file.open('rb') as f:
            data = f.read(32769)
        if len(data) > 32768:
            raise ValueError('input exceeds 32 KiB')
        print(build(json.loads(data.decode('utf-8'), object_pairs_hook=unique)))
    except (OSError, ValueError, UnicodeError) as e:
        p.error(str(e))


if __name__ == '__main__': main()
