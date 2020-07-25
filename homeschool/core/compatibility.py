from functools import reduce

from django.db.models.constants import LOOKUP_SEP
from ordered_model.models import OrderedModelQuerySet as UpstreamOrderedModelQuerySet


def get_lookup_value(obj, field):
    return reduce(lambda i, f: getattr(i, f), field.split(LOOKUP_SEP), obj)


class OrderedModelQuerySet(UpstreamOrderedModelQuerySet):
    def bulk_create(
        self, objs, batch_size=None, ignore_conflicts=False
    ):  # pragma: no cover
        """Bulk create objects.

        This implementation comes from
        https://github.com/bfirsh/django-ordered-model/pull/228

        The change is the inclusion of the `ignore_conflicts` parameter.
        """
        order_field_name = self._get_order_field_name()
        order_with_respect_to = self.model.order_with_respect_to
        objs = list(objs)
        if order_with_respect_to:
            order_with_respect_to_mapping: dict = {}
            order_with_respect_to = self._get_order_with_respect_to()
            for obj in objs:
                key = tuple(
                    get_lookup_value(obj, field) for field in order_with_respect_to
                )
                if key in order_with_respect_to_mapping:
                    order_with_respect_to_mapping[key] += 1
                else:
                    order_with_respect_to_mapping[
                        key
                    ] = self.filter_by_order_with_respect_to(obj).get_next_order()
                setattr(obj, order_field_name, order_with_respect_to_mapping[key])
        else:
            for order, obj in enumerate(objs, self.get_next_order()):
                setattr(obj, order_field_name, order)

        # MODIFIED: Skipping the local class' super because that's the one
        # that is broken.
        return super(UpstreamOrderedModelQuerySet, self).bulk_create(
            objs, batch_size=batch_size, ignore_conflicts=ignore_conflicts
        )
