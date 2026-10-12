This animation starts with a Python file. A title appears, a circle moves across the screen, and both fade away. A few lines describe the visuals and their timing. Faceless Champ turns those instructions into a video.

In this quickstart, we’ll build that animation from scratch, render our first MP4, and see how the same approach extends to narrated explainers and larger projects.

Faceless Champ is a Python library for creating animated videos. You describe what should appear, where it belongs, and how it changes over time.

The core ideas are scenes, components, and animations.

A scene holds the visual content and its timeline. Components are the things you place inside it: text, shapes, images, charts, or diagrams. Animations describe changes to those components, such as fading in, moving, or revealing text.

Let’s start with the setup.

You’ll need Python version three point twelve or newer, Git, and FFmpeg. FFmpeg handles video encoding, and its installation needs to include ffprobe and the H.264 encoder called libx264.

Clone the repository and open its folder. Create a Python virtual environment, activate it, and install the library from the checkout using the command on screen.

This gives us an isolated environment for the project and makes the Faceless Champ render command available.

Now create a file called hello dot py.

At the top, we import the tools we need: Canvas, Scene, Text, Circle, and three animation effects.

Next, we define a class called Hello that inherits from Scene. This is our first scene.

The initializer sets up a black canvas, nineteen twenty pixels wide and ten eighty pixels tall. These are design coordinates. When we export at a lower resolution, the framework scales the visuals with the canvas.

The construct method describes what happens in the scene.

First, we create a title that says Hello, Faceless Champ. We give it a font size, a white color, and a position.

Positions use two numbers: horizontal position, then vertical position. The origin is the top-left corner. Moving right increases the first number. Moving down increases the second.

Components use a center anchor by default. So our title’s position places its center at nine hundred sixty across and four hundred down.

Next, we create a turquoise circle. Its radius is sixty design pixels, and its starting position is near the lower-left side of the canvas.

We’ve described our objects. Now let’s put them on the timeline.

Our first play call combines a typewriter reveal for the title with a fade-in for the circle.

Because both animations are inside the same play call, they happen together. The run-time argument gives this step a duration of one and a half seconds.

Then we wait for half a second, giving the viewer time to read.

The next play call moves the circle to the right side of the canvas. The animate builder describes the target position, and run-time controls how long the movement takes.

Separate play calls happen in sequence. Animations inside one play call happen together. A wait creates a pause.

Those three rules are enough to build a simple timeline.

Finally, we pause, fade out both objects, and hold the empty canvas for a moment.

Save the file and run the render command shown here.

We pass the Python filename, the scene class name, and an output path. The low-quality preset makes a smaller preview, and we use lower antialiasing for this first check.

Open the exported MP4. You should see the title appear, the circle move, and both disappear.

Try changing one thing. Replace the title, choose another circle color, or increase the movement duration. Render again with the overwrite flag when you want to replace the existing output.

Now the connection is visible: a change in the code becomes a change in the video.

For longer videos, the same scene model supports imported images, audio, and subtitle timing.

You can attach an existing voiceover at time zero, load its SRT file, and schedule a visual at a subtitle cue. With word-level timestamps, this lets a diagram appear when the narration introduces it.

That makes the framework useful for math explainers, programming lessons, and system-design videos.

When a project needs more structure, Faceless Champ Kit adds named segments, reusable blocks, themes, asset management, and workflow commands on top of the core engine.

Install the bundled Kit, create a project from the silent template, and inspect the generated video file.

Run doctor to check the environment, validate to check the video, and preview to export a short section. Once the preview looks right, render the complete video.

For your first project, keep the scope small: one title, one visual, and one clear action.

Build the scene, check a short preview, and refine the timing. Then add narration and more scenes as the idea grows.

That’s your first Faceless Champ workflow: describe the visuals in Python, animate them on a timeline, and render the result into a video.