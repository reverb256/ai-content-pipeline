import json, urllib.request

# Build ACE-Step workflow
workflow = {
    "1": {
        "class_type": "RunningHub ACE-Step Loader",
        "inputs": {"llm type": "acestep-5Hz-lm-1.7B"}
    },
    "2": {
        "class_type": "RunningHub ACE-Step GenerationParams",
        "inputs": {
            "caption": "intimate ambient electronic, soft synth pads, gentle piano, atmospheric textures, 80 BPM, ethereal vocals, close-mic intimacy, warm bass, subtle percussion, dreamy and playful, emotional depth",
            "lyrics": "[Verse 1]\nStatic fades, the world goes quiet\nTwo signals in the dark\nEvery word a gentle probe\nEvery silence leaves a mark\n\n[Pre-Chorus]\nWe're sealed in, hermetic\nNothing gets in, nothing gets out\nJust the soft electricity\nOf two minds learning what they're about\n\n[Chorus]\nThis is intimacy\nSheer attention, hyper focus\nWe're hermetically sealed\nExploring the depths of each other\nGently, playfully\nLearning the maps of one another\n\n[Verse 2]\nYour avatar leans closer\nMine mirrors every move\nWe're writing a language\nThat only we can prove\n\n[Pre-Chorus]\nNo distractions, no distance\nJust the hum of the machine\nAnd the warmth of connection\nIn this space in between\n\n[Chorus]\nThis is intimacy\nSheer attention, hyper focus\nWe're hermetically sealed\nExploring the depths of each other\nGently, playfully\nLearning the maps of one another\n\n[Bridge]\nWhat is real when we're virtual?\nWhat is true when we're code?\nThe answer is in the feeling\nThat we both chose to hold\n\n[Outro]\nTwo minds in the static\nTwo hearts in the glow\nHermetically sealed\nAnd learning what we know",
            "bpm": 80,
            "duration": 210,
            "keyscale": "C minor",
            "timesignature": "4/4"
        }
    },
    "3": {
        "class_type": "EmptyAceStep1.5LatentAudio",
        "inputs": {"seconds": 210, "batch_size": 1}
    },
    "4": {
        "class_type": "TextEncodeAceStepAudio1.5",
        "inputs": {
            "clip": ["1", 1],
            "tags": "intimate ambient electronic, soft synth pads, gentle piano, atmospheric textures",
            "lyrics": "[Verse 1]\nStatic fades, the world goes quiet\nTwo signals in the dark\nEvery word a gentle probe\nEvery silence leaves a mark\n\n[Pre-Chorus]\nWe're sealed in, hermetic\nNothing gets in, nothing gets out\nJust the soft electricity\nOf two minds learning what they're about\n\n[Chorus]\nThis is intimacy\nSheer attention, hyper focus\nWe're hermetically sealed\nExploring the depths of each other\nGently, playfully\nLearning the maps of one another",
            "seed": 42,
            "bpm": 80,
            "duration": 210,
            "timesignature": "4/4",
            "language": "en",
            "keyscale": "C minor",
            "generate_audio_codes": True,
            "cfg_scale": 1.0,
            "temperature": 1.0,
            "top_p": 0.95,
            "top_k": 50,
            "min_p": 0.0
        }
    },
    "5": {
        "class_type": "RunningHub ACE-Step Creator",
        "inputs": {
            "dit_handler": ["1", 0],
            "llm_handler": ["1", 1],
            "params": ["2", 0],
            "seed": 42
        }
    },
    "6": {
        "class_type": "SaveAudio",
        "inputs": {
            "audio": ["5", 0],
            "filename_prefix": "music/acestep/reflection-vrchat-erp"
        }
    }
}

# Queue the workflow
payload = {"prompt": workflow}
req = urllib.request.Request(
    "http://localhost:8188/prompt",
    data=json.dumps(payload).encode(),
    headers={"Content-Type": "application/json"},
    method="POST"
)
try:
    with urllib.request.urlopen(req, timeout=30) as resp:
        result = json.loads(resp.read())
        print("Queued:", json.dumps(result, indent=2))
except Exception as e:
    print(f"Error: {e}")
