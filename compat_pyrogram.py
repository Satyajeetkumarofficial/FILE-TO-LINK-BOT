"""
Import this module FIRST (before anything that imports `pyrogram`).

wzgram is a drop-in fork of Pyrogram. Depending on how it is installed, the
importable package can be called `pyrogram` or `wzgram`. This shim makes both
work: if `pyrogram` is not importable, every `pyrogram.*` import is
transparently redirected to the matching `wzgram.*` module.
"""
import sys
import importlib
import importlib.abc
import importlib.util


class _AliasFinder(importlib.abc.MetaPathFinder, importlib.abc.Loader):
    SRC = "pyrogram"
    DST = "wzgram"

    def find_spec(self, name, path=None, target=None):
        if name == self.SRC or name.startswith(self.SRC + "."):
            return importlib.util.spec_from_loader(name, self)
        return None

    def create_module(self, spec):
        real = self.DST + spec.name[len(self.SRC):]
        return importlib.import_module(real)

    def exec_module(self, module):  # module is already fully initialised
        return None


def install():
    try:
        import pyrogram  # noqa: F401
        return "pyrogram"
    except ModuleNotFoundError:
        pass
    try:
        importlib.import_module("wzgram")
    except ModuleNotFoundError as e:
        raise SystemExit(
            "Neither 'pyrogram' nor 'wzgram' is installed. "
            "Run: pip install -r requirements.txt"
        ) from e
    sys.meta_path.insert(0, _AliasFinder())
    return "wzgram"


BACKEND = install()
