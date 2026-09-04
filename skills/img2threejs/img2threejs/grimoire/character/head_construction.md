# Creature Head Construction

Use this alongside `grimoire/character/reconstruction.md` (which fixes body proportions)
and `grimoire/character/structure_decomposition.md` (which fixes what parts exist). This
document is about the head specifically, because the head is where likeness lives and
where proportion error is least forgiving.

The worked case is the Vijay Ghume mini-dragon imp. Every number below was measured off
the reference pixels, not estimated.

## How these numbers were obtained

Reference: `vijay-ghume-mini-dragon-2.jpg`, the pure front view, 1920×1920.

Background was isolated by flood-filling inward from the image corners. The discriminator
is specific and worth recording, because a naive threshold eats the horns: the studio navy
has `b − r = +19…+21` at saturation ≈ 0.42, while the black horn keratin has `b − r =
+2…+9` at saturation 0.09…0.31. A test of `b − r ≥ 13 ∧ max < 78 ∧ sat > 0.32` separates
them cleanly. Flood-filling rather than thresholding also keeps enclosed dark regions —
pupils, mouth recess — on the foreground side.

Irises were found by thresholding saturated yellow inside bounded windows so the gold
jewellery could not contaminate them. Midline landmarks came from a vertical class scan at
`x = 959`. Widths that cross a *shading* boundary rather than a *silhouette* boundary — the
skull edge behind the ear, for instance — cannot be scanned and were read off a 25 px
measuring grid overlaid on the image. Each row below says which method produced it.

**Unit: `HH` = head height = crown to chin at the midline = 377 px.**

## Measured landmarks — front view

| Landmark | Pixel | Method |
|---|---|---|
| Horn tip, highest | y = 98 | scan |
| Crown, top of pink cranium at midline | y = 416 | scan |
| Frontal boss highlight band | y = 515…526 | scan |
| Eye line, iris centres | y = 586 | scan |
| Nostril band | y = 635…655 | grid |
| Lip ridge at midline | y = 686…690 | scan |
| Fang tips | y = 705 | grid |
| Chin / jaw bottom at midline | y = 793 | scan |
| Iris, left | x 776…876, y 541…629 | scan |
| Iris, right | x 1038…1141, y 543…631 | scan |
| Horn bases | centres at x = 959 ± 80, y ≈ 505; ⌀ ≈ 70 | scan |
| Skull width, widest, ears excluded | 456 | grid |
| Muzzle width, widest | 395 | grid |
| Ear tip to ear tip | 830 | grid |
| Hoof bottom | y = 1620 | grid |

The obvious trap: a naive "lowest foreground pixel" scan returns y = 1816 for the feet.
That is the cast shadow plus the tail's arrow tip, not the hoof. Cropping the leg region
and reading it directly gives 1620. The difference moves the head-to-body ratio from 3.7
to 3.2 head-units, so it matters.

## Proportion table

| Ratio | Value | Reading |
|---|---|---|
| **Skull width / HH** | **1.21** | the head is 21% wider than it is tall |
| Muzzle width / HH | 1.05 | the muzzle is as wide as the head is tall |
| Ear span / HH | 2.20 | the ears more than double the head's width |
| Interocular, iris centre to centre / HH | 0.70 | |
| Interocular / skull width | 0.58 | eyes sit in the outer half of the skull |
| Iris width / HH | 0.265 | roughly 5× the human relative iris size |
| Iris aspect, h/w | 0.88 | |
| **Eye line depth from crown** | **0.45** | eyes sit *above* the head's midpoint |
| Nostril band from crown | 0.63 | |
| Lip ridge from crown | 0.72 | |
| Fang tips from crown | 0.77 | |
| Chin | 1.00 | by definition |
| Horn length above crown / HH | 0.84 | |
| Head + horn total height / HH | 1.84 | |
| Horn base centre from midline | ±0.21 | |
| Horn base diameter / skull width | 0.15 | |
| Ear length / HH | 0.85 | |
| Ear axis rake off vertical | 29° | |
| Body height, crown to hoof / HH | 3.19 | **pose-dependent** — see below |

The 3.19 head-units figure is not a design constant. All five reference views share one
crouched jump pose with the legs folded, so crown-to-hoof is compressed. A proportion
scaffold should be driven by *segment lengths* (femur, tibia) rather than by posed
silhouette height.

## The depth axis is not measurable from this reference set

There is no orthographic profile view. View `-4` is a three-quarter, so every depth reading
is a projection of unknown foreshortening. What can be established:

- The muzzle's frontmost point sits **58 px ahead of the iris centre**, in a view where
  eye-to-chin is 213 px. Eye-to-chin is 207 px at HH = 377 in the front view, so the two
  views are within 3% of the same scale. That puts projected protrusion at **0.15 HH**,
  and correcting for a ~25° turn still only reaches ~0.17 HH.
- Below the mouth the profile *recedes*: at the chin the frontmost pixel is at x = 142…153
  against the muzzle's x = 110. **The chin is set back behind the upper lip.**
- Total head horizontal extent in that view is ≈ 0.62 HH, but the occiput is occluded by
  the ear and neck, so 0.62 is a lower bound on depth, not a measurement.

**Therefore: muzzle width-to-protrusion ≈ 1.05 / 0.17 ≈ 6 : 1.** This is a wide flat
frog-or-bat muzzle, not a long dog snout — the single most consequential fact about this
head, and the one most likely to be got wrong.

Cranium depth is *inferred*, not measured: **0.75–0.85 HH**, confidence moderate. The
reasoning is that 1.21 HH of width already supplies braincase volume laterally, so depth
does not need to compensate, while enough depth must remain behind for the neck joint and
jaw musculature. Treat it as a constrained assumption and validate by projecting the built
model back onto view `-4` at a matched camera.

## Block construction

Coordinates in HH. Origin at the crown on the midline; **y grows downward**; z forward.

| # | Block | Primitive | Extent | Placement | Join |
|---|---|---|---|---|---|
| 1 | Cranium | ellipsoid | W 1.21, H 0.60, D ~0.80 | centre y 0.30 | base form |
| 2 | Upper muzzle | flattened capsule | W 1.05, H 0.30, D ~0.20 | centre y 0.60 | smooth union, **deliberately overlapping the cranium from y 0.45–0.60** |
| 3 | Lower jaw / chin | ellipsoid | W ~0.80, H 0.25 | centre y 0.875, pushed back in −z | union, tucked under block 2 |
| 4 | Frontal boss | diamond wedge | W ~0.20, H ~0.25 | midline, y ≈ 0.26 | smooth union |
| 5 | Brow ridge | V-shaped tube pair | span ~1.10 | from the boss, sweeping down-and-outward | smooth union |
| 6 | Eye sockets | ellipsoid | — | x ±0.35, y 0.45 | **subtract** |
| 7 | Nose pad | small flattened capsule | — | midline, y 0.63 | union, sitting on block 2 |
| 8 | Lip ridge | hard crease, not a block | full muzzle width | y 0.72, corners lifting | crease |
| 9 | Fangs ×4 | cones | tips at y 0.77 | from the upper lip, pointing **down** | union |
| 10 | Ears ×2 | curved wedge shells | L 0.85, span 2.20 | base on the rear half of the skull, rake 29° | union |
| 11 | Horns ×2 | tapered curved capsules | L 0.84, base ⌀ 0.19 | base x ±0.21, y ≈ 0.24 | union |
| 12 | Mouth bag | inverted shell | — | behind the lip crease | subtract then shell |

The 0.45–0.60 overlap between muzzle and cranium is intentional, not an error: it is what
produces the cheek swell and the deep-set eye. Blocks that merely abut produce a seam.

## Design logic — what makes it read as "menacing but appealing"

Getting this backwards is easy, and an earlier pass of this analysis did get it backwards.
**Eye-line height is a threat cue here, not a cute cue.** Neoteny requires a *large*
forehead, which means the eye line sits *low* — around 0.50 for a human adult and 0.60 or
more for an infant. This head measures **0.45**, a smaller forehead than an adult human's.
That is a predator signal.

**Appeal comes from:**
- Interocular 0.58 of skull width — eyes pushed into the outer half, which reads as
  prey-animal or primitive creature rather than a forward-converging hunter
- Muzzle 1.05 HH wide at 6:1 width-to-depth — a frog-wide mouth, which cancels the wolf
- Ear span 2.20 HH at 29° rake — oversized sensory organs read as vulnerable
- Iris 0.265 HH, roughly 5× human relative scale
- A small cat-like nose pad, and smooth skin with no scales

**Threat comes from:**
- Eye line at 0.45 — compressed forehead
- A V-shaped supraorbital ridge overhanging the sockets, tilting the eye axis down-inward
- Horns at 0.84 HH with a base 0.15 of skull width — heavy, weapon-like, not decorative
- Four maxillary canines pointing down over a closed lower lip

The balance is structural: a predator's *features* mounted on a wide, flat, big-eared
*armature*. Remove either side and the design collapses into something ordinary.

## Sensitivity — what breaks likeness fastest

Ranked by how little error it takes to destroy the read:

1. **Muzzle width, 1.05 HH.** Narrow it 10–15% and the frog-wide mouth is gone; the
   character becomes a hellcat or a generic bat.
2. **Interocular, 0.58 of skull width.** Bring the eyes below 0.50 and the read flips from
   creature to primate.
3. **Muzzle protrusion, ~0.17 HH.** Push past 0.25 HH and it is a dog snout. This is the
   error a modeller trained on human or canine anatomy will make by reflex.
4. **Skull width, 1.21 HH.** Drop to 1.0 and the head "grows up" into a goblin or orc.
5. **Eye line, 0.45.** Raise it to 0.35 and the forehead disappears; the character reads
   as a troll.
6. **Horn length 0.84 HH and base 0.19 HH.** Thin or shorten them 20% and the triangular
   silhouette — horn apex spreading down to the ear tips — falls apart, leaving a child in
   a costume.

## Topology requirements

For a head that must open its mouth, blink and furrow its brow:

- **≥ 4 concentric loops around each eye**, packed tightly at the lid margin.
- **≥ 3 concentric loops around the mouth**, flowing continuously from the outer lip into
  the inner mouth bag so no lighting seam forms at the lip.
- **≥ 3 horizontal compression loops across the muzzle bridge**, so the surface can
  accordion when the character snarls instead of collapsing.
- **Poles at every horn and ear base.** Use a downward-pointing four-point transition to
  step a 12-point cylinder down to 8 points. Without this, loops from the appendages
  propagate down the neck and into the body.

## Ear structure

Five cartilage landmarks carry the read: helix (the folded outer rim), antihelix (the
inner raised ridge, forking into two branches), concha (the deep bowl), tragus and
antitragus. At 0.85 HH long, this ear needs three geometry layers — front surface, back
surface for thickness, and extruded ridges for the antihelix. The concha bowl should recess
roughly **0.15–0.20 HH** into the temporal mass; shallower and the ear reads as a flat
paddle.

## Jaw hinge

The lifted mouth corners at 0.72 HH, the set-back mandible and the downward maxillary
canines together imply a **low-set temporomandibular joint** — at or slightly below the
occlusal plane, the configuration that favours a fast, wide gape over crushing force.

If the mouth needs to open, place the jaw rotation axis at approximately:

- y = 0.72–0.75 HH
- z = −0.10 to −0.20 HH behind the skull centre, leaving room for the temporalis lever
- x = ±0.45–0.50 HH, out at the skull's lateral edge

## Build order

Steps marked **[likeness]** tolerate no more than ~5% error; the rest can be refined later.

1. **[likeness] Primary blocks.** Cranium, upper muzzle, lower jaw. Check from *top and
   bottom* views, not just front — the plan-view outline must be a flattened oval at
   roughly 1.5:1 width-to-depth. This is where the dog-snout error gets caught.
2. **[likeness] Eye line and sockets.** Fix y = 0.45, interocular 0.70 HH, then subtract
   the sockets.
3. **Brow and boss.** Add the midline diamond, sweep the V ridge down-and-outward. Check
   that the eye axis now tilts down-inward.
4. **[likeness] Silhouette appendages.** Horns at x ±0.21 running 0.84 HH; ears on the rear
   half of the skull at 29° rake, 2.20 HH span. Judge these as a black silhouette only.
5. **Creases and small forms.** Lip ridge at 0.72, nose pad at 0.63, four fangs with tips
   at 0.77. The lip is a *crease*, never a pair of fleshy human lips.
6. **Validate.** Project the model back onto view `-4` at a matched camera to test the
   depth assumption, which is the only axis the reference cannot pin down.

## Skills to develop, in order

1. **Camera matching.** Needed because the reference set has no clean profile, so depth can
   only be validated by projection. *Exercise:* put a box in the scene, load view `-4` as a
   backplate, and adjust rotation and FOV (35–50 mm range) until the box edges agree with
   the character's perspective. *Passing:* you can lock a camera that makes the reference
   silhouette overlay the model consistently.
2. **Non-human proportion control.** Human-anatomy habit forces a round skull and a
   protruding snout. This head is 1.21 wide and ~0.8 deep. *Exercise:* sculpt a frog or a
   ray head; scale on X with Y locked. *Passing:* your top-view outline measures the target
   ratio without you correcting it afterwards.
3. **Prognathic head framing.** A human Loomis has a vertical temple slice; this skull needs
   a horizontal one. *Exercise:* draw the slice plane and the C-curve from ear through
   cheekbone to chin. *Passing:* the zygomatic angle visibly bisects that C-curve.
4. **Hybrid anatomy blending.** Joining a reptile's sloped frontal deck to a broad
   mammalian cheek. *Exercise:* build the nasal deck as a flat plane driving into the wide
   zygomatic mass. *Passing:* the transition reads as one skull, not two glued halves.
5. **Hard creases on organic surfaces.** The lip ridge and lid margins are sharp on
   otherwise soft skin with no scales. *Exercise:* cut a deep crease across a smooth sphere
   without pinching artefacts at either end. *Passing:* the crease holds under smooth
   shading and subdivision.
6. **Deformation topology and appendage transitions.** *Exercise:* retopologise the face
   mask to 4 eye loops, 3 mouth loops, 3 muzzle compression loops; terminate horn and ear
   bases with four-point poles. *Passing:* a 45° jaw open produces no stretching at the
   mouth corners, and no loop from a horn reaches the neck.

## Acceptance rubric

Ten points. **Pass is > 9.0.** The reference head scores 10.

| # | Criterion | Weight | Full marks | Zero |
|---|---|---|---|---|
| 1 | Frame widths | 3.0 | skull W 1.19–1.23 HH and muzzle W 1.03–1.07 HH | muzzle W < 1.0 HH |
| 2 | Eye placement | 2.5 | eye line y 0.44–0.46 HH and interocular 0.56–0.60 of skull width | eye line y > 0.50, or interocular < 0.50 |
| 3 | Facial flatness | 1.5 | muzzle protrusion 0.15–0.18 HH, width-to-depth ≈ 6:1, chin behind the upper lip | protrusion > 0.25 HH |
| 4 | Appendage silhouette | 1.5 | horn 0.81–0.87 HH, ear span 2.15–2.25 HH, rake ≈ 29° | −1.0 per failure |
| 5 | Threat detail | 1.5 | four **upper** canines pointing down (0.5), V brow ridge (0.5), lip crease at y 0.72 (0.5) | fangs rising from the lower jaw scores 0 for that item |

Weights sum to 10.0. Each criterion is checkable by measurement, not opinion — which is
what makes a 9 mean something.

## Eight common failures

| Failure | Visible sign | Fix |
|---|---|---|
| Dog snout | muzzle juts forward in three-quarter view | flatten in z until width:depth ≈ 6:1 |
| Convergent eyes | eyes drift toward the midline; creature reads as a primate | restore interocular to 0.70 HH |
| Lost forehead | reads as an adult goblin or troll | keep y 0…0.45 clear above the eye line |
| Orc fangs | canines rise from the mandible | remove them; hang four from the maxilla, tips at y 0.77 |
| Human lips | upper and lower lips carry volume | flatten to a single crease at y 0.72 |
| Underbite | chin level with or ahead of the upper lip | push the mandible back in −z and blend into the neck |
| Wrong nose | a raised bridge or a bulbous tip | flatten to a pad with two keyhole nostrils |
| Narrow horn base | horns cluster on the crown like cattle | separate the bases to x ±0.21 and widen to ⌀ 0.19 HH |

## Gate notes

Criteria 1–3 are numeric and belong in the spec validator: they can be checked against the
emitted `RigSpec` and geometry bounds without rendering anything. Criterion 4 is a
silhouette check and belongs with Divine Eye. Criterion 5 is a part-inventory check — the
four maxillary canines must exist as L2 parts with the correct parent bone, per
`structure_decomposition.md`.
