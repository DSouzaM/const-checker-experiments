import django
import os
import sys

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
EXPERIMENTS_DIR = os.path.dirname(SCRIPTS_DIR)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'const_checker_experiments.settings')
sys.path.append(EXPERIMENTS_DIR)
django.setup()

import django_cpp_doc

def get_src_dir(package):
    return os.path.join(EXPERIMENTS_DIR, package.package_name.slug,
                        package.version, 'src')

def get_root_fd(package):
    root_fd, _ = django_cpp_doc.models.FileDescriptor.objects.get_or_create(
            package=package, parent=None, name='', path='')
    return root_fd

def get_fd(package, src_dir, abs_path):
    if not abs_path.startswith(src_dir):
        return None
    if not (os.path.isfile(abs_path) or os.path.isdir(abs_path)):
        print('Warning: "{}" does not exist'.format(abs_path))
        return None
    if src_dir == abs_path:
        return get_root_fd(package)
    assert(os.path.isfile(abs_path) or os.path.isdir(abs_path))
    parent = get_fd(package, src_dir, os.path.dirname(abs_path))
    name = os.path.basename(abs_path)
    path = os.path.relpath(abs_path, src_dir)
    fd, _ = django_cpp_doc.models.FileDescriptor.objects.get_or_create(
            package=package, parent=parent, name=name, path=path)
    return fd

def get_package(slug, version):
    from django_cpp_doc.models import Package, PackageName
    names = {
        'llvm': 'LLVM',
        'mosh': 'Mosh',
        'ninja': 'Ninja',
        'opencv': 'OpenCV',
        'protobuf': 'Protobuf',
    }
    package_name, _ = PackageName.objects.get_or_create(slug=slug, defaults={
        'name': names[slug] if slug in names else slug})
    package, _ = Package.objects.get_or_create(package_name=package_name, version=version)
    return package
