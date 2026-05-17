from django.contrib.admin.apps import AdminConfig as DjangoAdminConfig


def _patch_hashid_field_for_django_6() -> None:
    """Make hashid_field's custom lookup tolerate Django 6 SQL params.

    Django 6 returns tuples from lookup processing where older versions used lists.
    hashid_field's bundled lookup mutates params in-place, so convert to a list first.
    """

    try:
        from hashid_field.lookups import HashidExactLookup
    except ImportError:
        return

    if getattr(HashidExactLookup.as_sql, "__name__", "") == "as_sql":
        # Leave any explicit upstream override alone.
        pass

    def as_sql(self, compiler, connection):
        lhs_sql, params = self.process_lhs(compiler, connection)
        rhs_sql, rhs_params = self.process_rhs(compiler, connection)
        params = list(params)
        params.extend(rhs_params)
        rhs_sql = self.get_rhs_op(connection, rhs_sql)
        return "%s %s" % (lhs_sql, rhs_sql), params

    HashidExactLookup.as_sql = as_sql


class AdminConfig(DjangoAdminConfig):
    default_site = "project.admin.AdminSite"

    def ready(self):
        _patch_hashid_field_for_django_6()
        super().ready()
