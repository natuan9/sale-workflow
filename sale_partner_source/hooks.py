from odoo.upgrade import util


def create_source_from_partner_category(env):
    cr = env.cr
    UtmSource = env['utm.source']

    # Retrieve category names and existing utm.source names
    cr.execute("SELECT DISTINCT name FROM partner_category")
    category_names = [row[0] for row in cr.fetchall()]
    existing_source_names = UtmSource.search(
        [('name', 'in', category_names)]).mapped('name')

    # Create new utm.source records for names that do not exist
    new_names = [
        name for name in category_names if name not in existing_source_names]
    UtmSource.create([{'name': name} for name in new_names])


def migrate_partner_source_id(env):
    cr = env.cr
    cr.execute("""
        UPDATE res_partner rp
        SET source_id = (
            SELECT us.id
            FROM utm_source us
            JOIN partner_category pc ON us.name = pc.name
            WHERE rp.group_category_id = pc.id
            LIMIT 1
        )
        WHERE rp.group_category_id IS NOT NULL
        AND rp.source_id IS NULL
    """)


def migrate_sale_order(env):
    env.cr.execute("""
        UPDATE sale_order so
        SET source_id = (
            SELECT us.id
            FROM utm_source us
            JOIN res_partner rs ON us.id = rs.source_id
            WHERE rs.id = so.partner_id
        )
        WHERE so.source_id IS NULL;
    """)


def migrate_invoice(env):
    env.cr.execute("""
        UPDATE account_move am
        SET source_id = (
            SELECT us.id
            FROM utm_source us
            JOIN res_partner rs ON us.id = rs.source_id
            WHERE rs.id = am.partner_id
        )
        WHERE am.source_id IS NULL;
    """)


def _post_init_sale_partner_source(env):
    if not env["ir.module.module"].search(
        [("name", "=", "gts_partner_category")]
    ) or not util.table_exists(env.cr, "partner_category"):
        return

    create_source_from_partner_category(env)

    if util.column_exists(env.cr, "res_partner", "group_category_id"):
        migrate_partner_source_id(env)
        migrate_sale_order(env)
        migrate_invoice(env)

    util.remove_module(env.cr, "gts_partner_category")
