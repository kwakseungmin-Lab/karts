# cinematic

Cinematic video production pipeline — trailers, brand films, montages, and short dramatic edits.
Ported from [OpenMontage](https://github.com/calesthio/OpenMontage).

## When to use

When the user wants to produce or plan a cinematic short film, trailer, teaser, or mood-driven video.
Supports both source-footage-led work and AI-generated visuals.

## Pipeline stages

The Executive Producer orchestrates 9 stages serially. Read each director skill before starting the stage.

| Stage | Skill file | Key output |
|---|---|---|
| 0. Idea | `idea-director.md` | Brief: source mode, emotional arc, delivery shape |
| 1. Research | `research-director.md` | 3+ cinematic directions with visual & audio refs |
| 2. Proposal | `proposal-director.md` | Concept pack, renderer choice, user approval |
| 3. Script | `script-director.md` | Beat map, title cards, dialogue selects |
| 4. Scene plan | `scene-director.md` | Hero frames, transitions, 5-aspect scene specs |
| 5. Assets | `asset-director.md` | Source selects, generated inserts, music plan |
| 6. Edit | `edit-director.md` | Pacing decisions, audio turns, timeline |
| 7. Compose | `compose-director.md` | Render (Remotion / HyperFrames / FFmpeg) + grade |
| 8. Publish | `publish-director.md` | Hero export + cutdowns, metadata |

## How to run

```
1. Read pipeline_defs/cinematic.yaml
2. Read .claude/skills/cinematic/executive-producer.md
3. Start with idea-director.md to classify the brief
4. Execute each stage in order, reading the corresponding director skill first
5. Respect all quality gates and get user approval at proposal stage before spending budget
```

## Project context

This repo (`karts`) contains short film projects under `short-film-project/`.
Current project: **명예의 무게 (The Weight of Honor)** — see `short-film-project/overview.md`.

- Visual style: desaturated → color recovery arc, CinemaScope 2.39:1
- Audio: Suno AI BGM, ElevenLabs SFX, silence as primary dramatic tool
- Tools used: image2 (image gen), Seedance 2.0 (video gen), Premiere Pro (edit/grade)

When working on this project, apply the cinematic pipeline stages to the existing plan
and research materials in `short-film-project/plan/` and `short-film-project/research/`.
