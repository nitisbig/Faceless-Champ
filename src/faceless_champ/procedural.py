"""Stateless, seed-addressed backgrounds and particles; no native imports."""

from PIL import ImageColor

from .components import Component, finite


class ProceduralBackground(Component):
    _procedural = True

    def __init__(self, kind="aurora", *, width=1920, height=1080, seed=0, color="#68BFFF", speed=0.2, **options):
        super().__init__(**options)
        if kind not in {"aurora", "noise_gradient"}:
            raise ValueError("kind must be aurora or noise_gradient")
        if isinstance(seed, bool) or not isinstance(seed, int) or not 0 <= seed < 2**32:
            raise ValueError("seed must be an integer in [0, 2**32)")
        ImageColor.getcolor(color, "RGBA")
        self.kind, self.seed, self.color = kind, seed, color
        self.width, self.height = finite(width, "width", 1), finite(height, "height", 1)
        self.speed = finite(speed, "speed")

    def frame_key(self, age):
        import math

        from .effects import _phase

        return _phase(age, self.speed, math.tau * 10)


class ParticleField(ProceduralBackground):
    def __init__(self, *, count=1000, radius=2, lifetime=5, velocity=(0, -40), **options):
        super().__init__(**options)
        if isinstance(count, bool) or not isinstance(count, int) or not 1 <= count <= 100_000:
            raise ValueError("count must be an integer in [1,100000]")
        self.count, self.radius = count, finite(radius, "radius", 0.01)
        if self.radius > 4096:
            raise ValueError("Particle radius exceeds 4096 design pixels")
        self.lifetime = finite(lifetime, "lifetime", 0.001)
        if self.lifetime > 1_000_000:
            raise ValueError("lifetime exceeds 1000000 seconds")
        self.velocity = tuple(finite(v, "velocity") for v in velocity)
        if len(self.velocity) != 2:
            raise ValueError("velocity needs two coordinates")
        if any(abs(v) > 1_000_000 for v in self.velocity):
            raise ValueError("velocity exceeds 1000000 design pixels per second")

    def frame_key(self, age):
        return age % self.lifetime


def particle_data(component, age):
    """Float32 instance records shared by CPU and GPU, independent of sample order."""
    from ._effects_cpu import numpy

    np = numpy()
    ids = np.arange(component.count, dtype=np.uint32)

    def hashed(x):
        x = x ^ (x >> np.uint32(16))
        x = x * np.uint32(0x7FEB352D)
        x = x ^ (x >> np.uint32(15))
        x = x * np.uint32(0x846CA68B)
        return (x ^ (x >> np.uint32(16))).astype(np.float64) / 2**32

    phase = hashed(ids + np.uint32(component.seed))
    elapsed = np.remainder(age % component.lifetime + phase * component.lifetime, component.lifetime)
    x = np.remainder(
        hashed(ids + np.uint32(104729) + np.uint32(component.seed)) * component.width + elapsed * component.velocity[0],
        component.width,
    )
    y = np.remainder(
        hashed(ids + np.uint32(130363) + np.uint32(component.seed)) * component.height
        + elapsed * component.velocity[1],
        component.height,
    )
    alpha = np.sin(np.pi * elapsed / component.lifetime) ** 2
    return np.column_stack((x, y, alpha)).astype("f4")


__all__ = ["ParticleField", "ProceduralBackground"]
