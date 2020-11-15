import factory


class AnnouncementFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "notifications.Announcement"

    url = factory.Sequence(lambda n: f"/url-{n}/")
