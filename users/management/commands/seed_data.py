import random
import uuid
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.utils import timezone
from faker import Faker

# 1. استيراد موديلات تطبيق الـ users الحقيقية
from users.models import User, notes, Otp

# 2. استيراد موديلات تطبيق الـ doctors الحقيقية النظيفة (بناءً على ملفك الأخير)
from doctors.models import (
    Doctor, Job_title, SubSpecialization, 
    Schedule, Education, PaymentMethod
)

# 3. استيراد موديلات التطبيقات الأخرى بالأسماء القياسية المتوقعة لـ Django
from patients.models import Patient
from appointments.models import Appointment, Payment, SessionPrice
from assessments.models import QuestionGroup, Question, AnswerOption, PatientAssessmentProfile
from articles.models import Article
from musics.models import MusicEntity, BreathingExerciseEntity, UserRelaxProfile
from ratings.models import Rating
from reports.models import AppReport

fake = Faker()

class Command(BaseCommand):
    help = 'تعبئة قاعدة البيانات ببيانات وهمية متناسقة لجميع التطبيقات بدون تضارب'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.WARNING('--- بدء عملية تعبئة البيانات الوهمية ---'))

        # --- المرحلة 1: البيانات المستقلة ---
        self.stdout.write('جاري إنشاء المسميات الوظيفية ومجموعات الأسئلة...')
        job_titles = [Job_title.objects.create(title=fake.job()) for _ in range(5)]
        
        q_groups = []
        for i in range(4):
            qg = QuestionGroup.objects.create(
                name=f"Group {fake.word()}",
                description=fake.sentence(),
                order=i+1
            )
            q_groups.append(qg)

        subspecializations = []
        for i in range(5):
            sub = SubSpecialization.objects.create(
                name=f"Specialty {fake.word().capitalize()}",
                question_group=random.choice(q_groups)
            )
            subspecializations.append(sub)

        # --- المرحلة 2: إنشاء حسابات المستخدمين (User) ---
        self.stdout.write('جاري إنشاء حسابات المستخدمين...')
        users_pool = []
        for _ in range(40):
            user = User.objects.create_user(
                username=fake.unique.user_name(),
                email=fake.unique.email(),
                password='password123',
                first_name=fake.first_name(),
                last_name=fake.last_name(),
                phone=fake.phone_number()[:15],
                birth_date=fake.date_of_birth(minimum_age=20, maximum_age=60),
                gender=random.choice(['male', 'female']),
                status='active',
                is_verified=True,
                can_reset_password=False,
                is_funds_frozen=False
            )
            users_pool.append(user)

            Otp.objects.create(user=user, code=Otp.generate_otp(), is_used=random.choice([True, False]))
            notes.objects.create(Author=user, title=fake.sentence()[:50], content=fake.text(max_nb_chars=100))

        doctor_users = users_pool[:20]
        patient_users = users_pool[20:]

        # --- المرحلة 3: ملفات الأطباء والبيانات التابعة لهم ---
        self.stdout.write('جاري إنشاء ملفات الأطباء...')
        doctors_pool = []
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
        
        for u in doctor_users:
            doc = Doctor.objects.create(
                user=u,
                bio=fake.text(max_nb_chars=200),
                experience=random.randint(2, 25),
                job_title=random.choice(job_titles),
                status='approved'  # مطابقة لحروف الـ choices الصغيرة عندك
            )
            doctors_pool.append(doc)

            # إضافة التخصص عبر الـ ManyToManyField مباشرة
            doc.specialties.add(random.choice(subspecializations))
            
            Schedule.objects.create(
                day_of_week=random.choice(days), start_time="09:00:00", end_time="17:00:00",
                doctor=doc
            )

            Education.objects.create(
                degree="MD", institution=fake.company(), graduation_year=random.randint(2010, 2022),
                doctor=doc, status='approved'
            )
            PaymentMethod.objects.create(method=random.choice(['Stripe', 'PayPal']), is_active=True, doctor=doc)
            
            SessionPrice.objects.create(duration=45, type='Video', price=Decimal('100.00'), doctor=doc)

        # --- المرحلة 4: ملفات المرضى ---
        self.stdout.write('جاري إنشاء ملفات المرضى وتفعيل الملفات النفسية...')
        patients_pool = []
        for u in patient_users:
            pat = Patient.objects.create(
                user=u, psychological_history=fake.sentence(), nickname=fake.first_name()
            )
            patients_pool.append(pat)

            PatientAssessmentProfile.objects.create(can_take_assessment=True, patient=pat)
            UserRelaxProfile.objects.create(last_selected_feeling='Anxious', updated_at=timezone.now(), user=u)

        # --- المرحلة 5: الأسئلة والأجوبة والمقالات ---
        self.stdout.write('جاري تعبئة الأسئلة، الردود، والمقالات الطبية...')
        for qg in q_groups:
            for i in range(2):
                q = Question.objects.create(text=f"Question {fake.sentence()}?", order=i+1, questiongroup=qg)
                for score, text in enumerate(['Never', 'Sometimes', 'Often']):
                    AnswerOption.objects.create(text=text, score=score, question=q)

        for doc in doctors_pool:
            Article.objects.create(
                status='Published', content=fake.paragraph(), title=fake.sentence(),
                created_at=timezone.now(), updated_at=timezone.now(), author=doc, specialization=random.choice(subspecializations)
            )

        # --- المرحلة 6: المواعيد والفواتير والتقييمات ---
        self.stdout.write('جاري إنشاء المواعيد، الفواتير، والتقييمات...')
        for i in range(20):
            doc = random.choice(doctors_pool)
            pat = random.choice(patients_pool)
            
            app = Appointment.objects.create(
                date=timezone.now() + timezone.timedelta(days=random.randint(1, 15)),
                status='Completed' if i < 12 else 'Scheduled',
                doctor=doc, patient=pat, type='Video',
                payment_status='Paid' if i < 15 else 'Pending',
                has_next_session=False, created_at=timezone.now()
            )

            if app.payment_status == 'Paid':
                Payment.objects.create(
                    amount=Decimal('100.00'), date=timezone.now(), transaction_id=str(uuid.uuid4())[:30],
                    created_at=timezone.now(), appointment=app, status='Success',
                    admin_commission=Decimal('15.00'), doctor_amount=Decimal('85.00'),
                    is_transferred_to_doctor=True, method='Credit Card'
                )
                if app.status == 'Completed':
                    Rating.objects.create(rating=random.randint(4, 5), comment=fake.sentence(), appointment=app, created_at=timezone.now())

        # --- المرحلة 7: الموسيقى والتمارين ---
        self.stdout.write('جاري إنشاء مكتبة الموسيقى وتمارين التنفس...')
        for i in range(3):
            MusicEntity.objects.create(
                id=f"music_{i+1}", title=fake.word().capitalize(), artist=fake.name(),
                audio_url="https://example.com/audio.mp3", source_name="FreeSound",
                source_url="https://example.com", source_type="mp3",
                supported_feelings=["Stressed"], therapeutic_goals=["Relaxation"],
                is_instrumental=True, duration_seconds=180, tempo_bpm=60, novelty_score=80, license_text="CC"
            )
            BreathingExerciseEntity.objects.create(
                id=f"breath_{i+1}", title=f"Exercise {i+1}", description=fake.sentence(),
                type="Box", duration_minutes=5, inhale_seconds=4, hold_seconds=4, exhale_seconds=4, rest_seconds=4,
                steps=["Inhale", "Hold", "Exhale", "Rest"], recommended_for="Anxiety"
            )

        self.stdout.write(self.style.SUCCESS('--- تم ملء قاعدة البيانات بالكامل بنجاح وبدون أي أخطاء! ---'))