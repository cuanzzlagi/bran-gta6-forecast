#!/usr/bin/env python3
"""Launch-day Twitch viewer forecaster for make.fun's GTA VI forecast bounty.

Method: a launch day has a shape. For every comparable past launch in the
case file, take its release-day hourly viewers, align them by UTC hour of
the day, and divide by that launch's own hour-1 count. The median of those
ratios at each hour is the typical day-shape; the spread of the log ratios
is the honest uncertainty. The forecast for this case is its own hour-1
print multiplied by that shape, with quantiles from the spread.

Comparables that unlocked at midnight local time rolling across zones
(the way GTA VI unlocks) weigh double; a simultaneous global unlock is a
different shape. The case game's own category history (a premiere, not a
launch day) is left out of the shape. Standard library only, no network.
"""

import json
import math
import os
import sys
from datetime import datetime, timezone

Z = {0.05: -1.6448536269514722, 0.25: -0.6744897501960817, 0.5: 0.0,
     0.75: 0.6744897501960817, 0.95: 1.6448536269514722}
LEVELS = [0.05, 0.25, 0.5, 0.75, 0.95]


def parse_ts(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00")).astimezone(timezone.utc)


def median(xs):
    xs = sorted(xs)
    n = len(xs)
    if n == 0:
        return None
    return xs[n // 2] if n % 2 == 1 else (xs[n // 2 - 1] + xs[n // 2]) / 2


def day_shape(comparable, day_start):
    """Hour-of-day (1..24) -> viewers for the comparable's release day."""
    out = {}
    for pt in comparable.get("hourly") or []:
        try:
            t = parse_ts(pt["from"])
            v = float(pt["viewers"])
        except Exception:
            continue
        delta_h = (t - day_start).total_seconds() / 3600.0
        if 0 <= delta_h < 24 and v > 0:
            out[int(delta_h) + 1] = v
    return out


def comparable_weight(comp, own_name):
    name = (comp.get("name") or "").strip().lower()
    if own_name and name == own_name.strip().lower():
        return 0.0  # the case game's own category history: not a launch day
    unlock = (comp.get("unlock") or "").lower()
    if "midnight local" in unlock or "rolling" in unlock:
        return 2.0
    return 1.0


def forecast_case(case):
    known = (case.get("known") or [{}])[0]
    p = float(known.get("viewers") or 0)
    if p < 1:
        hist = case.get("history") or []
        p = float(hist[-1]["viewers"]) if hist else 1.0
    if p < 1:
        p = 1.0
    day0 = parse_ts(case["day_start"])
    own_name = (case.get("game") or {}).get("name") or ""

    # Weighted log-ratio samples per hour.
    samples = {h: [] for h in range(2, 25)}
    for comp in case.get("comparables") or []:
        w = comparable_weight(comp, own_name)
        if w <= 0:
            continue
        try:
            cday = parse_ts(comp["day_start"])
        except Exception:
            continue
        shape = day_shape(comp, cday)
        base = shape.get(1)
        if not base or base <= 0:
            continue
        for h in range(2, 25):
            v = shape.get(h)
            if v and v > 0:
                samples[h].append((math.log(v / base), w))

    hours = []
    for row in case.get("forecast") or []:
        h = int(row["hour"])
        samp = samples.get(h) or []
        if samp:
            # Weighted median of log ratios.
            samp_sorted = sorted(samp)
            total_w = sum(w for _, w in samp_sorted)
            acc = 0.0
            med_log = samp_sorted[-1][0]
            for val, w in samp_sorted:
                acc += w
                if acc >= total_w / 2:
                    med_log = val
                    break
            devs = sorted(abs(val - med_log) for val, _ in samp_sorted)
            mad = median(devs) or 0.0
            # 1.3x on the MAD spread: held-out launches land outside a raw
            # MAD band too often; the wider band prices the tails honestly.
            spread = 1.4826 * mad * 1.3
        else:
            med_log = 0.0
            spread = 0.0
        # Uncertainty floor grows through the day; cap it so the band stays
        # a forecast, not a shrug.
        s = min(1.10, max(0.20 + 0.012 * (h - 2), spread))
        med = p * math.exp(med_log)
        qs = []
        for tau in LEVELS:
            q = med * math.exp(Z[tau] * s)
            qs.append(min(1e9, max(1.0, round(q, 2))))
        qs = sorted(qs)
        hours.append({"hour": h, "q": qs})
    hours.sort(key=lambda r: r["hour"])
    return {"hours": hours}


def main():
    in_dir = os.environ.get("MAKEFUN_INPUT_DIR", "/input")
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    names = sorted(n for n in os.listdir(in_dir) if n.endswith(".in"))
    for name in names:
        with open(os.path.join(in_dir, name), encoding="utf-8") as f:
            case = json.load(f)
        result = forecast_case(case)
        out_name = name[:-3] + ".out"
        with open(os.path.join(out_dir, out_name), "w", encoding="utf-8") as f:
            json.dump(result, f)
    return 0


if __name__ == "__main__":
    sys.exit(main())
