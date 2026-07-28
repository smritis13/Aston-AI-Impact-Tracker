export interface RefPromptStarter {
  id: string;
  label: string;
  prompt: string;
}

// Standard REF requirements - non-Aston sourcing, quotes, publication dates,
// underpinning-research/impact separation, Aston-vs-individual attribution
// (including automatic affiliation discovery), REF-eligible date windows,
// numeric reference ordering, and draft/commentary separation - are all
// enforced automatically by the backend prompts and pipeline for every
// search and every report, regardless of what's typed here. They used to be
// repeated in full in every starter below; that's no longer necessary, so
// starters now only carry what's genuinely specific to each case: who the
// academic is, what their work is about, and good starting search angles.
const STANDARD_REQUIREMENTS_NOTE =
  "(Standard REF evidence requirements - non-Aston sourcing, quotes, dates, research/impact separation, automatic Aston-affiliation discovery - are applied automatically; no need to restate them here.)";

const buildRefPrompt = ({
  title,
  academics,
  focus,
  evidenceTargets,
  searchSeeds,
}: {
  title: string;
  academics: string;
  focus: string;
  evidenceTargets: string[];
  searchSeeds: string[];
}) => `Build REF-ready impact evidence for: ${title}

Named Aston academics / groups:
${academics}

Impact focus:
${focus}

${STANDARD_REQUIREMENTS_NOTE}

Evidence to look for:
${evidenceTargets.map((item) => `- ${item}`).join("\n")}

High-yield search angles:
${searchSeeds.map((item) => `- ${item}`).join("\n")}`;

const buildRefReportPrompt = ({
  title,
  academics,
  focus,
  reportPriorities,
}: {
  title: string;
  academics: string;
  focus: string;
  reportPriorities: string[];
}) => `Generate a REF-style impact case study report for: ${title}

Named Aston academics / groups:
${academics}

Report focus:
${focus}

${STANDARD_REQUIREMENTS_NOTE}

Pay particular attention to:
${reportPriorities.map((item) => `- ${item}`).join("\n")}`;

export const REF_PROMPT_STARTERS: RefPromptStarter[] = [
  {
    id: "custom-professor-template",
    label: "Template: fill in a new professor's details",
    prompt: buildRefPrompt({
      title: "[Impact area or project name]",
      academics: "[Professor/Dr Name], [Department, Institute, or research group]",
      focus:
        "[Describe their research area, key methods or technology, and the real-world impact domain - e.g. policy influence, industry adoption, clinical practice, public engagement.]",
      evidenceTargets: [
        "[Named funders, grants, or projects specific to their work]",
        "[Named partner organisations, companies, or agencies who adopted/used their research]",
        "[Specific outcomes, deployments, or beneficiaries to look for]",
        "[Anything else distinctive to this case - a spin-out, a KTP, a policy body, an award]",
      ],
      searchSeeds: [
        '"[Professor Name]" Aston [research area] impact',
        '"[Professor Name]" Aston [specific project or technology] deployment',
        '"[Named partner or funder]" Aston "[Professor Name]" collaboration',
      ],
    }),
  },
  {
    id: "industrial-decarbonisation-alaswad",
    label: "Industrial decarbonisation: Alaswad / CIRCARB / campus",
    prompt: buildRefPrompt({
      title: "Decarbonisation of energy-intensive industries at Aston",
      academics: "Abed Alaswad, EBRI, CIRCARB-related Aston energy systems researchers",
      focus:
        "Industrial carbon substitution, hydrogen/fuel cells, bioenergy, waste heat recovery, campus decarbonisation as a living lab, and possible links to Grid Edge energy optimisation.",
      evidenceTargets: [
        "EPSRC, Innovate UK, DESNZ, KTP or industry-funded projects linked to decarbonisation, hydrogen, bioenergy, circular carbon or industrial energy systems",
        "industrial partners in chemicals, plastics, construction, manufacturing, steel or cement",
        "documented deployments, pilots, TRL progression, demonstrations, policy influence, emissions reductions or cost savings",
        "evidence distinguishing campus demonstrator impact from external industrial uptake",
      ],
      searchSeeds: [
        '"Aston University" CIRCARB decarbonisation chemicals plastics construction EPSRC industry partners',
        '"Abed Alaswad" industrial decarbonisation hydrogen fuel cell Innovate UK impact',
        '"Aston University" campus decarbonisation living lab industry energy systems heat pumps',
        '"Grid Edge" Aston energy optimisation carbon reduction building deployment',
      ],
    }),
  },
  {
    id: "hybrid-energy-imran",
    label: "Hybrid energy systems: Muhammad Imran",
    prompt: buildRefPrompt({
      title: "Hybrid energy systems for industrial decarbonisation",
      academics: "Muhammad Imran, EBRI, Aston energy systems cluster",
      focus:
        "Hybrid multi-energy systems, waste heat recovery, ORC, heating/cooling, renewable integration, industrial energy resilience and demonstrators.",
      evidenceTargets: [
        "WHR-FIND, ORC, industrial waste heat recovery, heat pump, cooling, hybrid renewable and demonstrator projects",
        "industry partners, test sites, pilot deployments, TRL changes and scale-up activity",
        "energy savings, carbon savings, cost savings, resilience benefits or avoided fuel use",
        "links between modelling / techno-economic work and real-world demonstrator outcomes",
      ],
      searchSeeds: [
        '"Muhammad Imran" Aston hybrid energy systems ORC waste heat industry project impact',
        '"Aston University" "Waste Heat Recovery" foundation industries ORC Imran',
        '"hybrid energy systems" industrial decarbonisation UK university impact case study',
        '"organic Rankine cycle" industry UK deployment energy savings case study',
      ],
    }),
  },
  {
    id: "bioenergy-policy-thornley",
    label: "Bioenergy policy: Patricia Thornley",
    prompt: buildRefPrompt({
      title: "Bioenergy policy and low-carbon fuels policy influence",
      academics: "Patricia Thornley, Supergen Bioenergy Hub, EBRI",
      focus:
        "National bioenergy policy, low-carbon fuels, LCA, biomass sustainability, BECCS, DfT / DESNZ / CCC / Parliament advisory influence.",
      evidenceTargets: [
        "government advisory roles, consultation evidence, policy reports and cited research outputs",
        "direct links from Thornley / Supergen evidence to DfT, DESNZ, CCC, Defra or Parliamentary decisions",
        "policy outcomes, deployment changes, bioheat / bioenergy uptake, carbon budget influence or strategy changes",
        "corroboration sources suitable for letters: DfT, CCC, DESNZ, Supergen partners",
      ],
      searchSeeds: [
        '"Patricia Thornley" bioenergy policy low carbon fuels strategy DfT',
        '"Supergen Bioenergy Hub" policy impact government Thornley',
        '"bioenergy" "Climate Change Committee" Thornley biomass strategy evidence',
        '"Patricia Thornley" Parliament biomass sustainability evidence',
      ],
    }),
  },
  {
    id: "grid-edge",
    label: "Grid Edge: AI building energy optimisation",
    prompt: buildRefPrompt({
      title: "Reducing building carbon emissions through Grid Edge",
      academics: "Jim Scott, EBRI, Aston Grid Edge spin-out founders and collaborators",
      focus:
        "AI-driven building energy optimisation, demand response, commercial deployment, carbon and cost reduction, commercialisation from Aston research.",
      evidenceTargets: [
        "spin-out origin, Aston research contribution, founders, algorithms, demand-response or distributed energy systems work",
        "client deployments, number of buildings/meters, sectors served and national/international reach",
        "carbon savings, energy cost reductions, ROI, revenue growth, investment, jobs or customer case studies",
        "system-level contribution to flexible low-carbon energy infrastructure",
      ],
      searchSeeds: [
        '"Grid Edge" Aston University spinout energy savings buildings AI demand response',
        '"Grid Edge" case study commercial building energy savings HVAC carbon reduction',
        '"Grid Edge" investment revenue growth buildings AI energy platform UK results',
        '"Jim Scott" Aston Grid Edge distributed energy demand response',
      ],
    }),
  },
  {
    id: "endoscope-i",
    label: "Endoscope-i: primary care cancer pathway",
    prompt: buildRefPrompt({
      title: "Transforming cancer diagnosis pathways through Endoscope-i",
      academics: "Mark Prince and Aston-linked Endoscope-i / digital health collaborators",
      focus:
        "Low-cost mobile endoscopy, community or GP pathway redesign, remote specialist review, head and neck cancer triage, NHS pilots.",
      evidenceTargets: [
        "trial or pilot patient numbers, NHS sites, West Midlands / Staffordshire / UHNM deployments and pathway changes",
        "time to diagnosis, cancers missed, cancer detection, discharge rates, referral reductions and clinician workload changes",
        "primary care, nurse-led, community diagnostic or remote consultant review evidence",
        "NHS England, Cancer Alliance, hospital or clinical corroboration sources",
      ],
      searchSeeds: [
        '"Endoscope-i" Mark Prince Aston head neck cancer pathway NHS',
        '"Endoscope-i" hoarse voice pathway Staffordshire GP community diagnosis',
        '"Endoscope-i" 1800 patients cancers missed 23 hours consultant review',
        '"Endoscope-i" NHS innovation programme West Midlands cancer',
      ],
    }),
  },
  {
    id: "rice-straw-roeder",
    label: "Rice straw bioenergy: Mirjam Roeder",
    prompt: buildRefPrompt({
      title: "Transforming rice straw waste into sustainable energy systems",
      academics: "Mirjam Roeder, EBRI, rice straw biogas / RICE project collaborators",
      focus:
        "Rice straw bioenergy, LCA, techno-economic and socio-economic systems, Philippines / India deployment, rural development and emissions reduction.",
      evidenceTargets: [
        "Rice Straw Biogas Hub, RICE project, IRRI, Straw Innovations, Takachar and other partner evidence",
        "emissions avoided, GHG reduction percentages, biomass processed, hubs deployed, countries and farmer reach",
        "farmer income, energy access, community-scale ownership, SDG, air quality and public health benefits",
        "policy or international agency uptake such as FAO, national strategies or agricultural guidance",
      ],
      searchSeeds: [
        '"Mirjam Roeder" rice straw bioenergy Aston impact Philippines India',
        '"Rice Straw Biogas Hub" Aston University farmers emissions',
        '"Aston University" rice straw 300 million tonnes burning bioenergy',
        '"rice straw" biogas "68%" greenhouse gas Aston Roeder',
      ],
    }),
  },
  {
    id: "khamsin",
    label: "Khamsin: automated endoscope cleaning",
    prompt: buildRefPrompt({
      title: "Transforming infection control through Khamsin automated endoscope cleaning",
      academics: "Andy Sutherland, Tony Worthington, Aston KTP with PFE Medical",
      focus:
        "Biofilm removal, antimicrobial materials, automated endoscope cleaning, NHS deployment, patient safety, cost and environmental benefits.",
      evidenceTargets: [
        "KTP evidence, PFE Medical / Partnership Medical collaboration and Aston research contribution",
        "NHS adoption, UHB deployment, procedure volume, cleaning performance, turnaround time and cost savings",
        "microbial reduction, contamination reduction, infection-control outcomes and resistant pathogen evidence",
        "environmental benefits, workforce benefits, awards, media and clinical corroboration",
      ],
      searchSeeds: [
        '"Khamsin" Aston PFE Medical automated endoscope cleaning KTP',
        '"Khamsin" University Hospitals Birmingham 140000 procedures cost savings',
        '"Aston University" endoscope cleaning 1000 times more effective',
        '"Tony Worthington" "Andy Sutherland" endoscope biofilm Khamsin',
      ],
    }),
  },
  {
    id: "photonics-ellis-harper",
    label: "Photonics digital infrastructure: Ellis / Harper / Xtera",
    prompt: buildRefPrompt({
      title: "Enabling high-capacity fibre and submarine networks",
      academics: "Andrew Ellis, Paul Harper, Aston Institute of Photonic Technologies",
      focus:
        "High-capacity optical transmission, passive optical networks, Raman/WDM/coherent systems, industry engagement with BT, Nokia, Huawei, Xtera, Pilot Photonics and related telecoms partners.",
      evidenceTargets: [
        "Aston-period research outputs linked to capacity limits, modulation, PON, amplification or coherent systems",
        "industry collaboration evidence, EPSRC grants, vendor adoption, standards influence or partner statements",
        "capacity increases, cost reductions, efficiency improvements, fibre rollout or subsea upgrade benefits",
        "REF-safe attribution that treats Pilot Photonics / Azea / Xtera as knowledge exchange evidence, not overclaimed Aston spin-outs",
      ],
      searchSeeds: [
        '"Andrew Ellis" Aston optical communications fibre rollout impact',
        '"Paul Harper" Aston Xtera coherent communications Raman amplification',
        '"Aston Institute of Photonic Technologies" BT Nokia Huawei Xtera EPSRC',
        '"Pilot Photonics" Andrew Ellis advisor optical comb telecom networks',
      ],
    }),
  },
  {
    id: "ai-venture-ecosystem",
    label: "AI venture ecosystem: DFB / Greater Things",
    prompt: buildRefPrompt({
      title: "Accelerating inclusive fintech innovation through AI-enabled venture creation",
      academics: "Design Factory Birmingham, Aston digital innovation and enterprise ecosystem partners",
      focus:
        "AI-assisted coding, low/no-code venture creation, fintech startup development, inclusive entrepreneurship and West Midlands economic growth.",
      evidenceTargets: [
        "named startups created via DFB / Greater Things / SuperTech or related programmes",
        "funding raised, revenue, jobs, users, survival rates, products launched or founder outcomes",
        "AI-assisted coding productivity evidence such as time-to-MVP, cost reduction or learner progression",
        "inclusion metrics, underrepresented founders, regional growth, WMCA / SuperTech / partner corroboration",
      ],
      searchSeeds: [
        '"Design Factory Birmingham" "Greater Things" AI startup fintech Aston',
        '"Greater Things" West Midlands startups low code founders',
        '"Aston University" AI assisted coding venture creation fintech',
        '"SuperTech" Aston fintech startup innovation West Midlands',
      ],
    }),
  },
];

export const REF_REPORT_PROMPT_STARTERS: RefPromptStarter[] = [
  {
    id: "custom-professor-template-report",
    label: "Template: fill in a new professor's details",
    prompt: buildRefReportPrompt({
      title: "[Impact area or project name]",
      academics: "[Professor/Dr Name], [Department, Institute, or research group]",
      focus:
        "A REF case study report about [describe the impact domain and the pathway from their research to real-world impact].",
      reportPriorities: [
        "[Any case-specific nuance - e.g. distinguishing a demonstrator from real deployment, or attribution across partner organisations]",
        "[Specific metrics or evidence types most relevant to this case]",
        "[Anything to explicitly flag as a gap if not found]",
      ],
    }),
  },
  {
    id: "industrial-decarbonisation-alaswad-report",
    label: "Industrial decarbonisation: Alaswad / CIRCARB / campus",
    prompt: buildRefReportPrompt({
      title: "Decarbonisation of energy-intensive industries at Aston",
      academics: "Abed Alaswad, EBRI, CIRCARB-related Aston energy systems researchers",
      focus:
        "A REF case study narrative on industrial carbon substitution, hydrogen/fuel cells, bioenergy, waste heat recovery, campus decarbonisation as a living lab, and possible links to Grid Edge energy optimisation.",
      reportPriorities: [
        "separate demonstrator activity from external industrial uptake",
        "show the pathway from Aston research to partner adoption or policy/practice change",
        "identify emissions, cost, TRL, deployment or industry-beneficiary evidence",
        "flag any missing corroboration letters, partner statements or quantified outcomes",
      ],
    }),
  },
  {
    id: "hybrid-energy-imran-report",
    label: "Hybrid energy systems: Muhammad Imran",
    prompt: buildRefReportPrompt({
      title: "Hybrid energy systems for industrial decarbonisation",
      academics: "Muhammad Imran, EBRI, Aston energy systems cluster",
      focus:
        "A REF report about hybrid multi-energy systems, waste heat recovery, ORC, heating/cooling, renewable integration, industrial energy resilience and demonstrators.",
      reportPriorities: [
        "connect modelling and techno-economic research to practical demonstrator outcomes",
        "show industrial beneficiaries, adoption sites and partner roles",
        "use energy, carbon, cost or resilience metrics only where evidenced",
        "state what proof is still needed for reach, significance and attribution",
      ],
    }),
  },
  {
    id: "bioenergy-policy-thornley-report",
    label: "Bioenergy policy: Patricia Thornley",
    prompt: buildRefReportPrompt({
      title: "Bioenergy policy and low-carbon fuels policy influence",
      academics: "Patricia Thornley, Supergen Bioenergy Hub, EBRI",
      focus:
        "A REF case study report about bioenergy policy, low-carbon fuels, LCA, biomass sustainability, BECCS, and advisory influence on DfT / DESNZ / CCC / Parliament.",
      reportPriorities: [
        "distinguish research contribution from general policy background",
        "identify government, committee, consultation or strategy evidence",
        "explain policy reach and significance in REF terms",
        "flag missing policy citations, testimonial evidence or causal attribution",
      ],
    }),
  },
  {
    id: "grid-edge-report",
    label: "Grid Edge: AI building energy optimisation",
    prompt: buildRefReportPrompt({
      title: "Reducing building carbon emissions through Grid Edge",
      academics: "Jim Scott, EBRI, Aston Grid Edge spin-out founders and collaborators",
      focus:
        "A REF-ready report about AI-driven building energy optimisation, demand response, commercial deployment, carbon and cost reduction, and commercialisation from Aston research.",
      reportPriorities: [
        "show the Aston research and commercialisation pathway",
        "identify client deployments, building/meter reach and sectors served",
        "use carbon, energy, cost, revenue, investment or jobs evidence if available",
        "avoid overclaiming where customer case studies or spin-out attribution are incomplete",
      ],
    }),
  },
  {
    id: "endoscope-i-report",
    label: "Endoscope-i: primary care cancer pathway",
    prompt: buildRefReportPrompt({
      title: "Transforming cancer diagnosis pathways through Endoscope-i",
      academics: "Mark Prince and Aston-linked Endoscope-i / digital health collaborators",
      focus:
        "A REF case study report on low-cost mobile endoscopy, community or GP pathway redesign, remote specialist review, head and neck cancer triage, and NHS pilots.",
      reportPriorities: [
        "describe the clinical pathway change and external NHS beneficiaries",
        "use patient numbers, diagnostic times, referral/discharge changes and cancer-detection evidence where available",
        "separate clinical adoption evidence from product claims",
        "identify missing clinical corroboration, NHS statements or patient-outcome evidence",
      ],
    }),
  },
  {
    id: "rice-straw-roeder-report",
    label: "Rice straw bioenergy: Mirjam Roeder",
    prompt: buildRefReportPrompt({
      title: "Transforming rice straw waste into sustainable energy systems",
      academics: "Mirjam Roeder, EBRI, rice straw biogas / RICE project collaborators",
      focus:
        "A REF impact report about rice straw bioenergy, LCA, techno-economic and socio-economic systems, Philippines / India deployment, rural development and emissions reduction.",
      reportPriorities: [
        "show the route from Aston research to partner deployment or international practice change",
        "identify farmer, community, environmental and policy beneficiaries",
        "use emissions, biomass, income, energy-access or geographic reach metrics where evidenced",
        "flag missing field-deployment, partner or policy-corroboration evidence",
      ],
    }),
  },
  {
    id: "khamsin-report",
    label: "Khamsin: automated endoscope cleaning",
    prompt: buildRefReportPrompt({
      title: "Transforming infection control through Khamsin automated endoscope cleaning",
      academics: "Andy Sutherland, Tony Worthington, Aston KTP with PFE Medical",
      focus:
        "A REF case study report about biofilm removal, antimicrobial research, automated endoscope cleaning, NHS deployment, patient safety, cost and environmental benefits.",
      reportPriorities: [
        "show the pathway from Aston research and KTP activity to product/service adoption",
        "identify NHS, patient safety, workforce and commercial beneficiaries",
        "use cleaning efficacy, procedure volume, turnaround, cost or environmental evidence where available",
        "flag missing clinical adoption evidence, infection-control outcomes or independent corroboration",
      ],
    }),
  },
  {
    id: "photonics-ellis-harper-report",
    label: "Photonics digital infrastructure: Ellis / Harper / Xtera",
    prompt: buildRefReportPrompt({
      title: "Enabling high-capacity fibre and submarine networks",
      academics: "Andrew Ellis, Paul Harper, Aston Institute of Photonic Technologies",
      focus:
        "A REF-style report about high-capacity optical transmission, passive optical networks, Raman/WDM/coherent systems, and industry engagement with telecoms partners.",
      reportPriorities: [
        "make attribution REF-safe where partner companies have mixed origins",
        "connect Aston research outputs to industry collaboration, standards, adoption or network upgrades",
        "use capacity, cost, efficiency, rollout or subsea-network evidence only where sourced",
        "identify missing beneficiary statements or partner corroboration",
      ],
    }),
  },
  {
    id: "ai-venture-ecosystem-report",
    label: "AI venture ecosystem: DFB / Greater Things",
    prompt: buildRefReportPrompt({
      title: "Accelerating inclusive fintech innovation through AI-enabled venture creation",
      academics: "Design Factory Birmingham, Aston digital innovation and enterprise ecosystem partners",
      focus:
        "A REF report about AI-assisted coding, low/no-code venture creation, fintech startup development, inclusive entrepreneurship and West Midlands economic growth.",
      reportPriorities: [
        "show the route from Aston methods, facilities or expertise to founder/startup outcomes",
        "identify startups, funding, revenue, jobs, users, products or founder-progression evidence",
        "include inclusion and regional-economic-benefit evidence where available",
        "flag missing cohort data, partner corroboration or long-term sustainability evidence",
      ],
    }),
  },
];
