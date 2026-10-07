from faceless_champ import Axis, BarChart, Canvas, ChartReveal, Scene, Text

scene = Scene(Canvas(1920, 1080, "#0b101b"))
chart = BarChart(
    ["Q1", "Q2", "Q3"], {"Completed": [3, 5, 4]},
    width=1200, height=650, position=(960, 520),
    title="Project milestones", y_axis=Axis(limits=(0, 10)),
)
scene.add(Text("SYNTHETIC EXAMPLE DATA", font_size=24,
               color="#8996ad", position=(960, 960)))
scene.play(ChartReveal(chart), run_time=1)
scene.play(chart.animate.data_to({"Completed": [5, 7, 9]}), run_time=1.5)
scene.wait(0.5)
