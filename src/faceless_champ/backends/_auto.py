"""Capability-aware selection, once per render session, never mid-export."""


class AutoRenderer:
    def __init__(self, antialias=2, *, gpu=None, **options):
        self.antialias, self.gpu, self.options = antialias, gpu, options
        self.renderer = None
        self._closed = False
        self.identity = {"backend": "auto", "device": "unresolved", "resolved": False}

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()

    def validate(self, node):
        if self._closed:
            raise RuntimeError("AutoRenderer is closed")
        if self.renderer is not None:
            self.renderer.validate(node)
            return
        from ..renderer import create_renderer, rendering_identity

        failures = []
        for backend in ("moderngl", "skia", "pillow"):
            candidate = None
            try:
                candidate = create_renderer(backend, antialias=self.antialias, gpu=self.gpu, **self.options)
                if backend == "moderngl" and candidate.identity["device"] != "gpu":
                    raise RuntimeError("software OpenGL is excluded from automatic acceleration")
                candidate.validate(node)
            except (RuntimeError, ValueError, ImportError, OSError) as exc:
                failures.append({"backend": backend, "reason": str(exc)})
                if candidate is not None:
                    candidate.close()
            else:
                self.renderer = candidate
                self.identity = rendering_identity(backend, renderer=candidate) | {
                    "requested_backend": "auto",
                    "resolved": True,
                    "fallbacks": failures,
                }
                return
        raise RuntimeError("No fidelity-preserving renderer is available: " + "; ".join(f["reason"] for f in failures))

    def frame(self, node, time, size):
        if self.renderer is None:
            self.validate(node)
        if self._closed:
            raise RuntimeError("AutoRenderer is closed")
        return self.renderer.frame(node, time, size)

    def close(self):
        if self.renderer is not None:
            self.renderer.close()
        self._closed = True
