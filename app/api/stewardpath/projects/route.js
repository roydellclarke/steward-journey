import { createProject, listProjects } from "../store";

export async function GET() {
  try {
    return Response.json({ projects: await listProjects() });
  } catch (error) {
    return Response.json({ error: error.message }, { status: 500 });
  }
}

export async function POST(request) {
  try {
    const body = await request.json();
    const project = await createProject({
      name: body.name,
      profile: body.profile || {},
      intakeState: body.intakeState || null
    });
    return Response.json({ project }, { status: 201 });
  } catch (error) {
    return Response.json({ error: error.message }, { status: 500 });
  }
}
