from django.db import migrations


def seed_promis_data(apps, schema_editor):
    QuestionGroup = apps.get_model('assessments', 'QuestionGroup')
    Question = apps.get_model('assessments', 'Question')
    AnswerOption = apps.get_model('assessments', 'AnswerOption')

    # ─────────────────────────────────────────────
    # خيارات مشتركة (أبدًا → دائمًا)  score 1-5
    # ─────────────────────────────────────────────
    NEVER_TO_ALWAYS = [
        ('أبدًا',   1),
        ('نادرًا',  2),
        ('أحيانًا', 3),
        ('غالبًا',  4),
        ('دائمًا',  5),
    ]

    # خيارات الوظيفة الجسدية (عكسية – عاجز → بدون صعوبة)
    PHYSICAL_OPTIONS = [
        ('غير قادر إطلاقًا', 1),
        ('صعوبة شديدة',      2),
        ('صعوبة متوسطة',     3),
        ('صعوبة بسيطة',      4),
        ('بدون صعوبة',       5),
    ]

    # ─────────────────────────────────────────────
    # بيانات المجموعات والأسئلة
    # ─────────────────────────────────────────────
    data = [
        {
            'name': 'الاكتئاب',
            'description': 'Depression – PROMIS',
            'questions': [
                'شعرت بالحزن',
                'شعرت بأنني مكتئب',
                'شعرت بأنني لا أستمتع بالأشياء',
                'شعرت بأن حياتي بلا معنى',
            ],
            'options': NEVER_TO_ALWAYS,
        },
        {
            'name': 'القلق',
            'description': 'Anxiety – PROMIS',
            'questions': [
                'شعرت بالتوتر',
                'شعرت بالقلق',
                'شعرت بالخوف',
                'شعرت بأن شيئًا سيئًا قد يحدث',
            ],
            'options': NEVER_TO_ALWAYS,
        },
        {
            'name': 'التعب / الإرهاق',
            'description': 'Fatigue – PROMIS',
            'questions': [
                'شعرت بالتعب',
                'شعرت بالإرهاق',
                'شعرت بأنني بلا طاقة',
                'شعرت بالإجهاد',
            ],
            'options': NEVER_TO_ALWAYS,
        },
        {
            'name': 'اضطرابات النوم',
            'description': 'Sleep Disturbance – PROMIS',
            'questions': [
                'واجهت صعوبة في النوم',
                'كان نومي غير مريح',
                'واجهت صعوبة في البقاء نائمًا',
                'شعرت بأن نومي غير كافٍ',
            ],
            'options': NEVER_TO_ALWAYS,
        },
        {
            'name': 'الأداء الاجتماعي',
            'description': 'Ability to Participate in Social Roles – PROMIS',
            'questions': [
                'تمكنت من أداء أدواري الاجتماعية',
                'تمكنت من القيام بمسؤولياتي المعتادة',
                'كنت راضيًا عن تفاعلاتي الاجتماعية',
                'تمكنت من القيام بالأنشطة التي تهمني',
            ],
            'options': NEVER_TO_ALWAYS,
        },
        {
            'name': 'الألم – الشدة',
            'description': 'Pain Intensity – PROMIS',
            'questions': [
                'ما شدة الألم لديك بشكل عام؟',
            ],
            'options': [
                ('0 – لا يوجد ألم',            0),
                ('1',                           1),
                ('2',                           2),
                ('3',                           3),
                ('4',                           4),
                ('5',                           5),
                ('6',                           6),
                ('7',                           7),
                ('8',                           8),
                ('9',                           9),
                ('10 – أسوأ ألم يمكن تخيله',  10),
            ],
        },
        {
            'name': 'الألم – التداخل مع الحياة',
            'description': 'Pain Interference – PROMIS',
            'questions': [
                'أثر الألم على نشاطاتك اليومية',
                'أثر الألم على قدرتك على التركيز',
        'أثر الألم على نومك',
                'أثر الألم على تفاعلك مع الآخرين',
            ],
            'options': NEVER_TO_ALWAYS,
        },
        {
            'name': 'الوظيفة الجسدية',
            'description': 'Physical Function – PROMIS',
            'questions': [
                'قدرتك على المشي لمسافات قصيرة',
                'قدرتك على صعود الدرج',
                'قدرتك على حمل الأشياء',
                'قدرتك على القيام بالأعمال اليومية',
            ],
            'options': PHYSICAL_OPTIONS,
        },
    ]

    for group_order, group_data in enumerate(data, start=1):
        group = QuestionGroup.objects.create(
            name=group_data['name'],
            description=group_data['description'],
            order=group_order,
        )

        for q_order, q_text in enumerate(group_data['questions'], start=1):
            question = Question.objects.create(
                questiongroup=group,
                text=q_text,
                order=q_order,
            )

            for option_text, option_score in group_data['options']:
                AnswerOption.objects.create(
                    question=question,
                    text=option_text,
                    score=option_score,
                )


def reverse_seed(apps, schema_editor):
    QuestionGroup = apps.get_model('assessments', 'QuestionGroup')
    names = [
        'الاكتئاب',
        'القلق',
        'التعب / الإرهاق',
        'اضطرابات النوم',
        'الأداء الاجتماعي',
        'الألم – الشدة',
        'الألم – التداخل مع الحياة',
        'الوظيفة الجسدية',
    ]
    QuestionGroup.objects.filter(name__in=names).delete()


class Migration(migrations.Migration):

    # !! غيّر 'your_app' و '0001_initial' ليطابقا اسم تطبيقك والمايجريشن السابق
    dependencies = [
        ('assessments', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(seed_promis_data, reverse_code=reverse_seed),
    ]