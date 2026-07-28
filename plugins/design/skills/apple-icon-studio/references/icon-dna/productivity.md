# Icon DNA — Productivity

Tasks, notes, calendars, project management, writing tools. The category where the icon has to
survive being looked at more often than any other, which makes restraint the dominant virtue.

## 1. Mental model

Users choose productivity tools on **feel** far more than on features — the feature lists are
near-identical and everyone knows it. The icon is a large part of that feel because it is on
the home screen, in the dock, and in the menu bar all day.

The core tension:

| Pole | Promise | Register |
|---|---|---|
| Calm | Reduces anxiety, everything is handled | Soft, warm, low contrast, spacious |
| Power | Does more, faster, for serious people | Sharp, cool, high contrast, dense |

Things and Todoist sit at opposite ends of exactly this axis with functionally similar
products. Pick a pole. The middle is where undifferentiated productivity apps go.

An icon looked at 40 times a day must be **quiet**. High-saturation, high-contrast icons that
win in a store listing become irritating in a dock. This is the one category where deliberately
under-designing is correct.

## 2. Metaphors

**Exhausted:**
- Checkmark (owned by half the category; Todoist, Things, TickTick all variants)
- Clipboard, checklist, lined paper
- Calendar grid with a date number
- Sticky note
- Gantt bar / kanban column

**In use:** Things = blue circle+check · Todoist = red with strokes · Notion = monochrome
block glyph · Linear = angular violet-grey mark · Obsidian = purple gem · Bear = bear ·
Craft = paper form · Apple Notes = yellow notepad · Reminders = coloured dot list

**Open:**
- **Folded form** — a sheet with one fold; the fold does all the work (see the note-app example)
- **Stone / settled weight** — calm productivity; unusually strong material affordance
- **Vessel / bowl** — containment, "everything is in here"
- **Thread / spool** — continuity across days
- **Horizon line** — planning ahead; extremely simple silhouette
- **Nested containers** — hierarchy without depicting a tree UI
- **Knot being tied / untied** — closing loops

## 3. Shape language

- **Rounded rectangle** — the honest choice for structure and records; needs rotation or
  material contrast to avoid echoing the canvas mask
- **Circle** — calm pole; extremely common though
- **Layered stack** — versions, days, accumulation; fits the current Apple depth language
- **Ring** — closing the loop; the hole gives free negative space
- **Avoid:** the bare checkmark in any form

## 4. Material

| Role | Recommendation |
|---|---|
| Primary | **Glazed ceramic** (calm pole) or **anodised metal** (power pole) |
| Accent | Liquid glass, or a single brass/copper edge |
| Reflection | Subtle to medium |
| Transparency | 0–15% — legibility beats depth in a dock |
| Edge | Soft 2px chamfer |
| Finish | Satin to semi-gloss |

Paper is thematically obvious for notes and works well, but keep it *smooth* — visible fibre
becomes noise at menu-bar size.

## 5. Palette

**Calm pole:**
```
Warm white #FAFAF9 · Sand #E7E5E4 · one muted accent (dusty blue #7C93A8 / sage #84A98C)
```

**Power pole:**
```
Graphite #1F2937 · one saturated accent (violet #7C3AED / blue #2563EB) · white
```

**Collision map:** red → Todoist · pure monochrome → Notion · violet-grey → Linear ·
yellow notepad → Apple Notes · deep purple gem → Obsidian.

Lower the saturation more than feels right. A dock icon at 70% saturation reads as confident;
at 95% it reads as shouting.

## 6. Traps

| Trap | Why it fails |
|---|---|
| A checkmark | Half the category; conveys nothing about *this* tool |
| Depicting the UI (kanban columns, list rows) | Meaningless at 40px, and it dates with the UI |
| High saturation | Fine in the store, exhausting in the dock |
| A date number in a calendar icon | Text rule violation; also stale unless dynamically rendered |
| Three or more hues | This category's users see the icon constantly; noise compounds |
| Choosing the middle of the calm/power axis | Undifferentiated |

## 7. Prompt fragments

**Calm ceramic:**
```
a single smooth glazed ceramic form in warm off-white, soft subsurface scattering,
gentle broad specular from a large soft light above, matte-satin glaze,
warm sand-coloured field, extremely quiet and restrained
```

**Power graphite:**
```
a precise machined form in matte anodised graphite with one sharp violet inner edge,
fine anisotropic surface grain, single directional specular streak along the top chamfer,
deep near-black field, engineered and exact
```

**Paper fold:**
```
a single sheet of heavy smooth cardstock with one corner folded inward,
soft ambient occlusion inside the fold, matte non-reflective surface, no visible fibre texture,
short soft contact shadow
```

**Category negatives:**
```
checkmark, tick, checklist, clipboard, calendar grid, date number, sticky note, pencil,
kanban board, gantt chart, spiral notebook, lined paper, to-do list, UI screenshot
```
