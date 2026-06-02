import { appendLead, listLeads } from "../store";

export async function GET() {
  try {
    return Response.json({ leads: await listLeads() });
  } catch (error) {
    return Response.json({ error: error.message }, { status: 500 });
  }
}

export async function POST(request) {
  try {
    const body = await request.json();
    if (!body.email && !body.name) {
      return Response.json({ error: "Please include at least a name or email." }, { status: 400 });
    }
    return Response.json({ lead: await appendLead(body) }, { status: 201 });
  } catch (error) {
    return Response.json({ error: error.message }, { status: 500 });
  }
}
