# Approved condition icon family

Status: **approved and locked on 2026-09-01**.

The project-author-provided base images are retained in
`candidates/pro-luminous-tier-bands-v2`. The higher-intensity variants were
created with built-in image editing, then converted to genuine RGBA assets and
reviewed at the Toolkit's 64 x 64 display size.

## Tier mapping

| Status family | Tiers | Approved visual band |
| --- | --- | --- |
| Hardened Foe | I-II | Armoured foe, cold white-blue glow |
| Hardened Foe | III-IV | Brighter icy eyes and defensive glow |
| Hardened Foe | V-VI | White-blue eyes, pale-gold armour accents and defensive arc |
| Relentless Foe | I-II | Spiked foe, cold white-blue glow |
| Relentless Foe | III-IV | Amber eyes and face-centred war marks; rear spikes remain blue-white |
| Relentless Foe | V-VI | Red eyes, facial/fang glow and separate motion slashes; rear spikes remain blue-white |

`source/` contains the twelve production masters (`01` through `06` for each
family). Adjacent tier pairs intentionally duplicate one approved visual band.
The Toolkit-ready 64, 144 and 380 pixel files live under the module's
`GUI/SourceIcons` tree.

The production atlas is `AESN_ConditionIcons.dds`: 512 x 512, BC3_UNORM,
ten mip levels, with one explicit UV entry for each of the twelve status keys.
