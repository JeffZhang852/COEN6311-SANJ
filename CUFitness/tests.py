from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from django.core.exceptions import ValidationError
from datetime import timedelta
from django.contrib.auth import get_user_model
from CUFitness.models import CustomUser, Article, Challenge, CoachAvailability, CoachAppointment, EquipmentList, Recipe, RecipeIngredient
from CUFitness.forms import ArticleForm, CustomUserCreationForm, PrivacySettingsForm, UpdateEmailForm, UpdatePasswordForm
from decimal import Decimal


User = get_user_model()


# region ----------- Tests Helper Functions -----------
def make_member(email='member@test.com', password='Pass@1234'):
    return User.objects.create_user(
        email=email, password=password, role='MEMBER',
        first_name='Jane', last_name='Doe', date_of_birth='1995-06-15'
    )

def make_coach(email='coach@test.com', password='Pass@1234'):
    return User.objects.create_user(
        email=email, password=password, role='COACH',
        first_name='Bob', last_name='Smith', date_of_birth='1990-03-22'
    )

def make_staff(email='staff@test.com', password='Pass@1234'):
    # Note: is_staff is NOT passed here — CustomUser.save() sets it automatically from role
    return User.objects.create_user(
        email=email, password=password, role='STAFF',
        first_name='Alice', last_name='Admin', date_of_birth='1988-07-09'
    )

def make_article(author, title='Test Article', locked=False):
    return Article.objects.create(
        author=author, title=title,
        description='A short description.',
        body='Article body content.',
        locked=locked,
    )

def make_recipe(author, title='Protein Oats', locked=False):
    return Recipe.objects.create(
        author=author, title=title,
        description='A quick high-protein breakfast.',
        instructions='1. Cook oats.\n2. Add protein powder.\n3. Enjoy.',
        prep_time_minutes=5, cook_time_minutes=10,
        servings=2, difficulty='EASY', locked=locked,
    )
# endregion


# region ----------- Forms Tests -----------
class ArticleFormTest(TestCase):

    def test_correct_article(self):
        correct_article = ArticleForm(data={'title': 'valid title', 'description': 'Description.',
            'body': 'body content.', 'locked': False,})
        self.assertTrue(correct_article.is_valid())

    def test_missing_title(self):
        missing_title_article = ArticleForm(data={'title': '', 'description': 'Desc.', 'body': 'Body.', 'locked': False})
        self.assertFalse(missing_title_article.is_valid())
        self.assertIn('title', missing_title_article.errors)

    def test_title_over_limit(self):
        title_over_limit_article = ArticleForm(data={
            'title': 'x' * 101,  # max is 100
            'description': 'Desc.', 'body': 'Body.', 'locked': False,
        })
        self.assertFalse(title_over_limit_article.is_valid())
        self.assertIn('title', title_over_limit_article.errors)

    def test_description_over_limit(self):
        description_over_limit_article = ArticleForm(data={
            'title': 'Title',
            'description': 'x' * 251,  # max is 250
            'body': 'Body.', 'locked': False,
        })
        self.assertFalse(description_over_limit_article.is_valid())
        self.assertIn('description', description_over_limit_article.errors)

    def test_author_not_exposed_in_form(self):
        f = ArticleForm()
        self.assertNotIn('author', f.fields)

class RegistrationFormTest(TestCase):

    _base = {
        'first_name': 'New', 'last_name': 'User',
        'phone_number': '+1 514 555 0100',
        'address': '123 Test Street, Montreal, QC',
        'date_of_birth': '1995-06-15', 'membership': 'BASIC',
    }

    def test_valid_signup(self):
        data = {**self._base, 'email': 'newuser@test.com',
                'password1': 'StrongPass@99', 'password2': 'StrongPass@99'}
        self.assertTrue(CustomUserCreationForm(data=data).is_valid())

    def test_password_mismatch_fails(self):
        data = {**self._base, 'email': 'newuser@test.com',
                'password1': 'StrongPass@99', 'password2': 'DifferentPass@99'}
        self.assertFalse(CustomUserCreationForm(data=data).is_valid())

    def test_duplicate_email_blocked(self):
        make_member(email='existing@test.com')
        data = {**self._base, 'email': 'existing@test.com',
                'first_name': 'Dup',
                'password1': 'StrongPass@99', 'password2': 'StrongPass@99'}
        self.assertFalse(CustomUserCreationForm(data=data).is_valid())

class PrivacySettingsFormTest(TestCase):

    def setUp(self):
        self.member = make_member()

    def test_public_visibility_valid(self):
        f = PrivacySettingsForm(instance=self.member, data={'workout_visibility': 'PUBLIC'})
        self.assertTrue(f.is_valid())

    def test_coach_only_valid(self):
        f = PrivacySettingsForm(instance=self.member, data={'workout_visibility': 'COACH_ONLY'})
        self.assertTrue(f.is_valid())

    def test_bad_visibility_value_fails(self):
        f = PrivacySettingsForm(instance=self.member, data={'workout_visibility': 'EVERYONE'})
        self.assertFalse(f.is_valid())

class UpdateEmailFormTest(TestCase):

    def setUp(self):
        self.member = make_member()
        self.other_member = make_member(email='other@test.com')

    def test_new_email_accepted(self):
        f = UpdateEmailForm(instance=self.member, data={'email': 'newemail@test.com'})
        self.assertTrue(f.is_valid())

    def test_own_email_not_flagged_as_duplicate(self):
        f = UpdateEmailForm(instance=self.member, data={'email': 'member@test.com'})
        self.assertTrue(f.is_valid())

    def test_stolen_email_rejected(self):
        f = UpdateEmailForm(instance=self.member, data={'email': 'other@test.com'})
        self.assertFalse(f.is_valid())
        self.assertIn('email', f.errors)

    def test_mangled_email_rejected(self):
        f = UpdateEmailForm(instance=self.member, data={'email': 'not-an-email'})
        self.assertFalse(f.is_valid())
        self.assertIn('email', f.errors)

    def test_blank_email_rejected(self):
        f = UpdateEmailForm(instance=self.member, data={'email': ''})
        self.assertFalse(f.is_valid())
        self.assertIn('email', f.errors)

class UpdatePasswordFormTest(TestCase):

    def setUp(self):
        self.member = make_member()

    def test_valid_change_passes(self):
        f = UpdatePasswordForm(user=self.member, data={
            'old_password': 'Pass@1234',
            'new_password1': 'NewPass@9999',
            'new_password2': 'NewPass@9999',
        })
        self.assertTrue(f.is_valid())

    def test_wrong_old_pw_fails(self):
        f = UpdatePasswordForm(user=self.member, data={
            'old_password': 'WrongPassword!',
            'new_password1': 'NewPass@9999',
            'new_password2': 'NewPass@9999',
        })
        self.assertFalse(f.is_valid())
        self.assertIn('old_password', f.errors)

    def test_mismatched_new_pws_fail(self):
        f = UpdatePasswordForm(user=self.member, data={
            'old_password': 'Pass@1234',
            'new_password1': 'NewPass@9999',
            'new_password2': 'DifferentPass@9999',
        })
        self.assertFalse(f.is_valid())
        self.assertIn('new_password2', f.errors)

    def test_weak_pw_rejected_by_django(self):
        f = UpdatePasswordForm(user=self.member, data={
            'old_password': 'Pass@1234',
            'new_password1': '123',
            'new_password2': '123',
        })
        self.assertFalse(f.is_valid())
# endregion


# region ----------- Models Tests -----------
class CustomUserModel(TestCase):
    def test_new_user_defaults(self):
        u = CustomUser.objects.create_user(email="test@example.com", password="password123")
        self.assertEqual(u.role, "MEMBER")
        self.assertEqual(u.membership, "BASIC")
        self.assertTrue(u.is_active)
        self.assertEqual(str(u), "test@example.com")

class ArticleModel(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(email="user@test.com", password="password123")
        self.author = User.objects.create_user(email="author@test.com", password="password123")
        self.article = Article.objects.create(
            author=self.author,
            title="Test Article",
            description="A short description.",
            body="This is a test article body.",
            locked=False,
        )

    def test_article_creation(self):
        self.assertEqual(self.article.title, "Test Article")
        self.assertEqual(self.article.body, "This is a test article body.")
        self.assertFalse(self.article.locked)

    def test_article_author_relationship(self):
        self.assertEqual(self.article.author, self.author)

    def test_locked_field(self):
        self.article.locked = True
        self.article.save()
        refreshed = Article.objects.get(id=self.article.id)
        self.assertTrue(refreshed.locked)

    def test_str_method(self):
        self.assertIsInstance(str(self.article), str)

    def test_article_timestamps(self):
        self.assertIsNotNone(self.article.created_at)
        self.assertIsNotNone(self.article.updated_at)

class RecipeModelTest(TestCase):

    def setUp(self):
        self.staff = make_staff()
        self.recipe = make_recipe(author=self.staff)

    def test_fields_saved_correctly(self):
        self.assertEqual(self.recipe.title, 'Protein Oats')
        self.assertEqual(self.recipe.prep_time_minutes, 5)
        self.assertEqual(self.recipe.cook_time_minutes, 10)
        self.assertEqual(self.recipe.servings, 2)
        self.assertEqual(self.recipe.difficulty, 'EASY')
        self.assertFalse(self.recipe.locked)

    def test_total_time_is_prep_plus_cook(self):
        self.assertEqual(self.recipe.total_time_minutes, 15)

    def test_str_contains_title(self):
        self.assertIsInstance(str(self.recipe), str)
        self.assertIn('Protein Oats', str(self.recipe))

    def test_timestamps_set_on_create(self):
        self.assertIsNotNone(self.recipe.created_at)
        self.assertIsNotNone(self.recipe.updated_at)

    def test_deleting_author_nulls_field(self):
        self.staff.delete()
        self.recipe.refresh_from_db()
        self.assertIsNone(self.recipe.author)
        self.assertTrue(Recipe.objects.filter(id=self.recipe.id).exists())

    def test_calories_default_none(self):
        self.assertIsNone(self.recipe.calories_per_serving)

    def test_calories_can_be_saved(self):
        self.recipe.calories_per_serving = 350
        self.recipe.save()
        self.recipe.refresh_from_db()
        self.assertEqual(self.recipe.calories_per_serving, 350)

    def test_locked_toggles(self):
        self.recipe.locked = True
        self.recipe.save()
        self.recipe.refresh_from_db()
        self.assertTrue(self.recipe.locked)

    def test_multiple_dietary_restrictions_stored(self):
        self.recipe.dietary_restrictions = ['NO_GLUTEN', 'VEGAN']
        self.recipe.save()
        self.recipe.refresh_from_db()
        self.assertIn('NO_GLUTEN', self.recipe.dietary_restrictions)
        self.assertIn('VEGAN', self.recipe.dietary_restrictions)

    def test_scaled_ingredients_multiplies_qty(self):
        RecipeIngredient.objects.create(
            recipe=self.recipe, name='Oats', quantity=Decimal('1.00'), unit='CUP'
        )
        scaled = self.recipe.scaled_ingredients(2)
        self.assertEqual(scaled[0][1], Decimal('2.00'))

class RecipeIngredientTest(TestCase):

    def setUp(self):
        self.staff = make_staff()
        self.recipe = make_recipe(author=self.staff)

    def test_basic_ingredient_created(self):
        ing = RecipeIngredient.objects.create(
            recipe=self.recipe, name='Rolled oats', quantity=Decimal('1.00'), unit='CUP'
        )
        self.assertEqual(ing.name, 'Rolled oats')
        self.assertEqual(ing.quantity, Decimal('1.00'))
        self.assertEqual(ing.notes, '')

    def test_notes_appear_in_str(self):
        ing = RecipeIngredient.objects.create(
            recipe=self.recipe, name='Banana',
            quantity=Decimal('1.00'), unit='WHOLE', notes='sliced'
        )
        self.assertIn('sliced', str(ing))

    def test_no_empty_parens_when_no_notes(self):
        ing = RecipeIngredient.objects.create(
            recipe=self.recipe, name='Protein powder', quantity=Decimal('30.00'), unit='G'
        )
        result = str(ing)
        self.assertIn('Protein powder', result)
        self.assertNotIn('()', result)

    def test_ingredients_cascade_delete_with_recipe(self):
        RecipeIngredient.objects.create(
            recipe=self.recipe, name='Oats', quantity=Decimal('1.00'), unit='CUP'
        )
        rid = self.recipe.id
        self.recipe.delete()
        self.assertFalse(RecipeIngredient.objects.filter(recipe_id=rid).exists())

    def test_ingredients_ordered_by_insertion(self):
        names = ['Oats', 'Milk', 'Honey', 'Cinnamon']
        for n in names:
            RecipeIngredient.objects.create(
                recipe=self.recipe, name=n, quantity=Decimal('1.00'), unit='TSP'
            )
        stored = list(self.recipe.ingredients.values_list('name', flat=True))
        self.assertEqual(stored, names)

    def test_ingredient_count_correct(self):
        for i in range(4):
            RecipeIngredient.objects.create(
                recipe=self.recipe, name=f'Ingredient {i}', quantity=Decimal('1.00'), unit='G'
            )
        self.assertEqual(self.recipe.ingredients.count(), 4)

    def test_scaled_qty_multiplies_correctly(self):
        ing = RecipeIngredient.objects.create(
            recipe=self.recipe, name='Oats', quantity=Decimal('1.50'), unit='CUP'
        )
        self.assertEqual(ing.scaled_quantity(2), Decimal('3.00'))

class EquipmentListTest(TestCase):

    def test_equipment_created_ok(self):
        eq = EquipmentList.objects.create(name="Treadmill", description="Cardio machine")
        self.assertEqual(str(eq), "Treadmill")
        self.assertTrue(eq.is_active)

class EquipmentBookingTest(TestCase):

    def setUp(self):
        self.coach = CustomUser.objects.create_user(
            email="coach@example.com", password="pass123", role="COACH"
        )
        self.equipment = EquipmentList.objects.create(name="Bench Press")
        self.t0 = timezone.now()
        self.t1 = self.t0 + timedelta(hours=1)

    def test_equipment_is_active_by_default(self):
        self.assertTrue(self.equipment.is_active)

    def test_equipment_str_is_name(self):
        self.assertEqual(str(self.equipment), "Bench Press")

class CoachAvailabilityTest(TestCase):

    def setUp(self):
        self.coach = CustomUser.objects.create_user(
            email="coach2@example.com", password="pass123", role="COACH"
        )
        self.start = timezone.now()
        self.end = self.start + timedelta(hours=2)

    def test_slot_saves_fine(self):
        slot = CoachAvailability.objects.create(
            coach=self.coach, start_time=self.start, end_time=self.end
        )
        self.assertTrue(str(slot).startswith(self.coach.email))

    def test_overlap_rejected(self):
        CoachAvailability.objects.create(
            coach=self.coach, start_time=self.start, end_time=self.end
        )
        with self.assertRaises(ValidationError):
            CoachAvailability.objects.create(
                coach=self.coach,
                start_time=self.start + timedelta(minutes=30),
                end_time=self.end + timedelta(minutes=30),
            )

class CoachAppointmentTest(TestCase):

    def setUp(self):
        self.coach = CustomUser.objects.create_user(
            email="coach3@example.com", password="pass123", role="COACH"
        )
        self.member = CustomUser.objects.create_user(
            email="member@example.com", password="pass123", role="MEMBER"
        )
        self.start = timezone.now()
        self.end = self.start + timedelta(hours=1)

    def test_accepted_appointment_saves(self):
        appt = CoachAppointment.objects.create(
            coach=self.coach, member=self.member,
            start_time=self.start, end_time=self.end, status="ACCEPTED"
        )
        self.assertEqual(appt.status, "ACCEPTED")

    def test_double_booking_blocked(self):
        CoachAppointment.objects.create(
            coach=self.coach, member=self.member,
            start_time=self.start, end_time=self.end, status="ACCEPTED"
        )
        with self.assertRaises(ValidationError):
            CoachAppointment.objects.create(
                coach=self.coach, member=self.member,
                start_time=self.start + timedelta(minutes=30),
                end_time=self.end + timedelta(minutes=30),
                status="ACCEPTED"
            )
# endregion


# region ----------- Logged-In User (staff, member, coach) Views Tests -----------
class LoginView(TestCase):

    def setUp(self):
        self.client = Client()
        self.member = make_member()
        self.staff = make_staff()
        self.coach = make_coach()

    def test_member_logs_in(self):
        r = self.client.post(reverse('login'), {'email': 'member@test.com', 'password': 'Pass@1234'})
        self.assertRedirects(r, reverse('home'))

    def test_coach_logs_in(self):
        r = self.client.post(reverse('coach_login'), {'email': 'coach@test.com', 'password': 'Pass@1234'})
        self.assertRedirects(r, reverse('coach_home'))

    def test_staff_logs_in(self):
        r = self.client.post(reverse('staff_login'), {'email': 'staff@test.com', 'password': 'Pass@1234'})
        self.assertRedirects(r, reverse('home'))

    def test_staff_redirected_to_staff_login(self):
        r = self.client.post(reverse('login'), {'email': 'staff@test.com', 'password': 'Pass@1234'})
        self.assertRedirects(r, reverse('staff_login'))

    def test_coach_redirected_to_coach_login(self):
        r = self.client.post(reverse('login'), {'email': 'coach@test.com', 'password': 'Pass@1234'})
        self.assertRedirects(r, reverse('coach_login'))

    def test_member_cant_use_staff_login(self):
        r = self.client.post(reverse('staff_login'), {'email': 'member@test.com', 'password': 'Pass@1234'})
        self.assertRedirects(r, reverse('staff_login'))

    def test_wrong_password_bounced_back(self):
        r = self.client.post(reverse('login'), {'email': 'member@test.com', 'password': 'wrongpassword'})
        self.assertRedirects(r, reverse('login'))

    def test_logout_redirects_home(self):
        self.client.login(username='member@test.com', password='Pass@1234')
        r = self.client.get(reverse('logout'))
        self.assertRedirects(r, reverse('home'))

class ArticleView(TestCase):

    def setUp(self):
        self.client = Client()
        self.member = make_member()
        self.staff = make_staff()
        self.other_staff = make_staff(email='other@test.com')
        self.article = make_article(author=self.staff, title='My Article')
        self.free_article = make_article(self.staff, title='Free Article', locked=False)
        self.locked_article = make_article(self.staff, title='Locked Article', locked=True)

    def test_staff_articles_page_loads(self):
        self.client.force_login(self.staff)
        r = self.client.get(reverse('staff_articles'))
        self.assertEqual(r.status_code, 200)

    def test_detail_page_loads(self):
        self.client.force_login(self.staff)
        r = self.client.get(reverse('article_details', args=[self.article.id]))
        self.assertEqual(r.status_code, 200)

    def test_author_edits_own_article(self):
        self.client.force_login(self.staff)
        self.client.post(reverse('staff_edit_article', args=[self.article.id]), {
            'title': 'Updated Title', 'description': 'Updated description.',
            'body': 'Updated body.', 'locked': False,
        })
        self.article.refresh_from_db()
        self.assertEqual(self.article.title, 'Updated Title')

    def test_other_staff_cant_edit(self):
        self.client.force_login(self.other_staff)
        self.client.post(reverse('staff_edit_article', args=[self.article.id]), {
            'title': 'Hacked Title', 'description': 'x', 'body': 'x', 'locked': False,
        })
        self.article.refresh_from_db()
        self.assertNotEqual(self.article.title, 'Hacked Title')

    def test_author_deletes_own_article(self):
        self.client.force_login(self.staff)
        self.client.post(reverse('staff_delete_article', args=[self.article.id]))
        self.assertFalse(Article.objects.filter(id=self.article.id).exists())

    def test_other_staff_cant_delete(self):
        self.client.force_login(self.other_staff)
        self.client.post(reverse('staff_delete_article', args=[self.article.id]))
        self.assertTrue(Article.objects.filter(id=self.article.id).exists())

    def test_author_auto_assigned_on_create(self):
        self.client.force_login(self.staff)
        self.client.post(reverse('staff_create_article'), {
            'title': 'Brand New Article', 'description': 'Some description.',
            'body': 'Some body.', 'locked': False,
        })
        a = Article.objects.get(title='Brand New Article')
        self.assertEqual(a.author, self.staff)

    def test_missing_article_is_404(self):
        self.client.force_login(self.staff)
        r = self.client.get(reverse('article_details', args=[99999]))
        self.assertEqual(r.status_code, 404)

    def test_orphaned_article_can_be_edited_by_any_staff(self):
        # when the original author's account is deleted, the article's
        # author FK becomes NULL. Any staff member should still be able to edit it.
        article_id = self.article.id
        self.staff.delete()
        self.article.refresh_from_db()
        self.assertIsNone(self.article.author)
        # force_login AFTER the delete so the session isn't tied to the deleted user
        self.client.force_login(self.other_staff)
        self.client.post(reverse('staff_edit_article', args=[article_id]), {
            'title': 'Edited Orphan', 'description': 'Updated.', 'body': 'Updated body.', 'locked': False,
        })
        self.article.refresh_from_db()
        self.assertEqual(self.article.title, 'Edited Orphan')

    def test_orphaned_article_can_be_deleted_by_any_staff(self):
        # deletion should also work once the author is gone
        article_id = self.article.id
        self.staff.delete()
        self.client.force_login(self.other_staff)
        self.client.post(reverse('staff_delete_article', args=[article_id]))
        self.assertFalse(Article.objects.filter(id=article_id).exists())

    def test_free_article_visible_to_all(self):
        r = self.client.get(reverse('user_articles'))
        self.assertContains(r, 'Free Article')

    def test_locked_article_in_context(self):
        r = self.client.get(reverse('user_articles'))
        self.assertIn(self.locked_article, list(r.context['locked_articles']))

    def test_free_article_in_context(self):
        r = self.client.get(reverse('user_articles'))
        self.assertIn(self.free_article, list(r.context['free_articles']))

class RecipeView(TestCase):

    def setUp(self):
        self.client = Client()
        self.staff = make_staff()
        self.other_staff = make_staff(email='other@test.com')
        self.member = make_member()
        self.recipe = make_recipe(author=self.staff)

    def test_staff_recipes_page_loads(self):
        self.client.force_login(self.staff)
        r = self.client.get(reverse('staff_recipes'))
        self.assertEqual(r.status_code, 200)

    def test_anon_blocked_from_staff_recipes(self):
        r = self.client.get(reverse('staff_recipes'))
        self.assertNotEqual(r.status_code, 200)

    def test_member_blocked_from_staff_recipes(self):
        self.client.force_login(self.member)
        r = self.client.get(reverse('staff_recipes'))
        self.assertNotEqual(r.status_code, 200)

    def test_recipe_detail_loads(self):
        self.client.force_login(self.staff)
        r = self.client.get(reverse('recipe_details', args=[self.recipe.id]))
        self.assertEqual(r.status_code, 200)

    def test_bad_recipe_id_is_404(self):
        self.client.force_login(self.staff)
        r = self.client.get(reverse('recipe_details', args=[99999]))
        self.assertEqual(r.status_code, 404)

    def test_anon_blocked_from_locked_recipe(self):
        locked = make_recipe(author=self.staff, title='Locked Recipe', locked=True)
        r = self.client.get(reverse('recipe_details', args=[locked.id]))
        self.assertNotEqual(r.status_code, 200)

    def test_anon_can_see_unlocked_recipe(self):
        r = self.client.get(reverse('recipe_details', args=[self.recipe.id]))
        self.assertEqual(r.status_code, 200)

    def test_author_set_from_session_not_form(self):
        self.client.force_login(self.staff)
        self.client.post(reverse('staff_create_recipe'), {
            'title': 'New Recipe', 'description': 'A test description.',
            'difficulty': 'EASY', 'prep_time_minutes': 10, 'cook_time_minutes': 20,
            'servings': 2, 'instructions': 'Step 1. Do something.',
            'locked': False,
            'ingredients-TOTAL_FORMS': '0', 'ingredients-INITIAL_FORMS': '0',
            'ingredients-MIN_NUM_FORMS': '0', 'ingredients-MAX_NUM_FORMS': '1000',
        })
        recipe = Recipe.objects.get(title='New Recipe')
        self.assertEqual(recipe.author, self.staff)

    def test_member_cant_create_recipe(self):
        self.client.force_login(self.member)
        r = self.client.get(reverse('staff_create_recipe'))
        self.assertNotEqual(r.status_code, 200)

    def test_author_can_edit_own_recipe(self):
        self.client.force_login(self.staff)
        self.client.post(reverse('staff_edit_recipe', args=[self.recipe.id]), {
            'title': 'Updated Recipe', 'description': 'Updated description.',
            'difficulty': 'HARD', 'prep_time_minutes': 10, 'cook_time_minutes': 20,
            'servings': 4, 'instructions': 'Updated instructions.',
            'locked': False,
            'ingredients-TOTAL_FORMS': '0', 'ingredients-INITIAL_FORMS': '0',
            'ingredients-MIN_NUM_FORMS': '0', 'ingredients-MAX_NUM_FORMS': '1000',
        })
        self.recipe.refresh_from_db()
        self.assertEqual(self.recipe.title, 'Updated Recipe')

    def test_other_staff_cant_edit(self):
        self.client.force_login(self.other_staff)
        self.client.post(reverse('staff_edit_recipe', args=[self.recipe.id]), {
            'title': 'Hacked Title', 'description': 'x', 'difficulty': 'EASY',
            'prep_time_minutes': 1, 'cook_time_minutes': 1, 'servings': 1,
            'instructions': 'x', 'locked': False,
            'ingredients-TOTAL_FORMS': '0', 'ingredients-INITIAL_FORMS': '0',
            'ingredients-MIN_NUM_FORMS': '0', 'ingredients-MAX_NUM_FORMS': '1000',
        })
        self.recipe.refresh_from_db()
        self.assertNotEqual(self.recipe.title, 'Hacked Title')

    def test_author_can_delete_own_recipe(self):
        self.client.force_login(self.staff)
        self.client.post(reverse('staff_delete_recipe', args=[self.recipe.id]))
        self.assertFalse(Recipe.objects.filter(id=self.recipe.id).exists())

    def test_other_staff_cant_delete(self):
        self.client.force_login(self.other_staff)
        self.client.post(reverse('staff_delete_recipe', args=[self.recipe.id]))
        self.assertTrue(Recipe.objects.filter(id=self.recipe.id).exists())

class SettingsView(TestCase):

    def setUp(self):
        self.client = Client()
        self.member = make_member()

    def test_settings_page_loads(self):
        self.client.force_login(self.member)
        r = self.client.get(reverse('user_settings'))
        self.assertEqual(r.status_code, 200)

    def test_privacy_setting_saved(self):
        self.client.force_login(self.member)
        self.client.post(reverse('user_settings'), {
            'workout_visibility': 'PUBLIC', 'privacy_submit': '1',
        })
        self.member.refresh_from_db()
        self.assertEqual(self.member.workout_visibility, 'PUBLIC')

    def test_coach_request_goes_pending(self):
        self.client.force_login(self.member)
        self.client.post(reverse('user_settings'), {'coach_request_submit': '1'})
        self.member.refresh_from_db()
        self.assertEqual(self.member.coach_request_status, 'PENDING')

    def test_pending_stays_pending_on_resubmit(self):
        self.member.coach_request_status = 'PENDING'
        self.member.save()
        self.client.force_login(self.member)
        self.client.post(reverse('user_settings'), {'coach_request_submit': '1'})
        self.member.refresh_from_db()
        self.assertEqual(self.member.coach_request_status, 'PENDING')

class EmailUpdateView(TestCase):

    def setUp(self):
        self.client = Client()
        self.member = make_member()
        self.other_member = make_member(email='taken@test.com')

    def test_email_saved_on_valid_post(self):
        self.client.force_login(self.member)
        self.client.post(reverse('user_settings'), {'email': 'updated@test.com', 'email_submit': '1'})
        self.member.refresh_from_db()
        self.assertEqual(self.member.email, 'updated@test.com')

    def test_valid_update_redirects(self):
        self.client.force_login(self.member)
        r = self.client.post(reverse('user_settings'), {'email': 'updated@test.com', 'email_submit': '1'})
        self.assertRedirects(r, reverse('user_settings'))

    def test_taken_email_not_saved(self):
        self.client.force_login(self.member)
        self.client.post(reverse('user_settings'), {'email': 'taken@test.com', 'email_submit': '1'})
        self.member.refresh_from_db()
        self.assertNotEqual(self.member.email, 'taken@test.com')

    def test_taken_email_shows_form_error(self):
        self.client.force_login(self.member)
        r = self.client.post(reverse('user_settings'), {'email': 'taken@test.com', 'email_submit': '1'})
        self.assertEqual(r.status_code, 200)
        self.assertFormError(r.context['email_form'], 'email', 'This email address is already in use.')

    def test_bad_format_not_saved(self):
        self.client.force_login(self.member)
        orig = self.member.email
        self.client.post(reverse('user_settings'), {'email': 'not-valid', 'email_submit': '1'})
        self.member.refresh_from_db()
        self.assertEqual(self.member.email, orig)

    def test_coach_can_update_email(self):
        coach = make_coach()
        self.client.force_login(coach)
        self.client.post(reverse('coach_settings'), {'email': 'newcoach@test.com', 'email_submit': '1'})
        coach.refresh_from_db()
        self.assertEqual(coach.email, 'newcoach@test.com')

    def test_anon_blocked(self):
        r = self.client.post(reverse('user_settings'), {'email': 'hacker@test.com', 'email_submit': '1'})
        self.assertNotEqual(r.status_code, 200)

class PasswordUpdateView(TestCase):

    def setUp(self):
        self.client = Client()
        self.member = make_member()

    def _pw_post(self, old='Pass@1234', new1='NewPass@9999', new2='NewPass@9999'):
        return self.client.post(reverse('user_settings'), {
            'old_password': old,
            'new_password1': new1,
            'new_password2': new2,
            'password_submit': '1',
        })

    def test_new_pw_saved(self):
        self.client.force_login(self.member)
        self._pw_post()
        self.member.refresh_from_db()
        self.assertTrue(self.member.check_password('NewPass@9999'))

    def test_valid_change_redirects(self):
        self.client.force_login(self.member)
        r = self._pw_post()
        self.assertRedirects(r, reverse('user_settings'))

    def test_session_kept_after_pw_change(self):
        # update_session_auth_hash should stop the user getting logged out
        self.client.force_login(self.member)
        self._pw_post()
        r = self.client.get(reverse('user_settings'))
        self.assertEqual(r.status_code, 200)

    def test_wrong_old_pw_not_saved(self):
        self.client.force_login(self.member)
        self._pw_post(old='WrongPassword!')
        self.member.refresh_from_db()
        self.assertFalse(self.member.check_password('NewPass@9999'))
        self.assertTrue(self.member.check_password('Pass@1234'))

    def test_wrong_old_pw_shows_error(self):
        self.client.force_login(self.member)
        r = self._pw_post(old='WrongPassword!')
        self.assertEqual(r.status_code, 200)
        self.assertFormError(r.context['password_form'], 'old_password',
                             'Your old password was entered incorrectly. Please enter it again.')

    def test_mismatched_pws_not_saved(self):
        self.client.force_login(self.member)
        self._pw_post(new2='DifferentPass@9999')
        self.member.refresh_from_db()
        self.assertTrue(self.member.check_password('Pass@1234'))

    def test_coach_can_change_pw(self):
        coach = make_coach()
        self.client.force_login(coach)
        self.client.post(reverse('coach_settings'), {
            'old_password': 'Pass@1234',
            'new_password1': 'NewCoach@9999',
            'new_password2': 'NewCoach@9999',
            'password_submit': '1',
        })
        coach.refresh_from_db()
        self.assertTrue(coach.check_password('NewCoach@9999'))

    def test_anon_blocked(self):
        r = self._pw_post()
        self.assertNotEqual(r.status_code, 200)

class ChallengeView(TestCase):

    def setUp(self):
        self.client = Client()
        self.staff = make_staff()
        self.coach = make_coach()
        self.member = make_member()
        self.challenge = Challenge.objects.create(
            title='Test Challenge', description='Do the thing.',
            goal_target=10,
            start_date='2026-04-01', end_date='2026-04-30',
            created_by=self.staff,
        )

    def test_challenges_page_loads(self):
        self.client.force_login(self.member)
        r = self.client.get(reverse('user_challenges'))
        self.assertEqual(r.status_code, 200)

    # --- challenge_details access control ---

    def test_anon_blocked_from_challenge_details(self):
        r = self.client.get(reverse('challenge_details', args=[self.challenge.id]))
        self.assertNotEqual(r.status_code, 200)

    def test_member_can_see_challenge_details(self):
        self.client.force_login(self.member)
        r = self.client.get(reverse('challenge_details', args=[self.challenge.id]))
        self.assertEqual(r.status_code, 200)

    def test_coach_can_see_challenge_details(self):
        self.client.force_login(self.coach)
        r = self.client.get(reverse('challenge_details', args=[self.challenge.id]))
        self.assertEqual(r.status_code, 200)

    def test_staff_can_see_challenge_details(self):
        self.client.force_login(self.staff)
        r = self.client.get(reverse('challenge_details', args=[self.challenge.id]))
        self.assertEqual(r.status_code, 200)

    # --- update_progress guards ---

    def test_negative_progress_does_not_decrease_score(self):
        self.client.force_login(self.member)
        self.client.post(reverse('join_challenge', args=[self.challenge.id]))
        participation = self.member.challengeparticipation_set.get(challenge=self.challenge)
        participation.progress = 5
        participation.save()
        self.client.post(reverse('update_progress', args=[participation.id]), {'progress': '-999'})
        participation.refresh_from_db()
        self.assertEqual(participation.progress, 5)

    def test_non_integer_progress_does_not_crash(self):
        self.client.force_login(self.member)
        self.client.post(reverse('join_challenge', args=[self.challenge.id]))
        participation = self.member.challengeparticipation_set.get(challenge=self.challenge)
        r = self.client.post(reverse('update_progress', args=[participation.id]), {'progress': 'abc'})
        # should redirect cleanly, not 500
        self.assertEqual(r.status_code, 302)

    def test_progress_capped_at_goal_target(self):
        self.client.force_login(self.member)
        self.client.post(reverse('join_challenge', args=[self.challenge.id]))
        participation = self.member.challengeparticipation_set.get(challenge=self.challenge)
        self.client.post(reverse('update_progress', args=[participation.id]), {'progress': '99999'})
        participation.refresh_from_db()
        self.assertEqual(participation.progress, self.challenge.goal_target)
# endregion


# user manager/creation test
class UsersManagersTests(TestCase):

    def test_create_user(self):
        User = get_user_model()
        u = User.objects.create_user(email="normal@user.com", password="foo")
        self.assertEqual(u.email, "normal@user.com")
        self.assertTrue(u.is_active)
        self.assertFalse(u.is_staff)   # MEMBER role → is_staff should be False
        self.assertFalse(u.is_superuser)
        try:
            self.assertIsNone(u.username)
        except AttributeError:
            pass
        with self.assertRaises(TypeError):
            User.objects.create_user()
        with self.assertRaises(TypeError):
            User.objects.create_user(email="")
        with self.assertRaises(ValueError):
            User.objects.create_user(email="", password="foo")

    def test_is_staff_derived_from_role(self):
        # CustomUser.save() automatically sets is_staff based on role —
        # STAFF and ADMIN get True, everything else gets False
        staff = User.objects.create_user(email="staff@role.com", password="foo", role="STAFF")
        self.assertTrue(staff.is_staff)

        member = User.objects.create_user(email="member@role.com", password="foo", role="MEMBER")
        self.assertFalse(member.is_staff)

        coach = User.objects.create_user(email="coach@role.com", password="foo", role="COACH")
        self.assertFalse(coach.is_staff)

    def test_create_superuser(self):
        User = get_user_model()
        su = User.objects.create_superuser(email="super@user.com", password="foo")
        self.assertEqual(su.email, "super@user.com")
        self.assertTrue(su.is_active)
        self.assertTrue(su.is_staff)
        self.assertTrue(su.is_superuser)
        try:
            self.assertIsNone(su.username)
        except AttributeError:
            pass
        with self.assertRaises(ValueError):
            User.objects.create_superuser(email="super@user.com", password="foo", is_superuser=False)


# test some URLs (pages have special frontend for un-authenticated users )
class PublicPageTest(TestCase):

    def setUp(self):
        self.client = Client()

    def home_page(self):
        self.assertEqual(self.client.get(reverse('home')).status_code, 200)

    def services_page(self):
        self.assertEqual(self.client.get(reverse('services')).status_code, 200)

    def user_articles_page(self):
        self.assertEqual(self.client.get(reverse('user_articles')).status_code, 200)

    def user_recipes_page(self):
        self.assertEqual(self.client.get(reverse('user_recipes')).status_code, 200)

    def workout_plans_page(self):
        self.assertEqual(self.client.get(reverse('workout_plans')).status_code, 200)

    def user_exercises_page(self):
        self.assertEqual(self.client.get(reverse('user_exercises')).status_code, 200)

    def user_challenges_page(self):
        self.assertEqual(self.client.get(reverse('user_challenges')).status_code, 200)

    def chatbot_page(self):
        self.assertEqual(self.client.get(reverse('chatbot')).status_code, 200)

    def amenities_page(self):
        self.assertEqual(self.client.get(reverse('amenities')).status_code, 200)

    def gym_schedule_page(self):
        self.assertEqual(self.client.get(reverse('gym_schedule')).status_code, 200)

    def contact_us_page(self):
        self.assertEqual(self.client.get(reverse('contact_us')).status_code, 200)

    def about_page(self):
        self.assertEqual(self.client.get(reverse('about')).status_code, 200)

    def faq_page(self):
        self.assertEqual(self.client.get(reverse('faq')).status_code, 200)

    def privacy_policy_page(self):
        self.assertEqual(self.client.get(reverse('privacy_policy')).status_code, 200)

    def register_page(self):
        self.assertEqual(self.client.get(reverse('register')).status_code, 200)

    def member_login_page(self):
        self.assertEqual(self.client.get(reverse('login')).status_code, 200)

    def staff_login_page(self):
        self.assertEqual(self.client.get(reverse('staff_login')).status_code, 200)

    def coach_login_page(self):
        self.assertEqual(self.client.get(reverse('coach_login')).status_code, 200)


# access control
class AccessControl(TestCase):

    def setUp(self):
        self.client = Client()
        self.member = make_member()
        self.staff = make_staff()
        self.coach = make_coach()

    # unauthenticated users

    def test_anon_cant_see_profile(self):
        r = self.client.get(reverse('user_profile'))
        self.assertNotEqual(r.status_code, 200)

    def test_anon_cant_see_settings(self):
        r = self.client.get(reverse('user_settings'))
        self.assertNotEqual(r.status_code, 200)

    def test_anon_blocked_from_articles(self):
        r = self.client.get(reverse('staff_articles'))
        self.assertNotEqual(r.status_code, 200)

    # member can't reach staff pages

    def test_member_cant_access_staff_articles(self):
        self.client.force_login(self.member)
        r = self.client.get(reverse('staff_articles'))
        self.assertNotEqual(r.status_code, 200)

    def test_member_cant_access_staff_create_article(self):
        self.client.force_login(self.member)
        r = self.client.get(reverse('staff_create_article'))
        self.assertNotEqual(r.status_code, 200)

    # staff can reach their own pages

    def test_staff_sees_articles_list(self):
        self.client.force_login(self.staff)
        r = self.client.get(reverse('staff_articles'))
        self.assertEqual(r.status_code, 200)

    def test_staff_can_open_create_article(self):
        self.client.force_login(self.staff)
        r = self.client.get(reverse('staff_create_article'))
        self.assertEqual(r.status_code, 200)

    def test_staff_blocked_from_member_settings(self):
        self.client.force_login(self.staff)
        r = self.client.get(reverse('user_settings'))
        self.assertNotEqual(r.status_code, 200)


# coach request tests
class CoachRequestTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.member = make_member()

    def test_default_status_is_none(self):
        self.assertEqual(self.member.coach_request_status, 'NONE')

    def test_submitting_sets_pending(self):
        self.client.force_login(self.member)
        self.client.post(reverse('user_settings'), {'coach_request_submit': '1'})
        self.member.refresh_from_db()
        self.assertEqual(self.member.coach_request_status, 'PENDING')

class CoachRequestSubmissionGuardTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.member = make_member()

    def test_pending_cant_resubmit(self):
        self.member.coach_request_status = 'PENDING'
        self.member.save()
        self.client.force_login(self.member)
        self.client.post(reverse('user_settings'), {'coach_request_submit': '1'})
        self.member.refresh_from_db()
        self.assertEqual(self.member.coach_request_status, 'PENDING')

    def test_approved_cant_reset_to_pending(self):
        self.member.coach_request_status = 'APPROVED'
        self.member.save()
        self.client.force_login(self.member)
        self.client.post(reverse('user_settings'), {'coach_request_submit': '1'})
        self.member.refresh_from_db()
        self.assertEqual(self.member.coach_request_status, 'APPROVED')

    def test_rejected_can_resubmit(self):
        self.member.coach_request_status = 'REJECTED'
        self.member.save()
        self.client.force_login(self.member)
        self.client.post(reverse('user_settings'), {'coach_request_submit': '1'})
        self.member.refresh_from_db()
        self.assertEqual(self.member.coach_request_status, 'PENDING')

    def test_fresh_member_can_submit(self):
        self.assertEqual(self.member.coach_request_status, 'NONE')
        self.client.force_login(self.member)
        self.client.post(reverse('user_settings'), {'coach_request_submit': '1'})
        self.member.refresh_from_db()
        self.assertEqual(self.member.coach_request_status, 'PENDING')


# staff requests page
class StaffRequestsPageTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.staff = make_staff()
        self.member = make_member()
        self.other_member = make_member(email='other@test.com')

    def test_staff_can_load_page(self):
        self.client.force_login(self.staff)
        r = self.client.get(reverse('coach_requests'))
        self.assertEqual(r.status_code, 200)

    def test_anon_blocked(self):
        r = self.client.get(reverse('coach_requests'))
        self.assertNotEqual(r.status_code, 200)

    def test_member_blocked(self):
        self.client.force_login(self.member)
        r = self.client.get(reverse('coach_requests'))
        self.assertNotEqual(r.status_code, 200)

    def test_pending_member_shows_up(self):
        self.member.coach_request_status = 'PENDING'
        self.member.save()
        self.client.force_login(self.staff)
        r = self.client.get(reverse('coach_requests'))
        self.assertIn(self.member, r.context['pending_requests'])

    def test_approved_member_shows_up(self):
        self.member.coach_request_status = 'APPROVED'
        self.member.save()
        self.client.force_login(self.staff)
        r = self.client.get(reverse('coach_requests'))
        self.assertIn(self.member, r.context['approved_requests'])

    def test_rejected_member_shows_up(self):
        self.member.coach_request_status = 'REJECTED'
        self.member.save()
        self.client.force_login(self.staff)
        r = self.client.get(reverse('coach_requests'))
        self.assertIn(self.member, r.context['rejected_requests'])

    def test_none_status_doesnt_leak_into_any_list(self):
        self.assertEqual(self.member.coach_request_status, 'NONE')
        self.client.force_login(self.staff)
        r = self.client.get(reverse('coach_requests'))
        self.assertNotIn(self.member, r.context['pending_requests'])
        self.assertNotIn(self.member, r.context['approved_requests'])
        self.assertNotIn(self.member, r.context['rejected_requests'])

    def test_multiple_pending_all_show(self):
        self.member.coach_request_status = 'PENDING'
        self.member.save()
        self.other_member.coach_request_status = 'PENDING'
        self.other_member.save()
        self.client.force_login(self.staff)
        r = self.client.get(reverse('coach_requests'))
        pending = list(r.context['pending_requests'])
        self.assertIn(self.member, pending)
        self.assertIn(self.other_member, pending)

# handle coach request view
class HandleCoachRequestTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.staff = make_staff()
        self.other_staff = make_staff(email='otherstaff@test.com')
        self.member = make_member()
        self.member.coach_request_status = 'PENDING'
        self.member.save()

    def test_anon_blocked(self):
        r = self.client.post(
            reverse('handle_coach_request', args=[self.member.id]), {'action': 'APPROVED'}
        )
        self.assertNotEqual(r.status_code, 200)

    def test_member_cant_handle_requests(self):
        other = make_member(email='another@test.com')
        self.client.force_login(other)
        r = self.client.post(
            reverse('handle_coach_request', args=[self.member.id]), {'action': 'APPROVED'}
        )
        self.assertNotEqual(r.status_code, 200)

    def test_get_redirects_no_changes(self):
        self.client.force_login(self.staff)
        r = self.client.get(reverse('handle_coach_request', args=[self.member.id]))
        self.assertRedirects(r, reverse('coach_requests'))
        self.member.refresh_from_db()
        self.assertEqual(self.member.coach_request_status, 'PENDING')

    def test_approve_sets_status(self):
        self.client.force_login(self.staff)
        self.client.post(reverse('handle_coach_request', args=[self.member.id]), {'action': 'APPROVED'})
        self.member.refresh_from_db()
        self.assertEqual(self.member.coach_request_status, 'APPROVED')

    def test_approve_bumps_role_to_coach(self):
        self.client.force_login(self.staff)
        self.client.post(reverse('handle_coach_request', args=[self.member.id]), {'action': 'APPROVED'})
        self.member.refresh_from_db()
        self.assertEqual(self.member.role, 'COACH')

    def test_approve_redirects_after(self):
        self.client.force_login(self.staff)
        r = self.client.post(reverse('handle_coach_request', args=[self.member.id]), {'action': 'APPROVED'})
        self.assertRedirects(r, reverse('coach_requests'))

    def test_reject_sets_status(self):
        self.client.force_login(self.staff)
        self.client.post(reverse('handle_coach_request', args=[self.member.id]), {'action': 'REJECTED'})
        self.member.refresh_from_db()
        self.assertEqual(self.member.coach_request_status, 'REJECTED')

    def test_reject_keeps_member_role(self):
        self.client.force_login(self.staff)
        self.client.post(reverse('handle_coach_request', args=[self.member.id]), {'action': 'REJECTED'})
        self.member.refresh_from_db()
        self.assertEqual(self.member.role, 'MEMBER')

    def test_reject_redirects_after(self):
        self.client.force_login(self.staff)
        r = self.client.post(reverse('handle_coach_request', args=[self.member.id]), {'action': 'REJECTED'})
        self.assertRedirects(r, reverse('coach_requests'))

    def test_garbage_action_changes_nothing(self):
        self.client.force_login(self.staff)
        self.client.post(reverse('handle_coach_request', args=[self.member.id]), {'action': 'MAKE_ADMIN'})
        self.member.refresh_from_db()
        self.assertEqual(self.member.coach_request_status, 'PENDING')
        self.assertEqual(self.member.role, 'MEMBER')

    def test_cant_act_on_none_status_user(self):
        no_req = make_member(email='norequst@test.com')
        self.assertEqual(no_req.coach_request_status, 'NONE')
        self.client.force_login(self.staff)
        self.client.post(reverse('handle_coach_request', args=[no_req.id]), {'action': 'APPROVED'})
        no_req.refresh_from_db()
        self.assertNotEqual(no_req.coach_request_status, 'APPROVED')
        self.assertNotEqual(no_req.role, 'COACH')

    def test_missing_user_is_404(self):
        self.client.force_login(self.staff)
        r = self.client.post(reverse('handle_coach_request', args=[99999]), {'action': 'APPROVED'})
        self.assertEqual(r.status_code, 404)

    def test_can_approve_previously_rejected(self):
        self.member.coach_request_status = 'REJECTED'
        self.member.save()
        self.client.force_login(self.staff)
        self.client.post(reverse('handle_coach_request', args=[self.member.id]), {'action': 'APPROVED'})
        self.member.refresh_from_db()
        self.assertEqual(self.member.coach_request_status, 'APPROVED')
        self.assertEqual(self.member.role, 'COACH')

    def test_any_staff_can_approve(self):
        self.client.force_login(self.other_staff)
        self.client.post(reverse('handle_coach_request', args=[self.member.id]), {'action': 'APPROVED'})
        self.member.refresh_from_db()
        self.assertEqual(self.member.role, 'COACH')
