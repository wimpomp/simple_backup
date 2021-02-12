#!/usr/bin/python3

from datetime import date, timedelta, datetime
from glob import iglob
from re import match
import os
from shutil import rmtree
from shlex import split
from subprocess import call
from argparse import ArgumentParser


def dates(sdate):
    # sdate: "20180508"
    sdate = date(int(sdate[:4]), int(sdate[4:6]), int(sdate[6:]))
    edate = datetime.now()
    edate = date(edate.year, edate.month, edate.day)
    return [(sdate + timedelta(i)) for i in range(int((edate - sdate).days))]


def days(d, n=7):
    return d[-n:]


def weeks(d, n=4):
    l = {}
    for i in d[-7*n:]:
        l[(i.year, i.isocalendar()[1])] = i
    return list(l.values())


def months(d, n=12):
    l = {}
    for i in d[-int(30.4375*n):]:
        l[(i.year, i.month)] = i
    return list(l.values())


def years(d, n=10):
    l = {}
    for i in d[-int(365.25*n):]:
        l[i.year] = i
    return list(l.values())


if __name__ == '__main__':
    parser = ArgumentParser(description='Backup files.')
    parser.add_argument('source', help='source path')
    parser.add_argument('dest', help='destination path')
    parser.add_argument('-r', '--rsync', help='arguments for rsync', default='-a')
    parser.add_argument('-v', '--verbose', help='verbose', action='store_true')
    parser.add_argument('-d', '--dry-run', help='dry-run', action='store_true')
    parser.add_argument('-l', '--latest', help='name of latest backup', default='latest')

    args = parser.parse_args()
    verbose = args.verbose
    run = not args.dry_run

    if not run:
        print('Dry-run: do not actually change anything.')

    backup_path_full = os.path.join(args.dest, datetime.now().strftime('%Y%m%d-%H%M%S'))
    if verbose:
        print('Backing up to: {}'.format(backup_path_full))
    if run:
        os.makedirs(backup_path_full, exist_ok=True)
    latest_path = os.path.join(args.dest, args.latest)
    if os.path.exists(latest_path):
        latest = '--link-dest="{}" '.format(os.path.join(latest_path, args.source[1:], ''))
    else:
        latest = ''

    if run:
        os.makedirs(os.path.join(backup_path_full, args.source[1:]))
    rsync = 'rsync {} --delete "{}" {} "{}"'.format(args.rsync, os.path.join(args.source, ''), latest,
        os.path.join(backup_path_full, args.source[1:]))

    if verbose:
        print('Running rsync: {}'.format(rsync))
    if run:
        call(split(rsync))
        if os.path.exists(latest_path):
            os.remove(latest_path)
        os.symlink(backup_path_full, latest_path)

    # Deleting old backups
    f = [i for i in iglob(os.path.join(args.dest, '*')) if not match('\d{8}-.*', os.path.split(i)[1]) is None]
    fn = [os.path.split(i)[1] for i in f]
    f = {date(int(j[:4]), int(j[4:6]), int(j[6:8])): i for i, j in zip(f, fn)}
    keys = sorted(list(f.keys()))
    keep = list(set(days(keys) + weeks(keys) + months(keys) + years(keys)))
    keep = {f[i] for i in keep}
    delete = set(f.values()) - keep
    if verbose:
        print('Deleting old backups: {}'.format(sorted(list(delete))))
    if run:
        for i in delete:
            if os.path.exists(i):
                rmtree(i, True)
