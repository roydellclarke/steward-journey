import { execFile } from "node:child_process";
import { Readable } from "node:stream";
import { appendAnalysis } from "../store";

const repoRoot = process.cwd();
const pythonBin = process.env.HARNESS_PYTHON || "python3";
const analyzerTimeoutMs = Number(process.env.STEWARDPATH_ANALYZER_TIMEOUT_MS || 150000);

function toSnakeProfile(profile) {
  return {
    business_name: profile.businessName || "",
    industry: profile.industry || "",
    years_operating: Number(profile.yearsOperating || 0),
    employees: Number(profile.employees || 0),
    revenue_range: profile.revenueRange || "",
    profit_margin: profile.profitMargin || "",
    owner_dependency: profile.ownerDependency || "",
    timeline: profile.timeline || "",
    owner_goal: profile.ownerGoal || "",
    fears: profile.fears || "",
    non_negotiables: profile.nonNegotiables || "",
    family_context: profile.familyContext || "",
    next_owner_traits: profile.nextOwnerTraits || ""
  };
}

export async function POST(request) {
  try {
    const body = await request.json();
    const profile = toSnakeProfile(body.profile || {});
    const script = `
import json
import sys
from mvp.stewardpath.backend.llm_reasoning import analyze_owner_profile_with_optional_llm
from mvp.stewardpath.backend.reasoning import OwnerProfile

payload = json.load(sys.stdin)
profile = OwnerProfile(**payload)
print(json.dumps(analyze_owner_profile_with_optional_llm(profile)))
`;
    const child = execFile(pythonBin, ["-c", script], {
      cwd: repoRoot,
      env: {
        ...process.env,
        PYTHONPATH: repoRoot
      },
      timeout: analyzerTimeoutMs,
      maxBuffer: 1024 * 1024 * 4
    });
    Readable.from([JSON.stringify(profile)]).pipe(child.stdin);
    const { stdout, stderr } = await new Promise((resolve, reject) => {
      let stdout = "";
      let stderr = "";
      child.stdout.on("data", (chunk) => {
        stdout += chunk.toString();
      });
      child.stderr.on("data", (chunk) => {
        stderr += chunk.toString();
      });
      child.on("error", reject);
      child.on("close", (code) => {
        if (code === 0) {
          resolve({ stdout, stderr });
        } else {
          const reason = child.killed ? ` after ${analyzerTimeoutMs}ms timeout` : "";
          const error = new Error(`Python analyzer exited with code ${code}${reason}`);
          error.stdout = stdout;
          error.stderr = stderr;
          reject(error);
        }
      });
    });
    const analysis = JSON.parse(stdout);
    let savedAnalysis = null;
    if (body.projectId) {
      savedAnalysis = await appendAnalysis(body.projectId, {
        profileSnapshot: body.profile || {},
        intakeSnapshot: body.intakeState || null,
        analysis
      });
    }
    return Response.json({ analysis, savedAnalysis, stderr });
  } catch (error) {
    return Response.json(
      { error: error.message, output: error.stdout || "", stderr: error.stderr || "" },
      { status: 500 }
    );
  }
}
