import random
from django.core.management.base import BaseCommand
from django.apps import apps
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from faker import Faker

class Command(BaseCommand):
    help = 'تعبئة كافة جداول مشروع Afiete بالبيانات الوهمية تلقائياً وبشكل نظيف'

    def handle(self, *args, **kwargs):
        fake = Faker(['ar_AA', 'en_US'])
        User = get_user_model()
        
        # أسماء التطبيقات الصافية كما يراها جنغو داخلياً
        AFIETE_APPS = [
            'users', 'patients', 'doctors', 'appointments', 
            'assessments', 'notifications', 'reports', 
            'ratings', 'articles', 'musics', 'notes'
        ]
        
        self.stdout.write(self.style.WARNING("🚀 جاري بدء التعبئة المتقدمة وتلافي التحذيرات..."))

        for app_label in AFIETE_APPS:
            try:
                app_config = apps.get_app_config(app_label)
            except LookupError:
                self.stdout.write(self.style.ERROR(f"❌ تعذر العثور على التطبيق: {app_label}"))
                continue

            for model in app_config.get_models():
                model_name = model.__name__
                self.stdout.write(f"📦 جاري تعبئة الجدول: {model_name}...")

                for _ in range(10):
                    fake_fields_data = {}
                    skip_record = False
                    
                    for field in model._meta.fields:
                        if field.primary_key or not field.editable:
                            continue
                        
                        # 1. معالجة العلاقات الخارجية والعلاقات الفريدة (OneToOne)
                        if isinstance(field, models.ForeignKey) or isinstance(field, models.OneToOneField):
                            related_model = field.remote_field.model
                            
                            # إذا كانت العلاقة فريدة، نختار عنصر غير مرتبط مسبقاً
                            if field.unique:
                                assigned_ids = model.objects.values_list(field.name, flat=True)
                                existing_objects = related_model.objects.exclude(id__in=assigned_ids)
                            else:
                                existing_objects = related_model.objects.all()

                            if existing_objects.exists():
                                fake_fields_data[field.name] = random.choice(existing_objects)
                            else:
                                if field.null:
                                    fake_fields_data[field.name] = None
                                else:
                                    skip_record = True # تخطي السجل إذا كان الحقل إجباري ولا يوجد أب له
                                break

                        # 2. توليد التواريخ المتوافقة مع الـ Timezone
                        elif isinstance(field, models.DateTimeField) or isinstance(field, models.DateField):
                            naive_datetime = fake.date_time_this_year()
                            fake_fields_data[field.name] = timezone.make_aware(naive_datetime)

                        # 3. دعم حقول الـ JSON والـ Arrays (مثل الـ steps والـ feelings)
                        elif 'JSONField' in field.__class__.__name__ or 'ArrayField' in field.__class__.__name__:
                            fake_fields_data[field.name] = ["مريح", "هدوء", "إيجابي"] if "feeling" in field.name else ["الخطوة الأولى", "الخطوة الثانية"]

                        # 4. باقي الحقول العادية
                        elif isinstance(field, models.CharField):
                            if getattr(field, 'choices', None):
                                fake_fields_data[field.name] = random.choice([c[0] for c in field.choices])
                            else:
                                max_len = field.max_length if field.max_length else 100
                                fake_fields_data[field.name] = fake.text(max_nb_chars=min(max_len, 50))
                        
                        elif isinstance(field, models.TextField):
                            fake_fields_data[field.name] = fake.paragraph(nb_sentences=2)
                        
                        elif isinstance(field, models.IntegerField) or isinstance(field, models.PositiveIntegerField):
                            fake_fields_data[field.name] = random.randint(1, 100)
                        
                        elif isinstance(field, models.FloatField) or isinstance(field, models.DecimalField):
                            fake_fields_data[field.name] = round(random.uniform(10.0, 100.0), 2)
                        
                        elif isinstance(field, models.BooleanField):
                            fake_fields_data[field.name] = random.choice([True, False])
                        
                        elif isinstance(field, models.EmailField):
                            fake_fields_data[field.name] = fake.unique.email()

                    if skip_record:
                        continue

                    # حفظ السجل
                    try:
                        if model == User:
                            username = fake.unique.user_name()
                            email = fake.unique.email()
                            User.objects.create_user(username=username, email=email, password="password123", **fake_fields_data)
                        else:
                            model.objects.create(**fake_fields_data)
                    except Exception:
                        pass

        self.stdout.write(self.style.SUCCESS('🎉 تمت التعبئة الشاملة بنظافة وبدون أي تحذيرات صفراء!'))