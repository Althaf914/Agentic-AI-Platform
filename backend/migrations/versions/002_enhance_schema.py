"""Enhance schema — campaigns table, new company/recommendation columns

Revision ID: 002
Revises: 001
Create Date: 2026-06-28 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa

revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade():
    # 1. Create campaigns table
    op.create_table(
        "campaigns",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column(
            "status",
            sa.Enum("draft", "active", "archived", name="campaign_status"),
            nullable=False,
            server_default="draft",
        ),
        sa.Column("domain", sa.String(255), nullable=False),
        sa.Column("wizard_step_completed", sa.Integer, nullable=False, server_default="0"),
        sa.Column("config_json", sa.JSON, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # 2. Add new columns to companies
    op.add_column("companies", sa.Column("tech_stack_detected", sa.JSON, nullable=True))
    op.add_column("companies", sa.Column("market_signals", sa.JSON, nullable=True))
    op.add_column("companies", sa.Column("domain_age_days", sa.Integer, nullable=True))
    op.add_column("companies", sa.Column("has_linkedin", sa.Boolean, nullable=False, server_default=sa.text("false")))
    op.add_column("companies", sa.Column("hiring_signal_score", sa.Float, nullable=True))
    op.add_column("companies", sa.Column("validation_details", sa.JSON, nullable=True))
    op.add_column("companies", sa.Column("score_breakdown", sa.JSON, nullable=True))

    # 3. Add campaign_id FK to workflows (nullable)
    op.add_column("workflows", sa.Column("campaign_id", sa.String(36), sa.ForeignKey("campaigns.id"), nullable=True))

    # 4. Add new columns to recommendations
    op.add_column("recommendations", sa.Column("buying_committee", sa.JSON, nullable=True))
    op.add_column("recommendations", sa.Column("talking_points", sa.JSON, nullable=True))
    op.add_column("recommendations", sa.Column("market_trigger", sa.String(255), nullable=True))
    op.add_column("recommendations", sa.Column("outreach_channel", sa.String(50), nullable=True))
    op.add_column("recommendations", sa.Column("follow_up_sequence", sa.JSON, nullable=True))


def downgrade():
    # Remove recommendation columns
    op.drop_column("recommendations", "follow_up_sequence")
    op.drop_column("recommendations", "outreach_channel")
    op.drop_column("recommendations", "market_trigger")
    op.drop_column("recommendations", "talking_points")
    op.drop_column("recommendations", "buying_committee")

    # Remove workflow campaign_id FK
    op.drop_column("workflows", "campaign_id")

    # Remove company columns
    op.drop_column("companies", "score_breakdown")
    op.drop_column("companies", "validation_details")
    op.drop_column("companies", "hiring_signal_score")
    op.drop_column("companies", "has_linkedin")
    op.drop_column("companies", "domain_age_days")
    op.drop_column("companies", "market_signals")
    op.drop_column("companies", "tech_stack_detected")

    # Drop campaigns table
    op.drop_table("campaigns")

    # Drop campaign status enum
    op.execute("DROP TYPE IF EXISTS campaign_status")
