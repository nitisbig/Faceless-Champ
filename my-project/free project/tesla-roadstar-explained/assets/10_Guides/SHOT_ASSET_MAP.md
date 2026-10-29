# Shot-to-Asset Map (Based on the 10-Scene Storyboard)

Scene 01, Opening: 01_Vehicle/roadster_wireframe_threequarter; 02_Ramps_and_Road/curved_half_loop; 05_Force_Vectors/gravity_vector; 06_Simulation_Overlays/perspective_grid
Scene 02, Reconstruction: 01_Vehicle/roadster_wireframe_{side,front,rear,top}; 03_Suction_and_Airflow/four_fan_assembly; 04_Thrusters/twin_pressure_vessels; 05_Force_Vectors/center_of_mass_target
Scene 03, Friction: 02_Ramps_and_Road/road_tire_contact; 05_Force_Vectors/force_decomposition; 07_Equations/{01_gravity,02_normal,03_friction,04_friction_limit}
Scene 04, Suction: 03_Suction_and_Airflow/{suction_fan_top,four_fan_assembly,suction_pressure_cutaway,deployable_skirt_cross_section,underbody_airflow_streamlines,pressure_field_heatmap}; 07_Equations/{05_suction_pressure,06_suction_normal}
Scene 05, Inversion: 02_Ramps_and_Road/{curved_half_loop,wall_and_ceiling}; 01_Vehicle/roadster_inverted; 05_Force_Vectors/{gravity_vector,suction_vector}; 07_Equations/{07_centripetal,08_loop_contact}
Scene 06, Cold Gas: 04_Thrusters/{pressure_vessel_wireframe,twin_pressure_vessels,cold_gas_thruster_nozzle,thruster_jet_plume,valve_piping_schematic}; 07_Equations/{09_rocket_thrust,17_thrust_flow}
Scene 07, Rotation: 01_Vehicle/roadster_wireframe_rear; 05_Force_Vectors/{torque_roll_arc,center_of_mass_target}; 06_Simulation_Overlays/angular_velocity_plot; 07_Equations/{10_torque,11_roll,12_roll_accel}
Scene 08, Flight Control: 05_Force_Vectors/six_dof_axes; 06_Simulation_Overlays/{control_loop,trajectory_parabola,data_panel_blank}; 07_Equations/13_euler_rotation
Scene 09, Landing: 01_Vehicle/roadster_wireframe_side; 05_Force_Vectors/{gravity_vector,thrust_vector}; 06_Simulation_Overlays/{altitude_velocity_graph,thrust_curve}; 07_Equations/{14_vertical_flight,15_freefall,16_energy,18_braking}
Scene 10, Replay: 08_Scene_Layouts/scene_10_the_complete_physics; all previous groups as coordinated layers.

All source SVGs are editable and carry no black background except the ten scene layouts.
