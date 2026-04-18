#!/usr/bin/env python3
# coding:utf-8
"""
MusicXML Difficulty Analyzer V2
Uses absolute time (milliseconds) instead of tempo deviation.
This approach is independent of time signature and provides more consistent results.
"""

import sys
from xml.dom import minidom
import math

def get_midi_note(step, octave, alter=0):
    """Convert step, octave, alter to MIDI note number."""
    step_to_number = {'C': 0, 'D': 2, 'E': 4, 'F': 5, 'G': 7, 'A': 9, 'B': 11}
    base = step_to_number.get(step, 0)
    midi_note = (octave + 1) * 12 + base + alter
    return midi_note

def analyze_musicxml(xml_path):
    """Analyze a MusicXML file and return difficulty analysis."""

    # Parse XML file
    xdoc = minidom.parse(xml_path)

    # Get BPM from the first sound tempo directive
    sound_elems = xdoc.getElementsByTagName("sound")
    actual_bpm = 120  # default
    for sound in sound_elems:
        if sound.hasAttribute("tempo"):
            actual_bpm = float(sound.getAttribute("tempo"))
            break

    # Get divisions (how many units per quarter note)
    divisions_elem = xdoc.getElementsByTagName("divisions")
    divisions = int(divisions_elem[0].firstChild.nodeValue) if divisions_elem else 1

    # Analyze key signatures and detect modulations
    key_elems = xdoc.getElementsByTagName("key")
    sharps_or_flats = 0
    key_changes = 0
    total_abs_sharps_flats = 0
    key_count = 0
    prev_key = None

    for key_elem in key_elems:
        fifths_elem = key_elem.getElementsByTagName("fifths")
        if fifths_elem and fifths_elem[0].firstChild:
            current_key = int(fifths_elem[0].firstChild.nodeValue)

            # Track first key signature
            if key_count == 0:
                sharps_or_flats = current_key

            # Count key changes (modulations)
            if prev_key is not None and current_key != prev_key:
                key_changes += 1

            # Accumulate absolute sharps/flats for averaging
            total_abs_sharps_flats += abs(current_key)
            key_count += 1
            prev_key = current_key

    # Calculate average absolute sharps/flats across all keys
    avg_abs_sharps_flats = total_abs_sharps_flats / key_count if key_count > 0 else 0

    # Analyze notes
    notes = xdoc.getElementsByTagName("note")
    total_duration = 0
    note_count = 0
    short_note_count = 0      # < 300ms
    very_short_note_count = 0 # <= 150ms
    accidental_count = 0
    total_interval = 0
    interval_count = 0
    prev_midi = None

    # Calculate quarter note duration in ms
    quarter_note_ms = 60000 / actual_bpm

    for note in notes:
        # Skip rests and chord notes
        if note.getElementsByTagName("rest") or note.getElementsByTagName("chord"):
            continue

        duration_elem = note.getElementsByTagName("duration")
        if duration_elem and duration_elem[0].firstChild:
            duration = int(duration_elem[0].firstChild.nodeValue)
            total_duration += duration
            note_count += 1

            # Count short and very short notes (in milliseconds)
            duration_quarters = duration / divisions
            duration_ms = duration_quarters * quarter_note_ms

            if duration_ms < 250:
                short_note_count += 1
            if duration_ms <= 125:
                very_short_note_count += 1

        # Count accidentals
        if note.getElementsByTagName("accidental"):
            accidental_count += 1

        # Calculate interval (pitch jump)
        pitch_elem = note.getElementsByTagName("pitch")
        if pitch_elem and len(pitch_elem) > 0:
            step_elem = pitch_elem[0].getElementsByTagName("step")
            octave_elem = pitch_elem[0].getElementsByTagName("octave")

            if step_elem and octave_elem:
                step = step_elem[0].firstChild.nodeValue
                octave = int(octave_elem[0].firstChild.nodeValue)

                alter = 0
                alter_elem = pitch_elem[0].getElementsByTagName("alter")
                if alter_elem and len(alter_elem) > 0 and alter_elem[0].firstChild:
                    alter = int(alter_elem[0].firstChild.nodeValue)

                midi_note = get_midi_note(step, octave, alter)

                if prev_midi is not None:
                    interval = abs(midi_note - prev_midi)
                    total_interval += interval
                    interval_count += 1

                prev_midi = midi_note

    if note_count == 0:
        return {"error": "No notes found"}

    # Calculate metrics
    avg_note_quarters = (total_duration / divisions) / note_count
    avg_note_ms = avg_note_quarters * quarter_note_ms
    short_note_ratio = short_note_count / note_count
    very_short_note_ratio = very_short_note_count / note_count
    accidental_ratio = accidental_count / note_count
    avg_interval = total_interval / interval_count if interval_count > 0 else 0

    # Calculate base score from average note duration (ms)
    # Baseline: 500ms note = 0 points
    # Shorter = harder (positive points), Longer = easier (negative points)
    baseline_ms = 500
    if avg_note_ms < baseline_ms:
        # Shorter notes = harder
        # Use inverse relationship: halving time doubles difficulty
        base_score = (baseline_ms / avg_note_ms - 1) * 30
    else:
        # Longer notes = easier
        base_score = (baseline_ms - avg_note_ms) / baseline_ms * 30

    # Calculate penalty points (complexity penalties)
    penalty_points = 0

    # Short note penalty
    if short_note_ratio > 0.6:
        penalty_points += 15
    elif short_note_ratio > 0.4:
        penalty_points += 10
    elif short_note_ratio > 0.2:
        penalty_points += 5

    # Very short note penalty
    if very_short_note_ratio > 0.4:
        penalty_points += 15
    elif very_short_note_ratio > 0.2:
        penalty_points += 10
    elif very_short_note_ratio > 0.1:
        penalty_points += 5

    # Key signature penalty
    penalty_points += min(int(avg_abs_sharps_flats), 7) * 3

    # Modulation penalty
    if key_changes >= 2:
        penalty_points += 5
    elif key_changes >= 1:
        penalty_points += 3

    # Accidental penalty
    if accidental_ratio > 0.25:
        penalty_points += 25
    elif accidental_ratio > 0.20:
        penalty_points += 20
    elif accidental_ratio > 0.15:
        penalty_points += 15
    elif accidental_ratio > 0.10:
        penalty_points += 10
    elif accidental_ratio > 0.05:
        penalty_points += 5

    # Interval penalty
    if avg_interval > 4:
        penalty_points += 10
    elif avg_interval > 3:
        penalty_points += 5

    # Final score = base_score + penalties
    final_score = base_score + penalty_points

    # Determine difficulty (1-5) based on final score
    if final_score <= -20:
        difficulty = 1
        difficulty_label = "Very Easy"
    elif final_score < -6:
        difficulty = 2
        difficulty_label = "Easy"
    elif final_score < 10:
        difficulty = 3
        difficulty_label = "Medium"
    elif final_score < 26:
        difficulty = 4
        difficulty_label = "Hard"
    else:
        difficulty = 5
        difficulty_label = "Very Hard"

    return {
        "actual_bpm": actual_bpm,
        "avg_note_ms": avg_note_ms,
        "base_score": base_score,
        "penalty_points": penalty_points,
        "final_score": final_score,
        "difficulty": difficulty,
        "difficulty_label": difficulty_label,
        "metrics": {
            "avg_note_quarters": avg_note_quarters,
            "avg_note_ms": avg_note_ms,
            "short_note_ratio": short_note_ratio,
            "very_short_note_ratio": very_short_note_ratio,
            "key_signature": sharps_or_flats,
            "key_changes": key_changes,
            "avg_abs_sharps_flats": avg_abs_sharps_flats,
            "accidental_ratio": accidental_ratio,
            "avg_interval": avg_interval,
            "total_notes": note_count
        }
    }

def main():
    if len(sys.argv) < 2:
        print("Usage: python analyzer_v2.py <musicxml_file>")
        sys.exit(1)

    xml_path = sys.argv[1]
    result = analyze_musicxml(xml_path)

    if "error" in result:
        print(f"Error: {result['error']}")
        sys.exit(1)

    # Print results
    print("=" * 50)
    print("MusicXML Difficulty Analysis V2 (MS-based)")
    print("=" * 50)
    print(f"Actual BPM:       {result['actual_bpm']}")
    print(f"Avg Note (ms):    {result['avg_note_ms']:.1f}ms")
    print(f"Base Score:       {result['base_score']:.1f}")
    print(f"Penalty Points:   {result['penalty_points']}")
    print(f"Final Score:      {result['final_score']:.1f}")
    print(f"Difficulty:       {result['difficulty']}/5 ({result['difficulty_label']})")
    print()
    print("Metrics:")
    print(f"  Average note:   {result['metrics']['avg_note_quarters']:.2f} quarters = {result['metrics']['avg_note_ms']:.1f}ms")
    print(f"  Short notes:    {result['metrics']['short_note_ratio']:.1%} (< 250ms)")
    print(f"  Very short:     {result['metrics']['very_short_note_ratio']:.1%} (<= 125ms)")
    print(f"  Key signature:  {result['metrics']['key_signature']} (sharps/flats)")
    print(f"  Key changes:    {result['metrics']['key_changes']} (modulations)")
    print(f"  Avg key diff:   {result['metrics']['avg_abs_sharps_flats']:.1f} (avg abs sharps/flats)")
    print(f"  Accidentals:    {result['metrics']['accidental_ratio']:.1%}")
    print(f"  Avg interval:   {result['metrics']['avg_interval']:.1f} semitones")
    print(f"  Total notes:    {result['metrics']['total_notes']}")
    print("=" * 50)

if __name__ == "__main__":
    main()
