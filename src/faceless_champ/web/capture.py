"""Explicit offline browser preparation. The renderer never starts a browser."""

from __future__ import annotations

import hashlib
import json
import math
import shutil
import tempfile
import threading
from contextlib import contextmanager
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import quote, urlsplit

from ..components import finite
from .model import HtmlPage, WebCapture, WebError, WebScript

# CSS animations use their own document timeline, independently of JS timers.
# Pause new animations at their authored creation time, then seek them explicitly.
ANIMATION_DRIVER = r"""t => {
  window.__fcAnimations ||= new Map();
  for (const a of document.getAnimations()) {
    if (!window.__fcAnimations.has(a)) {
      window.__fcAnimations.set(a, t); a.pause(); a.currentTime = 0;
    }
  }
  for (const [a, start] of window.__fcAnimations) {
    if (!a.effect || !a.effect.target?.isConnected) {
      window.__fcAnimations.delete(a); continue;
    }
    const age = Math.max(0, t - start);
    const end = a.effect.getComputedTiming().endTime;
    if (Number.isFinite(end) && age >= end) {
      if (a.playState !== 'finished') a.finish();
    } else { a.pause(); a.currentTime = age; }
  }
}"""


@contextmanager
def local_server(root):
    class Handler(SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=str(root), **kwargs)

        def log_message(self, *args):
            pass

        def do_GET(self):
            target = Path(self.translate_path(self.path)).resolve()
            if not target.is_relative_to(root) or not target.is_file():
                self.send_error(404)
                return
            super().do_GET()

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}"
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


def input_digest(page, excluded=()):
    """Hash local source files; never hash this feature's generated cache."""
    digest = hashlib.sha256()
    ignored = {".git", ".venv", "__pycache__", ".web-cache", "output", ".pytest_cache", ".ruff_cache"}
    for path in sorted(page.asset_root.rglob("*")):
        relative = path.relative_to(page.asset_root)
        if any(part in ignored for part in relative.parts) or any(path.is_relative_to(p) for p in excluded):
            continue
        if path.is_file():
            if not path.resolve().is_relative_to(page.asset_root):
                raise WebError(f"Asset symlink escapes asset_root: {relative}")
            digest.update(str(relative).encode())
            digest.update(hashlib.sha256(path.read_bytes()).digest())
    return digest.hexdigest()


def capture_html(
    page: HtmlPage,
    script: WebScript,
    *,
    fps=30,
    cache_dir=".web-cache",
    start_time=0,
    end_time=None,
    sample_times=None,
    timeout=10,
    progress=None,
):
    """Prepare a full capture, source-time range, or sparse storyboard samples.

    Replay starts at zero even for a range. Only requested frames are persisted.
    Browser installation is explicit: ``python -m playwright install chromium``.
    """
    fps = finite(fps, "fps", 0.001)
    timeout = finite(timeout, "timeout", 0.001)
    start = finite(start_time, "start_time", 0)
    end = script.duration if end_time is None else finite(end_time, "end_time", 0)
    if not 0 <= start < end <= script.duration:
        raise WebError("Capture range must satisfy 0 <= start < end <= duration")
    count = math.ceil(script.duration * fps - 1e-9)
    if sample_times is None:
        indices = set(range(math.floor(start * fps + 1e-9), min(count, math.ceil(end * fps - 1e-9))))
    else:
        times = [finite(t, "sample time", 0) for t in sample_times]
        if not times or any(t >= script.duration for t in times):
            raise WebError("Samples must be nonempty and inside script duration")
        indices = {math.floor(t * fps + 1e-9) for t in times}
    cache_dir = Path(cache_dir).resolve()
    source_hash = input_digest(page, (cache_dir,))
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise WebError("Install faceless-champ[web], then run: python -m playwright install chromium") from exc
    cache_dir.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as engine:
        try:
            browser = engine.chromium.launch()
        except Exception as exc:
            raise WebError("Chromium could not start; run: python -m playwright install chromium. " + str(exc)) from exc
        try:
            identity = {
                "schema": 1,
                "driver": 1,
                "source": source_hash,
                "path": str(page.path.relative_to(page.asset_root)),
                "viewport": page.viewport,
                "storage": page.storage,
                "ready": page.ready,
                "script": script.record(),
                "fps": fps,
                "browser": browser.version,
                "frames": sorted(indices),
            }
            key = hashlib.sha256(json.dumps(identity, sort_keys=True).encode()).hexdigest()
            destination = cache_dir / key
            if destination.exists():
                try:
                    return WebCapture(destination)
                except WebError:
                    shutil.rmtree(destination)
            with tempfile.TemporaryDirectory(prefix=".preparing-", dir=cache_dir) as temporary:
                temporary = Path(temporary)
                with local_server(page.asset_root) as origin:
                    context = browser.new_context(
                        viewport={"width": page.viewport[0], "height": page.viewport[1]},
                        device_scale_factor=1,
                        locale="en-US",
                        timezone_id="UTC",
                        color_scheme="light",
                        service_workers="block",
                    )
                    try:
                        _prepare(context, origin, page, script, fps, indices, temporary, identity, timeout, progress)
                    finally:
                        context.close()
                # Rename a complete directory; no reader sees a half-written manifest.
                try:
                    temporary.rename(destination)
                except OSError:
                    if not destination.is_dir():
                        raise
                    return WebCapture(destination)
            return WebCapture(destination)
        finally:
            browser.close()


def _prepare(context, origin, source, script, fps, indices, directory, identity, timeout, progress):
    errors = []

    def route(request_route):
        url = request_route.request.url
        if url.startswith(origin + "/") or urlsplit(url).scheme in {"data", "blob", "about"}:
            request_route.continue_()
        else:
            errors.append(f"External request blocked: {url}")
            request_route.abort()

    context.route("**/*", route)

    def block_socket(socket):
        errors.append(f"WebSocket unavailable in offline capture: {socket.url}")
        socket.close()

    context.route_web_socket("**/*", block_socket)
    context.add_init_script("""(() => {
      let seed = 123456789;
      Math.random = () => {seed = (1664525 * seed + 1013904223) >>> 0; return seed / 4294967296;};
    })();""")
    context.add_init_script(
        "for (const [k,v] of Object.entries(" + json.dumps(source.storage) + ")) localStorage.setItem(k,v);"
    )
    page = context.new_page()
    page.set_default_timeout(timeout * 1000)
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.on(
        "response",
        lambda response: errors.append(f"HTTP {response.status}: {response.url}") if response.status >= 400 else None,
    )
    page.clock.install(time=1704067200000)
    page.clock.pause_at(1704067200000)
    page.goto(origin + "/" + quote(str(source.path.relative_to(source.asset_root))), wait_until="load")
    page.evaluate(
        "async () => { await document.fonts.ready; await Promise.all([...document.images].map(i => i.decode())); }"
    )
    for selector in source.ready:
        _target(page, selector, "initial readiness", 0)
    # Native smooth scrolling has a separate clock. Authored scroll interpolation owns it.
    page.add_style_tag(content="* { scroll-behavior: auto !important; caret-color: transparent !important; }")
    page.evaluate(ANIMATION_DRIVER, 0)
    actions = sorted(script.actions, key=lambda action: action.at)
    events = []
    for order, action in enumerate(actions):
        events.append((action.at, order, action, "start", 0))
        if action.kind == "type":
            for i, char in enumerate(action.value):
                events.append((action.at + action.duration * (i + 1) / len(action.value), order, action, "char", char))
        elif action.duration:
            events.append((action.at + action.duration, order, action, "end", 1))
    events.sort(key=lambda event: (event[0], event[1], {"start": 0, "char": 1, "end": 2}[event[3]]))
    cursor = [0.0, 0.0]
    clicks, frames, active = [], {}, {}
    event_index, milliseconds = 0, 0
    last_index = max(indices)

    def advance(time):
        nonlocal milliseconds
        goal = round(time * 1000)
        # Fixed small ticks discover CSS animations started by intermediate JS timers.
        while milliseconds < goal:
            step = min(10, goal - milliseconds)
            page.clock.run_for(step)
            milliseconds += step
            page.evaluate(ANIMATION_DRIVER, milliseconds)

    def interpolate(time):
        for order, (action, initial, target) in list(active.items()):
            fraction = min(1, max(0, (time - action.at) / action.duration)) if action.duration else 1
            fraction = fraction * fraction * (3 - 2 * fraction)
            xy = [a + (b - a) * fraction for a, b in zip(initial, target)]
            if action.kind == "move":
                cursor[:] = xy
                page.mouse.move(*xy)
            else:
                page.locator(action.selector).evaluate("(el,p) => el.scrollTo(p[0],p[1])", xy)
            if fraction >= 1:
                del active[order]

    for index in range(last_index + 1):
        time = index / fps
        while event_index < len(events) and events[event_index][0] <= time + 1e-9:
            at, order, action, phase, value = events[event_index]
            advance(at)
            interpolate(at)
            try:
                target = _target(page, action.selector, action.kind, at)
                box = target.bounding_box()
                center = [box["x"] + box["width"] / 2, box["y"] + box["height"] / 2]
                if phase == "char":
                    target.focus()
                    page.keyboard.insert_text(value)
                elif phase == "start":
                    if action.kind == "move":
                        active[order] = (action, cursor[:], center)
                        interpolate(at)
                    elif action.kind == "scroll":
                        initial = target.evaluate("el => [el.scrollLeft, el.scrollTop]")
                        active[order] = (action, initial, action.value)
                        interpolate(at)
                    elif action.kind == "click":
                        cursor[:] = center
                        page.mouse.click(*center)
                        clicks.append({"at": at, "position": center})
                    elif action.kind == "type":
                        target.focus()
                    elif action.kind == "press":
                        target.focus()
                        page.keyboard.press(action.value)
                    elif action.kind == "select":
                        target.select_option(action.value, timeout=timeout * 1000)
                page.evaluate(ANIMATION_DRIVER, milliseconds)
            except Exception as exc:
                raise WebError(f"{action.kind} {action.selector!r} at {at:g}s: {exc}") from exc
            event_index += 1
        advance(time)
        interpolate(time)
        page.evaluate(ANIMATION_DRIVER, milliseconds)
        if errors:
            raise WebError("Browser preparation failed: " + "; ".join(errors))
        if index not in indices:
            continue
        geometry = {}
        for selector in script.selectors:
            locator = page.locator(selector)
            if locator.count() == 1 and locator.is_visible():
                box = locator.bounding_box()
                if box:
                    # Intersect all clipping ancestors and the viewport.
                    geometry[selector] = locator.evaluate("""el => {
                      const r = el.getBoundingClientRect(); let l=Math.max(0,r.left), t=Math.max(0,r.top),
                      b=Math.min(innerHeight,r.bottom), right=Math.min(innerWidth,r.right);
                      for(let p=el.parentElement;p;p=p.parentElement) {
                        const s=getComputedStyle(p), q=p.getBoundingClientRect();
                        if (/(auto|scroll|hidden|clip)/.test(s.overflowX)) {l=Math.max(l,q.left);right=Math.min(right,q.right);}
                        if (/(auto|scroll|hidden|clip)/.test(s.overflowY)) {t=Math.max(t,q.top);b=Math.min(b,q.bottom);}
                      }
                      return right>l && b>t ? [l,t,right,b] : null;
                    }""")
        page.screenshot(path=str(directory / f"{index:08d}.png"), animations="allow", caret="hide")
        frames[str(index)] = {
            "geometry": geometry,
            "cursor": cursor[:],
            "clicks": [c for c in clicks if 0 <= time - c["at"] <= 0.6],
        }
        if progress:
            progress(len(frames), len(indices))
    manifest = {
        "schema": 1,
        "identity": identity,
        "fps": fps,
        "duration": script.duration,
        "viewport": source.viewport,
        "frames": frames,
    }
    (directory / "manifest.json").write_text(json.dumps(manifest, sort_keys=True))


def _target(page, selector, kind, at):
    target = page.locator(selector)
    if target.count() != 1:
        raise WebError(f"{kind} {selector!r} at {at:g}s: expected one target, found {target.count()}")
    if not target.is_visible() or not target.is_enabled():
        raise WebError(f"{kind} {selector!r} at {at:g}s: target is hidden or disabled")
    box = target.bounding_box()
    if not box or box["width"] <= 0 or box["height"] <= 0:
        raise WebError(f"{kind} {selector!r} at {at:g}s: target has no visible bounds")
    if kind in {"click", "move"} and not target.evaluate("""el => {
        const r=el.getBoundingClientRect(), x=r.x+r.width/2, y=r.y+r.height/2;
        const hit=document.elementFromPoint(x,y); return hit && (hit===el || el.contains(hit));
    }"""):
        raise WebError(f"{kind} {selector!r} at {at:g}s: target center is offscreen or covered; scroll first")
    return target
