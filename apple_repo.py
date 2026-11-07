#
# partcad-openusd-apple, 2026
#
# Licensed under Apache License, Version 2.0.
#
"""A PartCAD 'basic' repository plugin that serves Apple's AR Quick Look gallery as parts.

Published as ``//pub/collection/openusd/apple/assets``. The models are the USDZ
files of Apple's AR Quick Look gallery
(https://developer.apple.com/quick-look-gallery/), which openusd.org's
Downloads page lists among its "Additional Assets" as "ARKit Example Assets":
a toy biplane, a teapot, a Fender Stratocaster, a chameleon, ... A part per
model, named as the gallery names its folder: ``teapot``, ``toycar``,
``biplane``, ``baseball-glove``. Each is ``type: usd``, built by PartCAD's
own part type of that name from the model's USDZ, which the plugin hands over as Apple
publishes it.

The gallery is read from its page, for the models it links to; the models it
is known to have had are kept beside that (see KNOWN), so a page that changed
its markup still lists them. Its '.reality' files are RealityKit's, not USD,
and are not parts.

Apple's site terms let nobody mirror its content: the plugin fetches a model
for the user who asked for it, from Apple, and keeps it in their cache, as a
browser would; nothing of Apple's is in this repository.

PartCAD runs this script once per key (via runpy) with the key in
``request["key"]``; the answer goes in ``output``.
"""

import importlib.util
import os
import posixpath
import re
import sys

# When this plugin's answers stopped meaning what they meant before. PartCAD
# keys everything it caches of this package on it, so raise it with any change
# to what is answered - here, or in usd_assets.py.
#
# v1: the gallery's USDZ models, as PartCAD 'usd' parts.
# v2: with the files a part's look is read from - its shaders, and its colour and finish
#     images, a smaller copy where the source keeps one ('looks').
CACHE_VERSION = 2


def _shared():
    """usd_assets.py, beside this script, under a name of this plugin's own."""
    name = "_partcad_openusd_apple_usd_assets"
    if name not in sys.modules:
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "usd_assets.py")
        spec = importlib.util.spec_from_file_location(name, path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
    return sys.modules[name]


ua = _shared()

SITE = "https://developer.apple.com"
GALLERY = SITE + "/quick-look-gallery/"
# Where the models are. The gallery used to be under
# /augmented-reality/quick-look/, and a model asked for there now redirects to
# the gallery's page - an HTML page, answered 200 - so only this path is asked.
MODELS = "/quick-look-gallery/models/"
TERMS = "https://www.apple.com/legal/internet-services/terms/site.html"

# The models the gallery is known to have, as of November 2026, by its own paths.
KNOWN = [
    "baseball-glove/glove_baseball_mtl_variant.usdz",
    "baseball/ball_baseball_realistic.usdz",
    "basketball/ball_basketball_realistic.usdz",
    "biplane/toy_biplane_realistic.usdz",
    "boxing-glove/boxing_glove_realistic.usdz",
    "chameleon/chameleon_anim_mtl_variant.usdz",
    "drummertoy/toy_drummer.usdz",
    "football/ball_football_realistic.usdz",
    "hummingbird/hummingbird_anim.usdz",
    "kids-slide/slide.usdz",
    "pancakes/pancakes_photogrammetry.usdz",
    "seahorse/seahorse_anim_mtl_variant.usdz",
    "soccerball/ball_soccerball_realistic.usdz",
    "solar-panels/solar_panels.usdz",
    "stratocaster/fender_stratocaster.usdz",
    "teapot/teapot.usdz",
    "toycar/toy_car.usdz",
    "vintagerobot2k/robot.usdz",
]

# What each is, where its name alone does not say.
TITLES = {
    "biplane": "A toy biplane.",
    "chameleon": "A chameleon; it is animated, and has material variants.",
    "drummertoy": "A toy drummer.",
    "hummingbird": "A hummingbird; it is animated.",
    "kids-slide": "A children's slide.",
    "pancakes": "A stack of pancakes, photogrammetry.",
    "seahorse": "A seahorse; it is animated, and has material variants.",
    "stratocaster": "A Fender Stratocaster.",
    "toycar": "A toy car.",
    "vintagerobot2k": "A vintage toy robot.",
    "baseball-glove": "A baseball glove, with material variants.",
}

_LINK = re.compile(r'href="(%s[^"]+\.usdz)"' % re.escape(MODELS), re.IGNORECASE)


class Apple(ua.Source):
    NAME = "openusd-apple"
    TITLE = "Apple"
    URL = GALLERY
    DESC = (
        "Apple's AR Quick Look gallery (developer.apple.com/quick-look-gallery): its USDZ models, a part each, "
        "fetched from Apple when first built."
    )
    LICENSE = "LicenseRef-Apple-Website-Terms"
    VERSION = CACHE_VERSION
    REPOSITORY = "partcad-collection-openusd-apple"
    PLUGIN = "//pub/collection/openusd/apple:apple_repo"

    def models(self):
        """The models' paths under MODELS: what the gallery links to, and what it is known to have had."""
        found = list(KNOWN)
        try:
            page = self.http.get(GALLERY, "the gallery", headers={"Accept": "text/html"}, stale=True)
            for link in _LINK.findall(page.decode("utf-8", "replace")):
                path = link[len(MODELS) :]
                if path not in found:
                    found.append(path)
        except ua.SourceError as e:
            ua.warn("%s: the gallery could not be read, so only the models it is known to have are listed: %s"
                    % (self.NAME, e))  # fmt: skip
        return sorted(found)

    def assets(self, collection):
        store = _ModelStore(self.http, SITE + MODELS, {path: 0 for path in self.models()})
        found = {}
        for path in store.listing():
            name = path.split("/", 1)[0]
            desc = TITLES.get(name) or "A %s." % name.replace("-", " ")
            found[ua.safe_id(name)] = ua.Asset(name, store, path, desc=desc, url=GALLERY, author="Apple")
        return found


class _ModelStore(ua.HttpStore):
    """The gallery's models, each checked to be one: a page in its place is a redirect gone wrong."""

    def read(self, path):
        data = super().read(path)
        if ua.layer_kind(data) != "usdz":
            raise ua.SourceError(
                "%s: Apple answered %s with something that is not a USDZ model%s"
                % (self.http.name, posixpath.basename(path), " (a web page)" if b"<html" in data[:2048].lower() else "")
            )
        return data


def get(key):
    return ua.serve(Apple(globals().get("request")), key)


# Last, so that everything above is defined when PartCAD runs this.
if __name__ == "get":
    output = {"result": get(request["key"])}  # noqa: F821 - injected by the runtime
else:
    output = {}
