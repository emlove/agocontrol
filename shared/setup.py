# Small setup.py to create package to install agoclient into
# the default python module space.
from distutils.core import setup
setup(name='agoclient',
  version='1.02',
  description='agocontrol client library',
  author='Harald Klein',
  author_email='hari@vt100.at',
  url='http://www.agocontrol.org/sigs/distutils-sig/',                        
  maintainer='Peer Oliver Schmidt',
  maintainer_email='pos@linuxmce.org',
  py_modules=['agoclient'],
)