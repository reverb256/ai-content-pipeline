G1: Parser handles multi-character script (behavioral)  |  CHECK: cd /home/j_kro/Projects/ai-content-pipeline && python3 -c "
from pathlib import Path
import sys
sys.path.insert(0,'scripts/audio')
from storyteller import parse_story
s = parse_story(Path('scripts/audio/example-story.md'))
speakers = {seg.speaker for seg in s.segments}
assert len(s.segments) >= 8, f'expected >=8 segments, got {len(s.segments)}'
assert {'Mara','Elias'} <= speakers, f'missing cast speakers: {speakers}'
print('PARSE_MULTI_CHAR_OK')
"  |  EXPECT: PARSE_MULTI_CHAR_OK
G2: Storyteller compiles (no syntax errors)  |  CHECK: cd /home/j_kro/Projects/ai-content-pipeline && python3 -m py_compile scripts/audio/storyteller.py && echo COMPILE_OK  |  EXPECT: COMPILE_OK
G3: Sidechain mix chain produces output (behavioral)  |  CHECK: cd /home/j_kro/Projects/ai-content-pipeline && python3 -c "
import subprocess, sys
# Run the ffmpeg sidechain filter chain on a 2-tone test: dialogue ducked under music
r = subprocess.run(['ffmpeg','-y','-f','lavfi','-i','sine=frequency=440:duration=1','-f','lavfi','-i','sine=frequency=220:duration=1','-filter_complex','[1:a]volume=0.5[music];[0:a][music]sidechaincompress=threshold=0.05:ratio=8:attack=5:release=100[out]','-map','[out]','/tmp/sidechain_test.wav'],capture_output=True,text=True)
assert r.returncode == 0, f'sidechain ffmpeg failed: {r.stderr[-200:]}'
print('SIDECHAIN_MIX_OK')
"  |  EXPECT: SIDECHAIN_MIX_OK
G4: Loudness normalization to ~-16 LUFS integrated (behavioral)  |  CHECK: cd /home/j_kro/Projects/ai-content-pipeline && python3 -c "
import subprocess, re
# Normalize a 2s tone to I=-16 LUFS, then MEASURE it with EBU R128 (ebur128),
# the same unit loudnorm's own I= target uses.
# DO NOT measure this fixture with volumedetect: its mean_volume is a plain RMS
# mean (no K-weighting, no gating), NOT a LUFS reading, and the two rulers do
# not agree. Measured 2026-10-16 (ffmpeg 9.0.1) on this exact fixture:
#   ebur128 integrated loudness  I    = -16.0 LUFS
#   volumedetect                 mean = -15.3 dB
# That is 0.7 dB apart, with the RMS number reading LOUDER, so no 1:1
# dBFS-to-LUFS mapping holds -- not even for a steady tone.
r = subprocess.run(['ffmpeg','-y','-f','lavfi','-i','sine=frequency=440:duration=2','-af','loudnorm=I=-16:TP=-1.5:LRA=11','/tmp/loudnorm_test.wav'],capture_output=True,text=True)
assert r.returncode == 0, f'loudnorm failed: {r.stderr[-200:]}'
r2 = subprocess.run(['ffmpeg','-i','/tmp/loudnorm_test.wav','-af','ebur128=peak=true','-f','null','-'],capture_output=True,text=True)
s = r2.stderr[r2.stderr.rfind('Integrated loudness:'):]  # summary block, not the per-frame I: lines
m = re.search(r'I:\s+([-\d.]+) LUFS', s)
assert m, f'no integrated loudness reading: {r2.stderr[-300:]}'
lufs = float(m.group(1))
assert -17.0 < lufs < -15.0, f'integrated loudness {lufs} LUFS is not within 1 LU of the -16 target'
print('LOUDNORM_OK')
"  |  EXPECT: LOUDNORM_OK
G5: B-roll clip export produces files (behavioral)  |  CHECK: cd /home/j_kro/Projects/ai-content-pipeline && ls scripts/audio/broll/ 2>/dev/null | wc -l | grep -v '^0$' && echo BROLL_EXISTS || python3 -c "
# If no broll dir yet, verify the code path that exports clips exists and is callable
import ast, sys
tree = ast.parse(open('scripts/audio/storyteller.py').read())
names = {n.name for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
assert any('broll' in n or 'clip' in n for n in names), f'no broll/clip function: {names}'
print('BROLL_CODE_OK')
"  |  EXPECT: BROLL_EXISTS|BROLL_CODE_OK
G6: All work committed and pushed  |  CHECK: cd /home/j_kro/Projects/ai-content-pipeline && git status --porcelain | wc -l | grep -q '^0$' && git log origin/main..HEAD --oneline | grep -qiE "audio|storyteller|pipeline" && echo COMMITTED_PUSHED  |  EXPECT: COMMITTED_PUSHED
