"""Owned rendering for supplied, deepcopy-safe scientific scene descriptions.

Descriptions provide parts/style/camera/framing, state_at(time), frame_key(age)
and annotation_overlay(time, factor). No engineering frontend is imported here.
"""

from dataclasses import dataclass


@dataclass(frozen=True, eq=False)
class PyVistaSource:
    scene: object
    isolate: bool = False
    requirements = ("3d",)

    @property
    def intrinsic_size(self):
        return max(1, round(self.scene.width)), max(1, round(self.scene.height))

    @property
    def fingerprint(self):
        return self.scene.fingerprint

    @property
    def duration(self):
        return max(0, self.scene.duration - self.scene.source_start) or None

    def frame_key(self, age):
        return self.scene.frame_key(age)

    def open(self, size):
        factor = size[0] / self.scene.width
        if self.isolate:
            from ._worker import ArchWorker

            worker = ArchWorker()
            scene = self.scene

            class Session:
                def __init__(self):
                    self.worker = worker

                def frame(self, age):
                    image = self.worker.sprite(scene, {}, factor, age)
                    return image if image.size == size else image.resize(size)

                def close(self):
                    worker.close()

            return Session()
        from ._environment import _preserve_float_environment
        from .rendering import ArchSession

        with _preserve_float_environment():
            native = ArchSession(self.scene, factor)

        class Session:
            def __init__(self):
                self.native = native

            def frame(self, age):
                with _preserve_float_environment():
                    image = native.frame(age)
                return image if image.size == size else image.resize(size)

            def close(self):
                with _preserve_float_environment():
                    native.close()

        return Session()
