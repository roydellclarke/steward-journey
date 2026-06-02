import { appendAnalysis, listAnalyses } from "../../../store";

export async function GET(_request, { params }) {
  try {
    const { projectId } = await params;
    return Response.json({ analyses: await listAnalyses(projectId) });
  } catch (error) {
    return Response.json({ error: error.message }, { status: 500 });
  }
}

export async function POST(request, { params }) {
  try {
    const { projectId } = await params;
    const body = await request.json();
    const entry = await appendAnalysis(projectId, {
      profileSnapshot: body.profileSnapshot,
      analysis: body.analysis
    });
    if (!entry) {
      return Response.json({ error: "Project not found" }, { status: 404 });
    }
    return Response.json({ analysisEntry: entry }, { status: 201 });
  } catch (error) {
    return Response.json({ error: error.message }, { status: 500 });
  }
}
