"""One diagnostic contract for Python and command-line users."""

from facelesschamp_kit.diagnostics import KitError


class AgentError(KitError):
    def __init__(self, code, message, *, suggested_fix="Inspect the referenced input and rerun the operation", **scope):
        self.code, self.message, self.scope = code, message, scope
        self.suggested_fix = suggested_fix
        ValueError.__init__(self, f"{code}: {message}")

    def as_dict(self):
        return {"code": self.code, "message": self.message, "suggested_fix": self.suggested_fix, **self.scope}
