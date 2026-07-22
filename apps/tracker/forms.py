import datetime

from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User
from django.utils import timezone

from .models import Business, Category, DEFAULT_CATEGORY_NAMES, InventoryItem, Product


class FriendlyAuthenticationForm(AuthenticationForm):
    """
    Same as Django's default AuthenticationForm, except it tells the user
    specifically whether the username doesn't exist or the password is
    wrong, instead of one generic "invalid credentials" message.

    Trade-off: this leaks which usernames are registered (user
    enumeration). Fine for internal/dev testing; swap back to the plain
    AuthenticationForm before this has real external users.
    """

    def clean(self):
        username = self.cleaned_data.get("username")
        password = self.cleaned_data.get("password")

        if username and password:
            if not User.objects.filter(username=username).exists():
                raise forms.ValidationError(
                    "Δεν υπάρχει χρήστης με αυτό το username.", code="no_such_user"
                )

            self.user_cache = authenticate(self.request, username=username, password=password)
            if self.user_cache is None:
                raise forms.ValidationError(
                    "Λάθος κωδικός πρόσβασης.", code="wrong_password"
                )
            self.confirm_login_allowed(self.user_cache)

        return self.cleaned_data


class SignupForm(UserCreationForm):
    email = forms.EmailField(required=True)
    business_name = forms.CharField(max_length=200, label="Επωνυμία επιχείρησης")
    business_type = forms.ChoiceField(choices=Business.BusinessType.choices)

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")

    def save(self, commit=True):
        user = super().save(commit=commit)
        business = Business.objects.create(
            owner=user,
            name=self.cleaned_data["business_name"],
            business_type=self.cleaned_data["business_type"],
            trial_ends_at=timezone.localdate() + datetime.timedelta(days=Business.TRIAL_LENGTH_DAYS),
        )
        Category.objects.bulk_create(
            [Category(business=business, name=name) for name in DEFAULT_CATEGORY_NAMES]
        )
        return user


class InventoryItemForm(forms.ModelForm):
    product_name = forms.CharField(max_length=200, label="Προϊόν")
    barcode = forms.CharField(
        max_length=64, required=False, label="Barcode",
        widget=forms.TextInput(attrs={"id": "id_barcode"}),
    )
    category = forms.ModelChoiceField(
        queryset=Category.objects.none(), required=False, label="Κατηγορία",
        empty_label="— Χωρίς κατηγορία —",
    )
    unit = forms.ChoiceField(choices=Product.Unit.choices, initial=Product.Unit.PIECE)
    unit_cost = forms.DecimalField(
        max_digits=10, decimal_places=2, required=False, label="Κόστος/μονάδα (€)",
    )
    min_required_quantity = forms.DecimalField(
        max_digits=10, decimal_places=2, required=False, label="Ελάχιστο απόθεμα",
    )

    class Meta:
        model = InventoryItem
        fields = ["quantity", "batch_number", "expiration_date", "notes"]
        widgets = {
            "expiration_date": forms.DateInput(attrs={"type": "date"}),
        }

    field_order = [
        "product_name", "barcode", "category", "unit", "unit_cost", "min_required_quantity",
        "quantity", "batch_number", "expiration_date", "notes",
    ]

    def __init__(self, *args, business=None, **kwargs):
        self.business = business
        super().__init__(*args, **kwargs)
        self.fields["category"].queryset = Category.objects.filter(business=business, is_active=True)
        if self.instance and self.instance.pk:
            self.fields["product_name"].initial = self.instance.product.name
            self.fields["barcode"].initial = self.instance.product.barcode
            self.fields["category"].initial = self.instance.product.category_id
            self.fields["unit"].initial = self.instance.product.unit
            self.fields["unit_cost"].initial = self.instance.product.unit_cost
            self.fields["min_required_quantity"].initial = self.instance.product.min_required_quantity

    def clean(self):
        cleaned = super().clean()
        product_name = cleaned.get("product_name")
        if product_name and self.business:
            is_new_product = not Product.objects.filter(business=self.business, name=product_name).exists()
            if is_new_product and self.business.product_limit_reached:
                raise forms.ValidationError(
                    f"Έχεις φτάσει το όριο των {self.business.TRIAL_PRODUCT_LIMIT} προϊόντων του trial. "
                    "Αναβάθμισε τη συνδρομή σου για απεριόριστα προϊόντα."
                )
        return cleaned

    def save(self, commit=True):
        product, _ = Product.objects.get_or_create(
            business=self.business,
            name=self.cleaned_data["product_name"],
            defaults={
                "barcode": self.cleaned_data["barcode"],
                "category": self.cleaned_data["category"],
                "unit": self.cleaned_data["unit"],
                "unit_cost": self.cleaned_data["unit_cost"],
                "min_required_quantity": self.cleaned_data["min_required_quantity"],
            },
        )
        new_values = {
            "barcode": self.cleaned_data["barcode"],
            "category_id": self.cleaned_data["category"].id if self.cleaned_data["category"] else None,
            "unit": self.cleaned_data["unit"],
            "unit_cost": self.cleaned_data["unit_cost"],
            "min_required_quantity": self.cleaned_data["min_required_quantity"],
        }
        if any(getattr(product, field) != value for field, value in new_values.items()):
            for field, value in new_values.items():
                setattr(product, field, value)
            product.save()

        item = super().save(commit=False)
        item.business = self.business
        item.product = product
        if commit:
            item.save()
        return item


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ["name"]
        labels = {"name": "Νέα κατηγορία"}

    def __init__(self, *args, business=None, **kwargs):
        self.business = business
        super().__init__(*args, **kwargs)

    def clean_name(self):
        name = self.cleaned_data["name"]
        if Category.objects.filter(business=self.business, name=name, is_active=True).exists():
            raise forms.ValidationError("Υπάρχει ήδη κατηγορία με αυτό το όνομα.")
        return name

    def save(self, commit=True):
        # Reactivate a previously soft-deleted category instead of violating the unique constraint.
        existing = Category.objects.filter(
            business=self.business, name=self.cleaned_data["name"], is_active=False
        ).first()
        if existing:
            existing.is_active = True
            if commit:
                existing.save()
            return existing

        category = super().save(commit=False)
        category.business = self.business
        if commit:
            category.save()
        return category


class NotificationSettingsForm(forms.ModelForm):
    class Meta:
        model = Business
        fields = ["notify_days_before", "notify_email", "notify_phone"]
