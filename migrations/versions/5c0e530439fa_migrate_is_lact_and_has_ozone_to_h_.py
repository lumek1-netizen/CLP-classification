"""Migrate is_lact and has_ozone to H-phrases

Revision ID: 5c0e530439fa
Revises: 7154063ef3f8
Create Date: 2026-01-20 18:46:12.184334

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5c0e530439fa'
down_revision = '7154063ef3f8'
branch_labels = None
depends_on = None


def upgrade():
    """
    Migrace H362 (is_lact) a H420 (has_ozone) do H-phrases.
    """
    connection = op.get_bind()
    
    # 1. Migrace H362 (Laktace) z is_lact do health_h_phrases
    substances_with_lact = connection.execute(
        sa.text("SELECT id, health_h_phrases FROM substance WHERE is_lact = 1")
    ).fetchall()
    
    for row in substances_with_lact:
        substance_id = row[0]
        current_h_phrases = row[1]
        
        # Parsovat existující H-phrases
        h_list = []
        if current_h_phrases:
            h_list = [h.strip() for h in current_h_phrases.split(',')]
        
        # Přidat H362 pokud ještě není
        if 'H362' not in h_list:
            h_list.append('H362')
        
        # Uložit zpět
        new_h_phrases = ', '.join(h_list)
        connection.execute(
            sa.text("UPDATE substance SET health_h_phrases = :h_phrases WHERE id = :id"),
            {"h_phrases": new_h_phrases, "id": substance_id}
        )
    
    # 2. Migrace H420 (Ozonová vrstva) z has_ozone do env_h_phrases
    substances_with_ozone = connection.execute(
        sa.text("SELECT id, env_h_phrases FROM substance WHERE has_ozone = 1")
    ).fetchall()
    
    for row in substances_with_ozone:
        substance_id = row[0]
        current_h_phrases = row[1]
        
        # Parsovat existující H-phrases
        h_list = []
        if current_h_phrases:
            h_list = [h.strip() for h in current_h_phrases.split(',')]
        
        # Přidat H420 pokud ještě není
        if 'H420' not in h_list:
            h_list.append('H420')
        
        # Uložit zpět
        new_h_phrases = ', '.join(h_list)
        connection.execute(
            sa.text("UPDATE substance SET env_h_phrases = :h_phrases WHERE id = :id"),
            {"h_phrases": new_h_phrases, "id": substance_id}
        )
    
    # 3. Odstranit deprecated sloupce
    with op.batch_alter_table('substance', schema=None) as batch_op:
        batch_op.drop_column('is_lact')
        batch_op.drop_column('has_ozone')


def downgrade():
    """
    Obnovení sloupců is_lact a has_ozone z H-phrases.
    """
    connection = op.get_bind()
    
    # 1. Obnovit sloupce
    with op.batch_alter_table('substance', schema=None) as batch_op:
        batch_op.add_column(sa.Column('is_lact', sa.Boolean(), nullable=True))
        batch_op.add_column(sa.Column('has_ozone', sa.Boolean(), nullable=True))
    
    # 2. Obnovit data z H-phrases do is_lact
    substances = connection.execute(
        sa.text("SELECT id, health_h_phrases FROM substance WHERE health_h_phrases IS NOT NULL")
    ).fetchall()
    
    for row in substances:
        substance_id = row[0]
        health_h = row[1]
        
        if health_h and 'H362' in health_h:
            connection.execute(
                sa.text("UPDATE substance SET is_lact = 1 WHERE id = :id"),
                {"id": substance_id}
            )
    
    # 3. Obnovit data z H-phrases do has_ozone
    substances = connection.execute(
        sa.text("SELECT id, env_h_phrases FROM substance WHERE env_h_phrases IS NOT NULL")
    ).fetchall()
    
    for row in substances:
        substance_id = row[0]
        env_h = row[1]
        
        if env_h and 'H420' in env_h:
            connection.execute(
                sa.text("UPDATE substance SET has_ozone = 1 WHERE id = :id"),
                {"id": substance_id}
            )
