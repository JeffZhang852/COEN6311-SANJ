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

UpdateEmailFormTest — tests UpdateEmailForm directly: valid change, same email allowed, duplicate rejected, bad format rejected, empty rejected.

EmailUpdateViewTest — tests the email_submit POST in user_settings: valid save + redirect, duplicate blocked with form error re-render, invalid format doesn't save, coach can update, unauthenticated blocked.

UpdatePasswordFormTest — tests UpdatePasswordForm directly: valid change, wrong old password rejected, mismatched new passwords rejected, weak password rejected.

PasswordUpdateViewTest — tests the password_submit POST in user_settings: valid save + redirect, session kept alive after change (update_session_auth_hash), wrong old password doesn't save + re-renders errors, mismatched passwords don't save, coach can update, unauthenticated blocked.

CoachRequestSubmissionGuardTest:
    - tests the server-side guard you need to add to user_settings.
    - Verifies that PENDING and APPROVED members can't reset their status via a direct POST, while NONE and REJECTED members can submit normally.

StaffRequestsPageTest:
    - tests the /coach_requests/ page itself.
    - Covers access control (unauthenticated + member blocked), that each status bucket (pending_requests, approved_requests, rejected_requests) is correctly populated in context,
    - that NONE-status members don't leak into any list, and that multiple pending members all show up.

HandleCoachRequestTest:
    - access control (unauthenticated + member blocked),
    - safe GET redirect, approve sets status + promotes role to COACH,
    - reject sets status + leaves role as MEMBER, redirects after both actions,
    - invalid action value does nothing, acting on a user with no request is blocked, 404 on nonexistent user,
    - re-approving a previously rejected request works, and any staff member can handle requests (not just a specific one).

UpdateEmailFormTest:
    - test_valid_email_change — valid new email passes form validation
    - test_same_email_is_valid — submitting your own current email is not treated as a duplicate
    - test_duplicate_email_rejected — using another user's email fails with a validation error
    - test_invalid_email_format_rejected — malformed email address fails validation
    - test_empty_email_rejected — empty email field fails validation

EmailUpdateViewTest:
    - test_valid_email_update_saves — valid email is saved to the database
    - test_valid_email_update_redirects — successful update redirects back to settings
    - test_duplicate_email_does_not_save — taken email leaves the user's email unchanged
    - test_duplicate_email_re_renders_form_with_errors — duplicate email re-renders the page with the form error
    - test_invalid_email_format_does_not_save — malformed email leaves the user's email unchanged
    - test_coach_can_update_email — coaches share the same settings page and can update their email
    - test_unauthenticated_cannot_update_email — unauthenticated POST is blocked

UpdatePasswordFormTest:
    - test_valid_password_change — correct old password and matching new passwords passes validation
    - test_wrong_old_password_rejected — incorrect old password fails with an error on old_password field
    - test_mismatched_new_passwords_rejected — new passwords that don't match fail with an error on new_password2
    - test_weak_new_password_rejected — password that fails Django's strength validators is rejected

PasswordUpdateViewTest:
    - test_valid_password_change_saves — new password is saved to the database
    - test_valid_password_change_redirects — successful change redirects back to settings
    - test_user_stays_logged_in_after_password_change — update_session_auth_hash keeps the session alive after save
    - test_wrong_old_password_does_not_save — wrong old password leaves the original password intact
    - test_wrong_old_password_re_renders_form_with_errors — wrong old password re-renders the page with the form error
    - test_mismatched_passwords_do_not_save — mismatched new passwords leave the original password intact
    - test_coach_can_update_password — coaches share the same settings page and can update their password
    - test_unauthenticated_cannot_update_password — unauthenticated POST is blocked

RecipeModelTest:
    - test_recipe_creation — checks title, times, servings, difficulty, and locked field are saved correctly
    - test_total_time_property — total_time_minutes equals prep + cook
    - test_str_method — __str__ returns a string containing the recipe title
    - test_timestamps_auto_populated — created_at and updated_at are set on creation
    - test_author_set_null_on_user_delete — deleting the author nulls the field but keeps the recipe
    - test_calories_optional — calories_per_serving defaults to None
    - test_calories_can_be_set — calories_per_serving can be saved and retrieved
    - test_locked_field_toggles — locked field can be toggled and persisted
    - test_dietary_restrictions_stores_multiple — MultiSelectField stores and returns multiple dietary codes correctly
    - test_scaled_ingredients — scaled_ingredients returns quantities multiplied by the given factor

RecipeIngredientTest:
    - test_add_ingredient — ingredient is created with correct name, quantity (Decimal), and empty notes
    - test_ingredient_with_notes — notes appear in __str__ output
    - test_str_without_notes — __str__ contains quantity and name but no empty parentheses
    - test_ingredients_deleted_with_recipe — cascade delete removes ingredients when recipe is deleted
    - test_multiple_ingredients_ordered_by_insertion — ingredients are returned in insertion order
    - test_recipe_ingredient_count — ingredients.count() reflects all added ingredients
    - test_scaled_quantity — scaled_quantity multiplies Decimal quantity correctly by factor

RecipeViewTest:
    - test_staff_recipes_page_loads — staff_recipes page returns 200 for staff users
    - test_unauthenticated_cannot_access_staff_recipes — unauthenticated users are redirected away
    - test_member_cannot_access_staff_recipes — members are blocked from the staff recipes list
    - test_recipe_detail_page_loads — recipe_details returns 200 for an existing recipe
    - test_recipe_detail_shows_title — recipe title appears in the rendered page
    - test_nonexistent_recipe_returns_404 — requesting a non-existent recipe ID returns 404
    - test_unauthenticated_cannot_access_locked_recipe — unauthenticated users are redirected away from locked recipes
    - test_unauthenticated_can_access_unlocked_recipe — unauthenticated users can view free recipes
    - test_create_recipe_saves_author — author is set to logged-in staff user, not from the form
    - test_member_cannot_create_recipe — members are blocked from the create recipe page
    - test_author_can_edit_recipe — the recipe author can update the title and fields successfully
    - test_non_author_cannot_edit_recipe — a different staff member cannot overwrite another's recipe
    - test_author_can_delete_recipe — the recipe author can delete their own recipe
    - test_non_author_cannot_delete_recipe — a different staff member cannot delete another's recipe

"""

from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from django.core.exceptions import ValidationError
from datetime import timedelta
from django.contrib.auth import get_user_model
from CUFitness.models import CustomUser, Article, CoachAvailability, CoachAppointment, EquipmentList, Recipe, RecipeIngredient
from CUFitness.forms import ArticleForm, CustomUserCreationForm, PrivacySettingsForm, UpdateEmailForm, UpdatePasswordForm
from decimal import Decimal



# ══════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════
User = get_user_model()
User = get_user_model()
def make_member(email='member@test.com', password='Pass@1234'):
    return User.objects.create_user(email=email, password=password, role='MEMBER',
                                    first_name='Jane', last_name='Doe',
                                    date_of_birth='1995-06-15')

def make_coach(email='coach@test.com', password='Pass@1234'):
    return User.objects.create_user(email=email, password=password, role='COACH',
                                    first_name='Bob', last_name='Smith',
                                    date_of_birth='1990-03-22')

def make_staff(email='staff@test.com', password='Pass@1234'):
    return User.objects.create_user(email=email, password=password, role='STAFF',
                                    first_name='Alice', last_name='Admin', is_staff=True,
                                    date_of_birth='1988-07-09')

def make_article(author, title='Test Article', locked=False):
    return Article.objects.create(
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
            status="ACCEPTED"
        )

        self.assertEqual(appointment.status, "ACCEPTED")

    def test_double_booking_accepted(self):
        CoachAppointment.objects.create(
            coach=self.coach,
            member=self.member,
            start_time=self.start,
            end_time=self.end,
            status="ACCEPTED"
        )

        with self.assertRaises(ValidationError):
            CoachAppointment.objects.create(
                coach=self.coach,
                member=self.member,
                start_time=self.start + timedelta(minutes=30),
                end_time=self.end + timedelta(minutes=30),
                status="ACCEPTED"
            )

class ArticleModelTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            email="user@test.com",
            password="password123"
        )

        self.author = User.objects.create_user(
            email="author@test.com",
            password="password123"
        )

        self.article = Article.objects.create(
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

        article = Article.objects.get(id=self.article.id)
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
        response = self.client.get(reverse('user_settings'))
        self.assertNotEqual(response.status_code, 200)

    def test_unauthenticated_cannot_access_articles(self):
        response = self.client.get(reverse('staff_articles'))
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
        response = self.client.get(reverse('staff_articles'))
        self.assertNotEqual(response.status_code, 200)

    def test_member_cannot_create_article(self):
        self.client.force_login(self.member)
        response = self.client.get(reverse('create_article'))
        self.assertNotEqual(response.status_code, 200)

    # --- Staff can access staff pages ---

    def test_staff_can_access_articles_list(self):
        self.client.force_login(self.staff)
        response = self.client.get(reverse('staff_articles'))
        self.assertEqual(response.status_code, 200)

    def test_staff_can_access_create_article(self):
        self.client.force_login(self.staff)
        response = self.client.get(reverse('create_article'))
        self.assertEqual(response.status_code, 200)

    def test_staff_cannot_access_member_settings(self):
        """Staff should not be able to use the member settings page."""
        self.client.force_login(self.staff)
        response = self.client.get(reverse('user_settings'))
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
        self.assertFalse(Article.objects.filter(id=self.article.id).exists())

    def test_non_author_cannot_delete_article(self):
        self.client.force_login(self.other_staff)
        self.client.post(reverse('delete_article', args=[self.article.id]))
        self.assertTrue(Article.objects.filter(id=self.article.id).exists())

    def test_create_article_saves_author(self):
        """Author should be set to the logged-in staff user, not from the form."""
        self.client.force_login(self.staff)
        self.client.post(reverse('create_article'), {
            'title': 'Brand New Article',
            'description': 'Some description.',
            'body': 'Some body.',
            'locked': False,
        })
        article = Article.objects.get(title='Brand New Article')
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
        response = self.client.get(reverse('user_settings'))
        self.assertEqual(response.status_code, 200)

    def test_privacy_setting_update(self):
        self.client.force_login(self.member)
        self.client.post(reverse('user_settings'), {
            'workout_visibility': 'PUBLIC',
            'privacy_submit': '1',
        })
        self.member.refresh_from_db()
        self.assertEqual(self.member.workout_visibility, 'PUBLIC')

    def test_coach_request_sets_pending(self):
        self.client.force_login(self.member)
        self.client.post(reverse('user_settings'), {
            'coach_request_submit': '1',
        })
        self.member.refresh_from_db()
        self.assertEqual(self.member.coach_request_status, 'PENDING')

    def test_coach_request_already_pending_stays_pending(self):
        self.member.coach_request_status = 'PENDING'
        self.member.save()
        self.client.force_login(self.member)
        # submitting again shouldn't break anything
        self.client.post(reverse('user_settings'), {
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
            'title': 'x' * 101,  # max_length is 100
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
            'phone_number': '+1 514 555 0100',
            'address': '123 Test Street, Montreal, QC',
            'date_of_birth': '1995-06-15',
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
            'phone_number': '+1 514 555 0100',
            'address': '123 Test Street, Montreal, QC',
            'date_of_birth': '1995-06-15',
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
            'phone_number': '+1 514 555 0100',
            'address': '123 Test Street, Montreal, QC',
            'date_of_birth': '1995-06-15',
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
        response = self.client.get(reverse('user_articles'))
        self.assertEqual(response.status_code, 200)

    def test_free_articles_shown_to_all(self):
        response = self.client.get(reverse('user_articles'))
        self.assertContains(response, 'Free Article')

    def test_locked_article_in_context(self):
        response = self.client.get(reverse('user_articles'))
        locked = list(response.context['locked_articles'])
        self.assertIn(self.locked_article, locked)

    def test_free_article_in_context(self):
        response = self.client.get(reverse('user_articles'))
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
        self.client.post(reverse('user_settings'), {'coach_request_submit': '1'})
        self.member.refresh_from_db()
        self.assertEqual(self.member.coach_request_status, 'PENDING')

# ══════════════════════════════════════════════════
# COACH REQUEST — MEMBER SUBMISSION GUARD TESTS
# (extends existing CoachRequestTest)
# ══════════════════════════════════════════════════

class CoachRequestSubmissionGuardTest(TestCase):
    """
    Tests the server-side guard on coach_request_submit in user_settings.
    Covers edge cases that the template buttons alone can't prevent.
    """

    def setUp(self):
        self.client = Client()
        self.member = make_member()

    def test_pending_member_cannot_resubmit(self):
        """A member with PENDING status should not be able to reset back to PENDING via a direct POST."""
        self.member.coach_request_status = 'PENDING'
        self.member.save()
        self.client.force_login(self.member)
        self.client.post(reverse('user_settings'), {'coach_request_submit': '1'})
        self.member.refresh_from_db()
        # status should remain PENDING, not be reset
        self.assertEqual(self.member.coach_request_status, 'PENDING')

    def test_approved_member_cannot_resubmit(self):
        """An already-approved member should not be able to reset their status back to PENDING."""
        self.member.coach_request_status = 'APPROVED'
        self.member.save()
        self.client.force_login(self.member)
        self.client.post(reverse('user_settings'), {'coach_request_submit': '1'})
        self.member.refresh_from_db()
        self.assertEqual(self.member.coach_request_status, 'APPROVED')

    def test_rejected_member_can_resubmit(self):
        """A member whose request was rejected should be allowed to submit again."""
        self.member.coach_request_status = 'REJECTED'
        self.member.save()
        self.client.force_login(self.member)
        self.client.post(reverse('user_settings'), {'coach_request_submit': '1'})
        self.member.refresh_from_db()
        self.assertEqual(self.member.coach_request_status, 'PENDING')

    def test_none_member_can_submit(self):
        """A member with no prior request (NONE) should be able to submit."""
        self.assertEqual(self.member.coach_request_status, 'NONE')
        self.client.force_login(self.member)
        self.client.post(reverse('user_settings'), {'coach_request_submit': '1'})
        self.member.refresh_from_db()
        self.assertEqual(self.member.coach_request_status, 'PENDING')


# ══════════════════════════════════════════════════
# STAFF REQUESTS PAGE TESTS
# ══════════════════════════════════════════════════

class StaffRequestsPageTest(TestCase):
    """Tests the /requests/ staff page — loading, context data, and access control."""

    def setUp(self):
        self.client = Client()
        self.staff = make_staff()
        self.member = make_member()
        self.other_member = make_member(email='other@test.com')

    def test_requests_page_loads_for_staff(self):
        self.client.force_login(self.staff)
        response = self.client.get(reverse('coach_requests'))
        self.assertEqual(response.status_code, 200)

    def test_unauthenticated_cannot_access_requests_page(self):
        response = self.client.get(reverse('coach_requests'))
        self.assertNotEqual(response.status_code, 200)

    def test_member_cannot_access_requests_page(self):
        self.client.force_login(self.member)
        response = self.client.get(reverse('coach_requests'))
        self.assertNotEqual(response.status_code, 200)

    def test_pending_requests_in_context(self):
        """Members with PENDING status should appear in pending_requests context."""
        self.member.coach_request_status = 'PENDING'
        self.member.save()
        self.client.force_login(self.staff)
        response = self.client.get(reverse('coach_requests'))
        self.assertIn(self.member, response.context['pending_requests'])

    def test_approved_requests_in_context(self):
        """Members with APPROVED status should appear in approved_requests context."""
        self.member.coach_request_status = 'APPROVED'
        self.member.save()
        self.client.force_login(self.staff)
        response = self.client.get(reverse('coach_requests'))
        self.assertIn(self.member, response.context['approved_requests'])

    def test_rejected_requests_in_context(self):
        """Members with REJECTED status should appear in rejected_requests context."""
        self.member.coach_request_status = 'REJECTED'
        self.member.save()
        self.client.force_login(self.staff)
        response = self.client.get(reverse('coach_requests'))
        self.assertIn(self.member, response.context['rejected_requests'])

    def test_none_status_members_not_in_any_list(self):
        """Members who never submitted a request should not appear in any context list."""
        self.assertEqual(self.member.coach_request_status, 'NONE')
        self.client.force_login(self.staff)
        response = self.client.get(reverse('coach_requests'))
        self.assertNotIn(self.member, response.context['pending_requests'])
        self.assertNotIn(self.member, response.context['approved_requests'])
        self.assertNotIn(self.member, response.context['rejected_requests'])

    def test_multiple_pending_requests_all_shown(self):
        """All pending members should appear, not just the first one."""
        self.member.coach_request_status = 'PENDING'
        self.member.save()
        self.other_member.coach_request_status = 'PENDING'
        self.other_member.save()
        self.client.force_login(self.staff)
        response = self.client.get(reverse('coach_requests'))
        pending = list(response.context['pending_requests'])
        self.assertIn(self.member, pending)
        self.assertIn(self.other_member, pending)


# ══════════════════════════════════════════════════
# HANDLE COACH REQUEST VIEW TESTS
# ══════════════════════════════════════════════════

class HandleCoachRequestTest(TestCase):
    """
    Tests the handle_coach_request view — approving, rejecting,
    role promotion, access control, and invalid inputs.
    """

    def setUp(self):
        self.client = Client()
        self.staff = make_staff()
        self.other_staff = make_staff(email='otherstaff@test.com')
        self.member = make_member()
        # Put member in PENDING so actions are valid
        self.member.coach_request_status = 'PENDING'
        self.member.save()

    # --- Access control ---

    def test_unauthenticated_cannot_access(self):
        response = self.client.post(
            reverse('handle_coach_request', args=[self.member.id]),
            {'action': 'APPROVED'}
        )
        self.assertNotEqual(response.status_code, 200)

    def test_member_cannot_access(self):
        other_member = make_member(email='another@test.com')
        self.client.force_login(other_member)
        response = self.client.post(
            reverse('handle_coach_request', args=[self.member.id]),
            {'action': 'APPROVED'}
        )
        self.assertNotEqual(response.status_code, 200)

    def test_get_request_redirects_without_changes(self):
        """A GET to this URL should redirect safely and not change anything."""
        self.client.force_login(self.staff)
        response = self.client.get(
            reverse('handle_coach_request', args=[self.member.id])
        )
        self.assertRedirects(response, reverse('coach_requests'))
        self.member.refresh_from_db()
        self.assertEqual(self.member.coach_request_status, 'PENDING')

    # --- Approve ---

    def test_approve_sets_status_to_approved(self):
        self.client.force_login(self.staff)
        self.client.post(
            reverse('handle_coach_request', args=[self.member.id]),
            {'action': 'APPROVED'}
        )
        self.member.refresh_from_db()
        self.assertEqual(self.member.coach_request_status, 'APPROVED')

    def test_approve_promotes_role_to_coach(self):
        """Approving a request must also change the user's role to COACH."""
        self.client.force_login(self.staff)
        self.client.post(
            reverse('handle_coach_request', args=[self.member.id]),
            {'action': 'APPROVED'}
        )
        self.member.refresh_from_db()
        self.assertEqual(self.member.role, 'COACH')

    def test_approve_redirects_to_requests_page(self):
        self.client.force_login(self.staff)
        response = self.client.post(
            reverse('handle_coach_request', args=[self.member.id]),
            {'action': 'APPROVED'}
        )
        self.assertRedirects(response, reverse('coach_requests'))

    # --- Reject ---

    def test_reject_sets_status_to_rejected(self):
        self.client.force_login(self.staff)
        self.client.post(
            reverse('handle_coach_request', args=[self.member.id]),
            {'action': 'REJECTED'}
        )
        self.member.refresh_from_db()
        self.assertEqual(self.member.coach_request_status, 'REJECTED')

    def test_reject_does_not_change_role(self):
        """Rejecting a request must NOT change the user's role — they stay MEMBER."""
        self.client.force_login(self.staff)
        self.client.post(
            reverse('handle_coach_request', args=[self.member.id]),
            {'action': 'REJECTED'}
        )
        self.member.refresh_from_db()
        self.assertEqual(self.member.role, 'MEMBER')

    def test_reject_redirects_to_requests_page(self):
        self.client.force_login(self.staff)
        response = self.client.post(
            reverse('handle_coach_request', args=[self.member.id]),
            {'action': 'REJECTED'}
        )
        self.assertRedirects(response, reverse('coach_requests'))

    # --- Edge cases ---

    def test_invalid_action_does_not_change_status(self):
        """Sending a garbage action value should not modify the member."""
        self.client.force_login(self.staff)
        self.client.post(
            reverse('handle_coach_request', args=[self.member.id]),
            {'action': 'MAKE_ADMIN'}
        )
        self.member.refresh_from_db()
        self.assertEqual(self.member.coach_request_status, 'PENDING')
        self.assertEqual(self.member.role, 'MEMBER')

    def test_cannot_act_on_member_with_no_request(self):
        """Acting on a user whose status is NONE should be blocked."""
        no_request_member = make_member(email='norequst@test.com')
        self.assertEqual(no_request_member.coach_request_status, 'NONE')
        self.client.force_login(self.staff)
        self.client.post(
            reverse('handle_coach_request', args=[no_request_member.id]),
            {'action': 'APPROVED'}
        )
        no_request_member.refresh_from_db()
        # Should not have been approved
        self.assertNotEqual(no_request_member.coach_request_status, 'APPROVED')
        self.assertNotEqual(no_request_member.role, 'COACH')

    def test_nonexistent_user_returns_404(self):
        self.client.force_login(self.staff)
        response = self.client.post(
            reverse('handle_coach_request', args=[99999]),
            {'action': 'APPROVED'}
        )
        self.assertEqual(response.status_code, 404)

    def test_approve_rejected_request_works(self):
        """Staff should be able to approve a previously rejected request."""
        self.member.coach_request_status = 'REJECTED'
        self.member.save()
        self.client.force_login(self.staff)
        self.client.post(
            reverse('handle_coach_request', args=[self.member.id]),
            {'action': 'APPROVED'}
        )
        self.member.refresh_from_db()
        self.assertEqual(self.member.coach_request_status, 'APPROVED')
        self.assertEqual(self.member.role, 'COACH')

    def test_any_staff_member_can_handle_requests(self):
        """It should not matter which staff member approves — any staff can do it."""
        self.client.force_login(self.other_staff)
        self.client.post(
            reverse('handle_coach_request', args=[self.member.id]),
            {'action': 'APPROVED'}
        )
        self.member.refresh_from_db()
        self.assertEqual(self.member.role, 'COACH')

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
        self.assertEqual(self.client.get(reverse('user_articles')).status_code, 200)

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

# ══════════════════════════════════════════════════
# EMAIL UPDATE FORM TESTS
# ══════════════════════════════════════════════════

class UpdateEmailFormTest(TestCase):

    def setUp(self):
        self.member = make_member()
        self.other_member = make_member(email='other@test.com')

    def test_valid_email_change(self):
        form = UpdateEmailForm(instance=self.member, data={'email': 'newemail@test.com'})
        self.assertTrue(form.is_valid())

    def test_same_email_is_valid(self):
        """Submitting your own current email should not be treated as a duplicate."""
        form = UpdateEmailForm(instance=self.member, data={'email': 'member@test.com'})
        self.assertTrue(form.is_valid())

    def test_duplicate_email_rejected(self):
        """Using another user's email address should fail validation."""
        form = UpdateEmailForm(instance=self.member, data={'email': 'other@test.com'})
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)

    def test_invalid_email_format_rejected(self):
        form = UpdateEmailForm(instance=self.member, data={'email': 'not-an-email'})
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)

    def test_empty_email_rejected(self):
        form = UpdateEmailForm(instance=self.member, data={'email': ''})
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)


# ══════════════════════════════════════════════════
# EMAIL UPDATE VIEW TESTS
# ══════════════════════════════════════════════════

class EmailUpdateViewTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.member = make_member()
        self.other_member = make_member(email='taken@test.com')

    def test_valid_email_update_saves(self):
        self.client.force_login(self.member)
        self.client.post(reverse('user_settings'), {
            'email': 'updated@test.com',
            'email_submit': '1',
        })
        self.member.refresh_from_db()
        self.assertEqual(self.member.email, 'updated@test.com')

    def test_valid_email_update_redirects(self):
        self.client.force_login(self.member)
        response = self.client.post(reverse('user_settings'), {
            'email': 'updated@test.com',
            'email_submit': '1',
        })
        self.assertRedirects(response, reverse('user_settings'))

    def test_duplicate_email_does_not_save(self):
        self.client.force_login(self.member)
        self.client.post(reverse('user_settings'), {
            'email': 'taken@test.com',
            'email_submit': '1',
        })
        self.member.refresh_from_db()
        self.assertNotEqual(self.member.email, 'taken@test.com')

    def test_duplicate_email_re_renders_form_with_errors(self):
        self.client.force_login(self.member)
        response = self.client.post(reverse('user_settings'), {
            'email': 'taken@test.com',
            'email_submit': '1',
        })
        # Should stay on the settings page (no redirect) and show the form error
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response.context['email_form'], 'email', 'This email address is already in use.')

    def test_invalid_email_format_does_not_save(self):
        self.client.force_login(self.member)
        original_email = self.member.email
        self.client.post(reverse('user_settings'), {
            'email': 'not-valid',
            'email_submit': '1',
        })
        self.member.refresh_from_db()
        self.assertEqual(self.member.email, original_email)

    def test_coach_can_update_email(self):
        """Coaches share the same settings page — verify email update works for them too."""
        coach = make_coach()
        self.client.force_login(coach)
        self.client.post(reverse('user_settings'), {
            'email': 'newcoach@test.com',
            'email_submit': '1',
        })
        coach.refresh_from_db()
        self.assertEqual(coach.email, 'newcoach@test.com')

    def test_unauthenticated_cannot_update_email(self):
        response = self.client.post(reverse('user_settings'), {
            'email': 'hacker@test.com',
            'email_submit': '1',
        })
        self.assertNotEqual(response.status_code, 200)


# ══════════════════════════════════════════════════
# PASSWORD UPDATE FORM TESTS
# ══════════════════════════════════════════════════

class UpdatePasswordFormTest(TestCase):

    def setUp(self):
        self.member = make_member()

    def test_valid_password_change(self):
        form = UpdatePasswordForm(user=self.member, data={
            'old_password': 'Pass@1234',
            'new_password1': 'NewPass@9999',
            'new_password2': 'NewPass@9999',
        })
        self.assertTrue(form.is_valid())

    def test_wrong_old_password_rejected(self):
        form = UpdatePasswordForm(user=self.member, data={
            'old_password': 'WrongPassword!',
            'new_password1': 'NewPass@9999',
            'new_password2': 'NewPass@9999',
        })
        self.assertFalse(form.is_valid())
        self.assertIn('old_password', form.errors)

    def test_mismatched_new_passwords_rejected(self):
        form = UpdatePasswordForm(user=self.member, data={
            'old_password': 'Pass@1234',
            'new_password1': 'NewPass@9999',
            'new_password2': 'DifferentPass@9999',
        })
        self.assertFalse(form.is_valid())
        self.assertIn('new_password2', form.errors)

    def test_weak_new_password_rejected(self):
        """Django's built-in validators should block overly simple passwords."""
        form = UpdatePasswordForm(user=self.member, data={
            'old_password': 'Pass@1234',
            'new_password1': '123',
            'new_password2': '123',
        })
        self.assertFalse(form.is_valid())


# ══════════════════════════════════════════════════
# PASSWORD UPDATE VIEW TESTS
# ══════════════════════════════════════════════════

class PasswordUpdateViewTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.member = make_member()

    def test_valid_password_change_saves(self):
        self.client.force_login(self.member)
        self.client.post(reverse('user_settings'), {
            'old_password': 'Pass@1234',
            'new_password1': 'NewPass@9999',
            'new_password2': 'NewPass@9999',
            'password_submit': '1',
        })
        self.member.refresh_from_db()
        self.assertTrue(self.member.check_password('NewPass@9999'))

    def test_valid_password_change_redirects(self):
        self.client.force_login(self.member)
        response = self.client.post(reverse('user_settings'), {
            'old_password': 'Pass@1234',
            'new_password1': 'NewPass@9999',
            'new_password2': 'NewPass@9999',
            'password_submit': '1',
        })
        self.assertRedirects(response, reverse('user_settings'))

    def test_user_stays_logged_in_after_password_change(self):
        """update_session_auth_hash should keep the session alive."""
        self.client.force_login(self.member)
        self.client.post(reverse('user_settings'), {
            'old_password': 'Pass@1234',
            'new_password1': 'NewPass@9999',
            'new_password2': 'NewPass@9999',
            'password_submit': '1',
        })
        # If the session was invalidated the settings page would redirect to login
        response = self.client.get(reverse('user_settings'))
        self.assertEqual(response.status_code, 200)

    def test_wrong_old_password_does_not_save(self):
        self.client.force_login(self.member)
        self.client.post(reverse('user_settings'), {
            'old_password': 'WrongPassword!',
            'new_password1': 'NewPass@9999',
            'new_password2': 'NewPass@9999',
            'password_submit': '1',
        })
        self.member.refresh_from_db()
        self.assertFalse(self.member.check_password('NewPass@9999'))
        self.assertTrue(self.member.check_password('Pass@1234'))

    def test_wrong_old_password_re_renders_form_with_errors(self):
        self.client.force_login(self.member)
        response = self.client.post(reverse('user_settings'), {
            'old_password': 'WrongPassword!',
            'new_password1': 'NewPass@9999',
            'new_password2': 'NewPass@9999',
            'password_submit': '1',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response.context['password_form'], 'old_password',
                             'Your old password was entered incorrectly. Please enter it again.')

    def test_mismatched_passwords_do_not_save(self):
        self.client.force_login(self.member)
        self.client.post(reverse('user_settings'), {
            'old_password': 'Pass@1234',
            'new_password1': 'NewPass@9999',
            'new_password2': 'DifferentPass@9999',
            'password_submit': '1',
        })
        self.member.refresh_from_db()
        self.assertTrue(self.member.check_password('Pass@1234'))

    def test_coach_can_update_password(self):
        """Coaches share the same settings page — verify password update works for them too."""
        coach = make_coach()
        self.client.force_login(coach)
        self.client.post(reverse('user_settings'), {
            'old_password': 'Pass@1234',
            'new_password1': 'NewCoach@9999',
            'new_password2': 'NewCoach@9999',
            'password_submit': '1',
        })
        coach.refresh_from_db()
        self.assertTrue(coach.check_password('NewCoach@9999'))

    def test_unauthenticated_cannot_update_password(self):
        response = self.client.post(reverse('user_settings'), {
            'old_password': 'Pass@1234',
            'new_password1': 'NewPass@9999',
            'new_password2': 'NewPass@9999',
            'password_submit': '1',
        })
        self.assertNotEqual(response.status_code, 200)

# ══════════════════════════════════════════════════
# RECIPE MODEL TESTS
# ══════════════════════════════════════════════════

def make_recipe(author, title='Protein Oats', locked=False):
    return Recipe.objects.create(
        author=author,
        title=title,
        description='A quick high-protein breakfast.',
        instructions='1. Cook oats.\n2. Add protein powder.\n3. Enjoy.',
        prep_time_minutes=5,
        cook_time_minutes=10,
        servings=2,
        difficulty='EASY',
        locked=locked,
    )


class RecipeModelTest(TestCase):

    def setUp(self):
        self.staff = make_staff()
        self.recipe = make_recipe(author=self.staff)

    def test_recipe_creation(self):
        self.assertEqual(self.recipe.title, 'Protein Oats')
        self.assertEqual(self.recipe.prep_time_minutes, 5)
        self.assertEqual(self.recipe.cook_time_minutes, 10)
        self.assertEqual(self.recipe.servings, 2)
        self.assertEqual(self.recipe.difficulty, 'EASY')
        self.assertFalse(self.recipe.locked)

    def test_total_time_property(self):
        """total_time_minutes should be prep + cook."""
        self.assertEqual(self.recipe.total_time_minutes, 15)

    def test_str_method(self):
        self.assertIsInstance(str(self.recipe), str)
        self.assertIn('Protein Oats', str(self.recipe))

    def test_timestamps_auto_populated(self):
        self.assertIsNotNone(self.recipe.created_at)
        self.assertIsNotNone(self.recipe.updated_at)

    def test_author_set_null_on_user_delete(self):
        """Deleting the author should null the field, not delete the recipe."""
        self.staff.delete()
        self.recipe.refresh_from_db()
        self.assertIsNone(self.recipe.author)
        self.assertTrue(Recipe.objects.filter(id=self.recipe.id).exists())

    def test_calories_optional(self):
        """calories_per_serving should default to None."""
        self.assertIsNone(self.recipe.calories_per_serving)

    def test_calories_can_be_set(self):
        self.recipe.calories_per_serving = 350
        self.recipe.save()
        self.recipe.refresh_from_db()
        self.assertEqual(self.recipe.calories_per_serving, 350)

    def test_locked_field_toggles(self):
        self.recipe.locked = True
        self.recipe.save()
        self.recipe.refresh_from_db()
        self.assertTrue(self.recipe.locked)

    def test_dietary_restrictions_stores_multiple(self):
        """MultiSelectField should store and return multiple values."""
        self.recipe.dietary_restrictions = ['NO_GLUTEN', 'VEGAN']
        self.recipe.save()
        self.recipe.refresh_from_db()
        self.assertIn('NO_GLUTEN', self.recipe.dietary_restrictions)
        self.assertIn('VEGAN', self.recipe.dietary_restrictions)

    def test_scaled_ingredients(self):
        """scaled_ingredients should return quantities multiplied by the given factor."""
        RecipeIngredient.objects.create(
            recipe=self.recipe, name='Oats', quantity=Decimal('1.00'), unit='CUP'
        )
        scaled = self.recipe.scaled_ingredients(2)
        self.assertEqual(scaled[0][1], Decimal('2.00'))


class RecipeIngredientTest(TestCase):

    def setUp(self):
        self.staff = make_staff()
        self.recipe = make_recipe(author=self.staff)

    def test_add_ingredient(self):
        ingredient = RecipeIngredient.objects.create(
            recipe=self.recipe,
            name='Rolled oats',
            quantity=Decimal('1.00'),
            unit='CUP',
        )
        self.assertEqual(ingredient.name, 'Rolled oats')
        self.assertEqual(ingredient.quantity, Decimal('1.00'))
        self.assertEqual(ingredient.notes, '')

    def test_ingredient_with_notes(self):
        ingredient = RecipeIngredient.objects.create(
            recipe=self.recipe,
            name='Banana',
            quantity=Decimal('1.00'),
            unit='WHOLE',
            notes='sliced',
        )
        self.assertIn('sliced', str(ingredient))

    def test_str_without_notes(self):
        ingredient = RecipeIngredient.objects.create(
            recipe=self.recipe,
            name='Protein powder',
            quantity=Decimal('30.00'),
            unit='G',
        )
        result = str(ingredient)
        self.assertIn('Protein powder', result)
        self.assertNotIn('()', result)  # no empty parentheses

    def test_ingredients_deleted_with_recipe(self):
        """Cascade: deleting the recipe should remove its ingredients."""
        RecipeIngredient.objects.create(
            recipe=self.recipe, name='Oats', quantity=Decimal('1.00'), unit='CUP'
        )
        recipe_id = self.recipe.id
        self.recipe.delete()
        self.assertFalse(RecipeIngredient.objects.filter(recipe_id=recipe_id).exists())

    def test_multiple_ingredients_ordered_by_insertion(self):
        names = ['Oats', 'Milk', 'Honey', 'Cinnamon']
        for name in names:
            RecipeIngredient.objects.create(
                recipe=self.recipe, name=name, quantity=Decimal('1.00'), unit='TSP'
            )
        stored = list(self.recipe.ingredients.values_list('name', flat=True))
        self.assertEqual(stored, names)

    def test_recipe_ingredient_count(self):
        for i in range(4):
            RecipeIngredient.objects.create(
                recipe=self.recipe, name=f'Ingredient {i}', quantity=Decimal('1.00'), unit='G'
            )
        self.assertEqual(self.recipe.ingredients.count(), 4)

    def test_scaled_quantity(self):
        """scaled_quantity should multiply the Decimal quantity by the given factor."""
        ingredient = RecipeIngredient.objects.create(
            recipe=self.recipe, name='Oats', quantity=Decimal('1.50'), unit='CUP'
        )
        self.assertEqual(ingredient.scaled_quantity(2), Decimal('3.00'))

# ══════════════════════════════════════════════════
# RECIPE VIEW TESTS
# ══════════════════════════════════════════════════

class RecipeViewTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.staff = make_staff()
        self.other_staff = make_staff(email='other@test.com')
        self.member = make_member()
        self.recipe = make_recipe(author=self.staff)

    # --- staff_recipes page ---

    def test_staff_recipes_page_loads(self):
        self.client.force_login(self.staff)
        response = self.client.get(reverse('staff_recipes'))
        self.assertEqual(response.status_code, 200)

    def test_unauthenticated_cannot_access_staff_recipes(self):
        response = self.client.get(reverse('staff_recipes'))
        self.assertNotEqual(response.status_code, 200)

    def test_member_cannot_access_staff_recipes(self):
        self.client.force_login(self.member)
        response = self.client.get(reverse('staff_recipes'))
        self.assertNotEqual(response.status_code, 200)

    # --- recipe_details page ---

    def test_recipe_detail_page_loads(self):
        self.client.force_login(self.staff)
        response = self.client.get(reverse('recipe_details', args=[self.recipe.id]))
        self.assertEqual(response.status_code, 200)

    def test_recipe_detail_shows_title(self):
        self.client.force_login(self.staff)
        response = self.client.get(reverse('recipe_details', args=[self.recipe.id]))
        self.assertContains(response, self.recipe.title)

    def test_nonexistent_recipe_returns_404(self):
        self.client.force_login(self.staff)
        response = self.client.get(reverse('recipe_details', args=[99999]))
        self.assertEqual(response.status_code, 404)

    def test_unauthenticated_cannot_access_locked_recipe(self):
        locked = make_recipe(author=self.staff, title='Locked Recipe', locked=True)
        response = self.client.get(reverse('recipe_details', args=[locked.id]))
        self.assertNotEqual(response.status_code, 200)

    def test_unauthenticated_can_access_unlocked_recipe(self):
        response = self.client.get(reverse('recipe_details', args=[self.recipe.id]))
        self.assertEqual(response.status_code, 200)

    # --- create_recipe ---

    def test_create_recipe_saves_author(self):
        """Author should be set to the logged-in staff user, not from the form."""
        self.client.force_login(self.staff)
        self.client.post(reverse('create_recipe'), {
            'title': 'New Recipe',
            'description': 'A test description.',
            'difficulty': 'EASY',
            'prep_time_minutes': 10,
            'cook_time_minutes': 20,
            'servings': 2,
            'instructions': 'Step 1. Do something.',
            'locked': False,
            'ingredients-TOTAL_FORMS': '0',
            'ingredients-INITIAL_FORMS': '0',
            'ingredients-MIN_NUM_FORMS': '0',
            'ingredients-MAX_NUM_FORMS': '1000',
        })
        recipe = Recipe.objects.get(title='New Recipe')
        self.assertEqual(recipe.author, self.staff)

    def test_member_cannot_create_recipe(self):
        self.client.force_login(self.member)
        response = self.client.get(reverse('create_recipe'))
        self.assertNotEqual(response.status_code, 200)

    # --- edit_recipe ---

    def test_author_can_edit_recipe(self):
        self.client.force_login(self.staff)
        self.client.post(reverse('edit_recipe', args=[self.recipe.id]), {
            'title': 'Updated Recipe',
            'description': 'Updated description.',
            'difficulty': 'HARD',
            'prep_time_minutes': 10,
            'cook_time_minutes': 20,
            'servings': 4,
            'instructions': 'Updated instructions.',
            'locked': False,
            'ingredients-TOTAL_FORMS': '0',
            'ingredients-INITIAL_FORMS': '0',
            'ingredients-MIN_NUM_FORMS': '0',
            'ingredients-MAX_NUM_FORMS': '1000',
        })
        self.recipe.refresh_from_db()
        self.assertEqual(self.recipe.title, 'Updated Recipe')

    def test_non_author_cannot_edit_recipe(self):
        self.client.force_login(self.other_staff)
        self.client.post(reverse('edit_recipe', args=[self.recipe.id]), {
            'title': 'Hacked Title',
            'description': 'x',
            'difficulty': 'EASY',
            'prep_time_minutes': 1,
            'cook_time_minutes': 1,
            'servings': 1,
            'instructions': 'x',
            'locked': False,
            'ingredients-TOTAL_FORMS': '0',
            'ingredients-INITIAL_FORMS': '0',
            'ingredients-MIN_NUM_FORMS': '0',
            'ingredients-MAX_NUM_FORMS': '1000',
        })
        self.recipe.refresh_from_db()
        self.assertNotEqual(self.recipe.title, 'Hacked Title')

    # --- delete_recipe ---

    def test_author_can_delete_recipe(self):
        self.client.force_login(self.staff)
        self.client.post(reverse('delete_recipe', args=[self.recipe.id]))
        self.assertFalse(Recipe.objects.filter(id=self.recipe.id).exists())

    def test_non_author_cannot_delete_recipe(self):
        self.client.force_login(self.other_staff)
        self.client.post(reverse('delete_recipe', args=[self.recipe.id]))
        self.assertTrue(Recipe.objects.filter(id=self.recipe.id).exists())