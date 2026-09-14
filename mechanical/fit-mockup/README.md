# First fit mockup — revision 0.6

Print **seven satellite shells/lids and one main shell/lid** from `print/`, in millimetres. These are simple flat fit coupons: 20 × 38 × 10.5 mm regular, 24 × 64 × 10.5 mm main when closed. Shells print floor down; lids print flat. The 14 mm wire mouths have a 2.4 mm-high opening and need a short bridge in an upright shell print; inspect the sliced bridge. Use temporary tape to retain the lids and an external elastic wrap for a wrist size trial. There are no clips, final TPU links or clasp yet.

The `reference-only/` meshes are rigid **nonfunctional gauges**, kept separate from printable housing parts. The cell gauge represents only the nominal 12 × 32 × 3 mm protected battery body, not leads, expansion or tolerance. The LRA gauge excludes its adhesive, foam and flex tail. PCB gauges simplify the native board chamfers into square corners; use native PCB outlines for the eventual manufactured boards.

Cells bond to the lid inner surface; there is no compartment or shelf. The flat 1 mm shell floor is the LRA bonding surface. The PCB datum is 2 mm above the shell's wrist face. These first coupons do not include PCB retention/support ledges: use removable 1 mm spacers above the 1 mm floor for a bench fit trial. Do not populate cells during an unsupported PCB fit test. Final supports must avoid components and wire terminations.

Main shell openings follow the current USB and side-button placement; the LED has a 2.4 mm square lid window. No light pipe/button extender is modeled. The main cell allocation remains x=5..19, y=22..56 mm; regular allocation x=3..17, y=2..36 mm. Battery allocation z=5.8..9.3 mm, adhesive z=9.3..9.5 mm. Check a physical sample with its factory PCM and lead bend. LRA lands are 1 mm offset from the old centred-opening study to accommodate the tail.

`mesh-checks.json` records successful post-export watertightness, winding, single connected mesh, positive volume and dimensions for each STL. These checks establish mesh integrity only. The 195 mm wrist fit, curved contact pressure, material flexibility, cable strain, actual component heights, tail folding, lid removal, and RF performance remain physical design work.

Regenerate with the bundled dependency Python and `tools/build_fit_mockup.py`. Source geometry is the editable Python plus the native placement JSON. These STL coupons are not a finished wearable enclosure or STEP solids.
