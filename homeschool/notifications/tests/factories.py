import factory


class AnnouncementFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "notifications.Announcement"

    url = factory.Sequence(lambda n: f"/url-{n}/")


class NotificationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "notifications.Notification"

    user = factory.SubFactory("homeschool.users.tests.factories.UserFactory")
    announcement = factory.SubFactory(AnnouncementFactory)
