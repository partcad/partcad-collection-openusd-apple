# Apple's AR Quick Look gallery for PartCAD

Serves the USDZ models of [Apple's AR Quick Look gallery](https://developer.apple.com/quick-look-gallery/)
- the "ARKit Example Assets" [openusd.org's Downloads page](https://openusd.org/release/dl_downloads.html)
lists - as PartCAD parts, published as `//pub/collection/openusd/apple/assets`: a part per model, named as
the gallery names its folder.

| Parts |
| --- |
| `baseball-glove`, `baseball`, `basketball`, `biplane`, `boxing-glove`, `chameleon`, `drummertoy`, `football`, `hummingbird`, `kids-slide`, `pancakes`, `seahorse`, `soccerball`, `solar-panels`, `stratocaster`, `teapot`, `toycar`, `vintagerobot2k` |

```shell
pc list parts //pub/collection/openusd/apple/assets
pc search parts -P //pub/collection/openusd/apple/assets -k teapot
pc inspect //pub/collection/openusd/apple/assets:toycar
pc render -t png --style shaded //pub/collection/openusd/apple/assets:teapot
```

The gallery is read from its page, for every USDZ it links to, beside the models it is known to have
had, so a page that changes its markup still lists them. Its `.reality` files are RealityKit's, not
USD, and are not parts.

**Apple's terms.** Apple states no licence for these models; its site's terms of use
(<https://www.apple.com/legal/internet-services/terms/site.html>) let nobody copy, republish or mirror
its content without Apple's consent. The plugin fetches a model from Apple for the person who asked
for it and keeps it in their cache, as their browser would. Nothing of Apple's is in this repository;
use what you build from it accordingly.

**No geometry is vendored.** Every model is fetched from developer.apple.com the first time a part of
it is built, and kept by PartCAD from then on.

**Nothing here is manufacturable.** These are models made to be looked at in AR; the package says
`manufacturable: false`, and so does the plugin of what it serves.

Requires PartCAD 0.9.11 or newer: the first release whose `//builtin` has the `usd` part type.

## Listing, searching, building

**Listing and searching download no asset.** `pc list parts` and `pc search parts` are answered from
the gallery's page, about 110 KB, read once a week. What a part is made of is fetched when the part is
built - by `pc inspect`, `pc render`, `pc export`, or an assembly that places it - and then only that
asset's own files, and kept.

`pc search parts -k <words>` is answered by the plugin, from the same catalog: a part matches when
every word is in its name, its description, its author, its tags or its package's name, and the ones
whose name matches come first. Each package answers with at most 20, or what `--limit` says (up to
100); search a package and every one below it with `-P '<package>...'`.

## What a part is

Every part here is `type: usd`: PartCAD's own part type for OpenUSD, in its `//builtin`, which reads a
stage with Pixar's USD library (`usd-core`), installed into the sandbox that builds the part and
nowhere else. The plugin's part is the file, and the part type makes the shape of it.

- **The file.** A part's file is a USDZ package of the asset, which the plugin makes when the part is
  built. An asset published as a `.usdz` is served as it is. One published as `.usd`, `.usda` or
  `.usdc` layers is a root layer that names others by relative path - sublayers, references,
  payloads - and the plugin follows those names (in a text layer its `@asset paths@`, in a binary one
  its token table) and packs the root and everything it reaches into a USDZ, root first, as the format
  wants it. Of the files that are not layers, it carries what the part's look is read from (the
  plugin's `looks`): the shaders the layers name, and the images of the colour, roughness and
  metalness - a smaller copy of each where the source keeps one, else each of up to 8 MB - and not
  the normal, height or occlusion maps. `textures` carries every one, as it is. A file an asset names
  that the source does not have is reported, and the asset is served without it.
- **The shape.** What is built is the stage's default prim - what a reference to the asset brings
  in - and every mesh it shows: through native instancing and point instancers, of the purpose asked
  for, visible ones only, in millimetres (by the stage's `metersPerUnit`) with Z up. A cube, sphere,
  cylinder, cone or capsule is meshed; curves, points and volumes are not surfaces, and are left out
  and counted. Up to 20 000 triangles, each triangle is a face, and two that share an edge share it:
  the part is drawn as lines, written to STEP, and made the solid it bounds where it closes. Past
  that, the triangles of each look are one mesh: fast at any size, drawn shaded (`pc render --style
  shaded`) and written as STL, 3MF or glTF, but with no edges for a line drawing. The part is a
  surface as USD describes it - what a renderer draws - and PartCAD says so when it is not a solid.
- **The look.** Each face is in the colour, roughness and metalness its material says - the material
  bound to its mesh, or to the subset of its faces - and as see-through: a colour a texture gives is
  read off the image where the face lies on it. `UsdPreviewSurface`, MaterialX and NVIDIA's OmniPBR,
  OmniGlass and OmniSurface are read, an MDL preset calling one included; a face with no material, or
  none of those, is in its `displayColor`. Each is stated under PartCAD's `usd` convention by the
  material's name, so a package of yours can claim one with a colour, material or finish of its own
  (`ids: {usd: Ceramic}`); one nothing claims is drawn as the stage says, and is display-only. A shaded
  `pc render` draws the roughness and metalness too.
- **The size.** It is what the asset says it is, by its `metersPerUnit`: an asset authored in the
  wrong units comes out as large, or as small, as it says.
- **The other reader.** `reader=cadmpeg` reads the same file with cadmpeg instead, PartCAD's
  converter for CAD formats, which reads USD from its 0.6.8 release on: what a render shows, at the
  stage's static values. It does no point instancer (the City Set's buildings, the chess set's pawns
  are left out), no `purpose` but `render` and no `time` but `default`, and a prim it reads as an
  exact surface (a cube, a sphere) is counted and left out rather than meshed. It is there as a
  second opinion and a fallback; `usd-core` is the reader to use.

Every part takes the part type's parameters, in its name (`King;purpose=proxy`) or in the `with` of
an enrich of it:

| Parameter | Default | What it is |
| --- | --- | --- |
| `reader` | `usd-core` | What reads the stage: `usd-core`, or `cadmpeg` (see above). |
| `prim` | the default prim | Build only what is under this prim; `/` is the whole stage. |
| `purpose` | `render` | `render`: what a final render draws; `proxy`: the stand-ins a viewer draws; `all`: both, and guides. |
| `surface` | `auto` | `faces`: a face per triangle; `mesh`: a mesh per colour; `auto`: `faces` up to 20 000 triangles. |
| `time` | `default` | The time code to read animated geometry at, skinning a character to it. `default` is what a viewer opens the stage at (its start time code, else its earliest sample), unposed. |
| `maxTriangles` | 5000000 | The most triangles the part may be: a scene of more is refused, saying so. |

PartCAD's own documentation of the part type is
[the `usd` part type](https://partcad.readthedocs.io/en/latest/config_parts.html#usd-files).

The models are 5 to 32 MB each, and tens of thousands to hundreds of thousands of triangles: the
toy car is 30 thousand, the teapot 104 thousand. They are drawn shaded; their colours are in their
textures, which PartCAD does not read, so a model is drawn in one colour.

## Parameters of the plugin

| Parameter | Default | What it is |
| --- | --- | --- |
| `max_size_mb` | `512` | The most a part's USDZ may be, in MB. |

A model is a USDZ already, so it is handed over as Apple publishes it, textures included; the plugin
takes no `textures` parameter.

## Caching

The plugin keeps what Apple answered under `~/.cache/partcad-openusd-apple/` (or
`$PARTCAD_OPENUSD_APPLE_CACHE`): the gallery's page for a week, and each model for good. Delete the
directory to start over. PartCAD keeps every answer the plugin gives, files included.

The gallery used to be under `/augmented-reality/quick-look/`, and a model asked for there is now
redirected to the gallery's page - an HTML page, answered 200 - so only `/quick-look-gallery/models/`
is asked, and an answer that is not a USDZ is refused for what it is.

Every request says what it is: `User-Agent: Mozilla/5.0 (compatible; PartCAD-openusd-apple/<version>;
+https://github.com/partcad/partcad-collection-openusd-apple)`.

## Status

Run against developer.apple.com: the gallery's page lists the 18 models - listing and searching
them read that page and nothing else, 111 KB - and the teapot and the toy car were fetched and read
back by the part type with usd-core 26.11 (334 by 245 by 333 mm, and 124 by 313 by 116 mm).

Each model was drawn in its look (`pc render -t png --style shaded`), its textures read where each face
lies on them: the teapot's cream enamel, chrome bail and wooden grip, the toy car's rusted paint, the
biplane, the Stratocaster's sunburst, the chameleon, the robot and the solar panels.

Through PartCAD's own `usd` part type, run from the change that adds it to `//builtin` before its
release, with all six `partcad-collection-openusd-*` packages in one workspace: `pc list packages -r`
listed their 17 packages, and `pc search parts -P '<workspace>...'` answered across all of them in
about two seconds, each collection searching its own catalog. `pc info` of the teapot built it with
each reader, `usd-core` and `cadmpeg`, and both gave 334 by 245 by 333 mm.

## Layout

| Path | Purpose |
| --- | --- |
| `partcad.yaml` | `//pub/collection/openusd/apple`; the `assets` external dependency and the `apple_repo` repository that serves it. |
| `apple_repo.py` | The repository plugin: where Apple keeps its gallery. |
| `usd_assets.py` | What every OpenUSD collection plugin shares, byte for byte: following a USD asset's layers, packing a USDZ, reading remote archives, buckets and listings a piece at a time, searching a catalog, the keys PartCAD asks. |
| `shared.sha256` | The digests of the shared files and their tests. They are the same in every `partcad-collection-openusd-*` repository - pixar, usd-wg, apple, nvidia, aswf-dpel and disney-moana - and a test fails when one here differs: change them in all of them. |
| `test_*.py` | The tests. Nothing in them touches the network. |

```shell
python -m pytest
```

When what the plugin answers changes - here or in `usd_assets.py` - raise `CACHE_VERSION` in
`apple_repo.py`: PartCAD keys everything it caches of this package on it, and an unchanged version
is answered from what it cached before.

## Licensing

The code here is Apache-2.0 (`LICENSE`). The models are Apple's, under the terms of Apple's site.
Nothing of them is in this repository.
