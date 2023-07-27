import os
import sys
import setuptools

import numpy
from Cython.Build import cythonize, build_ext

if sys.platform == 'darwin':
    unix_copt = ['-Xpreprocessor', '-fopenmp', '-lomp']
    unix_lopt = ['-Xpreprocessor', '-fopenmp', '-lomp']
else:
    unix_copt = ['-fopenmp',]
    unix_lopt = ['-fopenmp',]


copt = {"msvc": ["/openmp"], "mingw32": ["-fopenmp"], "unix": unix_copt}

lopt = {"mingw32": ["-fopenmp"], "unix": unix_lopt}


class build_ext_subclass(build_ext):
    def build_extensions(self):
        c = self.compiler.compiler_type
        print("Compiler", c)
        if c in copt:
            for e in self.extensions:
                e.extra_compile_args = copt[c]
        if c in lopt:
            for e in self.extensions:
                e.extra_link_args = lopt[c]
        for e in self.extensions:
            e.include_dirs = [numpy.get_include()]
        build_ext.build_extensions(self)


setuptools.setup(
    cmdclass={"build_ext": build_ext_subclass},
    ext_modules=cythonize(
        [
            setuptools.Extension(
                "count",
                ["count.pyx"],
            ),
        ]
    ),
)
