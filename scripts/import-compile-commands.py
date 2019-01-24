#!/usr/bin/env python

import django_common

import argparse
import django_cpp_doc
import os
import json

def find_compilation_commands_file(package, src_dir):
    matches = []
    for root, dirs, files in os.walk(src_dir):
        for name in files:
            if name == 'compile_commands.json':
                matches.append(os.path.join(root, name))
    assert(len(matches) == 1)
    return matches[0]

def import_entry(package, src_dir, entry):
    dir = entry['directory']
    dir_fd = django_common.get_fd(package, src_dir, dir)
    file_fd = django_common.get_fd(package, src_dir,
                                   os.path.join(dir, entry['file']))

    if file_fd is None:
        return

    django_cpp_doc.models.CompileCommand.objects.get_or_create(
        package=package, file=file_fd,
        defaults={'directory': dir_fd, 'command_line': entry['arguments']})

def main():
    parser = argparse.ArgumentParser('Import compilation commands.')
    parser.add_argument('slug', help='Package slug to import commands to')
    parser.add_argument('version', help='Package version to import commands to')
    args = parser.parse_args()

    package = django_common.get_package(args.slug, args.version)
    src_dir = django_common.get_src_dir(package)
    compilation_commands_file = find_compilation_commands_file(package, src_dir)
    with open(compilation_commands_file, 'r') as f:
        for entry in json.load(f):
            import_entry(package, src_dir, entry)

if __name__ == '__main__':
    main()
