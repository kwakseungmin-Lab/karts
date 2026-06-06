import base64, json, os, subprocess, time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Optional

for line in open('/Users/ksm2761/karts/.env'):
    line = line.strip()
    if line and not line.startswith('#') and '=' in line:
        k, v = line.split('=', 1)
        os.environ[k.strip()] = v.strip()

from openai import OpenAI
client = OpenAI()

PROJECT_ROOT = Path('/Users/ksm2761/karts/short-film-project')
FRAMES_DIR = PROJECT_ROOT / 'final/frames'
BRIDGE_KV = PROJECT_ROOT / 'images/key_visuals/kv_bridge.png'
SINGLE_FRAME = ' Single cinematic frame only — no comic panels, no split screens, no diptych, no multi-panel layout.'
TITLE_CARD_PROMPT = ('Cinematic title card for a medieval fantasy short film. Deep black background. '
    'Center composition: two crossed swords forming an X — a Western longsword with runic engravings '
    'on the left blade, and a Japanese nodachi with cherry blossom handguard on the right blade. '
    'Where the blades cross, a faint golden light glows. '
    'Below the crossed swords: elegant serif text The Weight of Honor in small-cap typography. '
    'Extremely desaturated near-black palette with only subtle warm gold glow at the blade crossing. '
    'For Honor cinematic title card style, photorealistic, dramatic chiaroscuro lighting, single frame, 1920x1080 16:9.')

def upscale(src, dst):
    subprocess.run(['ffmpeg','-y','-i',str(src),'-vf','scale=1920:1080:flags=lanczos','-q:v','2',str(dst)], check=True, capture_output=True)

def get_cuts():
    cuts = []
    for sc in range(4, 13):
        p = PROJECT_ROOT / f'storyboard/scene{sc:02d}_storyboard.json'
        if not p.exists(): continue
        with open(p) as f: d = json.load(f)
        scene_cuts = d.get('cuts') or []
        if not scene_cuts:
            for v in d.values():
                if isinstance(v, list) and v and isinstance(v[0], dict):
                    scene_cuts = v; break
        for i, cut in enumerate(scene_cuts, 1):
            is_title = (sc == 12 and i == 6)
            prompt = TITLE_CARD_PROMPT if is_title else (cut.get('frame_prompt','') + SINGLE_FRAME)
            char_refs = [r for r in cut.get('character_refs',[]) if r]
            refs = []
            if BRIDGE_KV.exists(): refs.append(BRIDGE_KV)
            char_path = PROJECT_ROOT / char_refs[0] if char_refs else None
            if char_path and char_path.exists(): refs.append(char_path)
            cuts.append({'scene':sc,'cut':i,'prompt':prompt,'refs':refs,
                         'out': FRAMES_DIR / f'scene{sc:02d}_cut{i:02d}_hd.png'})
    return cuts

def process(cut):
    label = f"scene{cut['scene']:02d}_cut{cut['cut']:02d}"
    refs = cut['refs']
    try:
        if refs:
            handles = [open(p,'rb') for p in refs]
            try:
                resp = client.images.edit(model='gpt-image-2', image=handles, prompt=cut['prompt'], size='1792x1024')
            finally:
                for h in handles: h.close()
        else:
            resp = client.images.generate(model='gpt-image-2', prompt=cut['prompt'], size='1792x1024', quality='high', n=1)
        data = base64.b64decode(resp.data[0].b64_json)
        tmp = cut['out'].with_suffix('.tmp.png')
        tmp.write_bytes(data)
        upscale(tmp, cut['out'])
        tmp.unlink(missing_ok=True)
        print(f'OK  {label}  bridge={len([r for r in refs if "bridge" in str(r)])} char={len(refs)-len([r for r in refs if "bridge" in str(r)])}')
        return label, True
    except Exception as e:
        print(f'FAIL {label}: {str(e)[:100]}')
        return label, False

cuts = get_cuts()
print(f'씬04~12 총 {len(cuts)}컷 재생성 시작')
results = {}
with ThreadPoolExecutor(max_workers=4) as ex:
    for label, ok in ex.map(process, cuts):
        results[label] = ok

ok = sum(results.values())
print(f'완료: {ok}/{len(cuts)}')
