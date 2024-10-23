import logging

_logger = logging.getLogger(__name__)


def _post_init_sale_partner_source(env):
    cr = env.cr
    # Create source from partner category
    cr.execute("""
        INSERT INTO utm_source (name, create_uid, create_date, write_uid, write_date)
        SELECT name, create_uid, create_date, write_uid, write_date
        FROM partner_classification
    """)

    # Migrate partner's source_id
    cr.execute("""
        UPDATE res_partner rp
        SET source_id = (
            SELECT us.id
            FROM utm_source us
            JOIN partner_classification pc ON rp.partner_classification_id = pc.id
            WHERE us.name = pc.name
            LIMIT 1
        )
        WHERE rp.source_id IS NULL
    """)
