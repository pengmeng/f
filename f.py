#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function
import os
import sys
import fcntl
import cPickle
import argparse

space_path = os.path.expanduser('~/.f')
config_pickle = 'config.pickle'
config_raw = 'config.cfg'
inner_config = {
    'db_pickle': os.path.join(space_path, 'db.pickle'),
    'path_to_tag': os.path.join(space_path, 'path2tag.pickle'),
    'trie_pickle': os.path.join(space_path, 'trie.pickle')
}
user_config = None


class pickler(object):

    def __init__(self, filename):
        self._filename = filename
        try:
            self._file = open(filename, 'r+')
        except IOError:
            on_error('Data file not found, may be you forget to run init')
        self._pickle = None

    def __enter__(self):
        fcntl.flock(self._file, fcntl.LOCK_EX)
        self._pickle = cPickle.load(self._file)
        return self._pickle

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._file.truncate(0)
        self._file.seek(0)
        cPickle.dump(self._pickle, self._file, cPickle.HIGHEST_PROTOCOL)
        self._file.close()


def trie_add(trie, tag, path, index=0):
    if index >= len(tag):
        if '__value__' in trie:
            trie['__value__'].append(path)
        else:
            trie['__value__'] = [path]
        return
    char = tag[index]
    if char not in trie:
        trie[char] = {}
    trie_add(trie[char], tag, path, index + 1)


def trie_delete(trie, tag, path, index=0):
    if index >= len(tag):
        if '__value__' in trie:
            try:
                trie['__value__'].remove(path)
            except ValueError:
                pass
        return
    char = tag[index]
    if char in trie:
        trie_delete(trie[char], tag, path, index + 1)


def trie_match(trie, tag, acc, index=0):
    if index >= len(tag):
        _trie_walk(trie, acc)
        return acc
    char = tag[index]
    if char in trie:
        trie_match(trie[char], tag, acc, index + 1)
    else:
        raise ValueError('No tag match prefix [{}]'.format(tag))


def _trie_walk(trie, acc):
    if '__value__' in trie:
        for path in trie['__value__']:
            acc.append(path)
    for char, sub_trie in trie.iteritems():
        if len(char) == 1:
            _trie_walk(sub_trie, acc)


def u_print(message):
    print(message, file=sys.stderr)


def on_error(message):
    u_print(message)
    exit(1)


def on_succ(path):
    print(path)
    exit(0)


def ask(message):
    u_print(message)
    value = raw_input()
    return value


def abs_path(path):
    if '~' in path:
        path = os.path.expanduser(path)
    return os.path.abspath(path)


def _add_freq(path, db, p2t):
    name = os.path.split(path)[1]
    tag = str(db['__last__'])
    db['__freq__'][tag] = (tag, name, path, 1)
    db['__last__'] += 1
    p2t[path] = tag


def _incr_freq(tag, db):
    if tag in db['__freq__']:
        tag, name, path, cnt = db['__freq__'][tag]
        db['__freq__'][tag] = (tag, name, path, cnt + 1)


def _add_or_incr_freq(path, db, p2t):
    if path in p2t:
        _incr_freq(p2t[path], db)
    else:
        _add_freq(path, db, p2t)


def add_fav(path, tag=None):
    with pickler(inner_config['path_to_tag']) as p2t:
        old_tag = p2t[path] if path in p2t else None
        name = os.path.split(path)[1]
        with pickler(inner_config['db_pickle']) as db:
            if old_tag:
                if tag is None:
                    exit(2)
                else:
                    db['__fav__'].pop(old_tag, None)
                    db['__freq__'].pop(old_tag, None)
            if not tag:
                tag = str(db['__last__'])
                db['__last__'] += 1
            if tag in db['__fav__']:
                on_error('tag already exists: ' + tag)
            db['__fav__'][tag] = (tag, name, path)
        p2t[path] = tag
    with pickler(inner_config['trie_pickle']) as trie:
        if old_tag:
            trie_delete(trie, old_tag, path)
        trie_add(trie, tag, path)
    exit(2)


def listall():
    _temp = {}
    with pickler(inner_config['db_pickle']) as db:
        for tag, _, path in db['__fav__'].itervalues():
            u_print(tag + '\t' + path)
            _temp[tag] = path
        top = sorted(db['__freq__'].itervalues(), key=lambda x: x[-1], reverse=True)[:10]
        for tag, _, path, _ in top:
            u_print(tag + '\t' + path)
            _temp[tag] = path
        if not _temp:
            exit(2)
        tag = ask('Enter a tag to jump:')
        if tag in _temp:
            _incr_freq(tag, db)
            on_succ(_temp[tag])
        else:
            on_error('No match tag')


def jump_path(path):
    with pickler(inner_config['path_to_tag']) as p2t, pickler(inner_config['db_pickle']) as db:
        _add_or_incr_freq(path, db, p2t)
    on_succ(path)


def jump_hint(hint):
    with pickler(inner_config['db_pickle']) as db:
        if hint in db['__fav__']:
            on_succ(db['__fav__'][hint][2])
        elif hint in db['__freq__']:
            tag, name, path, cnt = db['__freq__'][hint]
            db['__freq__'][hint] = (tag, name, path, cnt + 1)
            on_succ(path)
        else:
            match = []
            with pickler(inner_config['trie_pickle']) as trie:
                try:
                    trie_match(trie, hint, match)
                except ValueError as e:
                    on_error(e.message)
            if len(match) == 0:
                on_error('No tag match prefix [{}]'.format(hint))
            if len(match) == 1:
                on_succ(match[0])
            else:
                _temp = {}
                with pickler(inner_config['path_to_tag']) as p2t:
                    for path in match:
                        tag = p2t[path]
                        u_print(tag + '\t' + path)
                        _temp[tag] = path
                tag = ask('Enter a tag to jump:')
                if tag in _temp:
                    _incr_freq(tag, db)
                    on_succ(_temp[tag])
                else:
                    on_error('No match tag')


def delete(tag):
    with pickler(inner_config['db_pickle']) as db:
        path = None
        if tag in db['__fav__']:
            path = db['__fav__'].pop(tag)[2]
        elif tag in db['__freq__']:
            path = db['__freq__'].pop(tag)[2]
        else:
            on_error('Tag [{}] not found in db.'.format(tag))
    with pickler(inner_config['path_to_tag']) as p2t:
        del p2t[path]
    with pickler(inner_config['trie_pickle']) as trie:
        trie_delete(trie, tag, path)
    exit(2)


def load_config():
    path = os.path.join(space_path, config_pickle)
    try:
        with open(path, 'r') as cf:
            global user_config
            user_config = cPickle.load(cf)
    except IOError:
        on_error('Config file not found, may be you forget to run init')


def load_history():
    path = abs_path('~/.bash_history')
    if not os.path.exists(path):
        print('~/.bash_history not found, skip history rebuild')
        return
    temp = {}
    with open(path) as hfile:
        for line in (line.strip() for line in hfile if line.startswith('cd')):
            parts = line.split(' ')
            if len(parts) != 2:
                continue
            raw_path = parts[1]
            for _try in (abs_path(raw_path), abs_path('~/' + raw_path)):
                if os.path.exists(_try):
                    temp[_try] = temp.get(_try, 0) + 1
                    break
    with pickler(inner_config['path_to_tag']) as p2t, pickler(inner_config['db_pickle']) as db:
        _home = abs_path('~')
        for path, cnt in temp.iteritems():
            if cnt <= 1 or path == _home:
                continue
            _add_or_incr_freq(path, db, p2t)


def init():
    if not os.path.exists(space_path):
        os.makedirs(space_path)
    # TODO: parse config and dump pickle
    db = {
        '__last__': 0,
        '__fav__': {},
        '__freq__': {},
    }
    with open(os.path.join(space_path, inner_config['db_pickle']), 'w') as dbf:
        cPickle.dump(db, dbf, cPickle.HIGHEST_PROTOCOL)
    with open(os.path.join(space_path, inner_config['path_to_tag']), 'w') as p2tf:
        cPickle.dump({}, p2tf, cPickle.HIGHEST_PROTOCOL)
    with open(os.path.join(space_path, inner_config['trie_pickle']), 'w') as p2tf:
        cPickle.dump({}, p2tf, cPickle.HIGHEST_PROTOCOL)
    load_history()
    print('f init success!')
    exit(2)


def main():
    if len(sys.argv) == 1:
        add_fav(os.getcwd())
    elif len(sys.argv) == 2 and sys.argv[1][0] != '-':
        if_path = abs_path(sys.argv[1])
        if os.path.exists(if_path):
            jump_path(if_path)
        else:
            jump_hint(sys.argv[1])
    else:
        args = parser.parse_args()
        if args.init:
            init()
        elif args.listall:
            listall()
        elif args.favorite:
            add_fav(os.getcwd(), args.favorite)
        elif args.delete:
            delete(args.delete)
    exit(2)

parser = argparse.ArgumentParser()
parser.add_argument('-f', '--favorite', type=str, help='add current dir to favorite with tag')
parser.add_argument('-l', '--listall', action='store_true', help='list all memorized dirs')
parser.add_argument('-d', '--delete', type=str, help='delete a dir with full tag')
parser.add_argument('--init', action='store_true', help='init f')
_raw_help = parser.print_help


def _print_help():
    _raw_help(file=sys.stderr)
    exit(2)
parser.print_help = _print_help

if __name__ == '__main__':
    main()
