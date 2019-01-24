#!/usr/bin/env python

import django_common

import argparse
import django_cpp_doc
import os
import subprocess
import sys
import time

MAX_PROCESSES = 4

def spawn_process(compile_command_id):
    env = dict(os.environ)
    env['CONST_CHECKER_BASE_DIR'] = django_common.EXPERIMENTS_DIR
    args = ['const-checker',
            str(compile_command_id)]
    return subprocess.Popen(args, env=env)

def wait_for_queue(queue):
    while len(queue) >= MAX_PROCESSES:
        time.sleep(1)
        for q in queue:
            r = q.poll()
            if r is not None:
                queue.remove(q)
                if r != 0:
                    print(' '.join(q.args))
                    sys.exit(1)

def main():
    parser = argparse.ArgumentParser('Run clang compile commands.')
    parser.add_argument('slug', help='Package slug to run compile commands for')
    parser.add_argument('version', help='Package version to run compile commands for')
    args = parser.parse_args()

    package = django_common.get_package(args.slug, args.version)
    queue = []
    for cc in django_cpp_doc.models.CompileCommand.objects.filter(package=package):
        if cc.file.path.endswith('.S'):
            continue

        wait_for_queue(queue)
        print('\033[1;33m{}\033[0;33m {}\033[m'.format(cc.id, cc.file.path))
        queue.append(spawn_process(cc.id, args.assumption))
    wait_for_queue(queue)

if __name__ == '__main__':
    main()
