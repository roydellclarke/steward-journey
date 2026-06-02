import { execFile } from "node:child_process";
import { mkdtemp, writeFile } from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import { promisify } from "node:util";

const execFileAsync = promisify(execFile);
const repoRoot = process.cwd();
const workspaceRoot = path.join(repoRoot, "workspace");
const pythonBin = process.env.HARNESS_PYTHON || "python3";

function harnessEnv() {
  return {
    ...process.env,
    HARNESS_WORKSPACE: workspaceRoot,
    HARNESS_USE_LLM: process.env.HARNESS_USE_LLM || "false",
    PYTHONPATH: repoRoot,
    APP_BASE_URL: process.env.APP_BASE_URL || "http://localhost:3000"
  };
}

async function runHarness(args) {
  const { stdout, stderr } = await execFileAsync(pythonBin, ["-m", "harness.main", ...args], {
    cwd: repoRoot,
    env: harnessEnv(),
    timeout: 120000,
    maxBuffer: 1024 * 1024 * 8
  });
  return [stdout, stderr].filter(Boolean).join("\n");
}

export async function POST(request) {
  try {
    const body = await request.json();
    const action = body.action;

    if (action === "init") {
      const output = await runHarness(["init"]);
      return Response.json({ output });
    }

    if (action === "run") {
      const goals = String(body.goals || "").trim();
      if (!goals) {
        return Response.json({ error: "Goals are required." }, { status: 400 });
      }
      const tmp = await mkdtemp(path.join(os.tmpdir(), "agent-harness-goals-"));
      const goalsPath = path.join(tmp, "goals.md");
      await writeFile(goalsPath, goals, "utf8");
      const output = await runHarness(["run", "--goals", goalsPath]);
      return Response.json({ output });
    }

    if (action === "resume") {
      const output = await runHarness(["resume"]);
      return Response.json({ output });
    }

    if (action === "abort") {
      const output = await runHarness(["abort", "--reason", "aborted from UI"]);
      return Response.json({ output });
    }

    if (action === "doctor") {
      const output = await runHarness(["doctor"]);
      return Response.json({ output });
    }

    if (action === "jobs") {
      const output = await runHarness(["jobs"]);
      return Response.json({ output, jobs: JSON.parse(output || "[]") });
    }

    if (action === "job-create") {
      const payload = {
        goal: String(body.goals || "").trim()
      };
      const args = [
        "job-create",
        "--name",
        String(body.name || "Scheduled harness goal"),
        "--kind",
        body.schedule ? "scheduled_goal" : "harness_goal",
        "--payload-json",
        JSON.stringify(payload)
      ];
      if (body.schedule) {
        args.push("--schedule", String(body.schedule));
      }
      const output = await runHarness(args);
      return Response.json({ output, job: JSON.parse(output) });
    }

    if (action === "job-run") {
      const jobId = String(body.jobId || "");
      if (!jobId) {
        return Response.json({ error: "jobId is required." }, { status: 400 });
      }
      const output = await runHarness(["job-run", "--job-id", jobId]);
      return Response.json({ output });
    }

    if (action === "job-approve") {
      const jobId = String(body.jobId || "");
      if (!jobId) {
        return Response.json({ error: "jobId is required." }, { status: 400 });
      }
      const output = await runHarness(["job-approve", "--job-id", jobId]);
      return Response.json({ output, job: JSON.parse(output) });
    }

    if (action === "scheduler-status") {
      const output = await runHarness(["scheduler-status"]);
      return Response.json({ output, scheduler: JSON.parse(output) });
    }

    if (action === "connectors") {
      const output = await runHarness(["connectors"]);
      return Response.json({ output, connectors: JSON.parse(output || "[]") });
    }

    if (action === "connector-add-meta") {
      const pageId = String(body.pageId || "").trim();
      if (!pageId) {
        return Response.json({ error: "pageId is required." }, { status: 400 });
      }
      const output = await runHarness([
        "connector-add-meta",
        "--name",
        String(body.name || "Meta Pages"),
        "--page-id",
        pageId,
        "--token-env-var",
        String(body.tokenEnvVar || "META_PAGE_ACCESS_TOKEN")
      ]);
      return Response.json({ output, connector: JSON.parse(output) });
    }

    return Response.json({ error: `Unsupported action: ${action}` }, { status: 400 });
  } catch (error) {
    return Response.json(
      { error: error.message, output: error.stdout || "", stderr: error.stderr || "" },
      { status: 500 }
    );
  }
}
