"""
PDF generation service.
Renders Jinja2 HTML templates to PDF via xhtml2pdf.
Interface is independent of the underlying library.
"""
import os
import uuid
from pathlib import Path
from typing import Optional
from jinja2 import Environment, FileSystemLoader
from app.core.config import settings
from app.core.logging import logger

_TEMPLATE_DIR = Path(__file__).parent.parent / "templates" / "reports"
_jinja_env = Environment(loader=FileSystemLoader(str(_TEMPLATE_DIR)), autoescape=True)


def _render_html(template_name: str, context: dict) -> str:
    tmpl = _jinja_env.get_template(template_name)
    return tmpl.render(**context)


def _html_to_pdf(html: str, output_path: str) -> str:
    """Convert HTML string to PDF file. Returns the path."""
    try:
        from xhtml2pdf import pisa

        with open(output_path, "wb") as f:
            result = pisa.CreatePDF(html, dest=f)
        if result.err:
            logger.error(f"xhtml2pdf error: {result.err}")
            return ""
        return output_path
    except ImportError:
        logger.error("xhtml2pdf not installed — PDF generation skipped.")
        return ""
    except Exception as e:
        logger.error(f"PDF generation failed: {e}")
        return ""


def _output_path(report_type: str) -> str:
    report_dir = settings.ensure_report_dir()
    filename = f"{report_type}_{uuid.uuid4().hex[:8]}.pdf"
    return os.path.join(report_dir, filename)


def generate_engineer_report_pdf(context: dict) -> Optional[str]:
    """Render engineer_report.html with context and save as PDF. Returns PDF path or None."""
    try:
        html = _render_html("engineer_report.html", context)
        path = _output_path("engineer")
        result = _html_to_pdf(html, path)
        if result:
            logger.info(f"Engineer PDF generated: {path}")
            return result
        return None
    except Exception as e:
        logger.error(f"Engineer PDF failed: {e}")
        return None


def generate_admin_report_pdf(context: dict) -> Optional[str]:
    """Render admin_report.html with context and save as PDF. Returns PDF path or None."""
    try:
        html = _render_html("admin_report.html", context)
        path = _output_path("admin")
        result = _html_to_pdf(html, path)
        if result:
            logger.info(f"Admin PDF generated: {path}")
            return result
        return None
    except Exception as e:
        logger.error(f"Admin PDF failed: {e}")
        return None


def render_engineer_html(context: dict) -> str:
    """Return rendered HTML string without writing to disk."""
    return _render_html("engineer_report.html", context)


def render_admin_html(context: dict) -> str:
    """Return rendered HTML string without writing to disk."""
    return _render_html("admin_report.html", context)
