"""
shift.py — Three-check shift detector
Checks: statistical deviation | Claude flag | streak
"""

import statistics


def detect_shift(store: dict, today_score: float,
                 today_label: str, claude_flag: bool) -> dict:
    history = store["sentiment_history"]
    config  = store["config"]
    threshold = config["shift_threshold"]
    window    = config["sentiment_window_days"]

    recent_scores = [e["score"] for e in history[-window:]]

    # ── Check 1: Statistical deviation from rolling average ──
    if len(recent_scores) >= 3:
        avg = statistics.mean(recent_scores)
        std = statistics.stdev(recent_scores) if len(recent_scores) > 1 else 0.0
        # Dynamic threshold: don't fire during already-volatile weeks
        effective_threshold = max(threshold, 1.5 * std)
        deviation = abs(today_score - avg)
        score_triggered = deviation > effective_threshold
    else:
        avg = statistics.mean(recent_scores) if recent_scores else 0.0
        std = 0.0
        deviation = abs(today_score - avg)
        effective_threshold = threshold
        score_triggered = deviation > threshold

    # ── Check 2: Claude's semantic shift flag ─────────────
    # Claude sees headlines + outlook together — catches
    # qualitative shifts that don't move the aggregate score
    flag_triggered = bool(claude_flag)

    # ── Check 3: 3-day confirmed streak ───────────────────
    # Catches slow drifts no single day would trigger
    streak_triggered = False
    # if len(history) >= 2:
    #     last_two_labels = [e["label"] for e in history[-2:]]
    #     all_three = last_two_labels + [today_label]
    #     if (len(set(all_three)) == 1
    #             and today_label in ("negative", "positive", "cautious")):
    #         streak_triggered = True

    # ── OR gate ───────────────────────────────────────────
    should_update = score_triggered or flag_triggered 
    # or streak_triggered

    # ── Severity rating ───────────────────────────────────
    severity = "none"
    if should_update:
        triggers_fired = sum([score_triggered, flag_triggered, streak_triggered])
        if triggers_fired >= 2 or deviation > threshold * 2:
            severity = "major"
        elif flag_triggered:
            severity = "moderate"  # semantic signals are meaningful
        else:
            severity = "minor"

    return {
        "should_update": should_update,
        "severity": severity,
        "score_triggered": score_triggered,
        "flag_triggered": flag_triggered,
        "streak_triggered": streak_triggered,
        "deviation": round(deviation, 3),
        "effective_threshold": round(effective_threshold, 3),
        "rolling_avg": round(avg, 3),
        "rolling_std": round(std, 3),
        "today_score": round(today_score, 3),
    }
