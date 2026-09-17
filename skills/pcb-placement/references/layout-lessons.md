# Layout lessons and editing mechanics

These are decision criteria, not universal numerical limits. Obtain device-specific requirements from current manufacturer documentation and board-specific limits from the actual stackup and fabrication rules.

## Electrical groups

### Build local subgroups before the board-wide arrangement

The user's preferred process is to group components with the parts they functionally support in the schematic and arrange those in tight subgroups before arranging the groups on the board. Use the schematic to understand ownership; this does not itself authorize redrawing it.

1. Identify the associated IC/function and actual pins for each passive: bypass, feedback, termination, pull-up, strap, filter, current sense, or bias. Group by electrical function, not reference-number order or visual proximity in the existing PCB.
2. Arrange and rotate the subgroup around those pins, respecting critical supply/return loops and routing channels. Aim for at least one useful same-layer termination per passive where practical.
3. Arrange the subgroups around fixed mechanical/RF anchors and their interface connections. Preserve useful internal arrangements while moving/rotating a group; refine individual parts where group interfaces require it.
4. Inspect passives with immediate via exits on both pads. Trace each end to its functional destination and consider a rotation, a local move, or a subgroup orientation change before accepting two layer changes. Do not move the via into the solder pad as a substitute for better placement.
5. Recheck local routing and surrounding congestion, then compare length/via counts and DRC. A small global score increase can be acceptable when local loops, same-layer connections or routability improve.

This two-via observation is a review heuristic, not an automatic failure. A ground-plane via beside a bypass capacitor is often useful. Via count alone cannot justify lengthening a return path or violating electrical constraints. Distinguish two short plane connections from avoidable fan-out caused by a passive placed away from both of its destinations. Do not invent a universal millimetre threshold for "immediate"; inspect the local geometry and state any threshold used by a future analyzer.

The bundled length evaluator does **not** yet classify functional subgroups or detect passives with via exits at both ends. Perform that review from schematic/board connectivity and routes; do not claim the metric report checks it.

### Preferred four-layer arrangement

| Layer | Preferred role |
| --- | --- |
| F.Cu | Components, short local connections and signal routing |
| In1.Cu | Continuous, unbroken ground reference plane |
| In2.Cu | Power distribution partitioned into regions for the required rails |
| B.Cu | Signal/local routing and components where the assembly permits |

Keep general signal traces on the two outer layers. Do not cut signal channels through the ground plane to rescue a crowded placement. "Unbroken" means preserve a continuous useful return reference, allowing necessary holes/antipads and documented RF keepouts; inspect those features for accidental slots or narrow necks. Avoid blanket ground removal beneath ordinary signal paths.

Rail regions on the power layer must remain electrically isolated where required and have adequate current-carrying paths. Bottom signals can reference this adjacent power layer, so a power-plane split can disrupt their return path even with an unbroken ground plane elsewhere. Review crossings, actual layer spacing, reference changes and suitable return paths rather than assuming the preferred layer names guarantee signal integrity. Critical signals may need relocation to the top layer. Retain the user's preference unless a verified requirement warrants a explained exception; it is not permission to silently redesign another project's stackup.

- Place primary bypass capacitors for a short supply-and-return path to the actual IC pins. Distance to a component centre is not sufficient. A close capacitor with a long ground detour is not good decoupling. Secondary bulk capacitance has different placement priority.
- Arrange regulator input capacitor, power pins, inductor and output capacitor around the manufacturer's current paths. Minimize high-di/dt loop area; avoid using aggregate airwire length as a substitute. Keep feedback/sense paths away from switching copper and join control/power grounds as specified for that regulator.
- Order USB protection and passives according to the actual circuit and device guidance. Place protection near the connector; keep paired routes continuous and avoid stubs or unnecessary layer transitions. Do not assume a numerical trace width or spacing until the production stackup is known. Series-resistor location is device-specific.
- Place reset, strap and pull-up parts near their relevant pins when this shortens useful routing. Check boot requirements and service access; do not add hardware to eliminate a documented symbol-model ERC limitation without checking the actual device behavior.
- Maintain return-path continuity. A short trace crossing a reference-plane gap can be worse than a longer trace over a continuous reference. Plane assignments and solid-versus-thermal policies belong to the project, not to this general skill.
- Preserve antenna keepout geometry from the exact module drawing, including applicable copper layers, components, metal fasteners, batteries and enclosure material. A footprint/library mismatch on an RF module warrants inspection, not automatic replacement of the user's footprint.

## Mechanical and assembly constraints

- F.Cu/B.Cu are file layer names, not synonyms for outward/skin-facing. Inspect the physical stack and current layer assignments. A top-view drawing of B.Cu is not a bottom-side assembly view; label viewing conventions.
- Check courtyards together with full component height, screw heads, standoff bodies, tool access, wire bends, battery adhesive, actuator travel and enclosure contact strips. Opposite-side parts may overlap in XY but still collide through holes or the assembled stack.
- Mechanical drawing guides do not enforce copper/placement keepouts. Identify which constraints are actual DRC rules and which need a separate geometry check.
- PCB-as-shell construction makes exposed pads, button loads and supported edges part of placement. Put a low-profile top-push switch on the intended accessible face; do not infer finger usability from its electrical package height. A flexible cover must avoid preload and needs a physical feel/overtravel trial.
- Preserve accepted assembly methods and user capabilities. Do not substitute a larger package solely on assumptions about the user's soldering skill. Check actual process limits, solder-mask webs and via-in-pad policy.

## Footprints and 3D models

- Read the dimensional drawing for the exact suffix. Similar switch families can have different terminal cutouts, land patterns and stencil requirements. Body size is not land-pattern size.
- Check pin numbering, duplicate-number pads, mounting tabs, underside exposed metal and no-solder regions. A schematic/PCB net match cannot prove that the physical pin numbering is right.
- Paste area percentages are area ratios, not per-axis scale factors. If a symmetric reduction uses a ratio r per edge, retained area is (1 + 2r)^2. Record the stencil thickness separately.
- Prefer exact manufacturer or trusted-library STEP models. If unavailable and a simple visualization is useful, create a clearly labeled nominal envelope from verified dimensions. Do not portray terminal/internal details or tolerance fit as verified. Put shared models in a project-local directory with relocatable paths, and attach them to both library and placed footprints.
- Render the actual placed side and inspect seating plane, scale, actuator direction and alignment. B-side transforms should be handled by the footprint placement rather than an improvised mirrored STEP.

## KiCad automation lessons

- Prefer native APIs/CLI for geometry and validation, with a narrowly bounded source patch when a full save would rewrite unrelated user content. Parse S-expressions with a real parser or quote-aware balanced scan, not an unrestricted regex for nested structure.
- Keep library IDs, footprint UUIDs, schematic paths and pad nets through replacement. Do not assume Python exposes a writable `m_Uuid` property. Verify the installed API instead of guessing setter names.
- In KiCad 10's legacy Python API, add a loaded footprint to its board before calling `Flip`; an unattached footprint hung in this workflow. Use an explicit supported flip direction.
- Newly added metadata fields may default to visible silkscreen. Hide MPN/manufacturer/BOM notes, put them on fabrication layers, and handle B-side text mirroring. Otherwise metadata creates spurious silkscreen and edge violations.
- KiCad DRC reports a track object's position, which may be its start rather than the nearest unconnected endpoint. Do not measure that position blindly. The bundled evaluator resolves pad and track anchors, and errors on unsupported endpoints.
- Raw ratsnest objects in the installed legacy Python bindings may be opaque SWIG pointers. Do not claim an exact ratsnest extraction when using a reconstructed metric.
- On managed Windows, use writable `KICAD_DOCUMENTS_HOME` and `KICAD_CONFIG_HOME`. Registry warnings alone did not imply export failure here; use exit status, output existence and parsed content to decide success.
- Reopen externally edited files in a live KiCad editor before saving its stale copy. If there is evidence of unsaved user work, preserve/resolve it before mutation; a warning after overwriting does not protect that work.
- KiCad's legacy Python API is version-dependent and deprecated. The bundle is tested with KiCad 10; inspect or migrate APIs when the installed version changes. Historical migration scripts are not safe incremental editors.
