"""Local multi-file web revisions, captured explicitly before rendering."""

from facelesschamp_kit.playground import CodeCheckpoint, PlaygroundScript
from facelesschamp_kit.templates import coding_playground

HTML = """<!doctype html>
<html>
<link rel="stylesheet" href="style.css">
<body>
  <main>
    <h1>Hello, developer</h1>
    <button id="count">Count: 0</button>
  </main>
  <script src="app.js"></script>
</body>
</html>
"""
CSS = """body {
  margin: 0;
  background: #eef4fc;
  font: 28px sans-serif;
}
main { padding: 60px 32px; }
h1 { color: COLOR; }
button {
  background: #243d75;
  color: white;
  border: 0;
  border-radius: 14px;
  padding: 20px;
  font: inherit;
}
"""
JS = """let count = 0;
const button = document.querySelector("#count");
button.onclick = () => {
  button.textContent = `Count: ${++count}`;
  console.log("Count:", count);
};
"""


def script():
    from facelesschamp_kit.web import WebScript

    def files(color):
        return {"index.html": HTML, "style.css": CSS.replace("COLOR", color), "app.js": JS}

    return PlaygroundScript(
        [
            CodeCheckpoint(
                "blue",
                files("#243d75"),
                "style.css",
                "index.html",
                0,
                1,
                1,
                runtime="web",
                ready=("#count",),
                web_script=WebScript(3).click("#count", at=0.5),
            ),
            CodeCheckpoint(
                "pink",
                files("#d83478"),
                "style.css",
                "index.html",
                2.5,
                4,
                4,
                runtime="web",
                ready=("#count",),
                web_script=WebScript(2).click("#count", at=0.5),
            ),
        ],
        duration=6,
        mode="web",
        viewport=(720, 620),
    )


def build(ctx):
    return coding_playground(ctx, script(), timeout=60)
