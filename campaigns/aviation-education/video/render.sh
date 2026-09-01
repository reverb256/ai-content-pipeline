#!/usr/bin/env bash
cd /home/j_kro/Projects/ai-content-pipeline/campaigns/aviation-education/video

echo "=== Cleaning up test files ==="
python3 -c "import os; [os.remove(f) for f in ['test_deps.py','test_render.py','test_render1.sh','test_render2.sh','test_render3.sh','test_render4.sh','clean.py'] if os.path.exists(f)]"
echo "=== Cleaning old test_render directory ==="
python3 -c "import shutil; shutil.rmtree('media/videos/test_render', ignore_errors=True); print('cleaned')"

echo "=== Production render (720p30) ==="
manim -qh script.py Scene1_Hook Scene2_Stakes Scene3_GoTeam Scene4_PartySystem Scene5_Timeline Scene6_PublicRecord Scene7_InvisibleSystem Scene8_PayoffCTA --media_dir media/ 2>&1

echo "=== Done ==="
