# Cue-locked production plan

This implements the approved ten-chapter, forty-shot film. The supplied `scene-plan.md` remains unchanged. Exact source cue numbers govern the schedule; the original narration and both SRT files are preserved.

Target: **3840×2160 / 30 fps / 738.300 s / 22,149 frames**. Deliver scenes, generated assets, storyboard and narrated previews. Full export remains unrendered.

## Visual grammar

Black canvas, white clay and cyan contours. Establish each concept large, then retain it beside the developing diagrams and equations. Clear between chapters. Stable orthographic mathematics, slow cinematic views, STIX equations, DM Sans annotations and Space Grotesk labels. Reported hardware, schematic placements and illustrative numerical models are identified separately.

## 01 — THE IMPOSSIBLE MANEUVER

| Shot | Source seconds | Original word cues | Focus |
|---|---|---|---|
| 01A | 0.000–6.760 | 1–15 | Roadster reveal |
| 01B | 6.760–15.680 | 16–38 | Climb and inversion |
| 01C | 15.680–23.560 | 39–56 | Rotation and landing |
| 01D | 23.560–51.600 | 57–134 | Three physical questions |

**Narration:** On October 15, 2026, Tesla demonstrated something that appeared to defy the laws of physics. A roadster accelerated toward a massive curved ramp, climbed almost vertically, continued driving while completely upside down, and then launched into the air. But instead of falling uncontrollably, it rotated through 180 degrees, corrected its orientation, and landed on its wheels. Think about what this requires. How can a car remain attached to a surface when gravity is pulling it away? How can it rotate its entire body while airborne? And how can a vehicle weighing nearly two tons survive such a landing? To answer these questions, we're going to reconstruct the manoeuvre using mathematical equations, three-dimensional engineering models, and physics simulations, and we'll discover that this apparently impossible stunt is actually a combination of several well-understood physical principles.

**Narrated review excerpt:** 0.000–23.560s.

## 02 — ENGINEERING RECONSTRUCTION

| Shot | Source seconds | Original word cues | Focus |
|---|---|---|---|
| 02A | 51.600–62.400 | 135–159 | Blueprint and assembly |
| 02B | 62.400–69.760 | 160–183 | Fans versus thrusters |
| 02C | 69.760–86.500 | 184–224 | Mass and weight |
| 02D | 86.500–100.920 | 225–263 | Contact reaction |

**Narration:** Let's begin with the vehicle itself. Tesla's system combines electric motors, four powerful suction fans, deployable aerodynamic skirts, and a collection of compressed gas thrusters. The fans control how strongly the car presses against a surface, the thrusters control its motion when the wheels can no longer provide support. For our calculations, let's assume a vehicle mass of 1700 kg, approximately the reported target mass of the roadster. The force of gravity acting on this mass is given by mass multiplied by gravitational acceleration, that gives us approximately 16,700 newtons. In ordinary driving, the road balances this downward force through its normal reaction, but during Tesla's manoeuvre, both the direction and magnitude of the contact forces change dramatically, and understanding that change is the key to the entire demonstration.

**Progressive equation reveals:**

- Cue 193, 72.760s: `m=1700\,\mathrm{kg}`
- Cue 203, 77.360s: `W=mg`
- Cue 217, 80.700s: `W=1700\times9.81\,\mathrm{N}`
- Cue 223, 84.590s: `W\approx16.7\,\mathrm{kN}`

**Narrated review excerpt:** 74.500–86.500s.

## 03 — THE LIMIT OF GRIP

| Shot | Source seconds | Original word cues | Focus |
|---|---|---|---|
| 03A | 100.920–121.640 | 264–323 | Resolve gravity |
| 03B | 121.640–132.960 | 324–353 | Tire contact |
| 03C | 132.960–146.160 | 354–393 | Derive the grip limit |
| 03D | 146.160–170.760 | 394–463 | The vertical limit |

**Narration:** Consider an ordinary car travelling up an inclined road. Gravity acts vertically downward, but we can divide it into two components. The perpendicular component is mass times gravity times the cosine of the incline angle. The parallel component is mass times gravity times the sine of that angle. The parallel component is what pulls the car backward down the slope. To overcome this force, the tyres must generate sufficient traction, but traction is limited by friction. A maximum friction force equals the coefficient of friction multiplied by the normal force. Combining these equations gives us a simple condition. The tangent of the incline angle must not exceed the friction coefficient. If the friction coefficient is 1, the car can theoretically resist sliding on an incline of up to 45 degrees. As the angle increases, gravity pulls more strongly down the slope, while the normal force decreases. At 90 degrees, the gravitational contribution to the normal force becomes 0. And without some additional mechanism, the tyres cannot generate the traction required to climb a vertical wall. Making the motors more powerful cannot solve this problem by itself. The car needs another source of normal force, and that's exactly what Tesla engineered.

**Progressive equation reveals:**

- Cue 285, 108.280s: `N=mg\cos\theta`
- Cue 300, 113.790s: `F_{\parallel}=mg\sin\theta`
- Cue 338, 126.360s: `F_{\max}=\mu N`
- Cue 354, 132.960s: `\mu mg\cos\theta\geq mg\sin\theta`
- Cue 362, 135.520s: `\tan\theta\leq\mu`
- Cue 374, 139.740s: `\mu=1\;\Rightarrow\;\theta_{\max}=45^\circ`

**Narrated review excerpt:** 132.960–144.960s.

## 04 — PRESSURE BECOMES GRIP

| Shot | Source seconds | Original word cues | Focus |
|---|---|---|---|
| 04A | 170.760–179.040 | 464–485 | Underbody fans |
| 04B | 179.040–197.520 | 486–541 | Pressure field |
| 04C | 197.520–228.720 | 542–623 | Pressure calculation |
| 04D | 228.720–268.880 | 624–735 | Powered wall climb |

**Narration:** Beneath the roadster are four electrically powered suction fans. Tesla's engineers reported that these fans are rated at approximately 20 kilowatts each. The fans remove air from beneath the vehicle, while deployable skirts help restrict the flow of surrounding air into the low pressure region. This creates a pressure difference between the two sides of the car. Higher atmospheric pressure pushes the vehicle toward the road. The resulting force equals the pressure difference multiplied by the effective area. Tesla claims its system can generate a suction force, equivalent to approximately twice the vehicle's weight. For our 1700 kilogram model, that's around 33,400 newtons. Now suppose the effective suction area is two square meters. Dividing the force by the area gives a required pressure difference of approximately 16.7 kilopascals. That's only about 16% of standard atmospheric pressure. So the system doesn't need to create a perfect vacuum. It simply needs to maintain a substantial pressure difference across a large enough surface. Now look at how this changes tyre grip. On a straight incline, the normal force becomes the gravitational normal component, plus the suction force. At 90 degrees, gravity contributes nothing to this normal load, but the fans can still press the tyres against the wall. With a friction coefficient of one, our simulated car would have approximately 33,400 newtons of available traction. Gravity pulls it downward, with only 16,700 newtons. So in this idealised case, the available traction is twice the force needed to hold the car stationary. That's how the roadster can climb a nearly vertical surface. But what happens when the road curves beyond vertical and the car becomes inverted?

**Progressive equation reveals:**

- Cue 530, 193.140s: `F_s=\Delta p\,A`
- Cue 554, 201.400s: `F_s=2mg\approx33.4\,\mathrm{kN}`
- Cue 574, 210.650s: `A=2\,\mathrm{m^2}`
- Cue 577, 211.920s: `\Delta p=\frac{F_s}{A}`
- Cue 590, 215.480s: `\Delta p\approx16.7\,\mathrm{kPa}`
- Cue 638, 232.400s: `N=mg\cos\theta+F_s`
- Cue 681, 248.050s: `F_{\max}=\mu N\approx33.4\,\mathrm{kN}`

**Narrated review excerpt:** 208.200–220.200s.

## 05 — DRIVING UPSIDE DOWN

| Shot | Source seconds | Original word cues | Focus |
|---|---|---|---|
| 05A | 268.880–285.520 | 736–788 | Static ceiling contact |
| 05B | 285.520–301.160 | 789–827 | Curved motion |
| 05C | 301.160–321.400 | 828–881 | Radial force balance |
| 05D | 321.400–353.400 | 882–962 | Curvature calculation |

**Narration:** At the top of an inverted road, gravity is no longer pressing the car against the surface. It's pulling the car away. If the car is stationary, suction must exceed its weight to maintain contact. With a suction force equal to twice the weight, the remaining contact force is approximately one vehicle weight. But the demonstration also involves a curved trajectory and curved motion introduces centripetal acceleration. Its magnitude equals velocity squared, divided by the local radius of curvature. Multiplying by mass gives the net inward force required to follow the curve. Consider a simplified circular loop, with the car moving along its inside surface, at the very top, the inward direction points downward. The radial force equation combines the road's normal reaction, gravity, and suction. Rearranging it gives the normal force as suction plus mass times velocity squared divided by radius. Minus the vehicle's weight. Let's assume a curved radius of 12 meters and a speed of 12 meters per second. The required centripetal force is approximately 20,400 newtons. Combining this with our assumed suction and gravitational forces gives a road contact reaction of about 37,000 newtons. This shows why the geometry matters. Contact force depends on suction, gravity, speed, and the local curvature of the road. And because centripetal acceleration scales with velocity squared, changing speed can dramatically alter the forces acting on the vehicle.

**Progressive equation reveals:**

- Cue 761, 275.820s: `N=F_s-mg`
- Cue 801, 289.920s: `a_c=\frac{v^2}{R}`
- Cue 852, 309.100s: `N+mg-F_s=\frac{mv^2}{R}`
- Cue 862, 313.560s: `N=F_s+\frac{mv^2}{R}-mg`
- Cue 904, 329.350s: `\frac{mv^2}{R}=20.4\,\mathrm{kN}`
- Cue 922, 336.460s: `N\approx37.1\,\mathrm{kN}`

**Narrated review excerpt:** 321.400–333.400s.

## 06 — MOMENTUM ON DEMAND

| Shot | Source seconds | Original word cues | Focus |
|---|---|---|---|
| 06A | 353.400–374.800 | 963–1019 | Release and pressure vessels |
| 06B | 374.800–389.500 | 1020–1060 | Nozzle momentum |
| 06C | 389.500–404.560 | 1061–1099 | Thrust and mass flow |
| 06D | 404.560–420.720 | 1100–1142 | Finite gas budget |

**Narration:** Now the roadster reaches the end of the ramp as the vehicle separates from the surface. The road's contact force disappears. The car becomes a freely moving rigid body. Tesla solves the next problem using compressed gas thrusters developed with technology from SpaceX. The reported flight configuration contains 10 nozzles and approximately 250 kg of compressed gas. When pressurized gas escapes through a nozzle, it carries momentum in one direction. Conservation of momentum produces a reaction force in the opposite direction. The rocket thrust equation relates this force to gas mass flow, exhaust velocity, and nozzle exit pressure. For a simplified model, thrust equals mass flow rate multiplied by an effective exhaust velocity. Suppose we want 20,000 newtons of force, with an effective exhaust velocity of 600 m/s. That requires approximately 33 kg of gas every second. This explains why the thrusters can produce enormous forces, but only for short periods. The stored gas is finite, and pressure decreases as it is released. These systems are therefore particularly useful for rapid acceleration, trajectory corrections, and short bursts of rotational control.

**Progressive equation reveals:**

- Cue 1044, 383.160s: `F=\dot m v_e+(p_e-p_a)A_e`
- Cue 1061, 389.500s: `F=\dot m v_{\mathrm{eff}}`
- Cue 1079, 395.480s: `F=20\,\mathrm{kN}\,,\quad v_{\mathrm{eff}}=600\,\mathrm{m/s}`
- Cue 1094, 402.550s: `\dot m=\frac{F}{v_{\mathrm{eff}}}\approx33.3\,\mathrm{kg/s}`

**Narrated review excerpt:** 394.800–406.800s.

## 07 — A CONTROLLED HALF-ROLL

| Shot | Source seconds | Original word cues | Focus |
|---|---|---|---|
| 07A | 420.720–444.160 | 1143–1208 | Force versus torque |
| 07B | 444.160–469.240 | 1209–1278 | Inertia and two phases |
| 07C | 469.240–491.440 | 1279–1328 | Angular acceleration |
| 07D | 491.440–529.860 | 1329–1429 | The torque couple |

**Narration:** Now consider the car while it's upside down in mid-air. To land correctly, it must rotate approximately 180 degrees, but applying a force through the center of mass only accelerates the vehicle. To rotate it, we need torque. Torque is the cross product of the position vector and the applied force. For rotation around a principal axis, torque equals moment of inertia multiplied by angular acceleration. Let's model a role around the car's longitudinal axis. Assume its moment of inertia is 800 kg m2, and suppose we want to complete a half revolution in 1.6 seconds, beginning and ending with zero role velocity. We can divide the motion into two equal phases. During the first half, the thrusters accelerate the rotation. During the second half, they reverse the torque and reduce the angular velocity to zero. For constant acceleration and deceleration, the required angular acceleration magnitude is four times the rotation angle, divided by the total time squared. Substituting pi radians and 1.6 seconds gives approximately 4.9 radians per second squared. Multiplying by the moment of inertia gives a torque requirement of roughly 3,900 Newton meters. Now imagine two thrusters producing equal and opposite vertical forces on opposite sides of the chassis, with an effective separation of 1.5 meters, each thruster needs approximately 2,600 newtons to create the required couple. Their forces nearly cancel as a net vertical force, while their torques add. And by reversing that torque halfway through the manoeuvre, the car can reach an upright orientation with approximately zero angular velocity. The real manoeuvre is more complex, because pitch, roll and york can interact. In a complete simulation, we must use the vehicle's three-dimensional inertia tensor and calculate angular motion along all three axes,

**Progressive equation reveals:**

- Cue 1175, 431.880s: `\boldsymbol{\tau}=\mathbf{r}\times\mathbf{F}`
- Cue 1194, 437.880s: `\tau=I\alpha`
- Cue 1224, 449.230s: `I=800\,\mathrm{kg\,m^2}`
- Cue 1237, 453.620s: `\theta=\pi\,,\quad T=1.6\,\mathrm{s}`
- Cue 1289, 474.020s: `\alpha=\frac{4\theta}{T^2}`
- Cue 1309, 482.200s: `\alpha\approx4.91\,\mathrm{rad/s^2}`
- Cue 1326, 488.950s: `\tau\approx3.93\,\mathrm{kN\,m}`
- Cue 1350, 499.130s: `d=1.5\,\mathrm{m}`
- Cue 1356, 502.020s: `F=\frac{\tau}{d}\approx2.62\,\mathrm{kN}`

**Narrated review excerpt:** 509.920–521.920s.

## 08 — SIX DEGREES OF FREEDOM

| Shot | Source seconds | Original word cues | Focus |
|---|---|---|---|
| 08A | 529.860–547.880 | 1430–1482 | Translational and angular state |
| 08B | 547.880–562.400 | 1483–1520 | The feedback loop |
| 08C | 562.400–574.200 | 1521–1551 | Control allocation |
| 08D | 574.200–581.280 | 1552–1570 | Landing alignment |

**Narration:** but rotating the car is only part of the challenge. The system must also control the position and velocity of its centre of mass. Every thruster contributes a force, and depending on its location, a torque. The total force determines the car's linear acceleration. The total torque determines how its angular momentum changes. A flight controller must estimate the vehicle's current position, velocity, orientation, and angular velocity. It then calculates the force and torque needed to follow a desired trajectory. Finally, it determines which nozzles should fire, and for how long. This process is called control allocation. Tesla has not published its exact control algorithms, but the underlying mathematics is similar to that used in spacecraft attitude control and robotic flight systems. The goal is to reach the ground with the correct orientation, a manageable descent velocity, and minimal unwanted rotation.

**Progressive equation reveals:**

- Cue 1466, 541.200s: `m\ddot{\mathbf{r}}=\sum_i\mathbf{F}_i`
- Cue 1474, 544.400s: `\mathbf{I}\dot{\boldsymbol{\omega}}+\boldsymbol{\omega}\times(\mathbf{I}\boldsymbol{\omega})=\boldsymbol{\tau}`
- Cue 1521, 562.400s: `\mathbf{w}=\mathbf{B}\mathbf{u}\,,\quad\mathbf{B}\in\mathbb{R}^{6\times10}`

**Narrated review excerpt:** 550.400–562.400s.

## 09 — THE MATHEMATICS OF LANDING

| Shot | Source seconds | Original word cues | Focus |
|---|---|---|---|
| 09A | 581.280–605.840 | 1571–1632 | Free-fall experiment |
| 09B | 605.840–629.880 | 1633–1692 | Hovering is not braking |
| 09C | 629.880–651.760 | 1693–1754 | Braking distance |
| 09D | 651.760–677.920 | 1755–1823 | Controlled touchdown |

**Narration:** Now imagine the roadster descending toward the ground, suppose it falls from rest through 20 metres, without any thruster assistance. Conservation of energy tells us that gravitational potential energy becomes kinetic energy, and resulting impact speed is the square root of twice gravitational acceleration multiplied by height. That gives approximately 19.8 metres per second, or more than 70 kilometres per hour downward. To avoid a destructive landing, the car must reduce that velocity. The vertical equation of motion is simple. Mass times vertical acceleration equals upward directed thrust minus gravitational weight. For our simulated vehicle, a thrust of 16.7 kN would balance gravity, but balancing gravity does not automatically stop a falling object. To actually slow its descent, thrust must exceed weight. Now consider a simplified landing simulation. The vehicle begins falling from rest at 20 metres. We allow it to fall freely through the first 10 metres. This downward velocity reaches approximately 14 metres per second, then we activate the braking thrusters. To reduce that velocity to zero over the remaining 10 metres, the car needs a net upward acceleration of approximately 1g. The thrusters must therefore generate approximately twice the vehicle's weight, that's 33.4 kilonewtons of upward thrust. In this idealised scenario, the car could theoretically reduce its vertical speed to zero before touching the ground. The actual demonstration involved a different initial velocity, changing thrust directions, and a more complicated trajectory, but the principle is the same. The landing system must remove enough downward momentum before the wheels make contact.

**Progressive equation reveals:**

- Cue 1591, 589.120s: `mgh=\frac{1}{2}mv^2`
- Cue 1615, 598.080s: `v=\sqrt{2gh}\approx19.8\,\mathrm{m/s}`
- Cue 1647, 610.680s: `ma_z=T_z-mg`
- Cue 1688, 627.870s: `T_z>mg\quad\Rightarrow\quad a_z>0`
- Cue 1734, 644.440s: `v_f^2=v_i^2+2a\,d`
- Cue 1754, 651.210s: `a_{\mathrm{net}}\approx g`
- Cue 1766, 655.460s: `T_z=m(a_z+g)\approx33.4\,\mathrm{kN}`

**Narrated review excerpt:** 654.210–666.210s.

## 10 — THE COMPLETE PHYSICS

| Shot | Source seconds | Original word cues | Focus |
|---|---|---|---|
| 10A | 677.920–687.000 | 1824–1847 | One complete system |
| 10B | 687.000–703.240 | 1848–1884 | Coordinated replay |
| 10C | 703.240–726.240 | 1885–1943 | Physical limitations |
| 10D | 726.240–738.300 | 1944–1975 | Mathematics brought to life |

**Narration:** So did Tesla create a car that breaks the laws of physics? No. The demonstration combines several established physical principles in an extraordinary way. Pressure differences create artificial grip. Friction transfers propulsion forces to the road. The triple acceleration governs the curved inverted trajectory. Compressed gas thrusters generate impulse and rotational torque, and carefully directed thrust reduces the car's landing velocity. But performing this manoeuvre once is not the same as making it safe, efficient, or practical for everyday transportation. The system still faces limitations in stored gas, pressure loss, fan ceiling, energy consumption, and flight control precision. We also don't yet have the complete engineering data required to independently reconstruct Tesla's exact trajectory, but the underlying physics is clear. Tesla didn't escape gravity. It used pressure, momentum, and controlled forces to overcome the limitations of an ordinary car. And sometimes, what looks like impossible physics is simply mathematics brought to life.

**Narrated review excerpt:** 687.000–699.000s.

## Shared scientific checkpoints

| Quantity | SI value |
|---|---:|
| weight_N | 16677 |
| suction_N | 33354 |
| pressure_kPa | 16.677 |
| radial_N | 20400 |
| apex_normal_N | 37077 |
| mass_flow_kg_s | 33.3333333 |
| alpha_rad_s2 | 4.90873852 |
| torque_Nm | 3926.99082 |
| couple_each_N | 2617.99388 |
| freefall_speed_m_s | 19.8090888 |
| braking_speed_m_s | 14.007141 |
| landing_time_s | 2.85568625 |

## Generated asset placement

| Asset | Shots | Purpose |
|---|---|---|
| hero_front.png | 01A | Reference-matched cinematic opening |
| ramp_stage.png | 01A | Full-screen ramp establishment before the live climb |
| fan_macro.png | 04A | Underbody mechanism introduction |
| gas_macro.png | 06A | Stored-gas hardware accent |
| landing_hero.png | 10D | Quiet closing frame |

Full prompts, native image dimensions and hashes are in `assets/13_Generated/provenance.json`. Models, sections, force vectors, plots, mathematical text and diagrams are authored independently from these raster plates.

## Implementation and acceptance

The root Scene contains one narration clip at master zero. The public core Renderer protocol composes ArchChamp, Equation and FlowChamp with project-owned scientific overlays. All numerical states are functions of simulation time and can seek in either direction. The media clock controls when an experiment plays, pauses or resets; it does not change the equations.

Acceptance: unchanged source hashes and all five rounding overlaps; correct forces and torque signs; calculated zero-speed touchdown; closed capped surfaces; readable retained diagrams; 80 storyboard frames; representative 4K stills; ten completely decoded and audio-aligned narrated previews. `full_export_verified` stays false.
