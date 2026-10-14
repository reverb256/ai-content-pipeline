G1: Core modules import cleanly  |  CHECK: bash music/sunolocal/checks/g1_imports.sh  |  EXPECT: G1-OK
G2: Store roundtrip with negative controls  |  CHECK: bash music/sunolocal/checks/g2_store.sh  |  EXPECT: G2-OK
G3: Suno to engine mappings and defaults  |  CHECK: bash music/sunolocal/checks/g3_translate.sh  |  EXPECT: G3-OK
G4: Live HTTP API end-to-end with fixture engine  |  CHECK: bash music/sunolocal/checks/g4_api.sh  |  EXPECT: G4-OK
G5: Adapter contracts against stub renderer and mock HTTP  |  CHECK: bash music/sunolocal/checks/g5_adapters.sh  |  EXPECT: G5-OK
G6: Scope integrity and no shipped stubs  |  CHECK: bash music/sunolocal/checks/g6_scope.sh  |  EXPECT: G6-OK
