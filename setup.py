from distutils.core import setup
from Cython.Build import cythonize
 
setup(
    ext_modules = cythonize(["cython_example.pyx", "ta_c.pyx"])
)

#"ta_c.pyx"

#cd C:\Users\tomyi\Anaconda\envs\py3\Lib\site-packages\yzhang
#python setup.py build_ext --inplace
