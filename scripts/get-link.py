#!/usr/bin/env python

import django_common

import argparse

def main():
    parser = argparse.ArgumentParser('Get the url for a class.')
    parser.add_argument('slug', help='Package slug to search')
    parser.add_argument('version', help='Package version to search')
    parser.add_argument('qualified_name', help='Qualified name to search')
    args = parser.parse_args()

    package = django_common.get_package(args.slug, args.version)

    from django_cpp_doc.models import RecordDecl
    try:
        record = RecordDecl.objects.get(decl__package=package, decl__path=args.qualified_name)
        print(django_common.get_link(package, record))
    except RecordDecl.DoesNotExist:
        print('\x1B[31m{} not found in {} {}\x1B[m'.format(args.qualified_name, args.slug, args.version))

if __name__ == '__main__':
    main()
