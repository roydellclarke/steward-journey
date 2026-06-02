import { getLatestAnalysis } from "../../../../store";

export async function GET(_request, { params }) {
  try {
    const { projectId } = await params;
    const analysisEntry = await getLatestAnalysis(projectId);
    if (!analysisEntry) {
      return Response.json({ error: "No analysis has been saved for this project" }, { status: 404 });
    }
    return Response.json({ analysisEntry });
  } catch (error) {
    return Response.json({ error: error.message }, { status: 500 });
  }
}
