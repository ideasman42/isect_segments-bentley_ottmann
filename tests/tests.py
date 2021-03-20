
"""
Example of watching a single test:
  watch -n2 "USE_SVG=1 nice -n 20 pypy3 -m unittest tests.IsectTest.test_suzzane"
"""

import sys
import os
import unittest

# Export results to SVG?
USE_SVG = os.environ.get("USE_SVG")
# USE_SVG = True

# Slow (so disable by default)
USE_ROTATION = os.environ.get("USE_ROTATION")
# number of rotations to check
ROTATION_DIV = 20

POLY_ISECT_MODULE_PATH = os.path.join(os.path.dirname(__file__), "..")
TEST_DATA_PATH = os.path.join(os.path.dirname(__file__), "data")

sys.path.append(POLY_ISECT_MODULE_PATH)
sys.path.append(TEST_DATA_PATH)

import poly_point_isect

# ----------------------------------------------------------------------------
# SVG Support

def export_svg(name, s, ix):
    # write svg's to tests dir for now
    dirname = os.path.join(TEST_DATA_PATH, "..", "data_svg")
    os.makedirs(dirname, exist_ok=True)
    fp = os.path.join(dirname, name + ".svg")
    scale = 512.0
    margin = 1.1
    with open(fp, 'w', encoding="utf-8") as f:
        fw = f.write
        fw('<?xml version="1.0" encoding="UTF-8"?>\n')
        fw('<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1 Tiny//EN" "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11-tiny.dtd">\n')
        fw('<svg version="1.1" '
           'width="%d" height="%d" '
           'viewBox="%d %d %d %d" '
           'xmlns="http://www.w3.org/2000/svg">\n' %
           (
            # width, height
            int(margin * scale * 2), int(margin * scale * 2),
            # viewBox
            -int(margin * scale), -int(margin * scale), int(margin * scale * 2), int(margin * scale * 2),
            ))

        fw('<rect x="%d" y="%d" width="%d" height="%d" fill="black"/>\n' %
            (-int(margin * scale), -int(margin * scale), int(margin * scale * 2), int(margin * scale * 2),
            ))

        if s:
            fw('<g stroke="white" stroke-opacity="0.25" stroke-width="1">\n')
            for v0, v1 in s:
                fw('<line x1="%.4f" y1="%.4f" x2="%.4f" y2="%.4f" />\n' %
                (v0[0] * scale, -v0[1] * scale, v1[0] * scale, -v1[1] * scale))
            fw('</g>\n')
        if ix:
            fw('<g fill="yellow" fill-opacity="0.25" stroke="white" stroke-opacity="0.5" stroke-width="1">\n')
            for v0 in ix:
                fw('<circle cx="%.4f" cy="%.4f" r="2"/>\n' %
                (v0[0] * scale, -v0[1] * scale))
            fw('</g>\n')

        fw('</svg>')


def segments_rotate(s, angle):
    from math import sin, cos
    si = sin(angle)
    co = cos(angle)

    def point_rotate(x, y):
        return (x * co - y * si,
                x * si + y * co)

    s = [(point_rotate(*p0), point_rotate(*p1)) for (p0, p1) in s]

    return s



def isect_segments(s):
    ret = poly_point_isect.isect_segments(s)
    return tuple(sorted(set(ret)))


def isect_segments__naive(s):
    ret = poly_point_isect.isect_segments__naive(s)
    return tuple(sorted(set(ret)))


def isect_segments_compare(s):
    if USE_ROTATION:
        from math import radians
        for i in range(1, ROTATION_DIV):
            fac = (i / ROTATION_DIV) / 100000
            angle_deg = 44.999995 + fac
            if angle_deg not in {44.9999955, 45}:
                continue
            # print(angle_deg)
            # angle_deg = (360 / ROTATION_DIV) * i
            angle_rad = radians(angle_deg)
            s_rotate = segments_rotate(s, angle_rad)
            yield (s_rotate, isect_segments(s_rotate), isect_segments__naive(s_rotate), ".%.2f" % angle_deg)
        return
    if 1:
        yield (s, isect_segments(s), isect_segments__naive(s), "")
    else:
        from math import radians
        angle_deg = 45.0
        angle_rad = radians(angle_deg)
        s_rotate = segments_rotate(s, angle_rad)
        yield (s_rotate, isect_segments(s_rotate), isect_segments__naive(s_rotate), "")



def test_data_load(name):
    return __import__(name).data


class TestDataFile_Helper:

    def assertTestData(self, name):
        s = test_data_load(name)
        for s_alt, ix_final, ix_naive, ix_id in isect_segments_compare(s):
            if USE_SVG:
                ## incase we want to compare:
                export_svg(name + ix_id + ".naive", s_alt, ix_naive)
                export_svg(name + ix_id, s_alt, ix_final)
            # print(name + ix_id)

            if ix_final == ix_naive:
                continue

            if 0:
                # simple but we can get more useful output
                self.assertEqual(ix_final, ix_naive)
            else:
                # prints intersect points where differ,
                # more useful for debugging.
                ix_final_only = tuple(sorted(set(ix_final) - set(ix_naive)))
                ix_naive_only = tuple(sorted(set(ix_naive) - set(ix_final)))
                self.assertEqual((len(ix_final), ix_final_only, ix_naive_only), (len(ix_naive), (), ()))


class NoIsectTest(unittest.TestCase, TestDataFile_Helper):
    """
    Tests that don't have any intersections
    (ensure we have no false positives).
    """

    def test_line(self):
        self.assertTestData("test_none_line")

    def test_square(self):
        self.assertTestData("test_none_square")

    def test_circle_2x(self):
        self.assertTestData("test_none_circle_2x")

    def test_circle(self):
        self.assertTestData("test_none_circle")

    def test_circle_zigzag(self):
        self.assertTestData("test_none_circle_zigzag")

    def test_maze(self):
        self.assertTestData("test_none_maze")


class IsectDegenerate(unittest.TestCase, TestDataFile_Helper):
    """
    Tests that are degenerate (no intersections in this case).
    """

    # def test_colinear_01(self):
    #     self.assertTestData("test_degenerate_colinear_01")

    # def test_colinear_02(self):
    #     self.assertTestData("test_degenerate_colinear_02")

    def test_zero_length_01(self):
        self.assertTestData("test_degenerate_zero_length_01")

    def test_zero_length_02(self):
        self.assertTestData("test_degenerate_zero_length_02")

    # See bug #24.
    def test_duplicates_01(self):
        self.assertTestData("test_degenerate_duplicates_01")


class IsectTest(unittest.TestCase, TestDataFile_Helper):
    """
    Tests that self-intersect.
    """

    def test_bowtie(self):
        self.assertTestData("test_isect_bowtie_01")

    def test_cross(self):
        self.assertTestData("test_isect_cross_01")

    def test_crosshatch_01(self):
        self.assertTestData("test_isect_crosshatch_01")

    def test_crosshatch_02(self):
        self.assertTestData("test_isect_crosshatch_02")

    def test_crosshatch_03(self):
        self.assertTestData("test_isect_crosshatch_03")

    def test_bowtie_circle(self):
        self.assertTestData("test_isect_bowtie_circle_01")

    def test_suzzane(self):
        self.assertTestData("test_isect_suzzane")

    def test_scribble(self):
        self.assertTestData("test_isect_scribble_01")

    def test_scatter(self):
        self.assertTestData("test_isect_scatter_01")

    def test_spiro(self):
        self.assertTestData("test_isect_spiro_01")


if __name__ == '__main__':
    unittest.main()

    # little sanity check to see if we miss checking any data
    test_data_real = set([
        f for f in os.listdir(TEST_DATA_PATH)
        if f.endswith(".py")])
    test_data_used = set([
        os.path.basename(m.__file__) for m in sys.modules.values()
        if m.__file__.startswith(TEST_DATA_PATH)])

    test_data_unused = test_data_real - test_data_used
    if test_data_unused:
        print("Untested modules:")
        for f in sorted(test_data_unused):
            print("   ", f)
