cantilever
=============================

|pypi| |py_versions| |codecov| |docs| |tests| |style|

.. |pypi| image:: https://img.shields.io/pypi/v/cantilever.svg
    :target: https://pypi.python.org/pypi/cantilever
    :alt: Current PyPi Version

.. |py_versions| image:: https://img.shields.io/pypi/pyversions/cantilever.svg
    :target: https://pypi.python.org/pypi/cantilever
    :alt: Supported Python Versions

.. |codecov| image:: https://codecov.io/gh/delaunay/cantilever/branch/master/graph/badge.svg?token=40Cr8V87HI
   :target: https://codecov.io/gh/delaunay/cantilever

.. |docs| image:: https://readthedocs.org/projects/cantilever/badge/?version=latest
   :target:  https://cantilever.readthedocs.io/en/latest/?badge=latest

.. |tests| image:: https://github.com/delaunay/cantilever/actions/workflows/test.yml/badge.svg?branch=master
   :target: https://github.com/delaunay/cantilever/actions/workflows/test.yml

.. |style| image:: https://github.com/delaunay/cantilever/actions/workflows/style.yml/badge.svg?branch=master
   :target: https://github.com/delaunay/cantilever/actions/workflows/style.yml



.. code-block:: bash

   pip install cantilever


.. code-block:: python
   
   import time

   from cantilever.core.timer import show_timings, timeit

   with timeit("here"):
       for _ in range(10):
           with timeit("this"):
               time.sleep(0.1)

   show_timings(force=True)

.. code-block:: text

   Timings:
   #                                          |      avg |    total |       sd |    count
   # root ................................... |     1.00 |     1.00 |     0.00 |     1.00
   #  here                                    |     1.00 |     1.00 |     0.00 |     1.00
   #   this _________________________________ |     0.10 |     1.00 |     0.00 |    10.00

