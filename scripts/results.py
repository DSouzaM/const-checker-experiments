#!/usr/bin/env python

import django_common

import argparse
import random

def results(package):
    import django_cpp_doc.models as models
    num_records = 0
    num_records_has_methods = 0
    num_records_has_methods_all_const_all_explicit_fields = 0
    num_records_has_methods_all_const_not_all_explicit_fields = 0
    num_records_has_methods_some_const = 0
    num_records_has_methods_no_const_has_fields = 0
    num_records_has_methods_no_const_no_fields = 0
    num_records_only_fields = 0
    num_records_only_fields_all_explicit = 0
    num_records_only_fields_some_explicit = 0
    num_records_only_fields_no_explicit = 0

    num_records_easily_constable = 0
    num_records_easily_constable_no_const_no_fields = 0
    num_records_easily_constable_no_const_has_fields = 0
    num_records_easily_constable_some_const = 0

    records_has_methods_all_const_all_explicit_fields = []
    records_has_methods_all_const_not_all_explicit_fields = []
    records_has_methods_some_const = []
    records_has_methods_no_const_no_fields = []
    records_easily_constable = []
    records_easily_constable_no_const_no_fields = []
    records_easily_constable_no_const_has_fields = []
    records_easily_constable_some_const = []

    num_records_both_fields_methods = 0
    num_records_only_fields = 0
    num_records_only_methods = 0
    num_records_w_public_fields = 0
    num_records_all_const = 0
    num_records_no_const = 0
    records_all_const = []
    records_all_const_w_public = []
    records_no_const = []
    records_no_const_w_public = []

    num_records_has_const_complex = 0

    records_identical_mutable_const_view = []
    records_all_const_methods = []
    records_no_const_view = []
    records_no_const_with_fields = []
    records_has_easy_const_method = []
    records_has_const_complex_method = []

    records_easily_constable_trust = []

    num_non_trivial_records = 0
    records_has_methods_all_const_all_explicit_fields = []
    records_has_methods_no_const_no_fields = []
    records_immutable_non_trivial = []
    records_all_mutating_non_trivial = []

    num_methods = models.ClangImmutabilityCheckMethodResult.objects.filter(method__decl__package=package).count()
    
    for rc in models.RecordCounts.objects.filter(record__decl__package=package):
        if rc.num_fields == 0 and rc.num_const_methods == 0:
            records_no_const_view.append(rc.record)

        if rc.num_fields > 0 and rc.num_const_methods == 0:
            records_no_const_with_fields.append(rc.record)

        if rc.num_methods == rc.num_const_methods and rc.num_fields == rc.num_explicit_fields:
            records_identical_mutable_const_view.append(rc.record)

        if rc.num_methods == rc.num_const_methods and rc.num_fields != rc.num_explicit_fields:
            records_all_const_methods.append(rc.record)

        if rc.num_methods > 3:
            num_non_trivial_records += 1
        num_records += 1

        if rc.num_methods > 0:
            if rc.num_const_methods == 0:
                if rc.num_fields == 0:
                    num_records_has_methods_no_const_no_fields += 1
                    records_has_methods_no_const_no_fields.append(rc.record)
                    if rc.num_methods > 3:
                        records_all_mutating_non_trivial.append(rc.record)
                else:
                    num_records_has_methods_no_const_has_fields += 1
            elif rc.num_const_methods == rc.num_methods:
                if rc.num_fields == rc.num_explicit_fields:
                    num_records_has_methods_all_const_all_explicit_fields += 1
                    records_has_methods_all_const_all_explicit_fields.append(rc.record)
                else:
                    num_records_has_methods_all_const_not_all_explicit_fields += 1
                    records_has_methods_all_const_not_all_explicit_fields.append(rc.record)
            else:
                num_records_has_methods_some_const += 1
            num_records_has_methods += 1
        else:
            assert(rc.num_fields > 0)
            if rc.num_fields == rc.num_explicit_fields:
                num_records_only_fields_all_explicit += 1
            elif rc.num_explicit_fields > 0:
                num_records_only_fields_some_explicit += 1
            else:
                num_records_only_fields_no_explicit += 1
            num_records_only_fields += 1
        
        if rc.num_methods > 3:
            if rc.num_const_methods == 0:
                if rc.num_fields == 0:
                    records_all_mutating_non_trivial.append(rc.record)

            elif rc.num_const_methods == rc.num_methods:
                if rc.num_fields == rc.num_explicit_fields:
                    records_immutable_non_trivial.append(rc.record)

    num_methods_easily = models.ClangImmutabilityCheckMethodResult.objects.filter(method__decl__package=package, should_be_const=True).count()
    num_methods_not = models.ClangImmutabilityCheckMethodResult.objects.filter(method__decl__package=package, should_be_const=True).count()
    num_const_methods = models.ClangImmutabilityCheckMethodResult.objects.filter(method__decl__package=package, method__is_const=True).count()
    num_const_easily = models.ClangImmutabilityCheckMethodResult.objects.filter(method__decl__package=package, method__is_const=True, should_be_const=True).count()
    num_mutable_methods = models.ClangImmutabilityCheckMethodResult.objects.filter(method__decl__package=package, method__is_const=False).count()
    num_mutable_easily = models.ClangImmutabilityCheckMethodResult.objects.filter(method__decl__package=package, method__is_const=False, should_be_const=True).count()

    def get_link(r):
        return 'http://localhost:8000/package/{}/{}/decl/{}'.format(package.package_name.slug, package.version, r.decl.pk)

    print('#', package.package_name.name, package.version)
    print()
    print('## Table I')
    print('  - Classes:', num_records)
    print('  - Methods:', num_methods)
    print()
    print('## Table II')
    print('  - Has methods: {:.1f}%'.format(
        100*num_records_has_methods/num_records if num_records > 0 else 0.0))
    print('    - Immutable: {:.1f}%'.format(
        100*num_records_has_methods_all_const_all_explicit_fields/num_records if num_records > 0 else 0.0))
    print('    - Query: {:.1f}%'.format(
        100*num_records_has_methods_all_const_not_all_explicit_fields/num_records if num_records > 0 else 0.0))
    print('    - Mix: {:.1f}%'.format(
        100*num_records_has_methods_some_const/num_records if num_records > 0 else 0.0))
    print('    - Throwaway: {:.1f}%'.format(
        100*num_records_has_methods_no_const_has_fields/num_records if num_records > 0 else 0.0))
    print('    - Unannotated: {:.1f}%'.format(
        100*num_records_has_methods_no_const_no_fields/num_records if num_records > 0 else 0.0))
    print('  - Only fields: {:.1f}%'.format(
        100*num_records_only_fields/num_records if num_records > 0 else 0.0))
    print()
    print('## Table III-VII')
    print('  - Immutable', '&', num_records_has_methods_all_const_all_explicit_fields,
          '&', len(records_immutable_non_trivial))
    print('  - All-mutating', '&', num_records_has_methods_no_const_no_fields,
          '&', len(records_all_mutating_non_trivial))
    MAX_SAMPLES = 20
    print()
    if len(records_immutable_non_trivial) <= MAX_SAMPLES:
        print('### Immutable')
        for record in records_immutable_non_trivial:
            print('  - ', get_link(record), record)
    else:
        print('### Immutable ({} samples)'.format(MAX_SAMPLES))
        for record in random.sample(records_immutable_non_trivial, MAX_SAMPLES):
            print('  - ', get_link(record), record)

    print()
    if len(records_all_mutating_non_trivial) <= MAX_SAMPLES:
        print('### All-mutating')
        for record in records_all_mutating_non_trivial:
            print('  - ', get_link(record), record)
    else:
        print('### All-mutating ({} samples)'.format(MAX_SAMPLES))
        for record in random.sample(records_all_mutating_non_trivial, MAX_SAMPLES):
            print('  - ', get_link(record), record)
    print()
    print('## Figure 4')
    print('  - non-const methods: {:.0f}%'.format(100.0 * num_mutable_methods / num_methods if num_methods > 0 else 0.0))
    print('    -  easily const-able: {:.0f}%'.format(100.0 * num_mutable_easily / num_mutable_methods if num_mutable_methods > 0 else 0.0))
    print('  - const methods: {:.0f}%'.format(100.0 * num_const_methods / num_methods if num_methods > 0 else 0.0))
    print('    - easily const-able: {:.0f}%'.format(100.0 * num_const_easily / num_const_methods if num_const_methods > 0 else 0.0))
    print()
    print('## Table VIII')
    print('  - # non-trivial classes:', num_non_trivial_records)
    print('  - % immutable classes (developer-written): {:.0f}%'.format(100.0 * len(records_immutable_non_trivial) / num_non_trivial_records if num_non_trivial_records > 0 else 0.0))
def main():
    parser = argparse.ArgumentParser('Show results.')
    parser.add_argument('slug', help='Package slug to show results for')
    parser.add_argument('version', help='Package version to show results for')
    args = parser.parse_args()

    package = django_common.get_package(args.slug, args.version)

    results(package)

if __name__ == '__main__':
    main()
