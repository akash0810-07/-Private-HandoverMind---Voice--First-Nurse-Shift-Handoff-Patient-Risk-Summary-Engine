import click
from flask.cli import with_appcontext
from app.extensions import db
from app.models import Nurse, Ward


@click.command("init-db")
@with_appcontext
def init_db_command():
    """Create all tables (quick-start alternative to Alembic migrations)."""
    db.create_all()
    click.echo("Database tables created.")


@click.command("create-admin")
@click.option("--email", required=True)
@click.option("--password", required=True)
@click.option("--name", default="System Admin")
@with_appcontext
def create_admin_command(email, password, name):
    """Create an ADMIN nurse account."""
    if Nurse.query.filter_by(email=email).first():
        click.echo("A nurse with that email already exists.")
        return
    admin = Nurse(full_name=name, email=email.lower(), role="ADMIN")
    admin.set_password(password)
    db.session.add(admin)
    db.session.commit()
    click.echo(f"Admin created: {email}")


def register_cli(app):
    app.cli.add_command(init_db_command)
    app.cli.add_command(create_admin_command)
