"""명예의 무게 — ViMax script2video 실행 스크립트."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from pipelines.script2video_pipeline import Script2VideoPipeline

script = """
EXT. HEATHMOOR BATTLEFIELD - DAWN (PRE-TITLE SEQUENCE)
Extreme aerial wide shot. A fog-covered medieval battlefield at dawn. Three faction banners —
Knight cross, Viking raven, Samurai chrysanthemum — half-buried in mud.
Crows circle overhead. The air smells of blood and rust.
APOLLYON (V.O.): (gravelly, philosophical)
In this world, there are wolves and there are sheep.
Close-up: a crow perched on a rusted sword blade, feather trembling in the wind.
Slow tracking shot across battlefield ruins — broken swords, torn flags, collapsed armor.
APOLLYON (V.O.):
Which are you?

EXT. ASHFELD VILLAGE - NIGHT (FLASHBACK - THREE DAYS AGO)
AIDEN (30s, Knight Warden, dark steel armor scarred with battle) stands rigid as
Blackstone soldiers torch a village. Women and children scream.
BLACKSTONE COMMANDER: Execute the order, Warden.
Aiden grips his longsword. His gauntleted fist shakes. He stares at a child cowering behind a barrel.
AIDEN (V.O.): (internal monologue, haunted)
Honor. What does that word mean, when the sword points at the innocent?
He throws down his sword. He turns and walks away from the massacre.
BLACKSTONE COMMANDER: Deserter! DESERTER!
Aiden runs into the fog without looking back.

EXT. THE MYRE WETLANDS - DUSK (FLASHBACK - TWO DAYS AGO)
KAGEMASA (40s, Kensei Samurai, lacquered black-and-gold armor, menpō face mask)
leads a column of samurai warriors through misty bamboo marshlands heading west.
Viking war horns blast in the distance.
Suddenly — arrows rain from the trees. Vikings ambush.
His warriors fall one by one. Kagemasa fights desperately, cutting down Vikings.
When the battle ends, he is the only one standing.
He kneels beside his fallen comrades, removes his menpō, and bows his head in silence.
KAGEMASA (V.O.): (Japanese-accented Korean)
I have lost everything except my blade and my duty.

EXT. THE BORDER BRIDGE - FOGGY MORNING (PRESENT)
A crumbling stone bridge spans a dark river between Ashfeld and The Myre.
Fog rolls in thick. Aiden emerges from one end. Kagemasa from the other.
They stop. Twenty meters apart. Eyes lock.
Neither speaks — they do not share a language.
Aiden draws his longsword. Kagemasa draws his nodachi.
They adopt fighting stances. Wind stirs the fog between them.
Long tense beat. A crow takes flight.

EXT. THE BORDER BRIDGE - CONTINUOUS (THE DUEL BEGINS)
Kagemasa moves first — a powerful overhead strike. Aiden barely deflects it, staggering.
Sparks fly as steel meets steel. The bridge shakes.
Aiden counters with a shield bash, forcing Kagemasa back.
They exchange furious blows — longsword style vs. nodachi technique,
two entirely different martial philosophies colliding.
Insert: close-up of crossed blades locked, both warriors straining.
Insert: Aiden's scarred eye, focused and calculating.
Insert: Kagemasa's eyes above his menpō, ancient and unreadable.

EXT. THE BORDER BRIDGE - MOMENTS LATER (BRIEF RESPITE)
Both warriors breathe hard. They circle each other warily.
Kagemasa notices Aiden's crossed-out Blackstone insignia on his pauldron.
Aiden sees the empty scabbards on Kagemasa's belt — the places where his fallen comrades' tokens would hang.
A moment of unspoken recognition. Two men broken by the same war.

EXT. THE BORDER BRIDGE - CONTINUOUS (THE SECOND CLASH)
The duel resumes — but now more desperate, more personal.
Kagemasa executes a lightning-fast spinning strike.
Aiden barely dodges, the blade grazing his cheek.
Aiden answers with a powerful two-handed vertical slash.
The blow catches Kagemasa's pauldron and sends him to one knee.
Aiden raises his sword for the killing blow — point aimed at Kagemasa's exposed throat.
He freezes.

EXT. THE BORDER BRIDGE - THE MOMENT OF CHOICE (SLOW MOTION)
Time slows.
Aiden's sword tip hovers inches from Kagemasa's throat.
Kagemasa does not flinch. He closes his eyes. He accepts death with dignity.
Aiden stares at him. Something shifts in Aiden's eyes.
He lowers the sword.
Kagemasa opens his eyes. Surprised. He rises slowly, nodachi still in hand.
He could strike now. He doesn't.
The two warriors stand facing each other — both alive, both choosing not to kill.
AIDEN (quietly, in his own language Kagemasa cannot understand):
I'm done.
Kagemasa sheathes his nodachi. He performs a formal bow — warrior to warrior.
Aiden, moved, performs a knight's salute in return. A gesture of equal respect.

EXT. DISTANT HILLS - SAME MOMENT
War horns blast from multiple directions. Black banners on the horizon — armies converging.
Both the Knight and Samurai turn to look.
Their brief peace shatters against the thunder of ten thousand boots.

EXT. THE BORDER BRIDGE - CONTINUOUS (DEPARTURE)
Aiden picks up his longsword. He looks at Kagemasa one last time.
Kagemasa nods — a silent acknowledgment.
They turn their backs on each other and walk into their respective armies.
Slow pull back aerial shot: two tiny figures walking away from the bridge,
consumed by advancing armies, the fog closing behind them.

EXT. THE BORDER BRIDGE - AFTER THE BATTLE (EPILOGUE)
The bridge stands empty. Wind carries ash.
A single crow lands on the bridge railing where the two warriors stood.
The fog swallows everything.
FADE TO BLACK.
TITLE CARD: 명예의 무게 (The Weight of Honor)
APOLLYON (V.O.): (final whisper)
Wolves... or sheep?
The question hangs in silence.
"""

user_requirement = """
- Target runtime: 7 to 10 minutes
- Shot duration: 8 seconds per shot
- Style: Dark epic medieval cinematic, photorealistic
- Color: Desaturated near-grayscale for prologue and epilogue,
  blue-grey for battle scenes, warm bright morning light for the climax choice moment
- No dialogue title cards — convey emotion through visuals and motion
- For Honor E3 2015 cinematic trailer aesthetic
- Camera work: dramatic wide establishing shots, extreme close-ups for emotion, slow aerial pullbacks
- Characters:
  * AIDEN: dark steel partial plate armor with chain mail, barbuta helmet showing jaw,
    two-handed longsword, Blackstone insignia scratched off left pauldron,
    scar over left eye, brown hair
  * KAGEMASA: lacquered black-gold lamellar armor (ō-yoroi style), black menpō face mask,
    nodachi, removes menpō in scene 9 to reveal weathered 40s Japanese face
- Music: silence except ambient wind and metal
- Final shot: aerial pullback from bridge, fog closes
"""

style = "For Honor cinematic trailer — photorealistic dark medieval fantasy, desaturated color palette"


async def main() -> None:
    pipeline = Script2VideoPipeline.init_from_config(
        config_path="configs/script2video_sora.yaml"
    )
    await pipeline(script=script, user_requirement=user_requirement, style=style)


if __name__ == "__main__":
    asyncio.run(main())
