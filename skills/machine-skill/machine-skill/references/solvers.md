# Solver recipes

Each machine gets a small, honest model: the few equations that set the number a viewer cares about, with real constants, solved every frame. These are starting points; check the operating point against the public figure for the real machine and say what you simplified in `lab.how()`.

Units: SI inside the solver, display units only at the edge (`fmt`). Air: R = 287 J/kg K, cp = 1005, gamma = 1.4. Hot gas: cp = 1150, gamma = 1.33. Water: rho = 998 kg/m3, mu = 1.0e-3 Pa s. Blood: rho = 1060, mu = 3.5e-3. Steel: rho = 7850, E = 200 GPa. Aluminium: 2700, 69 GPa. Titanium: 4430, 114 GPa.

## Gas turbines (turbofan, turbojet, turboprop)

0D Brayton cycle, static, ISA sea level (T0 = 288.15 K, p0 = 101,325 Pa). See `examples/turbofan.html`.

- Mass flow from the model's fan face annulus and an axial Mach number that follows N1: `mdot = rho A V`.
- Compression: `T_out = T_in [1 + (PR^((g-1)/g) - 1) / eta_c]`.
- Burner: `f = (cp_t T4 - cp T3) / (eta_b LHV - cp_t T4)`, LHV = 43 MJ/kg.
- Work balance per spool: turbine work = compressor (and fan) work / eta_mech, gives T45 and T5.
- Nozzles expand to ambient: `V = sqrt(2 cp T eta_n (1 - (p0/p)^((g-1)/g)))`.
- Thrust `F = mb V19 + mc (1 + f) V9`; TSFC = wf / F.
- Spool dynamics: first order lag on N1 and N2, slower down than up.
- Break: fan blade off. Blade mass from `GEO.volume` x density x hollow fraction; imbalance `F = m omega^2 r_cg`; kinetic energy `1/2 m (omega r_cg)^2` goes into the case.

## Rocket engines

- Chamber: `c* = sqrt(R_spec Tc / gamma) / Gamma(gamma)` with `Gamma = sqrt(gamma) (2/(gamma+1))^((gamma+1)/(2(gamma-1)))`. Methalox at O/F 3.6: Tc about 3,600 K, gamma about 1.2, molar mass about 22 g/mol.
- Throat: `mdot = pc At / c*`. Exit Mach from the area ratio (solve `A/At(M)` by Newton), exit pressure from isentropic relations.
- Thrust coefficient `CF = Gamma sqrt(2g/(g-1) (1 - (pe/pc)^((g-1)/g))) + (pe - pa)/pc * Ae/At`; `F = CF pc At`, `Isp = F / (mdot g0)`.
- Throttle by chamber pressure. Shock diamond spacing about `0.67 De sqrt(M_e^2 - 1)` (under-expanded jets: use the pressure ratio).
- Break: overpressure past the chamber's burst margin, or a turbopump overspeed (`P = T omega`).

## Piston engines

- Slider crank: `x = r cos(th) + sqrt(l^2 - r^2 sin^2(th))`, piston speed and acceleration from its derivatives. Mean piston speed `2 s n`.
- Torque from BMEP: `T = BMEP Vd / (4 pi)` (four stroke). BMEP follows a curve over rpm (about 11 to 13 bar for a good NA petrol engine).
- Power `P = T omega`. Firing order sets the crank angles (cross plane V8: 1-8-4-3-6-5-7-2, 90 degree throws).
- Valve lift from a cam profile; valve float when spring force < valve train inertia force `m a`, which grows with rpm squared.
- Break: over-rev past valve float, then piston to valve contact; or rod tension `m_recip r omega^2 (1 + r/l)` past the rod's capacity.

## Clocks and watches

- Balance wheel: torsional oscillator, `f = (1 / 2pi) sqrt(k / I)`; 4 Hz = 28,800 vph is the modern standard.
- Escapement locks and releases the escape wheel twice per balance period; the gear train sets hand speeds (seconds wheel 1 rev/min).
- Amplitude follows mainspring torque through the train: `T_balance ~ T_spring / ratio x efficiency`; a healthy amplitude is 270 to 310 degrees.
- Power reserve: mainspring turns x barrel ratio / hours per turn.
- Isochronism error and positional error as small rate changes in s/day.
- Break: a shock knocks the balance (amplitude spikes, then the hairspring can overbank and the watch gains); or let the mainspring run down.

## Rotors in wind and water (wind turbines, propellers, hydro)

- Power `P = 1/2 rho A V^3 Cp(lambda, beta)`; tip speed ratio `lambda = omega R / V`.
- Cp from the standard fit `Cp = 0.5176 (116/li - 0.4 beta - 5) e^(-21/li) + 0.0068 lambda`, `1/li = 1/(lambda + 0.08 beta) - 0.035/(beta^3 + 1)`. Betz limit 0.593.
- Rotor speed: `J domega/dt = T_aero - T_gen`; generator torque follows `k omega^2` below rated, constant power above; pitch control holds rated speed above rated wind.
- Thrust on the rotor `T = 1/2 rho A V^2 Ct`; tower base moment = thrust x hub height.
- Break: storm with pitch control off: overspeed, then the brake or blade failure; or cut out at 25 m/s.

## Pumps and fans (centrifugal, axial, heart pumps)

- Euler: `H = (u2 c_u2 - u1 c_u1) / g`. A pump curve `H(Q) = H0 - k Q^2` at the design speed, scaled by the affinity laws `Q ~ n`, `H ~ n^2`, `P ~ n^3`.
- System curve `H_sys = H_static + R Q^2`; the operating point is where they cross (solve every frame).
- Hydraulic power `rho g H Q`; efficiency `eta = rho g H Q / P_shaft`.
- Heart pump (LVAD): about 5,400 rpm, 4 to 6 L/min against 70 to 90 mmHg; the pump's pressure head is the aortic minus the ventricular pressure, which pulses with the heartbeat, so flow pulses too.
- Break: suction (the inflow collapses when the ventricle empties: flow drops to zero, pressure spikes negative), or a thrombus raising power draw.

## Machine tools (spindles, lathes, mills)

- Cutting force by Kienzle: `Fc = kc1.1 b h^(1 - mc)`, aluminium kc1.1 about 700 N/mm2 and mc 0.25; steel about 1,800 and 0.25.
- Chip thickness `h = fz sin(kappa)`; material removal rate `Q = ae ap vf`.
- Spindle torque `T = Fc D/2`, power `P = Fc vc`; check against the spindle's power and torque curves (constant torque to base speed, constant power above).
- Tool deflection as a cantilever: `delta = F L^3 / (3 E I)`, `I = pi d^4 / 64` (about 0.8 d for a fluted tool).
- Break: deflection or chip load past the tool's limit (the tool snaps), or chatter when the depth of cut exceeds the stability lobe.

## Brewing and fluids through porous beds (espresso, filters)

- Darcy: `Q = k A dP / (mu L)`; the puck's permeability k falls as the grind gets finer (about 1e-13 to 1e-12 m2) and as it compacts.
- Boiler: saturated steam table gives pressure from temperature (`p_sat(120 C) = 1.98 bar`).
- Extraction yield (TDS x beverage mass / dose) of 18 to 22 % is the target; a shot is about 36 g in 25 to 30 s at 9 bar.
- Break: channeling (a crack lowers L locally, flow jumps, extraction collapses) or grind too fine (flow chokes).

## Electric machines

- Torque `T = kt I`, back EMF `E = ke omega`, `V = I R + E`; power out `T omega`, copper loss `I^2 R`.
- Thermal: first order `C dT/dt = P_loss - (T - T_amb)/R_th`.
- Break: overcurrent heats the windings past the insulation class (155 C class F).
