import { notFound } from "next/navigation";
import { getContent, CONTENT_SLUGS } from "../../../lib/content";
import { SITE_URL } from "../../../lib/site";
import "./content.css";

// Pre-render every guide at build time.
export function generateStaticParams() {
  return CONTENT_SLUGS.map((slug) => ({ slug }));
}

export async function generateMetadata({ params }) {
  const { slug } = await params;
  const c = getContent(slug);
  if (!c) return {};
  const path = `/content/${c.slug}`;
  return {
    title: c.title,
    description: c.description,
    alternates: {
      canonical: path,
      // Point AI clients at the clean Markdown mirror of this same page.
      types: { "text/markdown": `${SITE_URL}${path}.md` }
    },
    openGraph: { title: c.title, description: c.description, url: `${SITE_URL}${path}`, type: "article" }
  };
}

export default async function ContentPage({ params }) {
  const { slug } = await params;
  const c = getContent(slug);
  if (!c) notFound();

  return (
    <main className="publicShell">
      <article className="contentArticle">
        <p className="publicEyebrow">Guide for trades owners</p>
        <h1>{c.title}</h1>
        <p className="contentIntro">{c.intro}</p>

        {c.sections.map((section) => (
          <section key={section.heading} className="contentSection">
            <h2>{section.heading}</h2>
            {(section.body || []).map((para, i) => <p key={i}>{para}</p>)}
            {section.bullets?.length ? (
              <ul>{section.bullets.map((b, i) => <li key={i}>{b}</li>)}</ul>
            ) : null}
          </section>
        ))}

        {c.cta ? (
          <p className="contentCta">
            <a className="primaryCta" href={c.cta.href}>{c.cta.text}</a>
          </p>
        ) : null}
      </article>
    </main>
  );
}
