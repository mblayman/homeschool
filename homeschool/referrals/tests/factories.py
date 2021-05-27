import factory


class ReferralFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "referrals.Referral"

    referring_user = factory.SubFactory("homeschool.users.tests.factories.UserFactory")
