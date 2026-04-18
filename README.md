# MusicXML Difficulty Analyzer

A Python tool for analyzing the difficulty of musical pieces from MusicXML files. This analyzer calculates a difficulty score (1-5) based on multiple musical factors.

## Overview

This tool automatically assesses the difficulty of musical exercises and pieces for music education. It uses absolute time measurements (milliseconds) rather than tempo deviation, making it independent of time signature and providing consistent results across different pieces.

## Features

- **Automatic Difficulty Rating**: Assigns a difficulty level from 1 (Very Easy) to 5 (Very Hard)
- **Comprehensive Analysis**: Considers multiple musical factors including:
  - Note duration and tempo
  - Pitch intervals
  - Key signatures and modulations
  - Accidentals
  - Rhythmic complexity
- **Tempo-Independent**: Uses absolute time (milliseconds) for consistent analysis
- **Detailed Metrics**: Provides detailed breakdown of all analyzed factors

## Installation

### Requirements

- Python 3.x
- Standard library only (no external dependencies)

### Setup

```bash
git clone https://github.com/sekineko/musicxml-difficulty-analyzer.git
cd musicxml-difficulty-analyzer
```

## Usage

### Basic Usage

```bash
python analyzer.py <path-to-musicxml-file>
```

### Example

```bash
python analyzer.py ~/music/exercise1.xml
```

### Sample Output

```
==================================================
MusicXML Difficulty Analysis V2 (MS-based)
==================================================
Actual BPM:       120
Avg Note (ms):    375.0ms
Base Score:       10.0
Penalty Points:   15
Final Score:      25.0
Difficulty:       4/5 (Hard)

Metrics:
  Average note:   0.75 quarters = 375.0ms
  Short notes:    45.0% (< 250ms)
  Very short:     12.0% (<= 125ms)
  Key signature:  2 (sharps/flats)
  Key changes:    1 (modulations)
  Avg key diff:   2.5 (avg abs sharps/flats)
  Accidentals:    8.5%
  Avg interval:   3.2 semitones
  Total notes:    120
==================================================
```

## How It Works

### Difficulty Calculation

The analyzer calculates difficulty using a two-step scoring system:

#### 1. Base Score (from average note duration)

The base score is calculated from the average note duration in milliseconds:

- **Baseline**: 500ms note = 0 points
- **Shorter notes** (< 500ms): Harder → positive points
  - Uses inverse relationship: halving duration doubles difficulty
  - Formula: `(500 / avg_note_ms - 1) × 30`
- **Longer notes** (> 500ms): Easier → negative points
  - Formula: `(500 - avg_note_ms) / 500 × 30`

#### 2. Penalty Points (complexity factors)

Additional difficulty points are added based on various musical factors:

**Short Note Penalties:**
- \> 60% short notes (< 250ms): +15 points
- \> 40% short notes: +10 points
- \> 20% short notes: +5 points

**Very Short Note Penalties:**
- \> 40% very short notes (<= 125ms): +15 points
- \> 20% very short notes: +10 points
- \> 10% very short notes: +5 points

**Key Signature Penalties:**
- +3 points per sharp/flat (e.g. 2 sharps = +6, 4 flats = +12, max 7 = +21)

**Modulation Penalties:**
- ≥ 2 key changes: +5 points
- ≥ 1 key change: +3 points

**Accidental Penalties:**
- \> 25% notes with accidentals: +25 points
- \> 20% notes with accidentals: +20 points
- \> 15% notes with accidentals: +15 points
- \> 10% notes with accidentals: +10 points
- \> 5% notes with accidentals: +5 points

**Interval Penalties:**
- Average interval > 4 semitones: +10 points
- Average interval > 3 semitones: +5 points

#### 3. Final Difficulty Rating

```
Final Score = Base Score + Penalty Points
```

Difficulty levels are assigned based on the final score:

| Score Range | Difficulty | Label |
|------------|-----------|-------|
| ≤ -20 | 1 | Very Easy |
| -19 to -6 | 2 | Easy |
| -5 to 10 | 3 | Medium |
| 11 to 26 | 4 | Hard |
| ≥ 27 | 5 | Very Hard |

### Analyzed Metrics

The tool analyzes the following aspects of the music:

1. **Tempo (BPM)**: Extracted from the first MusicXML `<sound tempo="">` attribute (defaults to 120 BPM if not specified; tempo changes during the piece are ignored)
2. **Note Duration**: Average note length in milliseconds
3. **Short Notes**: Percentage of notes < 250ms
4. **Very Short Notes**: Percentage of notes ≤ 125ms
5. **Key Signature**: Number of sharps or flats
6. **Modulations**: Number of key changes throughout the piece
7. **Accidentals**: Percentage of notes with accidentals
8. **Pitch Intervals**: Average jump between consecutive notes (in semitones)
9. **Total Notes**: Number of notes in the piece (excluding rests and chord notes)

## Important Notes

### What This Tool Analyzes

- **Single melodic line**: Designed for monophonic musical exercises
- **Performance difficulty**: Focuses on factors relevant to reading and performing music
- **Tempo-aware**: Converts note durations to absolute time (milliseconds) for consistent analysis

### What This Tool Does NOT Consider

- **Harmonic complexity**: Does not analyze chords or polyphony
- **Lyrics/text**: Ignores text underlay
- **Dynamics**: Does not consider volume markings
- **Articulation**: Does not analyze staccato, legato, etc.
- **Performance techniques**: Does not consider ornaments, trills, etc.
- **Range**: Does not penalize for extreme high or low notes
- **Timbre**: Instrument-specific difficulties are not considered

### Limitations

1. **Subjectivity**: Musical difficulty is inherently subjective. This tool provides a quantitative baseline but may not match every musician's perception.

2. **Context-dependent**: The same piece may be easier or harder depending on:
   - Student's background and experience
   - Familiarity with the key or scale
   - Musical style and tradition

3. **MusicXML Quality**: Results depend on accurate MusicXML encoding:
   - Tempo markings should be present (defaults to 120 BPM if missing)
   - Only the first tempo marking is used (tempo changes are ignored)
   - Notes must be properly encoded
   - Time signatures should be accurate

4. **Educational Level**: This tool was calibrated for intermediate-level musical exercises. It may not accurately assess:
   - Beginner exercises (may over-estimate difficulty)
   - Advanced contemporary music (may under-estimate difficulty)

### Calibration Notes

The scoring thresholds were calibrated based on:
- Traditional music exercise books (Ladukhin, Berkowitz, etc.)
- Music pedagogy and performance practice
- Empirical testing with music students

You may need to adjust the thresholds in the source code if your use case differs significantly.

## Use Cases

- **Curriculum Design**: Automatically sort musical exercises by difficulty
- **Adaptive Learning**: Select appropriate pieces based on student level
- **Music Database**: Tag and organize large collections of musical exercises
- **Progress Tracking**: Measure student advancement through difficulty levels
- **Composition**: Get objective feedback on newly composed exercises or arrangements

## Technical Details

### MusicXML Parsing

The tool uses Python's built-in `xml.dom.minidom` parser to extract:
- `<sound tempo="">`: BPM
- `<divisions>`: Time resolution
- `<key><fifths>`: Key signature
- `<note>`: Pitch, duration, accidentals
- `<pitch><step><octave><alter>`: Note information

### MIDI Note Conversion

Pitches are converted to MIDI note numbers (0-127) for interval calculation:
```
MIDI Note = (octave + 1) × 12 + step + alter
```

### Time Calculation

Note durations are converted from MusicXML duration units to milliseconds:
```
Quarter Note Duration (ms) = 60000 / BPM
Note Duration (ms) = (duration / divisions) × Quarter Note Duration
```

## Contributing

Contributions are welcome! Areas for improvement:

- [ ] Add support for polyphonic analysis
- [ ] Consider vocal range difficulty
- [ ] Detect difficult rhythmic patterns
- [ ] Machine learning-based calibration
- [ ] Support for other notation formats (MIDI, MEI)
- [ ] Web interface
- [ ] Batch processing mode

## License

MIT License - see [LICENSE](LICENSE) file for details

## Author

sekineko - https://github.com/sekineko

## Acknowledgments

This tool was developed for use in music education and has been used to analyze thousands of exercises from classical music textbooks.

---

## Advanced Usage

### Using as a Library

You can import and use the analyzer in your own Python scripts:

```python
from analyzer import analyze_musicxml

result = analyze_musicxml("path/to/file.xml")

print(f"Difficulty: {result['difficulty']}/5")
print(f"Score: {result['final_score']}")
print(f"Metrics: {result['metrics']}")
```

### Batch Processing

For analyzing multiple files:

```bash
for file in exercises/*.xml; do
  echo "=== $file ==="
  python analyzer.py "$file"
  echo
done
```

### JSON Output (Custom)

Modify the script to output JSON for integration with other tools:

```python
import json
result = analyze_musicxml("file.xml")
print(json.dumps(result, indent=2))
```

## Troubleshooting

### "No notes found" Error

- Check that your MusicXML file contains `<note>` elements
- Ensure notes have `<pitch>` and `<duration>` elements
- Verify the file is valid MusicXML

### Unexpected Difficulty Rating

- Check the BPM: ensure `<sound tempo="">` is set correctly
  - **Note**: If no tempo is specified in the MusicXML file, the analyzer defaults to 120 BPM
- Verify time signature and note durations are accurate
- Review the detailed metrics to see which factors contribute most to the score

### Division by Zero

- Ensure the file has at least one note with duration
- Check that `<divisions>` is properly set

---

**For questions, bug reports, or feature requests, please open an issue on GitHub.**
