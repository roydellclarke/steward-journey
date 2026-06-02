import { execFile } from "node:child_process";
import path from "node:path";
import { promisify } from "node:util";

const execFileAsync = promisify(execFile);
const repoRoot = process.cwd();
const workspaceRoot = path.join(repoRoot, "workspace");
const pythonBin = process.env.HARNESS_PYTHON || "python3";

export async function GET() {
  try {
    const { stdout } = await execFileAsync(pythonBin, ["-m", "harness.main", "status"], {
      cwd: repoRoot,
      env: {
        ...process.env,
        HARNESS_WORKSPACE: workspaceRoot,
        HARNESS_USE_LLM: process.env.HARNESS_USE_LLM || "false",
        PYTHONPATH: repoRoot
      },
      timeout: 30000,
      maxBuffer: 1024 * 1024
    });
    const { stdout: jobsStdout } = await execFileAsync(pythonBin, ["-m", "harness.main", "jobs"], {
      cwd: repoRoot,
      env: {
        ...process.env,
        HARNESS_WORKSPACE: workspaceRoot,
        HARNESS_USE_LLM: process.env.HARNESS_USE_LLM || "false",
        PYTHONPATH: repoRoot
      },
      timeout: 30000,
      maxBuffer: 1024 * 1024
    });
    const { stdout: connectorsStdout } = await execFileAsync(pythonBin, ["-m", "harness.main", "connectors"], {
      cwd: repoRoot,
      env: {
        ...process.env,
        HARNESS_WORKSPACE: workspaceRoot,
        HARNESS_USE_LLM: process.env.HARNESS_USE_LLM || "false",
        PYTHONPATH: repoRoot
      },
      timeout: 30000,
      maxBuffer: 1024 * 1024
    });
    return Response.json({
      status: JSON.parse(stdout),
      jobs: JSON.parse(jobsStdout || "[]"),
      connectors: JSON.parse(connectorsStdout || "[]")
    });
  } catch (error) {
    return Response.json({ error: error.message }, { status: 500 });
  }
}
