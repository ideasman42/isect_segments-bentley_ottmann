
# Simple-BVH implementation
# (for finding all intersections in a set of line segments)

from __future__ import annotations

__all__ = (
    "isect_segments",
    "isect_polygon",

    # same as above but includes segments with each intersections
    "isect_segments_include_segments",
    "isect_polygon_include_segments",

    # for testing only (correct but slow)
    "isect_segments__naive",
    "isect_polygon__naive",
)

# ----------------------------------------------------------------------------
# Main Poly Intersection

# Defines to change behavior.
#
# Whether to ignore intersections of line segments when both
# their end points form the intersection point.
USE_IGNORE_SEGMENT_ENDINGS = True

# end defines!
# ------------

# ---------
# Constants
X, Y = 0, 1

# -----------------------------------------------------------------------------
# Switchable Number Implementation

NUMBER_TYPE = 'native'

if NUMBER_TYPE == 'native':
    Real = float
    NUM_EPS = Real("1e-10")
    NUM_INF = Real(float("inf"))
elif NUMBER_TYPE == 'decimal':
    # Not passing tests!
    import decimal
    Real = decimal.Decimal
    decimal.getcontext().prec = 80
    NUM_EPS = Real("1e-10")
    NUM_INF = Real(float("inf"))
elif NUMBER_TYPE == 'numpy':
    import numpy
    Real = numpy.float64
    del numpy
    NUM_EPS = Real("1e-10")
    NUM_INF = Real(float("inf"))
elif NUMBER_TYPE == 'gmpy2':
    # Not passing tests!
    import gmpy2
    gmpy2.set_context(gmpy2.ieee(128))
    Real = gmpy2.mpz
    NUM_EPS = Real(float("1e-10"))
    NUM_INF = gmpy2.get_emax_max()
    del gmpy2
else:
    raise Exception("Type not found")

NUM_EPS_SQ = NUM_EPS * NUM_EPS
NUM_ZERO = Real(0.0)
NUM_ONE = Real(1.0)


def _segments_clean(segments, validate=True):
    # order points left -> right
    if Real is float:
        segments = [
            # in nearly all cases, comparing X is enough,
            # but compare Y too for vertical lines
            (s[0], s[1]) if (s[0] <= s[1]) else
            (s[1], s[0])
            for s in segments]
    else:
        segments = [
            # in nearly all cases, comparing X is enough,
            # but compare Y too for vertical lines
            (
                (Real(s[0][0]), Real(s[0][1])),
                (Real(s[1][0]), Real(s[1][1])),
            ) if (s[0] <= s[1]) else
            (
                (Real(s[1][0]), Real(s[1][1])),
                (Real(s[0][0]), Real(s[0][1])),
            )
            for s in segments]

    # Ensure segments don't have duplicates or single points, see: #24.
    if validate:
        segments_old = segments
        segments = []
        visited = set()
        for s in segments_old:
            # Ignore points.
            if s[0] == s[1]:
                continue
            # Ignore duplicates.
            if s in visited:
                continue
            visited.add(s)
            segments.append(s)
        del segments_old
    return segments


def isect_segments_impl(segments, *, include_segments=False, validate=True) -> list:

    segments = _segments_clean(segments, validate=validate)

    queue = EventQueue(segments)
    sweep_line = SweepLine(queue)

    while len(queue.events_scan) > 0:
        if USE_VERBOSE:
            print(len(queue.events_scan), sweep_line._current_event_point_x)
        p, e_ls = queue.poll()
        for events_current in e_ls:
            if events_current:
                sweep_line._sweep_to(p)
                sweep_line.handle(p, events_current)

    if include_segments is False:
        return sweep_line.get_intersections()
    else:
        return sweep_line.get_intersections_with_segments()


def isect_polygon_impl(points, *, include_segments=False, validate=True) -> list:
    n = len(points)
    segments = [
        (tuple(points[i]), tuple(points[(i + 1) % n]))
        for i in range(n)
    ]
    return isect_segments__bvh_impl(segments, include_segments=include_segments, validate=validate)


def isect_segments(segments, *, validate=True) -> list:
    return isect_segments__bvh_impl(segments, include_segments=False, validate=validate)


def isect_polygon(segments, *, validate=True) -> list:
    return isect_polygon_impl(segments, include_segments=False, validate=validate)


def isect_segments_include_segments(segments, *, validate=True) -> list:
    return isect_segments__bvh_impl(segments, include_segments=True, validate=validate)


def isect_polygon_include_segments(segments, *, validate=True) -> list:
    return isect_polygon_impl(segments, include_segments=True, validate=validate)


# ----------------------------------------------------------------------------
# 2D math utilities


def sub_v2v2(a, b):
    return (
        a[0] - b[0],
        a[1] - b[1])


def dot_v2v2(a, b):
    return (
        (a[0] * b[0]) +
        (a[1] * b[1]))


def len_squared_v2v2(a, b):
    c = sub_v2v2(a, b)
    return dot_v2v2(c, c)


def line_point_factor_v2(p, l1, l2, default=NUM_ZERO):
    u = sub_v2v2(l2, l1)
    h = sub_v2v2(p, l1)
    dot = dot_v2v2(u, u)
    return (dot_v2v2(u, h) / dot) if dot != NUM_ZERO else default


def isect_seg_seg_v2_point(v1, v2, v3, v4, bias=NUM_ZERO):
    # Only for predictability and hashable point when same input is given
    if v1 > v2:
        v1, v2 = v2, v1
    if v3 > v4:
        v3, v4 = v4, v3

    if (v1, v2) > (v3, v4):
        v1, v2, v3, v4 = v3, v4, v1, v2

    div = (v2[0] - v1[0]) * (v4[1] - v3[1]) - (v2[1] - v1[1]) * (v4[0] - v3[0])
    if div == NUM_ZERO:
        return None

    vi = (((v3[0] - v4[0]) *
           (v1[0] * v2[1] - v1[1] * v2[0]) - (v1[0] - v2[0]) *
           (v3[0] * v4[1] - v3[1] * v4[0])) / div,
          ((v3[1] - v4[1]) *
           (v1[0] * v2[1] - v1[1] * v2[0]) - (v1[1] - v2[1]) *
           (v3[0] * v4[1] - v3[1] * v4[0])) / div,
          )

    fac = line_point_factor_v2(vi, v1, v2, default=-NUM_ONE)
    if fac < NUM_ZERO - bias or fac > NUM_ONE + bias:
        return None

    fac = line_point_factor_v2(vi, v3, v4, default=-NUM_ONE)
    if fac < NUM_ZERO - bias or fac > NUM_ONE + bias:
        return None

    return vi


# ----------------------------------------------------------------------------
# Simple naive line intersect, (for testing only)


def isect_segments__naive(segments) -> list:
    """
    Brute force O(n2) version of ``isect_segments`` for test validation.
    """
    isect = []

    # order points left -> right
    if Real is float:
        segments = [
            (s[0], s[1]) if s[0][X] <= s[1][X] else
            (s[1], s[0])
            for s in segments]
    else:
        segments = [
            (
                (Real(s[0][0]), Real(s[0][1])),
                (Real(s[1][0]), Real(s[1][1])),
            ) if (s[0] <= s[1]) else
            (
                (Real(s[1][0]), Real(s[1][1])),
                (Real(s[0][0]), Real(s[0][1])),
            )
            for s in segments]

    n = len(segments)

    for i in range(n):
        a0, a1 = segments[i]
        for j in range(i + 1, n):
            b0, b1 = segments[j]
            if a0 not in (b0, b1) and a1 not in (b0, b1):
                ix = isect_seg_seg_v2_point(a0, a1, b0, b1)
                if ix is not None:
                    # USE_IGNORE_SEGMENT_ENDINGS handled already
                    isect.append(ix)

    return isect


def isect_polygon__naive(points) -> list:
    """
    Brute force O(n2) version of ``isect_polygon`` for test validation.
    """
    isect = []

    n = len(points)

    if Real is float:
        pass
    else:
        points = [(Real(p[0]), Real(p[1])) for p in points]

    for i in range(n):
        a0, a1 = points[i], points[(i + 1) % n]
        for j in range(i + 1, n):
            b0, b1 = points[j], points[(j + 1) % n]
            if a0 not in (b0, b1) and a1 not in (b0, b1):
                ix = isect_seg_seg_v2_point(a0, a1, b0, b1)
                if ix is not None:

                    if USE_IGNORE_SEGMENT_ENDINGS:
                        if ((len_squared_v2v2(ix, a0) < NUM_EPS_SQ or
                             len_squared_v2v2(ix, a1) < NUM_EPS_SQ) and
                            (len_squared_v2v2(ix, b0) < NUM_EPS_SQ or
                             len_squared_v2v2(ix, b1) < NUM_EPS_SQ)):
                            continue

                    isect.append(ix)

    return isect


# ----------------------------------------------------------------------------
# Simple BVH line intersect

from collections import namedtuple
BVHNode = namedtuple(
    'BVHNode', (
        'child_min_max',
        'bounds_min',
        'bounds_max',
        'segment',
    ),
)
del namedtuple

def bvh_node_create_from_segments(segments):
    if len(segments) == 1:
        segment = segments[0]
        return BVHNode(
            child_min_max=None,
            bounds_min=(min(segment[0][0], segment[1][0]), min(segment[0][1], segment[1][1])),
            bounds_max=(max(segment[0][0], segment[1][0]), max(segment[0][1], segment[1][1])),
            segment=segment,
        )

    assert(len(segments) > 1)

    # Calculate the axis to split on:
    min_x = max_x = segments[0][0][0]
    min_y = max_y = segments[0][0][1]
    for s in segments:
        for p in s:
            min_x = min(min_x, p[0])
            max_x = max(max_x, p[0])

            min_y = min(min_y, p[1])
            max_y = max(max_y, p[1])

    axis = 0 if max_x - min_x > max_y - min_y else 1
    del min_x, min_y, max_x, max_y

    segments.sort(key=lambda s: min(s[0][axis], s[1][axis]))
    mid = len(segments) // 2
    child_min = bvh_node_create_from_segments(segments[:mid])
    child_max = bvh_node_create_from_segments(segments[mid:])

    return BVHNode(
        child_min_max=(child_min, child_max),
        bounds_min=(
            min(child_min.bounds_min[0], child_max.bounds_min[0]),
            min(child_min.bounds_min[1], child_max.bounds_min[1]),
        ),
        bounds_max=(
            max(child_min.bounds_max[0], child_max.bounds_max[0]),
            max(child_min.bounds_max[1], child_max.bounds_max[1]),
        ),
        segment=None,
    )


def bvh_overlap_aabb_pair_test(node_a, node_b):
    return (
        min(node_a.bounds_max[0], node_b.bounds_max[0]) >= max(node_a.bounds_min[0], node_b.bounds_min[0]) and
        min(node_a.bounds_max[1], node_b.bounds_max[1]) >= max(node_a.bounds_min[1], node_b.bounds_min[1])
    )


def bvh_overlap_iter_single(node):
    # Don't traverse ourselves multiple times.
    if node.child_min_max:
        if bvh_overlap_aabb_pair_test(*node.child_min_max):
            yield from bvh_overlap_iter_pair(*node.child_min_max)
        yield from bvh_overlap_iter_single(node.child_min_max[0])
        yield from bvh_overlap_iter_single(node.child_min_max[1])


def bvh_overlap_iter_pair(node_a, node_b):
    if node_a.child_min_max is None and node_b.child_min_max is not None:
        node_a, node_b = node_b, node_a

    # `node_a`, `node_b` intersect tests.
    if node_a.child_min_max:
        if node_b.child_min_max:
            for child_a in node_a.child_min_max:
                for child_b in node_b.child_min_max:
                    if bvh_overlap_aabb_pair_test(child_a, child_b):
                        yield from bvh_overlap_iter_pair(child_a, child_b)
        else:
            # `node_b is a segment.
            for child_a in node_a.child_min_max:
                if bvh_overlap_aabb_pair_test(child_a, node_b):
                    yield from bvh_overlap_iter_pair(child_a, node_b)
    else:
        # node_a and node_b are segments.
        yield node_a.segment, node_b.segment


def isect_segments__bvh_impl(segments, include_segments=False, validate=True):
    # Build the tree.
    segments = _segments_clean(segments, validate=validate)
    if len(segments) <= 1:
        return []

    if include_segments:
        isect_seg_map = {}

    root = bvh_node_create_from_segments(segments)

    isect = []
    for (a0, a1), (b0, b1) in bvh_overlap_iter_single(root):
        if a0 not in (b0, b1) and a1 not in (b0, b1):
            ix = isect_seg_seg_v2_point(a0, a1, b0, b1)
            if ix is not None:
                # USE_IGNORE_SEGMENT_ENDINGS handled already
                if include_segments:
                    ix_set = isect_seg_map.get(ix)
                    if ix_set:
                        ix_set.add(node_a.segment)
                        ix_set.add(node_b.segment)
                    else:
                        ix_set = {node_a.segment, node_b.segment}
                        isect_seg_map[ix] = ix_set
                        isect.append((ix, ix_set))
                else:
                    isect.append(ix)

    if include_segments:
        isect = [(ix, list(sorted(ix_set))) for ix, ix_set in isect]

    return isect


def isect_polygon__bvh(points) -> list:
    """
    TODO.
    """
    n = len(points)

    if Real is float:
        pass
    else:
        points = [(Real(p[0]), Real(p[1])) for p in points]

    segments = [
        (tuple(points[i]), tuple(points[(i + 1) % n]))
        for i in range(n)
    ]

    return isect_segments__bvh_impl(segments)


def isect_segments__bvh(segments) -> list:
    """
    TODO.
    """
    return isect_segments__bvh_impl(segments)
