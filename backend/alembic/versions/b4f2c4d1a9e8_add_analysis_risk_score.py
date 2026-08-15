"""add analysis risk score

Revision ID: b4f2c4d1a9e8
Revises: 4a8634371dbb
Create Date: 2026-08-15

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b4f2c4d1a9e8"
down_revision: Union[str, None] = "4a8634371dbb"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("analyses", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("classification", sa.String(length=32), server_default="SAFE", nullable=False)
        )
        batch_op.add_column(sa.Column("risk_score", sa.Numeric(precision=5, scale=2), nullable=True))
        batch_op.add_column(
            sa.Column("component_scores", sa.JSON(), server_default=sa.text("'{}'"), nullable=False)
        )
        batch_op.create_check_constraint(
            "ck_analyses_risk_score_range",
            "risk_score IS NULL OR (risk_score >= 0 AND risk_score <= 100)",
        )


def downgrade() -> None:
    with op.batch_alter_table("analyses", schema=None) as batch_op:
        batch_op.drop_constraint("ck_analyses_risk_score_range", type_="check")
        batch_op.drop_constraint("ck_analyses_classification", type_="check")
        batch_op.drop_column("component_scores")
        batch_op.drop_column("risk_score")
        batch_op.drop_column("classification")
