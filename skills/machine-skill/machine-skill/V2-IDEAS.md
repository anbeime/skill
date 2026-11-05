# Ideas for a second launch

Version 1 shows one machine from one line. A second launch should show that the same skill does much more. Each idea below is a film beat and a feature.

## 1. More kinds of machine

- **Fluids and heat:** a Francis hydro turbine, a heat pump with its refrigerant cycle on a p-h chart, a nuclear PWR loop, a steam locomotive.
- **Precision:** an EUV scanner stage, a hard disk actuator, a camera autofocus module, a tourbillon.
- **Robots:** a 6 axis arm with inverse kinematics and real joint torques, a quadruped with its gait, a gripper with contact forces.
- **Vehicles:** an EV drive unit with an inverter, a helicopter rotor head with cyclic pitch, a landing gear retraction.
- **Biology and medicine:** an insulin pump, a ventilator, a dialysis filter, a prosthetic knee.

Film beat: the montage grows from 8 to 40 machines, each from a single line.

## 2. Process lines and factories

- One line in, a whole line out: "a line that bottles 30,000 cans an hour". Machines from this skill sit on a factory floor run by a discrete event simulation (the sibling factory skill).
- Click any station to drop into its machine at full detail, running at the rate the line feeds it.
- The bottleneck moves when you change a cycle time, and the machine that becomes the bottleneck visibly works harder.

Film beat: zoom from a factory to one machine to one part inside it, in one shot.

## 3. Systems of machines

- Machines that connect through their physics: a turbofan feeding a generator feeding a grid, a pump feeding a turbine, a gearbox between a motor and a load.
- Shared ports (shaft, pipe, wire) with matched units, so torque, flow and power pass from one solver to the next.
- Break one part and watch the failure travel through the system.

Film beat: "a 5 MW wind farm on a gusty day" and the grid frequency dips when one turbine trips.

## 4. Edit by chat

- Follow up lines change the machine in place: "make the fan 10 % bigger", "swap the titanium blades for carbon", "add a third spool".
- The solver reruns and the page shows a before and after: thrust, mass, fuel burn.
- A history strip of every version, each a single HTML file.

Film beat: three follow up lines, three versions side by side, the numbers diffing.

## 5. Physics comparisons

- Two or three machines on one set running the same duty: a turbofan against a turboprop against an open rotor at the same thrust, a V8 against an electric motor, a centrifugal pump against an axial one.
- One shared slider drives all of them; the hero becomes a small table of live numbers.
- A "why" overlay that points at the part responsible for each difference.

Film beat: "Which is more efficient at 30,000 ft?" and the answer is computed on screen.

## 6. From the page to the real world

- Export the geometry as STEP or GLB and the solver as a Python notebook, so an engineer can take the result further.
- Load a real CAD file (STEP, STL) and have Claude add the solver, the cutaway and the film around it.
- AR on a phone: put the machine on your desk at real size.

## 7. Film upgrades

- Vertical cuts for Reels and Shorts out of the same take (camera keys per aspect ratio).
- A narrated version: Claude writes the voice over from the solver's numbers.
- A "build log" film: the parts list, the equations and the review rounds as the machine assembles.

## What to measure

- Time from the line to the first good frame, and to the film.
- How many of 20 random machine lines pass the quality bar without a second prompt.
- Frame rate on a three year old laptop and on a phone.
