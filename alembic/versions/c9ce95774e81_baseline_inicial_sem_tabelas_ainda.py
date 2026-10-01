"""baseline inicial (sem tabelas ainda)

Revision ID: c9ce95774e81
Revises: 
Create Date: 2026-10-01 22:32:47.220310

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c9ce95774e81'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
