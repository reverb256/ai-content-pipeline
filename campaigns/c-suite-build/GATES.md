G1: CCO role contract exists  |  CHECK: cd /home/j_kro/Projects/ai-content-pipeline && test -f profiles/cco/role.md && echo CCO_ROLE_OK  |  EXPECT: CCO_ROLE_OK
G2: CRO role contract exists  |  CHECK: cd /home/j_kro/Projects/ai-content-pipeline && test -f profiles/cro/role.md && echo CRO_ROLE_OK  |  EXPECT: CRO_ROLE_OK
G3: CAIO role contract exists  |  CHECK: cd /home/j_kro/Projects/ai-content-pipeline && test -f profiles/caio/role.md && echo CAIO_ROLE_OK  |  EXPECT: CAIO_ROLE_OK
G4: All 3 profiles deployed to ~/.hermes/profiles  |  CHECK: for b in cco cro caio; do test -f ~/.hermes/profiles/$b/SOUL.md || exit 1; done && echo ALL_CSUITE_DEPLOYED  |  EXPECT: ALL_CSUITE_DEPLOYED
G5: All 3 have working model (longcat on nous)  |  CHECK: for b in cco cro caio; do hermes config get -p $b model.default 2>/dev/null | grep -q longcat || exit 1; done && echo MODELS_SET  |  EXPECT: MODELS_SET
G6: All 3 have SPOC skills delegation  |  CHECK: for b in cco cro caio; do hermes config get -p $b skills.external_dirs 2>/dev/null | grep -q hermes/skills || exit 1; done && echo SKILLS_DELEGATED  |  EXPECT: SKILLS_DELEGATED
G7: All 3 respond to a smoke test  |  CHECK: for b in cco cro caio; do timeout 40 hermes -p $b chat -q "Say OK" 2>&1 | grep -qi "ok" || exit 1; done && echo ALL_RESPOND  |  EXPECT: ALL_RESPOND
G8: All work committed and pushed  |  CHECK: cd /home/j_kro/Projects/ai-content-pipeline && git status --porcelain | wc -l | grep -q '^0$' && git log origin/main -1 --format=%s | grep -qiE "c-suite|cco|cro|caio" && echo COMMITTED_PUSHED  |  EXPECT: COMMITTED_PUSHED
