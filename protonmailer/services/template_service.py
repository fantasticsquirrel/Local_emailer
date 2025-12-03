import jinja2

from protonmailer.models.template import Template


template_env = jinja2.Environment(autoescape=True)


def render_template(template: Template, context: dict) -> tuple[str, str]:
    """
    Render the given template's subject and body_html with the provided context.
    Missing variables are rendered as empty strings via Jinja2's default undefined behavior.
    """

    subject_template = template_env.from_string(template.subject or "")
    body_template = template_env.from_string(template.body_html or "")

    subject_rendered = subject_template.render(**context)
    body_rendered = body_template.render(**context)
    return subject_rendered, body_rendered
