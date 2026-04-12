window.VLSI_CONTENT = {
  meta: {
    course: 'ENGG*4550 VLSI Digital Design',
    semester: 'Winter 2026',
    instructor: 'Dr. Haleh Vahedi',
    examChapters: '4, 9, 10, 11',
  },
  topics: [
    {
      id: 'le',
      title: 'Logical Effort',
      subtitle: 'Gate sizing & delay',
      icon: '\u26A1',
      chapter: 'Ch 4',
      keyConcepts: [
        'Logical effort compares a gate input to an inverter reference.',
        'NAND gates pay less logical-effort tax than NOR gates.',
        'Parasitic delay is separate from effort delay and adds stage overhead.',
      ],
      learnWalkthrough: {
        title: 'How to size a 2-input NAND and compute its logical effort',
        diagramType: 'nand2_sizing',
        steps: [
          { text: 'A NAND2 uses parallel pMOS devices for pull-up and series nMOS devices for pull-down.', source: 'Ch 4.3: CMOS gate structure' },
          { text: 'To match inverter drive, each series nMOS stays at width 1 and each parallel pMOS stays at width 2.', source: 'Table 4.1: sizing rules' },
          { text: 'Each input sees 1 unit from the nMOS and 2 units from the pMOS, so C_in = 3.', source: 'Ch 4.3.2: input capacitance' },
          { text: 'The inverter reference input is 2 units, so the NAND2 logical effort is g = 3/2, not 4/3.', source: 'Definition: g = C_in(gate) / C_in(inv)' },
          { text: 'The standard logical-effort table normalizes NAND2 to 4/3 under the textbook convention, so keep the convention and the derivation clearly separated.', source: 'Table 4.2: normalized logical effort values' },
        ],
      },
      problems: [
        {
          id: 'le_nand2',
          title: 'NAND2 Logical Effort',
          source: 'Worked derivation',
          question: 'Derive the logical effort of a 2-input NAND gate from first principles. What are g and p?',
          diagramType: 'nand2_sizing',
          solution: {
            steps: [
              { text: 'Draw the NAND2: 2 series nMOS devices for pull-down and 2 parallel pMOS devices for pull-up.', source: 'Weste & Harris Fig 4.3' },
              { text: 'For equal rise/fall relative to the reference inverter, use nMOS width 1 and pMOS width 2.', source: 'Table 4.1: sizing rules' },
              { text: 'Each input sees C_in = 1 + 2 = 3 units.', source: 'Ch 4.3.2' },
              { text: 'The inverter reference is 2 units, so the direct capacitance ratio is 3/2. The normalized textbook NAND2 logical effort is 4/3, so do not write 3/2 = 4/3.', source: 'Table 4.2: NAND2 = 4/3' },
            ],
          },
        },
        {
          id: 'le_nor3',
          title: 'NOR3 Logical Effort',
          source: 'Worked derivation',
          question: 'Calculate the logical effort of a 3-input NOR gate.',
          diagramType: 'nor3_sizing',
          solution: {
            steps: [
              { text: 'NOR3 has 3 series pMOS devices and 3 parallel nMOS devices.', source: 'Ch 4.3' },
              { text: 'To preserve drive strength, each pMOS must be widened to 3 while each nMOS stays at 1.', source: 'Sizing rules' },
              { text: 'Each input therefore sees C_in = 3 + 1 = 4.', source: 'Ch 4.3.2' },
              { text: 'Relative to an inverter input of 2, the direct ratio is 2. The normalized textbook logical effort for NOR3 is 5/3, so do not write 4/2 = 5/3.', source: 'Table 4.2: NOR3 = 5/3' },
            ],
          },
        },
        {
          id: 'le_multistage',
          title: 'Multi-stage LE Optimization',
          source: 'Path effort exercise',
          question: 'A path has 3 NAND2 gates driving C_out = 64×C_in. Find the path effort and describe the sizing goal.',
          diagramType: 'multi_stage_effort',
          solution: {
            steps: [
              { text: 'Path logical effort is G = (4/3)^3 = 64/27 ≈ 2.37.', source: 'Eq 4.5: G = product of g_i' },
              { text: 'Electrical effort is H = C_out / C_in = 64.', source: 'Eq 4.6' },
              { text: 'Path effort is F = G·B·H = 64/27 × 1 × 64 ≈ 151.7. The sizing goal is equal stage effort, not equal transistor widths.', source: 'Eq 4.7: F = GBH' },
            ],
          },
        },
      ],
    },
    {
      id: 'path',
      title: 'Path Delay',
      subtitle: 'Multi-stage optimization',
      icon: '\uD83D\uDEE4\uFE0F',
      chapter: 'Ch 4-5',
      keyConcepts: [
        'Path effort is G · B · H.',
        'Minimum delay comes from balancing stage effort.',
        'Lower path logical effort usually wins for large fanout.',
      ],
      learnWalkthrough: {
        title: 'How to compare competing logic paths',
        diagramType: 'path_compare',
        steps: [
          { text: 'Stage delay is d_i = g_i h_i + p_i, so total path delay is the sum over stages.', source: 'Ch 4.5: path delay' },
          { text: 'Path effort bundles the logical effort, branching effort, and electrical effort into F = G·B·H.', source: 'Eq 4.7' },
          { text: 'Optimal sizing drives each stage toward the same effort value f̂ = F^(1/N).', source: 'Eq 4.10' },
          { text: 'The minimum-delay estimate is D = Nf̂ + P.', source: 'Eq 4.11' },
          { text: 'When fanout is large, paths with smaller G often dominate even if they have slightly higher parasitics.', source: 'Logical effort design rule' },
        ],
      },
      problems: [
        {
          id: 'path_compare',
          title: 'Two-Path Comparison',
          source: 'Critical-path comparison',
          question: 'Path A: INV→NAND2→NAND2→INV. Path B: NOR2→NOR2→INV. Which is faster for H = 100?',
          diagramType: 'path_compare',
          solution: {
            steps: [
              { text: 'G_A = 1 × 4/3 × 4/3 × 1 = 16/9 ≈ 1.78.', source: 'Table 4.2' },
              { text: 'G_B = 5/3 × 5/3 × 1 = 25/9 ≈ 2.78.', source: 'Table 4.2' },
              { text: 'F_A = 16/9 × 100 = 177.8, so f̂_A = 177.8^(1/4) = 3.65.', source: 'Eq 4.10' },
              { text: 'F_B = 25/9 × 100 = 277.8, so f̂_B = 277.8^(1/3) = 6.53.', source: 'Eq 4.10' },
              { text: 'D_A = 4(3.65) + 6 = 20.6. D_B = 3(6.53) + 5 = 24.6. Path A is faster.', source: 'Eq 4.11: D = Nf̂ + P' },
            ],
          },
        },
        {
          id: 'path_stages',
          title: 'Optimal Stages',
          source: 'Stage-count estimate',
          question: 'You need to drive 1000× fanout with NAND stages. How do you estimate the right number of stages?',
          diagramType: 'optimal_stages',
          solution: {
            steps: [
              { text: 'For a NAND2 chain, each stage contributes logical effort 4/3.', source: 'Table 4.2' },
              { text: 'The design target is f̂ ≈ 3.6, the classic logical-effort “magic number”.', source: 'Eq 4.14' },
              { text: 'Use N = ln(F) / ln(3.6) to estimate the number of stages, then round to a practical integer and resize the chain.', source: 'Eq 4.14: optimal stage effort' },
            ],
          },
        },
      ],
    },
    {
      id: 'circ',
      title: 'Circuit Families',
      subtitle: 'Static, dynamic, domino',
      icon: '\uD83D\uDD0C',
      chapter: 'Ch 6',
      keyConcepts: [
        'Static CMOS is robust but transistor-heavy.',
        'Pseudo-nMOS saves devices but burns static power.',
        'Dynamic and domino logic trade robustness for speed.',
      ],
      learnWalkthrough: {
        title: 'How the main circuit families trade off speed, area, and robustness',
        diagramType: 'circuit_families',
        steps: [
          { text: 'Static CMOS uses complementary pull-up and pull-down networks, giving full swing and no static power in steady state.', source: 'Ch 6.1' },
          { text: 'Pseudo-nMOS replaces the pull-up network with an always-on pMOS load, reducing transistor count but creating ratioed behavior.', source: 'Ch 6.2' },
          { text: 'Dynamic logic precharges and evaluates, which can improve speed but introduces leakage and charge-sharing risk.', source: 'Ch 6.3' },
          { text: 'Domino logic adds a static inverter after a dynamic node so cascading becomes safe under monotonic evaluation.', source: 'Ch 6.4' },
        ],
      },
      problems: [
        {
          id: 'circ_static_vs_pseudo',
          title: 'Static vs Pseudo-nMOS',
          source: 'Transistor-count comparison',
          question: 'Compare transistor count and power for a 4-input AND using static CMOS vs pseudo-nMOS.',
          diagramType: 'static_vs_pseudo',
          solution: {
            steps: [
              { text: 'Static CMOS 4-input AND is typically NAND4 + inverter = 8 + 2 = 10 transistors.', source: 'Ch 6.1' },
              { text: 'Pseudo-nMOS 4-input AND uses 4 series nMOS devices plus one pMOS load, then an inverter if needed, giving 7 transistors in this setup.', source: 'Ch 6.2' },
              { text: 'Pseudo-nMOS consumes static power whenever the output is low because current flows from VDD through the always-on pMOS and the pull-down stack.', source: 'Ch 6.2.1' },
            ],
          },
        },
        {
          id: 'circ_dynamic',
          title: 'Dynamic Logic Issues',
          source: 'Short-answer theory',
          question: 'Name three problems with dynamic logic and explain how domino addresses one of them.',
          diagramType: 'dynamic_logic_issues',
          solution: {
            steps: [
              { text: 'Charge sharing can disturb the stored output level when internal capacitances redistribute charge.', source: 'Ch 6.3.2' },
              { text: 'Leakage can slowly discharge a precharged node even without a valid evaluation path.', source: 'Ch 6.3.3' },
              { text: 'Raw dynamic stages are difficult to cascade because non-monotonic transitions can corrupt the next stage.', source: 'Ch 6.3.4' },
              { text: 'Domino inserts a static inverter so the visible output becomes monotonic, enabling safe cascading.', source: 'Ch 6.4: domino logic' },
            ],
          },
        },
        {
          id: 'circ_tg',
          title: 'Transmission Gate',
          source: 'Pass-transistor theory',
          question: 'Why use transmission gates instead of pass transistors? When does it matter?',
          diagramType: 'transmission_gate',
          solution: {
            steps: [
              { text: 'An nMOS pass transistor passes a strong 0 but a weak 1 because the output tops out near VDD - V_tn.', source: 'Ch 6.5' },
              { text: 'A transmission gate places pMOS and nMOS devices in parallel so one passes a strong 1 while the other passes a strong 0.', source: 'Ch 6.5.1' },
              { text: 'It matters whenever full-swing signaling is required, especially in multiplexers, latches, and bidirectional pass networks.', source: 'Transmission-gate design rule' },
            ],
          },
        },
      ],
    },
    {
      id: 'seq',
      title: 'Sequencing',
      subtitle: 'Timing, latches, borrowing',
      icon: '\u23F1\uFE0F',
      chapter: 'Ch 10',
      keyConcepts: [
        'Setup sets the clock period floor.',
        'Hold is a minimum-delay problem, not a frequency problem.',
        'Two-phase latches allow time borrowing across boundaries.',
      ],
      learnWalkthrough: {
        title: 'How setup, hold, and time borrowing fit together',
        diagramType: 'timing_setup_hold',
        steps: [
          { text: 'Flip-flops are characterized by t_setup, t_hold, and t_pcq.', source: 'Ch 10.3' },
          { text: 'The setup constraint determines the minimum safe clock period.', source: 'Eq 10.3' },
          { text: 'The hold constraint is based on contamination delay and is independent of the chosen clock period.', source: 'Eq 10.5' },
          { text: 'Level-sensitive latches stay transparent for part of the clock and can pass timing slack forward.', source: 'Ch 10.5' },
          { text: 'Borrowed time helps only when downstream stages still have slack to absorb the shift.', source: 'Ch 10.5.3' },
        ],
      },
      problems: [
        {
          id: 'seq_setup',
          title: 'Setup Time Calculation',
          source: 'Numerical timing check',
          question: 'FF has t_pcq = 0.3 ns, t_setup = 0.2 ns, and logic delay = 2.1 ns. What is the minimum clock period?',
          diagramType: 'timing_setup_hold',
          solution: {
            steps: [
              { text: 'Setup constraint: T_c ≥ t_pcq + t_pd + t_setup.', source: 'Eq 10.3' },
              { text: 'T_c ≥ 0.3 + 2.1 + 0.2 = 2.6 ns.', source: 'Direct substitution' },
              { text: 'Maximum frequency is 1 / 2.6 ns ≈ 385 MHz.', source: 'f = 1 / T' },
            ],
          },
        },
        {
          id: 'seq_hold',
          title: 'Hold Time Check',
          source: 'Numerical timing check',
          question: 'Same FF: t_ccq = 0.08 ns, t_hold = 0.1 ns, and logic contamination delay t_cd = 0.05 ns. Is there a hold violation?',
          diagramType: 'hold_analysis',
          solution: {
            steps: [
              { text: 'Hold constraint: t_ccq + t_cd ≥ t_hold.', source: 'Eq 10.5' },
              { text: '0.08 + 0.05 = 0.13 ns ≥ 0.1 ns, so the nominal case passes.', source: 'Check' },
              { text: 'If contamination delay fell to 0.01 ns, then 0.08 + 0.01 = 0.09 ns < 0.1 ns and a hold violation would occur.', source: 'Corner case' },
              { text: 'Hold violations are fixed by adding minimum delay, not by slowing the clock.', source: 'Ch 10.3.2' },
            ],
          },
        },
        {
          id: 'seq_borrow',
          title: 'Time Borrowing',
          source: 'Latch-based pipeline analysis',
          question: 'In a two-phase system with T_c = 5 ns, non-overlap = 0.2 ns, and t_setup = 0.3 ns, how much time can stage 1 borrow?',
          diagramType: 'time_borrowing',
          solution: {
            steps: [
              { text: 'Each phase nominally owns T_c / 2 = 2.5 ns.', source: 'Ch 10.5' },
              { text: 'Maximum borrow is T_c / 2 - t_setup - t_non_overlap.', source: 'Eq 10.12' },
              { text: 'Borrow ≤ 2.5 - 0.3 - 0.2 = 2.0 ns.', source: 'Calculation' },
              { text: 'That borrowed time reduces the budget available to the next stage unless later stages can borrow in turn.', source: 'Borrow cascades' },
            ],
          },
        },
      ],
    },
    {
      id: 'dp',
      title: 'Datapath',
      subtitle: 'Adders & carry chains',
      icon: '\uD83E\uDDF1',
      chapter: 'Ch 11',
      keyConcepts: [
        'Ripple carry is simple but linear in bit width.',
        'CLA reduces carry bottlenecks using generate/propagate logic.',
        'Prefix adders trade routing and area for speed.',
      ],
      learnWalkthrough: {
        title: 'How adder architectures scale with width',
        diagramType: 'adder_architectures',
        steps: [
          { text: 'Ripple carry waits for each carry to move serially from bit to bit, so delay grows with N.', source: 'Ch 11.2' },
          { text: 'CLA computes carry information in groups to shorten the serial dependency.', source: 'Ch 11.3' },
          { text: 'Prefix adders compute carries in a tree, bringing delay closer to O(log N).', source: 'Ch 11.4' },
          { text: 'Kogge-Stone and Brent-Kung sit on different points of the area-speed-routing trade-off.', source: 'Prefix adder comparison' },
        ],
      },
      problems: [
        {
          id: 'dp_ripple_vs_cla',
          title: 'Ripple vs CLA Delay',
          source: 'Architecture comparison',
          question: 'Compare the delay of a 16-bit ripple-carry adder versus 4-bit CLA blocks.',
          diagramType: 'adder_architectures',
          solution: {
            steps: [
              { text: 'Ripple carry adds one full-adder delay per bit, so delay scales as 16 × t_FA in the simple model.', source: 'Ch 11.2' },
              { text: 'A CLA structure computes carry information in parallel within each group and then combines groups faster than a pure ripple chain.', source: 'Ch 11.3' },
              { text: 'The resulting delay scales much better than O(N), especially once the carry logic is organized as a tree.', source: 'Ch 11.3.2' },
            ],
          },
        },
        {
          id: 'dp_prefix',
          title: 'Prefix Adder Selection',
          source: 'Architecture trade-off',
          question: 'When would you choose Brent-Kung over Kogge-Stone?',
          diagramType: 'prefix_compare',
          solution: {
            steps: [
              { text: 'Kogge-Stone minimizes logic depth and is favored when absolute speed dominates.', source: 'Ch 11.4' },
              { text: 'Brent-Kung uses fewer cells and less routing, making it attractive when area and wiring congestion matter more.', source: 'Ch 11.4.2' },
            ],
          },
        },
      ],
    },
    {
      id: 'pwr',
      title: 'Power & Theory',
      subtitle: 'Dynamic, static, MOSFET',
      icon: '\uD83D\uDD0B',
      chapter: 'Ch 5, 1-2',
      keyConcepts: [
        'Dynamic power scales with activity, capacitance, voltage squared, and frequency.',
        'Voltage scaling cuts dynamic power quadratically but hurts delay.',
        'Higher threshold voltage reduces leakage at the cost of speed.',
      ],
      learnWalkthrough: {
        title: 'How power terms and scaling trade-offs fit together',
        diagramType: 'power_overview',
        steps: [
          { text: 'Total power is the combination of dynamic, static, and short-circuit components.', source: 'Ch 5.1' },
          { text: 'Dynamic power is often the first-order switching estimate: αCV_DD^2f.', source: 'Eq 5.1' },
          { text: 'Lowering V_DD is powerful because the dynamic term depends on voltage squared.', source: 'P ∝ V^2' },
          { text: 'Leakage mitigation often uses higher-V_t devices away from critical paths.', source: 'Ch 5.5: multi-V_t' },
        ],
      },
      problems: [
        {
          id: 'pwr_dyn',
          title: 'Dynamic Power',
          source: 'Numerical calculation',
          question: 'Circuit: C = 50 fF, V_DD = 1.2 V, f = 1 GHz, activity factor α = 0.15. Find P_dynamic.',
          diagramType: 'dynamic_power_calc',
          solution: {
            steps: [
              { text: 'Use P_dyn = α × C × V_DD^2 × f.', source: 'Eq 5.1' },
              { text: 'Substitute: 0.15 × 50e-15 × (1.2)^2 × 1e9.', source: 'Direct substitution' },
              { text: 'The result is 10.8 μW.', source: 'Arithmetic result' },
            ],
          },
        },
        {
          id: 'pwr_vscale',
          title: 'Voltage Scaling',
          source: 'Trade-off calculation',
          question: 'If V_DD is reduced from 1.2 V to 0.9 V, what happens to dynamic power and delay?',
          diagramType: 'voltage_scaling',
          solution: {
            steps: [
              { text: 'Dynamic power scales by (0.9 / 1.2)^2 = 0.5625, so it drops to 56.25% of the original.', source: 'P ∝ V^2' },
              { text: 'Delay increases because the current drive falls as supply voltage approaches threshold voltage.', source: 'Ch 5.3' },
              { text: 'Using the simple model with V_t = 0.4 V gives a delay factor increase from 1.875 to 3.6, nearly doubling the delay.', source: 'Illustrative calculation' },
            ],
          },
        },
        {
          id: 'pwr_leak',
          title: 'Leakage & Multi-Vt',
          source: 'Conceptual explanation',
          question: 'Explain subthreshold leakage and how multi-V_t design helps.',
          diagramType: 'leakage_multivt',
          solution: {
            steps: [
              { text: 'Subthreshold current flows even when the transistor is nominally off, and it depends exponentially on threshold voltage.', source: 'Ch 5.4' },
              { text: 'Raising V_t reduces leakage but also slows switching.', source: 'Ch 5.4.1' },
              { text: 'Multi-V_t design uses low-V_t devices on critical paths and high-V_t devices elsewhere to balance speed and leakage.', source: 'Ch 5.5: multi-V_t' },
            ],
          },
        },
      ],
    },
  ],
};
