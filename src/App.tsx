import { useEffect, useState } from "react";
import type { Stage, Version } from "./types";
import { fetchVersions, useStore } from "./api";
import { Storyboard } from "./storyboard/Storyboard";
import { Final } from "./final/Final";
import { reviewToText } from "./text";

const STATUS: Record<string, string> = { in_review: "in review", changes_requested: "changes requested", approved: "approved" };

export function App() {
  const [wanted, setWanted] = useState<Stage | undefined>(() => (location.hash.slice(1) as Stage) || undefined);
  const [ver, setVer] = useState<number | undefined>(() => +(new URLSearchParams(location.search).get("v") || 0) || undefined);
  const { state, error, saving, update } = useStore(wanted, ver);
  const [versions, setVersions] = useState<Version[]>([]);
  useEffect(() => { fetchVersions().then(setVersions); }, [state?.manifest?.round, state?.gateStage]);
  const pickVersion = (round: number | undefined) => {
    const u = new URL(location.href);
    if (round) u.searchParams.set("v", String(round)); else u.searchParams.delete("v");
    history.replaceState(null, "", u);
    setVer(round);
  };
  const switchTo = (st: Stage) => { history.replaceState(null, "", `#${st}`); setWanted(st); };
  const [copied, setCopied] = useState(false);
  const [help, setHelp] = useState(false);

  useEffect(() => {
    if (state?.manifest) document.title = `${state.manifest.project} · AI Corner`;
  }, [state?.manifest]);

  if (error) return <div className="fatal">Server unreachable: {error}</div>;
  if (!state) return <div className="fatal muted">Loading…</div>;
  if (!state.manifest || state.errors.length) {
    return (
      <div className="fatal">
        <h1>Invalid manifest</h1>
        <p className="mono">{state.root}/review/manifest.json</p>
        <ul>{state.errors.map((e, i) => <li key={i} className="mono">{e}</li>)}</ul>
        <p className="muted">This page reloads by itself as soon as the file is fixed.</p>
      </div>
    );
  }
  const m = state.manifest;
  const r = state.review!;
  const archived = state.archived;
  const edit = archived ? (() => {}) as typeof update : update;   // version archivée : lecture seule
  const current = versions.find((x) => x.current);
  const vname = (x: Version) => `${x.label || `round ${x.round}`}${x.current ? " · actuelle" : ""}`;
  const stageStatus = (st: Stage) => r.stages?.[st]?.status ?? "in_review";
  const stages = state.stages || [m.stage];

  const copy = async () => {
    await navigator.clipboard.writeText(reviewToText(r, m));
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  };

  return (
    <div className={`app${archived ? " is-archived" : ""}`}>
      <header className="top">
        <div className="brand"><span className="logo">AI</span>AI Corner<small>Relecture</small></div>
        <div className="crumbs">
          <b>{m.title || m.project}</b>
          <div className="seg stage-switch" title="Switch between the storyboard and the final video">
            {(["storyboard", "final"] as Stage[]).map((st) => (
              <button key={st} className={m.stage === st ? "on" : ""} disabled={!stages.includes(st)}
                title={stages.includes(st) ? `${STATUS[stageStatus(st)]}${state.gateStage === st ? " · waiting on this review" : ""}` : "Not generated yet"}
                onClick={() => switchTo(st)}>
                <span className={`dot ${stageStatus(st) === "approved" ? "approved" : stageStatus(st) === "changes_requested" ? "changes" : ""}`} />
                {st === "storyboard" ? "Storyboard" : "Final video"}
              </button>
            ))}
          </div>
          {versions.length > 1 ? (
            <select className="version-pick" value={archived || m.round} title="Voir une version précédente"
              onChange={(e) => { const n = +e.target.value; const v = versions.find((x) => x.round === n);
                if (v?.current) pickVersion(undefined);
                else if (v && v.stage !== m.stage && v.round === Math.max(...versions.filter((x) => x.stage === v.stage).map((x) => x.round))) { pickVersion(undefined); switchTo(v.stage); }
                else pickVersion(n); }}>
              {versions.map((x) => <option key={x.round} value={x.round}>{vname(x)}</option>)}
            </select>
          ) : null}
          <span className="muted">round {m.round} · {m.canvas.w}×{m.canvas.h}{m.canvas.fps ? ` · ${m.canvas.fps} fps` : ""}</span>
        </div>
        <div className="top-right">
          <span className={`status-chip ${stageStatus(m.stage)}`}>{STATUS[stageStatus(m.stage)]}</span>
          <span className={`save ${saving}`}>{saving === "saving" ? "saving…" : saving === "error" ? "⚠︎ save failed" : "saved"}</span>
          <button className="ghost small" onClick={copy}>{copied ? "Copied ✓" : "Copy as text"}</button>
          <button className="ghost small" onClick={() => setHelp((h) => !h)}>?</button>
        </div>
      </header>
      {archived ? (
        <div className="archived-banner">
          Version archivée : {vname(versions.find((x) => x.round === archived) || { round: archived, stage: m.stage })}, en lecture seule.
          <button className="ghost small" onClick={() => pickVersion(undefined)}>Revenir à la version actuelle</button>
        </div>
      ) : null}
      {m.notes && <div className="notes">{m.notes}</div>}
      {help && <Help stage={m.stage} onClose={() => setHelp(false)} />}
      {m.stage === "storyboard"
        ? <Storyboard key={`sb-${m.round}-${archived || 0}`} m={m} review={r} update={edit} />
        : <Final key={`fi-${m.round}-${m.media?.video}-${archived || 0}`} m={m} review={r} update={edit} />}
    </div>
  );
}

function Help({ stage, onClose }: { stage: string; onClose: () => void }) {
  return (
    <div className="help" onClick={onClose}>
      <div className="help-card" onClick={(e) => e.stopPropagation()}>
        <h3>Shortcuts</h3>
        {stage === "storyboard" ? (
          <ul>
            <li><kbd>←</kbd>/<kbd>→</kbd> previous / next panel</li>
            <li><kbd>A</kbd> approve and go to the next · <kbd>X</kbd> needs changes</li>
            <li>Click in an image: comment pinned to that point · <kbd>C</kbd> general comment</li>
            <li><kbd>G</kbd> grid view · <kbd>Esc</kbd> cancel</li>
          </ul>
        ) : (
          <ul>
            <li><kbd>Space</kbd> play/pause · <kbd>L</kbd> play, then 1× → 1.5× → 2× · <kbd>K</kbd> pause · <kbd>J</kbd> −2 s</li>
            <li><kbd>,</kbd>/<kbd>.</kbd> or <kbd>←</kbd>/<kbd>→</kbd> frame by frame · <kbd>Shift</kbd> = 1 s</li>
            <li>Click in the video: selects the exact element and opens a comment · <kbd>Alt</kbd>+click next element under the cursor</li>
            <li>Click a timeline block: select it and move the playhead to its start · drag on the ruler: range</li>
            <li><kbd>C</kbd> comment the selection · <kbd>[</kbd>/<kbd>]</kbd> previous / next comment · <kbd>Esc</kbd></li>
          </ul>
        )}
        <p className="muted">Comments are saved to <span className="mono">review/review.json</span>. Then tell Claude "apply the review".</p>
      </div>
    </div>
  );
}
