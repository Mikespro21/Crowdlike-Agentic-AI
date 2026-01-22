import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from crowdlike.ui import bg_ratio
r = bg_ratio()
total = sum(r.values())
blue = 100 * r["blue"] / total
white = 100 * r["white"] / total
purple = 100 * r["purple"] / total
print("Background ratio (by gradient stops):")
print(f"  white : {white:.1f}%")
print(f"  blue  : {blue:.1f}%")
print(f"  purple: {purple:.1f}%")
ok = abs(white-60) < 0.01 and abs(blue-30) < 0.01 and abs(purple-10) < 0.01
print("PASS" if ok else "FAIL")
