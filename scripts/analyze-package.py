#!/usr/bin/env python

import django_common

import argparse
import django_cpp_doc
import json
import os
import subprocess
import sys
import time

MAX_PROCESSES = 4

def find_compilation_commands_file(package, src_dir):
    matches = []
    for root, dirs, files in os.walk(src_dir):
        for name in files:
            if name == 'compile_commands.json':
                matches.append(os.path.join(root, name))
    if package.package_name.slug == 'llvm':
        matches = list(filter(lambda x: x.endswith('build/compile_commands.json'), matches))
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

def import_compile_commands(package):
    src_dir = django_common.get_src_dir(package)
    compilation_commands_file = find_compilation_commands_file(package, src_dir)
    with open(compilation_commands_file, 'r') as f:
        for entry in json.load(f):
            import_entry(package, src_dir, entry)

def spawn_process(compile_command_id):
    env = dict(os.environ)
    env['CONST_CHECKER_BASE_DIR'] = django_common.EXPERIMENTS_DIR
    args = ['const-checker',
            str(compile_command_id)]
    return subprocess.Popen(args, env=env,
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

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

def run_clang_tool(package):
    queue = []
    for cc in django_cpp_doc.models.CompileCommand.objects.filter(package=package):
        if cc.file.path.endswith('.S'):
            continue

        wait_for_queue(queue)
        print('\033[1;33m{}\033[0;33m {}\033[m'.format(cc.id, cc.file.path))
        queue.append(spawn_process(cc.id))
    wait_for_queue(queue)
    
    
def populate_counts(package):
    import django_cpp_doc.models as models
    for record in models.RecordDecl.objects.filter(decl__package=package):
        num_methods = 0
        num_mutable_methods = 0
        num_mutable_no_easy = 0
        num_mutable_no_easy_non_stub = 0
        num_mutable_no_odd = 0
        num_mutable_maybe = 0
        num_mutable_no_ret_noop = 0
        num_mutable_no_ret_field_t = 0
        num_mutable_no_ret_field_nt = 0
        num_mutable_no_ret_other = 0
        num_mutable_maybe_ret_noop = 0
        num_mutable_maybe_ret_field_t = 0
        num_mutable_maybe_ret_field_nt = 0
        num_mutable_maybe_ret_other = 0
        num_const_methods = 0
        num_const_no_easy = 0
        num_const_no_odd = 0
        num_const_maybe = 0
        num_const_no_ret_noop = 0
        num_const_no_ret_field_t = 0
        num_const_no_ret_field_nt = 0
        num_const_no_ret_other = 0
        num_const_maybe_ret_noop = 0
        num_const_maybe_ret_field_t = 0
        num_const_maybe_ret_field_nt = 0
        num_const_maybe_ret_other = 0
        num_fields = 0
        num_explicit_fields = 0
        num_mutable_fields = 0
        num_transitive_fields = 0
        num_only_explicit_fields = 0
        num_only_transitive_fields = 0
        num_neither_explicit_transitive_fields = 0
        num_both_explicit_transitive_fields = 0
        for public_view in models.PublicView.objects.filter(record=record):

            try:
                method = public_view.decl.method
                assert(method.access == 0) # Assert every method is public

                try:
                    mutate_result = method.immutability_check.mutate_result
                    return_result = method.immutability_check.return_result
                except Exception as e:
                    print("Warning: Record '{}' with unimplemented method '{}'".format(record, method.decl.name))
                    continue
                is_const = method.is_const
                is_stub = False
                try:
                    method.stub
                    is_stub = True
                except:
                    pass
                if is_const:
                    if mutate_result == 1:
                        if return_result == 1:
                            num_const_no_easy += 1
                            num_const_no_ret_noop += 1
                        elif return_result == 2:
                            num_const_no_easy += 1
                            num_const_no_ret_field_t += 1
                        elif return_result == 3:
                            num_const_no_odd += 1
                            num_const_no_ret_field_nt += 1
                        elif return_result == 4:
                            num_const_no_easy += 1
                            num_const_no_ret_other += 1
                    elif mutate_result == 2:
                        if return_result == 1:
                            num_const_maybe_ret_noop += 1
                        elif return_result == 2:
                            num_const_maybe_ret_field_t += 1
                        elif return_result == 3:
                            num_const_maybe_ret_field_nt += 1
                        elif return_result == 4:
                            num_const_maybe_ret_other += 1
                        num_const_maybe += 1
                    num_const_methods += 1
                else:
                    if mutate_result == 1:
                        if return_result == 1:
                            num_mutable_no_easy += 1
                            if not is_stub:
                                num_mutable_no_easy_non_stub += 1
                            num_mutable_no_ret_noop += 1
                        elif return_result == 2:
                            num_mutable_no_easy += 1
                            if not is_stub:
                                num_mutable_no_easy_non_stub += 1
                            num_mutable_no_ret_field_t += 1
                        elif return_result == 3:
                            num_mutable_no_odd += 1
                            num_mutable_no_ret_field_nt += 1
                        elif return_result == 4:
                            # print(method)
                            num_mutable_no_easy += 1
                            if not is_stub:
                                num_mutable_no_easy_non_stub += 1
                            num_mutable_no_ret_other += 1
                    elif mutate_result == 2:
                        if return_result == 1:
                            num_mutable_maybe_ret_noop += 1
                        elif return_result == 2:
                            num_mutable_maybe_ret_field_t += 1
                        elif return_result == 3:
                            num_mutable_maybe_ret_field_nt += 1
                        elif return_result == 4:
                            num_mutable_maybe_ret_other += 1
                        num_mutable_maybe += 1
                    num_mutable_methods += 1
                num_methods += 1
            except:
                pass

            try:
                field = public_view.decl.field
                if field.is_mutable:
                    num_mutable_fields += 1
                if field.access != 0:
                    print("Warning: Record '{}' with non-public mutable field '{}' ({})".format(record, field.decl.name, field.decl.pk))
                try:
                    check = field.immutability_check
                except Exception as e:
                    print("Warning: Record '{}' with missing field '{}' ({})".format(record, field.decl.name, field.decl.pk))
                    continue
                    raise(e)
                is_explicit = check.is_explicit
                is_transitive = check.is_transitive
                if is_explicit and is_transitive:
                    num_both_explicit_transitive_fields += 1
                elif is_explicit:
                    num_only_explicit_fields += 1
                elif is_transitive:
                    num_only_transitive_fields += 1
                else:
                    num_neither_explicit_transitive_fields += 1
                num_fields += 1
            except models.FieldDecl.DoesNotExist:
                pass

        # If there are no methods here, it's not valid
        if num_methods == 0 and num_fields == 0:
            continue

        num_transitive_fields = num_only_transitive_fields + num_both_explicit_transitive_fields
        num_explicit_fields = num_only_explicit_fields + num_both_explicit_transitive_fields

        try:
            counts = record.counts
            counts.num_methods=num_methods
            counts.num_mutable_methods=num_mutable_methods
            counts.num_mutable_no_easy=num_mutable_no_easy
            counts.num_mutable_no_easy_non_stub=num_mutable_no_easy_non_stub
            counts.num_mutable_no_odd=num_mutable_no_odd
            counts.num_mutable_maybe=num_mutable_maybe
            counts.num_mutable_no_ret_noop=num_mutable_no_ret_noop
            counts.num_mutable_no_ret_field_t=num_mutable_no_ret_field_t
            counts.num_mutable_no_ret_field_nt=num_mutable_no_ret_field_nt
            counts.num_mutable_no_ret_other=num_mutable_no_ret_other
            counts.num_mutable_maybe_ret_noop=num_mutable_maybe_ret_noop
            counts.num_mutable_maybe_ret_field_t=num_mutable_maybe_ret_field_t
            counts.num_mutable_maybe_ret_field_nt=num_mutable_maybe_ret_field_nt
            counts.num_mutable_maybe_ret_other=num_mutable_maybe_ret_other
            counts.num_const_methods=num_const_methods
            counts.num_const_no_easy=num_const_no_easy
            counts.num_const_no_odd=num_const_no_odd
            counts.num_const_maybe=num_const_maybe
            counts.num_const_no_ret_noop=num_const_no_ret_noop
            counts.num_const_no_ret_field_t=num_const_no_ret_field_t
            counts.num_const_no_ret_field_nt=num_const_no_ret_field_nt
            counts.num_const_no_ret_other=num_const_no_ret_other
            counts.num_const_maybe_ret_noop=num_const_maybe_ret_noop
            counts.num_const_maybe_ret_field_t=num_const_maybe_ret_field_t
            counts.num_const_maybe_ret_field_nt=num_const_maybe_ret_field_nt
            counts.num_const_maybe_ret_other=num_const_maybe_ret_other
            counts.num_fields=num_fields
            counts.num_mutable_fields=num_mutable_fields
            counts.num_explicit_fields=num_explicit_fields
            counts.num_transitive_fields=num_transitive_fields
            counts.num_only_explicit_fields=num_only_explicit_fields
            counts.num_only_transitive_fields=num_only_transitive_fields
            counts.num_neither_explicit_transitive_fields=num_neither_explicit_transitive_fields
            counts.num_both_explicit_transitive_fields=num_both_explicit_transitive_fields
            counts.save()
        except models.RecordCounts.DoesNotExist:
            counts = models.RecordCounts.objects.create(
                record=record,
                num_methods=num_methods,
                num_mutable_methods=num_mutable_methods,
                num_mutable_no_easy=num_mutable_no_easy,
                num_mutable_no_easy_non_stub=num_mutable_no_easy_non_stub,
                num_mutable_no_odd=num_mutable_no_odd,
                num_mutable_maybe=num_mutable_maybe,
                num_mutable_no_ret_noop=num_mutable_no_ret_noop,
                num_mutable_no_ret_field_t=num_mutable_no_ret_field_t,
                num_mutable_no_ret_field_nt=num_mutable_no_ret_field_nt,
                num_mutable_no_ret_other=num_mutable_no_ret_other,
                num_mutable_maybe_ret_noop=num_mutable_maybe_ret_noop,
                num_mutable_maybe_ret_field_t=num_mutable_maybe_ret_field_t,
                num_mutable_maybe_ret_field_nt=num_mutable_maybe_ret_field_nt,
                num_mutable_maybe_ret_other=num_mutable_maybe_ret_other,
                num_const_methods=num_const_methods,
                num_const_no_easy=num_const_no_easy,
                num_const_no_odd=num_const_no_odd,
                num_const_maybe=num_const_maybe,
                num_const_no_ret_noop=num_const_no_ret_noop,
                num_const_no_ret_field_t=num_const_no_ret_field_t,
                num_const_no_ret_field_nt=num_const_no_ret_field_nt,
                num_const_no_ret_other=num_const_no_ret_other,
                num_const_maybe_ret_noop=num_const_maybe_ret_noop,
                num_const_maybe_ret_field_t=num_const_maybe_ret_field_t,
                num_const_maybe_ret_field_nt=num_const_maybe_ret_field_nt,
                num_const_maybe_ret_other=num_const_maybe_ret_other,
                num_fields=num_fields,
                num_mutable_fields=num_mutable_fields,
                num_explicit_fields=num_explicit_fields,
                num_transitive_fields=num_transitive_fields,
                num_only_explicit_fields=num_only_explicit_fields,
                num_only_transitive_fields=num_only_transitive_fields,
                num_neither_explicit_transitive_fields=num_neither_explicit_transitive_fields,
                num_both_explicit_transitive_fields=num_both_explicit_transitive_fields,
            )

def get_all_dependencies(method):
    all_dependencies = set()
    checked = set()
    def collect(method, all_dependencies, checked):
        if method in checked:
            return
        checked.add(method)
        for dependent in method.dependencies.all():
            all_dependencies.add(dependent.callee)
            collect(dependent.callee, all_dependencies, checked)
    collect(method, all_dependencies, checked)
    return all_dependencies

def check_all_dependencies(record, all_dependencies):
    for dependent in all_dependencies:
        try:
            mutate_result = dependent.immutability_check.mutate_result
            return_result = dependent.immutability_check.return_result
            # This is an internal call, return result doesn't matter
            if mutate_result != 1:
                return False
        except Exception as e:
            return False
    return True

def method_solve(package):
    import django_cpp_doc.models as models
    for record in models.RecordDecl.objects.filter(decl__package=package):
        for public_view in models.PublicView.objects.filter(record=record):
            try:
                method = public_view.decl.method
                try:
                    mutate_result = method.immutability_check.mutate_result
                    return_result = method.immutability_check.return_result
                except Exception as e:
                    print("Warning: Record '{}' with unimplemented method '{}'".format(record, method.decl.name))
                    continue
                all_dependencies = get_all_dependencies(method)
                if mutate_result == 1 and check_all_dependencies(record, all_dependencies):
                    models.ClangImmutabilityCheckMethodResult.objects.get_or_create(method=method,
                                                                            should_be_const=True)
                else:
                    models.ClangImmutabilityCheckMethodResult.objects.get_or_create(method=method,
                                                                            should_be_const=False)
            except Exception as e:
                pass

def main():
    parser = argparse.ArgumentParser('Analyze a package using const-checker.')
    parser.add_argument('slug', help='Package slug to analyze')
    parser.add_argument('version', help='Package version to analyze')
    args = parser.parse_args()

    package = django_common.get_package(args.slug, args.version)

    import_compile_commands(package)
    run_clang_tool(package)
    populate_counts(package)
    method_solve(package)

if __name__ == '__main__':
    main()
