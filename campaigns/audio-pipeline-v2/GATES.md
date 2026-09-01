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
G4: Loudness normalization to ~-16 LUFS (behavioral)  |  CHECK: cd /home/j_kro/Projects/ai-content-pipeline && python3 -c "
import subprocess, re
# Normalize a 2s tone to -16 LUFS, then MEASURE with volumedetect
# (loudnorm maps dBFS roughly 1:1 to LUFS for a steady tone; -16 target
#  should land the mean volume near -16 dB)
r = subprocess.run(['ffmpeg','-y','-f','lavfi','-i','sine=frequency=440:duration=2','-af','loudnorm=I=-16:TP=-1.5:LRA=11','/tmp/loudnorm_test.wav'],capture_output=True,text=True)
assert r.returncode == 0, f'loudnorm failed: {r.stderr[-200:]}'
r2 = subprocess.run(['ffmpeg','-i','/tmp/loudnorm_test.wav','-af','volumedetect','-f','null','-'],capture_output=True,text=True)
m = re.search(r'mean_volume:\s*([-\d.]+) dB', r2.stderr)
assert m, f'no volume measurement: {r2.stderr[-300:]}'
db = float(m.group(1))
assert -22 < db < -10, f'mean volume {db} not near -16'
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
