
************************
Poly Point Intersections
************************

This is a single-file, Python3 implementation of the Bentley-Ottmann sweep-line algorithm
for listing all intersections in a set of line segments.

This aims to be portable & self-contained, (move to other lower languages such as C & C++).

.. figure:: https://cloud.githubusercontent.com/assets/1869379/10564349/753dd564-75fc-11e5-8e99-08530e6f6ef0.png

   Test-case with showing all 73,002 intersections from 14,880 segments.


Motivation
==========

At the time of writing, all the open-source implementation of Bentley-Ottmann's sweep-line
I couldn't find a good reference implementation which performed well
and could be reused or ported to different environments.

So this is my attempt to write a reference implementation with comprehensive tests.


Existing Implementations
------------------------

- `CompGeom <https://github.com/bkiers/CompGeom>`__ (Java).
- CGAL `SweepLine <http://doc.cgal.org/latest/Sweep_line_2/index.html>`__ (C++).

  Not Bentley-Ottmann strictly speaking, but the method is very similar.
- The `geomalgorithms.com <http://geomalgorithms.com/a09-_intersect-3.html>`__,
  while a great introduction, and frequently linked to as a reference,
  it only detects weather the polygon is self-intersecting or not.


Goals
-----

- Keep the library small, robust & reusable.
- Use mainly language-agnostic features.

  *(Even though classes are used, theres no problem moving this to a language without OO).*


Usage
=====

``poly_point_isect`` is a single Python module, exposing 2 functions.

``isect_polygon(points, validate=True)``
   Where ``points`` are a sequence of number pairs.
``isect_segments(segments, validate=True)``
   Where ``segments`` is list of point-pairs.

Both return a list of intersections.

The ``validate`` argument ensures duplicate or zero length segments are ignored.

Example:

.. code-block:: python

   # Show the result of a simple bow-tie quad
   import poly_point_isect
   poly = (
       (1.0, 0.0),
       (0.0, 1.0),
       (0.0, 0.0),
       (1.0, 1.0),
   )
   isect = poly_point_isect.isect_polygon(poly)
   print(isect)
   # [(0.5, 0.5)]


There are also: ``isect_polygon_include_segments(points)`` and ``isect_segments_include_segments(segments)``,
versions of the functions described above which return a tuple for each intersection: ``(point, list_of_segments)``
so you can find which segments belong to an intersection.


Details
=======

- Permissive MIT license.

  Note that both bintrees and CompGeom are MIT Licensed too.
- Written in Python3 and runs in PyPy as well.
- Runs in vanilla Python without any dependencies.
- Uses `bintrees <https://pypi.python.org/pypi/bintrees>`__ Python module,
  with modifications to support a custom comparator function.
  Also removed some unused code.

  .. note::

     Using another binary-tree library shouldn't be a problem as long as you can override its comparison.
     Ideally allow passing a custom argument too (as is done here),
     to avoid using globals to access the sweep-line.

- Includes tests for:

  - Intersecting segments.
  - Non intersecting segments.
  - Degenerate segments (overlapping & zero length)

  Test output can be optionally written to SVG files,
  see: ``tests/data_svg/`` directory.


Known Limitations
=================

For the purpose of this section, errors in detecting intersections are defined by any discrepancy
with the result compared to testing every segment against every other segment.


Sweep Line Step-Size
--------------------

Very small step sizes over *near-vertical* lines can cause errors
*(note that _exactly_ vertical lines are supported but have to be handled separately)*.

So far I didn't find a good general solution to this, though there are some ways to work-around the problem.

One way to resolve the problem is to use higher precision calculation for the sweep-line then the input data.

In my own tests I found for double precision floating point,
ensuring at least ``4e-06`` between steps gives stable results \*
(rounding the input segments X axis to 5 decimal places).

\* Checked with the included test-set at ``3.6e-06`` degree rotation increments from the initial rotation.


Further Work
============

- More tests.
- More test variations *(different scales, rotations)*.
