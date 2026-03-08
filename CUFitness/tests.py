
# for user model

from django.contrib.auth import get_user_model
from django.test import TestCase

# --------------- used to test custom user class ---------------
class UsersManagersTests(TestCase):

    def test_create_user(self):
        User = get_user_model()
        user = User.objects.create_user(email="normal@user.com", password="foo")
        self.assertEqual(user.email, "normal@user.com")
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        try:
            # username is None for the AbstractUser option
            # username does not exist for the AbstractBaseUser option
            self.assertIsNone(user.username)
        except AttributeError:
            pass
        with self.assertRaises(TypeError):
            User.objects.create_user()
        with self.assertRaises(TypeError):
            User.objects.create_user(email="")
        with self.assertRaises(ValueError):
            User.objects.create_user(email="", password="foo")

    def test_create_superuser(self):
        User = get_user_model()
        admin_user = User.objects.create_superuser(email="super@user.com", password="foo")
        self.assertEqual(admin_user.email, "super@user.com")
        self.assertTrue(admin_user.is_active)
        self.assertTrue(admin_user.is_staff)
        self.assertTrue(admin_user.is_superuser)
        try:
            # username is None for the AbstractUser option
            # username does not exist for the AbstractBaseUser option
            self.assertIsNone(admin_user.username)
        except AttributeError:
            pass
        with self.assertRaises(ValueError):
            User.objects.create_superuser(
                email="super@user.com", password="foo", is_superuser=False)


#   --------- Extra Tests ---------
from django.test import TestCase
from django.utils import timezone
from django.core.exceptions import ValidationError
from datetime import timedelta

from CUFitness.models import (
    CustomUser,
    EquipmentList,
    EquipmentBooking,
    CoachAvailability,
    CoachAppointment, Articles

)
User = get_user_model()


class CustomUserModelTest(TestCase):

    def test_create_user_defaults(self):
        user = CustomUser.objects.create_user(
            email="test@example.com",
            password="password123"
        )

        self.assertEqual(user.role, "MEMBER")
        self.assertEqual(user.membership, "BASIC")
        self.assertTrue(user.is_active)
        self.assertEqual(str(user), "test@example.com")

class EquipmentListTest(TestCase):

    def test_create_equipment(self):
        equipment = EquipmentList.objects.create(
            name="Treadmill",
            description="Cardio machine"
        )

        self.assertEqual(str(equipment), "Treadmill")
        self.assertTrue(equipment.is_active)

class EquipmentBookingTest(TestCase):

    def setUp(self):
        self.coach = CustomUser.objects.create_user(
            email="coach@example.com",
            password="pass123",
            role="COACH"
        )

        self.equipment = EquipmentList.objects.create(
            name="Bench Press"
        )

        self.start_time = timezone.now()
        self.end_time = self.start_time + timedelta(hours=1)

    def test_valid_booking(self):
        booking = EquipmentBooking.objects.create(
            equipment=self.equipment,
            coach=self.coach,
            start_time=self.start_time,
            end_time=self.end_time
        )

        self.assertEqual(str(booking).startswith("Bench Press booked"), True)

    def test_invalid_time_booking(self):
        with self.assertRaises(ValidationError):
            EquipmentBooking.objects.create(
                equipment=self.equipment,
                coach=self.coach,
                start_time=self.end_time,
                end_time=self.start_time
            )

    def test_overlapping_booking(self):
        EquipmentBooking.objects.create(
            equipment=self.equipment,
            coach=self.coach,
            start_time=self.start_time,
            end_time=self.end_time
        )

        with self.assertRaises(ValidationError):
            EquipmentBooking.objects.create(
                equipment=self.equipment,
                coach=self.coach,
                start_time=self.start_time + timedelta(minutes=30),
                end_time=self.end_time + timedelta(minutes=30)
            )

class CoachAvailabilityTest(TestCase):

    def setUp(self):
        self.coach = CustomUser.objects.create_user(
            email="coach2@example.com",
            password="pass123",
            role="COACH"
        )

        self.start = timezone.now()
        self.end = self.start + timedelta(hours=2)

    def test_valid_availability(self):
        availability = CoachAvailability.objects.create(
            coach=self.coach,
            start_time=self.start,
            end_time=self.end
        )

        self.assertEqual(str(availability).startswith(self.coach.email), True)

    def test_overlapping_availability(self):
        CoachAvailability.objects.create(
            coach=self.coach,
            start_time=self.start,
            end_time=self.end
        )

        with self.assertRaises(ValidationError):
            CoachAvailability.objects.create(
                coach=self.coach,
                start_time=self.start + timedelta(minutes=30),
                end_time=self.end + timedelta(minutes=30)
            )

class CoachAppointmentTest(TestCase):

    def setUp(self):
        self.coach = CustomUser.objects.create_user(
            email="coach3@example.com",
            password="pass123",
            role="COACH"
        )

        self.member = CustomUser.objects.create_user(
            email="member@example.com",
            password="pass123",
            role="MEMBER"
        )

        self.start = timezone.now()
        self.end = self.start + timedelta(hours=1)

    def test_valid_appointment(self):
        appointment = CoachAppointment.objects.create(
            coach=self.coach,
            member=self.member,
            start_time=self.start,
            end_time=self.end,
            status="accepted"
        )

        self.assertEqual(appointment.status, "accepted")

    def test_double_booking_accepted(self):
        CoachAppointment.objects.create(
            coach=self.coach,
            member=self.member,
            start_time=self.start,
            end_time=self.end,
            status="accepted"
        )

        with self.assertRaises(ValidationError):
            CoachAppointment.objects.create(
                coach=self.coach,
                member=self.member,
                start_time=self.start + timedelta(minutes=30),
                end_time=self.end + timedelta(minutes=30),
                status="accepted"
            )

class ArticlesModelTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            email="user@test.com",
            password="password123"
        )

        self.author = User.objects.create_user(
            email="author@test.com",
            password="password123"
        )

        self.article = Articles.objects.create(
            #user=self.user,
            author=self.author,
            title="Test Article",
            body="This is a test article body.",
            locked=False
        )

    def test_article_creation(self):
        """Test article is created successfully"""
        self.assertEqual(self.article.title, "Test Article")
        self.assertEqual(self.article.body, "This is a test article body.")
        self.assertFalse(self.article.locked)

    def test_article_author_relationship(self):
        """Test article is linked to the correct author"""
        self.assertEqual(self.article.author, self.author)

    def test_locked_field(self):
        """Test locked field can be toggled"""
        self.article.locked = True
        self.article.save()

        article = Articles.objects.get(id=self.article.id)
        self.assertTrue(article.locked)

    def test_str_method(self):
        """Test __str__ method returns a string"""
        self.assertIsInstance(str(self.article), str)

    def test_article_timestamps(self):
        """Test timestamps are auto created"""
        self.assertIsNotNone(self.article.created_at)
        self.assertIsNotNone(self.article.updated_at)


