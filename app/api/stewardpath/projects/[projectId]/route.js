import { getProject, updateProject } from "../../store";

export async function GET(_request, { params }) {
  try {
    const { projectId } = await params;
    const project = await getProject(projectId);
    if (!project) {
      return Response.json({ error: "Project not found" }, { status: 404 });
    }
    return Response.json({ project });
  } catch (error) {
    return Response.json({ error: error.message }, { status: 500 });
  }
}

export async function PATCH(request, { params }) {
  try {
    const { projectId } = await params;
    const body = await request.json();
    const project = await updateProject(projectId, {
      name: body.name,
      profile: body.profile,
      intakeState: body.intakeState || null
    });
    if (!project) {
      return Response.json({ error: "Project not found" }, { status: 404 });
    }
    return Response.json({ project });
  } catch (error) {
    return Response.json({ error: error.message }, { status: 500 });
  }
}
