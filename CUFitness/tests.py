"""
UsersManagersTests:
    - test_create_user — verifies a normal user is created correctly and rejects missing/empty email
    - test_create_superuser — verifies a superuser has is_staff and is_superuser flags set, and can't be created with is_superuser=False

CustomUserModelTest — test_create_user_defaults — checks a new user defaults to MEMBER role, BASIC membership, and active status

EquipmentListTest — test_create_equipment — checks equipment is created with the correct name and defaults to active

EquipmentBookingTest:
    - test_valid_booking — confirms a normal booking saves successfully
    - test_invalid_time_booking — confirms a booking where end is before start is rejected
    - test_overlapping_booking — confirms a second booking that overlaps an existing one is rejected

CoachAvailabilityTest:
    - test_valid_availability — confirms a normal availability slot saves successfully
    - test_overlapping_availability — confirms a coach can't create two overlapping availability slots

CoachAppointmentTest:
    - test_valid_appointment — confirms a normal appointment saves successfully
    - test_double_booking_accepted — confirms a coach can't have two accepted overlapping appointments

ArticlesModelTest:
    - test_article_creation — checks title, body, and locked field are saved correctly
    - test_article_author_relationship — confirms the article is linked to the right author
    - test_locked_field — confirms the locked field can be toggled and persisted
    - test_str_method — confirms __str__ returns a string
    - test_article_timestamps — confirms created_at and updated_at are auto-populated

Authentication tests — verifies that members/coaches log in via /login/, staff get redirected to /staff_login/, wrong passwords fail, and logout works.
Access control tests — Checks that unauthenticated users can't reach protected pages, members can't access staff pages, and staff can't access the member settings page.
Article view tests — confirms that the author can edit/delete their own article, a different staff member cannot, the author gets auto-assigned on creation (not from the form), and a non-existent article returns a 404.
Settings view tests — tests that the privacy form saves correctly, and that submitting the coach request sets status to PENDING.
Form validation tests — tests ArticleForm, CustomUserCreationForm, and PrivacySettingsForm with valid and invalid inputs. Includes the title/description max length constraints and duplicate email registration.
Nutrition page tests — checks that free/locked articles are passed in the correct context variables
Public pages tests — a simple smoke test that every public URL returns a 200. Quick to run and immediately catches broken URL configs or template errors.

"""

from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from django.core.exceptions import ValidationError
from datetime import timedelta
from django.contrib.auth import get_user_model
from CUFitness.models import CustomUser, Articles, CoachAvailability, CoachAppointment, EquipmentList, EquipmentBooking
from CUFitness.forms import ArticleForm, CustomUserCreationForm, PrivacySettingsForm



# ══════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════
User = get_user_model()
def make_member(email='member@test.com', password='Pass@1234'):
    return User.objects.create_user(email=email, password=password, role='MEMBER',
                                    first_name='Jane', last_name='Doe')

def make_coach(email='coach@test.com', password='Pass@1234'):
    return User.objects.create_user(email=email, password=password, role='COACH',
                                    first_name='Bob', last_name='Smith')

def make_staff(email='staff@test.com', password='Pass@1234'):
    return User.objects.create_user(email=email, password=password, role='STAFF',
                                    first_name='Alice', last_name='Admin', is_staff=True)

def make_article(author, title='Test Article', locked=False):
    return Articles.objects.create(
        author=author,
        title=title,
        description='A short description.',
        body='Article body content.',
        locked=locked,
    )
# ══════════════════════════════════════════════════


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


# ══════════════════════════════════════════════════
# AUTHENTICATION VIEW TESTS
# ══════════════════════════════════════════════════

class LoginViewTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.member = make_member()
        self.staff = make_staff()
        self.coach = make_coach()

    def test_login_page_loads(self):
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)

    def test_member_login_success(self):
        response = self.client.post(reverse('login'), {
            'email': 'member@test.com',
            'password': 'Pass@1234',
        })
        self.assertRedirects(response, reverse('home'))

    def test_coach_login_success(self):
        response = self.client.post(reverse('login'), {
            'email': 'coach@test.com',
            'password': 'Pass@1234',
        })
        self.assertRedirects(response, reverse('home'))

    def test_staff_redirected_to_staff_login(self):
        """Staff logging in via member login should be redirected."""
        response = self.client.post(reverse('login'), {
            'email': 'staff@test.com',
            'password': 'Pass@1234',
        })
        self.assertRedirects(response, reverse('staff_login'))

    def test_invalid_credentials(self):
        response = self.client.post(reverse('login'), {
            'email': 'member@test.com',
            'password': 'wrongpassword',
        })
        self.assertRedirects(response, reverse('login'))

    def test_logout(self):
        self.client.login(username='member@test.com', password='Pass@1234')
        response = self.client.get(reverse('logout'))
        self.assertRedirects(response, reverse('home'))


class StaffLoginViewTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.staff = make_staff()
        self.member = make_member()

    def test_staff_login_page_loads(self):
        response = self.client.get(reverse('staff_login'))
        self.assertEqual(response.status_code, 200)

    def test_staff_login_success(self):
        response = self.client.post(reverse('staff_login'), {
            'email': 'staff@test.com',
            'password': 'Pass@1234',
        })
        self.assertRedirects(response, reverse('home'))

    def test_member_cannot_login_via_staff_login(self):
        response = self.client.post(reverse('staff_login'), {
            'email': 'member@test.com',
            'password': 'Pass@1234',
        })
        self.assertRedirects(response, reverse('staff_login'))


# ══════════════════════════════════════════════════
# ACCESS CONTROL TESTS
# ══════════════════════════════════════════════════

class AccessControlTest(TestCase):
    """Ensure pages are protected — unauthenticated users get redirected."""

    def setUp(self):
        self.client = Client()
        self.member = make_member()
        self.staff = make_staff()
        self.coach = make_coach()

    # --- Unauthenticated ---

    def test_unauthenticated_cannot_access_user_profile(self):
        response = self.client.get(reverse('user_profile'))
        self.assertNotEqual(response.status_code, 200)

    def test_unauthenticated_cannot_access_settings(self):
        response = self.client.get(reverse('settings'))
        self.assertNotEqual(response.status_code, 200)

    def test_unauthenticated_cannot_access_articles(self):
        response = self.client.get(reverse('articles'))
        self.assertNotEqual(response.status_code, 200)

    def test_unauthenticated_cannot_access_staff_home(self):
        response = self.client.get(reverse('staff_home'))
        self.assertNotEqual(response.status_code, 200)

    # --- Member cannot access staff pages ---

    def test_member_cannot_access_staff_home(self):
        self.client.force_login(self.member)
        response = self.client.get(reverse('staff_home'))
        self.assertNotEqual(response.status_code, 200)

    def test_member_cannot_access_articles_list(self):
        self.client.force_login(self.member)
        response = self.client.get(reverse('articles'))
        self.assertNotEqual(response.status_code, 200)

    def test_member_cannot_create_article(self):
        self.client.force_login(self.member)
        response = self.client.get(reverse('create_article'))
        self.assertNotEqual(response.status_code, 200)

    # --- Staff can access staff pages ---

    def test_staff_can_access_articles_list(self):
        self.client.force_login(self.staff)
        response = self.client.get(reverse('articles'))
        self.assertEqual(response.status_code, 200)

    def test_staff_can_access_create_article(self):
        self.client.force_login(self.staff)
        response = self.client.get(reverse('create_article'))
        self.assertEqual(response.status_code, 200)

    def test_staff_cannot_access_member_settings(self):
        """Staff should not be able to use the member settings page."""
        self.client.force_login(self.staff)
        response = self.client.get(reverse('settings'))
        self.assertNotEqual(response.status_code, 200)


# ══════════════════════════════════════════════════
# ARTICLE VIEW TESTS
# ══════════════════════════════════════════════════

class ArticleViewTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.staff = make_staff()
        self.other_staff = make_staff(email='other@test.com')
        self.article = make_article(author=self.staff, title='My Article')

    def test_article_detail_page_loads(self):
        self.client.force_login(self.staff)
        response = self.client.get(reverse('article_details', args=[self.article.id]))
        self.assertEqual(response.status_code, 200)

    def test_article_detail_shows_title(self):
        self.client.force_login(self.staff)
        response = self.client.get(reverse('article_details', args=[self.article.id]))
        self.assertContains(response, 'My Article')

    def test_author_can_edit_article(self):
        self.client.force_login(self.staff)
        response = self.client.post(reverse('edit_article', args=[self.article.id]), {
            'title': 'Updated Title',
            'description': 'Updated description.',
            'body': 'Updated body.',
            'locked': False,
        })
        self.article.refresh_from_db()
        self.assertEqual(self.article.title, 'Updated Title')

    def test_non_author_cannot_edit_article(self):
        self.client.force_login(self.other_staff)
        self.client.post(reverse('edit_article', args=[self.article.id]), {
            'title': 'Hacked Title',
            'description': 'x',
            'body': 'x',
            'locked': False,
        })
        self.article.refresh_from_db()
        self.assertNotEqual(self.article.title, 'Hacked Title')

    def test_author_can_delete_article(self):
        self.client.force_login(self.staff)
        self.client.post(reverse('delete_article', args=[self.article.id]))
        self.assertFalse(Articles.objects.filter(id=self.article.id).exists())

    def test_non_author_cannot_delete_article(self):
        self.client.force_login(self.other_staff)
        self.client.post(reverse('delete_article', args=[self.article.id]))
        self.assertTrue(Articles.objects.filter(id=self.article.id).exists())

    def test_create_article_saves_author(self):
        """Author should be set to the logged-in staff user, not from the form."""
        self.client.force_login(self.staff)
        self.client.post(reverse('create_article'), {
            'title': 'Brand New Article',
            'description': 'Some description.',
            'body': 'Some body.',
            'locked': False,
        })
        article = Articles.objects.get(title='Brand New Article')
        self.assertEqual(article.author, self.staff)

    def test_nonexistent_article_returns_404(self):
        self.client.force_login(self.staff)
        response = self.client.get(reverse('article_details', args=[99999]))
        self.assertEqual(response.status_code, 404)


# ══════════════════════════════════════════════════
# SETTINGS VIEW TESTS
# ══════════════════════════════════════════════════

class SettingsViewTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.member = make_member()

    def test_settings_page_loads(self):
        self.client.force_login(self.member)
        response = self.client.get(reverse('settings'))
        self.assertEqual(response.status_code, 200)

    def test_privacy_setting_update(self):
        self.client.force_login(self.member)
        self.client.post(reverse('settings'), {
            'workout_visibility': 'PUBLIC',
            'privacy_submit': '1',
        })
        self.member.refresh_from_db()
        self.assertEqual(self.member.workout_visibility, 'PUBLIC')

    def test_coach_request_sets_pending(self):
        self.client.force_login(self.member)
        self.client.post(reverse('settings'), {
            'coach_request_submit': '1',
        })
        self.member.refresh_from_db()
        self.assertEqual(self.member.coach_request_status, 'PENDING')

    def test_coach_request_already_pending_stays_pending(self):
        self.member.coach_request_status = 'PENDING'
        self.member.save()
        self.client.force_login(self.member)
        # submitting again shouldn't break anything
        self.client.post(reverse('settings'), {
            'coach_request_submit': '1',
        })
        self.member.refresh_from_db()
        self.assertEqual(self.member.coach_request_status, 'PENDING')


# ══════════════════════════════════════════════════
# FORM TESTS
# ══════════════════════════════════════════════════

class ArticleFormTest(TestCase):

    def test_valid_article_form(self):
        form = ArticleForm(data={
            'title': 'Valid Title',
            'description': 'Valid description.',
            'body': 'Valid body content.',
            'locked': False,
        })
        self.assertTrue(form.is_valid())

    def test_article_form_missing_title(self):
        form = ArticleForm(data={
            'title': '',
            'description': 'Desc.',
            'body': 'Body.',
            'locked': False,
        })
        self.assertFalse(form.is_valid())
        self.assertIn('title', form.errors)

    def test_article_form_title_too_long(self):
        form = ArticleForm(data={
            'title': 'x' * 76,  # max_length is 75
            'description': 'Desc.',
            'body': 'Body.',
            'locked': False,
        })
        self.assertFalse(form.is_valid())
        self.assertIn('title', form.errors)

    def test_article_form_description_too_long(self):
        form = ArticleForm(data={
            'title': 'Title',
            'description': 'x' * 251,  # max_length is 250
            'body': 'Body.',
            'locked': False,
        })
        self.assertFalse(form.is_valid())
        self.assertIn('description', form.errors)

    def test_author_not_in_article_form_fields(self):
        """Author should never be settable via the form."""
        form = ArticleForm()
        self.assertNotIn('author', form.fields)


class RegistrationFormTest(TestCase):

    def test_valid_registration(self):
        form = CustomUserCreationForm(data={
            'email': 'newuser@test.com',
            'first_name': 'New',
            'last_name': 'User',
            'membership': 'BASIC',
            'password1': 'StrongPass@99',
            'password2': 'StrongPass@99',
        })
        self.assertTrue(form.is_valid())

    def test_registration_password_mismatch(self):
        form = CustomUserCreationForm(data={
            'email': 'newuser@test.com',
            'first_name': 'New',
            'last_name': 'User',
            'membership': 'BASIC',
            'password1': 'StrongPass@99',
            'password2': 'DifferentPass@99',
        })
        self.assertFalse(form.is_valid())

    def test_registration_duplicate_email(self):
        make_member(email='existing@test.com')
        form = CustomUserCreationForm(data={
            'email': 'existing@test.com',
            'first_name': 'Dup',
            'last_name': 'User',
            'membership': 'BASIC',
            'password1': 'StrongPass@99',
            'password2': 'StrongPass@99',
        })
        self.assertFalse(form.is_valid())


class PrivacySettingsFormTest(TestCase):

    def setUp(self):
        self.member = make_member()

    def test_valid_privacy_form_public(self):
        form = PrivacySettingsForm(instance=self.member, data={
            'workout_visibility': 'PUBLIC',
        })
        self.assertTrue(form.is_valid())

    def test_valid_privacy_form_coach_only(self):
        form = PrivacySettingsForm(instance=self.member, data={
            'workout_visibility': 'COACH_ONLY',
        })
        self.assertTrue(form.is_valid())

    def test_invalid_privacy_form_bad_value(self):
        form = PrivacySettingsForm(instance=self.member, data={
            'workout_visibility': 'EVERYONE',  # not a valid choice
        })
        self.assertFalse(form.is_valid())


# ══════════════════════════════════════════════════
# NUTRITION PAGE TESTS
# ══════════════════════════════════════════════════

class NutritionViewTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.staff = make_staff()
        self.member = make_member()
        self.free_article = make_article(self.staff, title='Free Article', locked=False)
        self.locked_article = make_article(self.staff, title='Locked Article', locked=True)

    def test_nutrition_page_loads(self):
        response = self.client.get(reverse('nutrition'))
        self.assertEqual(response.status_code, 200)

    def test_free_articles_shown_to_all(self):
        response = self.client.get(reverse('nutrition'))
        self.assertContains(response, 'Free Article')

    def test_locked_article_in_context(self):
        response = self.client.get(reverse('nutrition'))
        locked = list(response.context['locked_articles'])
        self.assertIn(self.locked_article, locked)

    def test_free_article_in_context(self):
        response = self.client.get(reverse('nutrition'))
        free = list(response.context['free_articles'])
        self.assertIn(self.free_article, free)


# ══════════════════════════════════════════════════
# COACH ROLE REQUEST TESTS
# ══════════════════════════════════════════════════

class CoachRequestTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.member = make_member()

    def test_default_coach_request_status_is_none(self):
        self.assertEqual(self.member.coach_request_status, 'NONE')

    def test_submitting_request_sets_pending(self):
        self.client.force_login(self.member)
        self.client.post(reverse('settings'), {'coach_request_submit': '1'})
        self.member.refresh_from_db()
        self.assertEqual(self.member.coach_request_status, 'PENDING')


# ══════════════════════════════════════════════════
# PUBLIC PAGES TESTS
# ══════════════════════════════════════════════════

class PublicPageTest(TestCase):
    """All public-facing pages should load without authentication."""

    def setUp(self):
        self.client = Client()

    def test_home_page(self):
        self.assertEqual(self.client.get(reverse('home')).status_code, 200)

    def test_services_page(self):
        self.assertEqual(self.client.get(reverse('services')).status_code, 200)

    def test_memberships_page(self):
        self.assertEqual(self.client.get(reverse('memberships')).status_code, 200)

    def test_trainers_page(self):
        self.assertEqual(self.client.get(reverse('trainers')).status_code, 200)

    def test_nutrition_page(self):
        self.assertEqual(self.client.get(reverse('nutrition')).status_code, 200)

    def test_faq_page(self):
        self.assertEqual(self.client.get(reverse('faq')).status_code, 200)

    def test_policy_page(self):
        self.assertEqual(self.client.get(reverse('policy')).status_code, 200)

    def test_about_page(self):
        self.assertEqual(self.client.get(reverse('about')).status_code, 200)

    def test_contact_page(self):
        self.assertEqual(self.client.get(reverse('contact')).status_code, 200)

    def test_amenities_page(self):
        self.assertEqual(self.client.get(reverse('amenities')).status_code, 200)

    def test_schedule_page(self):
        self.assertEqual(self.client.get(reverse('schedule')).status_code, 200)

    def test_register_page(self):
        self.assertEqual(self.client.get(reverse('register')).status_code, 200)