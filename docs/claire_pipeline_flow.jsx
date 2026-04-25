import { useState } from "react";

const NAVY = "#1E3A5F";
const GOLD = "#C5A030";
const LIGHT = "#F4F1EA";
const MID = "#D6CFC0";
const GREEN = "#2D6A4F";
const RED = "#7B2D2D";
const AMBER = "#8B6914";

const phases = [
  {
    id: "automated",
    label: "AUTOMATED",
    color: NAVY,
    textColor: LIGHT,
    steps: [
      {
        id: "ingest",
        label: "Ingestion",
        sub: "PRAW pulls 6 subreddits\nhot(100) + top(week,50)\nSunday night, Task Scheduler",
        type: "process",
      },
      {
        id: "triage",
        label: "Triage",
        sub: "Haiku classifies 20 posts/call\nsignal_type · persona · source\ndrop_flag applied",
        type: "process",
      },
      {
        id: "gate",
        label: "Cross-Reference Gate",
        sub: "Developer persona → dropped\nFriction log match → HIGH\nNo match → MEDIUM\nContradict → LOW → archive",
        type: "decision",
      },
      {
        id: "synthesis",
        label: "Synthesis",
        sub: "Sonnet · 3 separate calls\nTrack A: memory + profile diffs\nTrack B: skill drafts\nTrack C: workflow techniques",
        type: "process",
      },
      {
        id: "digest",
        label: "Weekly Digest",
        sub: "Waterton .docx\n+ SKILL.md skeletons\n+ memory edit commands",
        type: "output",
      },
    ],
  },
  {
    id: "review",
    label: "WEEKLY REVIEW",
    color: GOLD,
    textColor: NAVY,
    steps: [
      {
        id: "open",
        label: "Open Digest",
        sub: "~15 min\nScan signal summary first\nUnderstand what Reddit was\ntalking about this week",
        type: "process",
      },
      {
        id: "evaluate",
        label: "Evaluate Each Candidate",
        sub: "HIGH confidence first\nDoes this match something\nyou've actually experienced?\nCheck source_posts links",
        type: "decision",
      },
    ],
  },
];

const decisions = [
  {
    id: "accept",
    label: "ACCEPT",
    color: GREEN,
    desc: "Pattern recognized\nfrom personal experience.\nHypothesis comes easily.",
    next: "Write hypothesis → Apply → Log",
  },
  {
    id: "defer",
    label: "DEFER",
    color: AMBER,
    desc: "Plausible but no\npersonal corroboration yet.\nMove to watch list.",
    next: "Archive for next cycle",
  },
  {
    id: "reject",
    label: "REJECT",
    color: RED,
    desc: "Doesn't match experience.\nConfig already handles it.\nSource signal was weak.",
    next: "Discard",
  },
];

const applySteps = [
  {
    id: "hypothesis",
    label: "Write Hypothesis",
    detail:
      'One sentence.\n"I expect [behavior] to change\nin [context], observable when [X]."\n\nIf you cannot write this,\ndo not apply the change.',
    critical: true,
  },
  {
    id: "apply",
    label: "Apply Change",
    detail:
      "Memory edit: paste command\ninto Claude memory system.\n\nSkill: install via skill workflow.\n\nProfile: edit directly.",
    critical: false,
  },
  {
    id: "log",
    label: "Log to change_log.json",
    detail:
      "date · type · summary\nsource_signal permalink\nhypothesis text\neval_notes: [] (empty for now)",
    critical: false,
  },
];

const evalSteps = [
  {
    id: "session",
    label: "Session Eval Note",
    timing: "Async — when relevant",
    detail:
      "After any session where the\nchanged behavior was exercised:\nDATE | CONTEXT | held/partial/no",
  },
  {
    id: "quarterly",
    label: "Quarterly Synthesis",
    timing: "Every 3 months — 30 min",
    detail:
      "Feed change_log.json +\nfriction_log.txt to Claude.\nRequest eval report.\nRevert what didn't hold.\nFlag weak source signal.",
  },
];

function Box({ label, sub, type, dimmed }) {
  const bg =
    type === "decision"
      ? "#2A1F6B"
      : type === "output"
      ? "#0F3320"
      : NAVY;
  const border =
    type === "decision"
      ? GOLD
      : type === "output"
      ? "#4CAF80"
      : "#3A5A7F";

  return (
    <div
      style={{
        background: dimmed ? "#1a1a2e" : bg,
        border: `1.5px solid ${dimmed ? "#333" : border}`,
        borderRadius: 8,
        padding: "10px 14px",
        opacity: dimmed ? 0.4 : 1,
        transition: "all 0.2s",
        minWidth: 180,
        maxWidth: 220,
      }}
    >
      <div
        style={{
          color: type === "output" ? "#4CAF80" : GOLD,
          fontFamily: "Georgia, serif",
          fontSize: 13,
          fontWeight: 700,
          letterSpacing: "0.04em",
          marginBottom: 5,
        }}
      >
        {label}
      </div>
      <div
        style={{
          color: "#A8B8C8",
          fontSize: 11,
          lineHeight: 1.55,
          whiteSpace: "pre-line",
          fontFamily: "monospace",
        }}
      >
        {sub}
      </div>
    </div>
  );
}

function Arrow({ label, color = "#4A6A8A", vertical = true }) {
  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        gap: 2,
        margin: vertical ? "6px 0" : "0 6px",
      }}
    >
      {label && (
        <span
          style={{
            fontSize: 10,
            color: color,
            fontFamily: "monospace",
            letterSpacing: "0.05em",
          }}
        >
          {label}
        </span>
      )}
      <div
        style={{
          width: vertical ? 2 : 24,
          height: vertical ? 20 : 2,
          background: color,
        }}
      />
      <div
        style={{
          width: 0,
          height: 0,
          borderLeft: vertical ? "5px solid transparent" : "none",
          borderRight: vertical ? "5px solid transparent" : "none",
          borderTop: vertical ? `7px solid ${color}` : "none",
          borderBottom: vertical ? "none" : `5px solid transparent`,
          borderTopRep: vertical ? "none" : `5px solid transparent`,
        }}
      />
    </div>
  );
}

function DecisionCard({ d, selected, onSelect }) {
  const isSelected = selected === d.id;
  return (
    <div
      onClick={() => onSelect(isSelected ? null : d.id)}
      style={{
        background: isSelected ? d.color + "22" : "#12121F",
        border: `2px solid ${isSelected ? d.color : "#2A2A3A"}`,
        borderRadius: 10,
        padding: "12px 16px",
        cursor: "pointer",
        transition: "all 0.2s",
        minWidth: 160,
        flex: 1,
      }}
    >
      <div
        style={{
          color: d.color,
          fontFamily: "Georgia, serif",
          fontWeight: 700,
          fontSize: 14,
          letterSpacing: "0.08em",
          marginBottom: 6,
        }}
      >
        {d.label}
      </div>
      <div
        style={{
          color: "#A8B8C8",
          fontSize: 11,
          lineHeight: 1.55,
          whiteSpace: "pre-line",
          fontFamily: "monospace",
        }}
      >
        {d.desc}
      </div>
      {isSelected && (
        <div
          style={{
            marginTop: 8,
            paddingTop: 8,
            borderTop: `1px solid ${d.color}44`,
            color: d.color,
            fontSize: 11,
            fontFamily: "monospace",
          }}
        >
          → {d.next}
        </div>
      )}
    </div>
  );
}

function ApplyStep({ step, active }) {
  return (
    <div
      style={{
        background: active ? (step.critical ? "#2D1A0A" : "#0A1A0F") : "#0D0D1A",
        border: `1.5px solid ${
          active
            ? step.critical
              ? GOLD
              : "#2D6A4F"
            : "#1A1A2A"
        }`,
        borderRadius: 8,
        padding: "10px 14px",
        opacity: active ? 1 : 0.3,
        transition: "all 0.3s",
        flex: 1,
        minWidth: 160,
      }}
    >
      <div
        style={{
          color: step.critical ? GOLD : "#4CAF80",
          fontFamily: "Georgia, serif",
          fontWeight: 700,
          fontSize: 12,
          marginBottom: 5,
          display: "flex",
          alignItems: "center",
          gap: 6,
        }}
      >
        {step.critical && (
          <span style={{ fontSize: 14 }}>⚑</span>
        )}
        {step.label}
      </div>
      <div
        style={{
          color: "#8A9AB0",
          fontSize: 11,
          lineHeight: 1.6,
          whiteSpace: "pre-line",
          fontFamily: "monospace",
        }}
      >
        {step.detail}
      </div>
    </div>
  );
}

export default function CLAIREFlow() {
  const [selectedDecision, setSelectedDecision] = useState(null);
  const [activeSection, setActiveSection] = useState("all");

  const showApply = selectedDecision === "accept";

  const sections = ["all", "automated", "review", "apply", "eval"];

  return (
    <div
      style={{
        background: "#08080F",
        minHeight: "100vh",
        padding: "32px 24px",
        fontFamily: "system-ui, sans-serif",
        color: LIGHT,
      }}
    >
      {/* Header */}
      <div style={{ textAlign: "center", marginBottom: 36 }}>
        <div
          style={{
            fontFamily: "Georgia, serif",
            fontSize: 28,
            fontWeight: 700,
            color: GOLD,
            letterSpacing: "0.12em",
          }}
        >
          CLAIRE
        </div>
        <div
          style={{
            color: "#5A7A9A",
            fontSize: 12,
            letterSpacing: "0.2em",
            marginTop: 4,
            fontFamily: "monospace",
          }}
        >
          DECISION PIPELINE — REDDIT SIGNAL TO LOCAL CHANGE
        </div>
        <div
          style={{
            display: "flex",
            justifyContent: "center",
            gap: 8,
            marginTop: 16,
            flexWrap: "wrap",
          }}
        >
          {sections.map((s) => (
            <button
              key={s}
              onClick={() => setActiveSection(s)}
              style={{
                background: activeSection === s ? NAVY : "transparent",
                border: `1px solid ${activeSection === s ? GOLD : "#2A2A3A"}`,
                color: activeSection === s ? GOLD : "#5A7A9A",
                padding: "4px 12px",
                borderRadius: 4,
                cursor: "pointer",
                fontSize: 11,
                fontFamily: "monospace",
                letterSpacing: "0.08em",
              }}
            >
              {s.toUpperCase()}
            </button>
          ))}
        </div>
      </div>

      {/* PHASE 1: AUTOMATED */}
      {(activeSection === "all" || activeSection === "automated") && (
        <div style={{ marginBottom: 32 }}>
          <div
            style={{
              color: "#3A5A7F",
              fontSize: 10,
              letterSpacing: "0.25em",
              fontFamily: "monospace",
              marginBottom: 12,
              paddingLeft: 4,
            }}
          >
            ── PHASE 1: AUTOMATED ─────────────────────────────
          </div>
          <div
            style={{
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              gap: 0,
            }}
          >
            {phases[0].steps.map((step, i) => (
              <div
                key={step.id}
                style={{
                  display: "flex",
                  flexDirection: "column",
                  alignItems: "center",
                }}
              >
                <Box
                  label={step.label}
                  sub={step.sub}
                  type={step.type}
                  dimmed={false}
                />
                {i < phases[0].steps.length - 1 && (
                  <Arrow
                    label={
                      i === 2
                        ? "HIGH + MEDIUM only"
                        : i === 3
                        ? "generates candidates"
                        : undefined
                    }
                    color={i === 2 ? GREEN : "#3A5A7F"}
                  />
                )}
              </div>
            ))}
          </div>
          <div
            style={{
              textAlign: "center",
              marginTop: 6,
              color: "#3A5A7F",
              fontSize: 10,
              fontFamily: "monospace",
            }}
          >
            lands in output/ folder
          </div>
        </div>
      )}

      {/* PHASE 2: WEEKLY REVIEW */}
      {(activeSection === "all" || activeSection === "review") && (
        <div style={{ marginBottom: 32 }}>
          <div
            style={{
              color: "#8B6914",
              fontSize: 10,
              letterSpacing: "0.25em",
              fontFamily: "monospace",
              marginBottom: 12,
              paddingLeft: 4,
            }}
          >
            ── PHASE 2: WEEKLY REVIEW (human) ─────────────────
          </div>

          <div
            style={{
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              gap: 0,
            }}
          >
            <Box
              label="Open Digest"
              sub={"~15 min\nScan signal summary first\nUnderstand Reddit context\nbefore reading candidates"}
              type="process"
            />
            <Arrow color={GOLD} />
            <Box
              label="Evaluate Each Candidate"
              sub={"HIGH confidence first\nRecognize from personal experience?\nCheck source_post links\nDoes the pattern match?"}
              type="decision"
            />
          </div>

          {/* Decision branches */}
          <div
            style={{
              marginTop: 20,
              marginBottom: 8,
              color: "#5A7A9A",
              fontSize: 10,
              fontFamily: "monospace",
              letterSpacing: "0.15em",
              textAlign: "center",
            }}
          >
            FOR EACH CANDIDATE — SELECT ONE:
          </div>
          <div
            style={{
              display: "flex",
              gap: 10,
              justifyContent: "center",
              flexWrap: "wrap",
            }}
          >
            {decisions.map((d) => (
              <DecisionCard
                key={d.id}
                d={d}
                selected={selectedDecision}
                onSelect={setSelectedDecision}
              />
            ))}
          </div>
          {!selectedDecision && (
            <div
              style={{
                textAlign: "center",
                marginTop: 10,
                color: "#3A3A5A",
                fontSize: 10,
                fontFamily: "monospace",
              }}
            >
              tap a decision to expand
            </div>
          )}
        </div>
      )}

      {/* PHASE 3: APPLY (only shown when ACCEPT selected) */}
      {(activeSection === "all" || activeSection === "apply") && (
        <div style={{ marginBottom: 32, opacity: showApply || activeSection === "apply" ? 1 : 0.25, transition: "opacity 0.3s" }}>
          <div
            style={{
              color: GREEN,
              fontSize: 10,
              letterSpacing: "0.25em",
              fontFamily: "monospace",
              marginBottom: 12,
              paddingLeft: 4,
            }}
          >
            ── PHASE 3: APPLY ACCEPTED CANDIDATE (human) ───────
          </div>
          {activeSection === "all" && !showApply && (
            <div style={{ color: "#3A3A5A", fontSize: 11, fontFamily: "monospace", textAlign: "center", marginBottom: 12 }}>
              ← select ACCEPT above to activate
            </div>
          )}
          <div
            style={{
              display: "flex",
              gap: 10,
              justifyContent: "center",
              flexWrap: "wrap",
            }}
          >
            {applySteps.map((step, i) => (
              <div
                key={step.id}
                style={{ display: "flex", alignItems: "center", gap: 10 }}
              >
                <ApplyStep step={step} active={showApply || activeSection === "apply"} />
                {i < applySteps.length - 1 && (
                  <div
                    style={{
                      color: GREEN,
                      fontSize: 18,
                      opacity: showApply || activeSection === "apply" ? 1 : 0.2,
                    }}
                  >
                    →
                  </div>
                )}
              </div>
            ))}
          </div>
          <div
            style={{
              marginTop: 14,
              padding: "10px 16px",
              background: "#1A0A00",
              border: `1px solid ${GOLD}44`,
              borderRadius: 8,
              color: "#8A7A5A",
              fontSize: 11,
              fontFamily: "monospace",
              lineHeight: 1.6,
              opacity: showApply || activeSection === "apply" ? 1 : 0.2,
            }}
          >
            ⚑ CRITICAL GATE: If you cannot write a hypothesis in one sentence, do not apply the change.
            The candidate goes back to DEFER. The inability to hypothesize is diagnostic — it means
            the candidate isn't specific enough to be testable, which means it isn't specific enough
            to be useful.
          </div>
        </div>
      )}

      {/* PHASE 4: EVAL LOOP */}
      {(activeSection === "all" || activeSection === "eval") && (
        <div style={{ marginBottom: 16 }}>
          <div
            style={{
              color: "#5A3A7F",
              fontSize: 10,
              letterSpacing: "0.25em",
              fontFamily: "monospace",
              marginBottom: 12,
              paddingLeft: 4,
            }}
          >
            ── PHASE 4: EVAL LOOP (async + quarterly) ──────────
          </div>
          <div
            style={{
              display: "flex",
              gap: 12,
              justifyContent: "center",
              flexWrap: "wrap",
            }}
          >
            {evalSteps.map((step) => (
              <div
                key={step.id}
                style={{
                  background: "#0F0A1A",
                  border: "1.5px solid #2A1A4A",
                  borderRadius: 8,
                  padding: "12px 16px",
                  flex: 1,
                  minWidth: 200,
                  maxWidth: 280,
                }}
              >
                <div
                  style={{
                    color: "#8A5ACF",
                    fontFamily: "Georgia, serif",
                    fontWeight: 700,
                    fontSize: 13,
                    marginBottom: 4,
                  }}
                >
                  {step.label}
                </div>
                <div
                  style={{
                    color: "#5A4A7A",
                    fontSize: 10,
                    fontFamily: "monospace",
                    marginBottom: 6,
                    letterSpacing: "0.08em",
                  }}
                >
                  {step.timing}
                </div>
                <div
                  style={{
                    color: "#7A8A9A",
                    fontSize: 11,
                    fontFamily: "monospace",
                    lineHeight: 1.6,
                    whiteSpace: "pre-line",
                  }}
                >
                  {step.detail}
                </div>
              </div>
            ))}
          </div>

          {/* Quarterly outcomes */}
          <div
            style={{
              marginTop: 14,
              display: "flex",
              gap: 8,
              justifyContent: "center",
              flexWrap: "wrap",
            }}
          >
            {[
              { label: "HELD", color: GREEN, action: "Keep. No action." },
              { label: "PARTIAL", color: AMBER, action: "Refine or re-scope." },
              { label: "DIDN'T HOLD", color: RED, action: "Revert + flag source signal as low-quality." },
            ].map((o) => (
              <div
                key={o.label}
                style={{
                  background: o.color + "11",
                  border: `1px solid ${o.color}44`,
                  borderRadius: 6,
                  padding: "7px 14px",
                  display: "flex",
                  gap: 10,
                  alignItems: "center",
                }}
              >
                <span
                  style={{
                    color: o.color,
                    fontFamily: "monospace",
                    fontSize: 11,
                    fontWeight: 700,
                    letterSpacing: "0.1em",
                  }}
                >
                  {o.label}
                </span>
                <span
                  style={{
                    color: "#6A7A8A",
                    fontSize: 11,
                    fontFamily: "monospace",
                  }}
                >
                  {o.action}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Footer */}
      <div
        style={{
          marginTop: 32,
          borderTop: "1px solid #1A1A2A",
          paddingTop: 16,
          display: "flex",
          justifyContent: "space-between",
          flexWrap: "wrap",
          gap: 8,
        }}
      >
        {[
          ["AUTOMATED", "Sunday night, weekly"],
          ["REVIEW", "~15 min, Monday morning"],
          ["APPLY", "2 min per accepted candidate"],
          ["EVAL", "Async notes + quarterly 30 min"],
        ].map(([phase, time]) => (
          <div
            key={phase}
            style={{ fontSize: 10, fontFamily: "monospace", color: "#3A4A5A" }}
          >
            <span style={{ color: "#5A6A7A" }}>{phase}</span> — {time}
          </div>
        ))}
      </div>
    </div>
  );
}
