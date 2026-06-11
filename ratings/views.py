from rest_framework.views import APIView
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db import transaction
from users.permissions import IsAccountActiveAndUnfrozen
from .serializers import RatingSerializer, RatingReadSerializer
from .models import Rating
from .pagination import RatingPagination

from users.permissions import IsPatient
from appointments.models import Appointment
from users.utils import is_doctor

class RatingCreateView(APIView):
    """
    واجهة برمجية ذكية لإنشاء التقييمات تطبق منطق وأسلوب تطبيق الحجز بالكامل:
    1. تمنع التقييم تماماً إلا إذا كانت حالة الموعد مكتملة (completed).
    2. تمنع التعليق النصي (comment) إذا كان الكورس العلاجي مستمراً (has_next_session=True).
    3. تحذف أي تقييمات سابقة للمريض مع هذا الطبيب لتبقي فقط على التقييم الأحدث تزامناً.
    """
    permission_classes = [IsAuthenticated, IsPatient, IsAccountActiveAndUnfrozen]

    def post(self, request, appointment_id):
        # جلب الموعد والتأكد من أنه يخص المريض الحالي لضمان عزل وأمان البيانات
        appointment = get_object_or_404(Appointment, id=appointment_id, patient=request.user.patient)

        # 1. التحقق من أن الجلسة مكتملة بالفعل (وليس بمجرد مقارنة الوقت)
        if appointment.status != 'completed':
            return Response(
                {"error": "You cannot review the doctor before the session is fully completed."}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        # 2. منع تقييم نفس الموعد (الأوبجكت الحالي) أكثر من مرة
        if hasattr(appointment, 'rating'):
            return Response(
                {"error": "You have already reviewed this specific appointment instance."}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = RatingSerializer(data=request.data)
        if serializer.is_valid():
            comment = serializer.validated_data.get('comment')
            
            # 3. قاعدة الكورس العلاجي: إذا كان لديه جلسة قادمة متبقية، يمنع التعليق النصي ويسمح بالنجوم فقط
            if appointment.has_next_session is True and comment:
                return Response(
                    {
                        "error": "Since the treatment course is ongoing, you can only provide a star rating. Text commentary is restricted until the course finishes."
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            # تنفيذ العمليات بشكل ذري وآمن داخل قاعدة البيانات لمنع التضارب
            with transaction.atomic():
                # 4. منطق تطهير التكرار: حذف التقييمات السابقة لهذا المريض مع نفس الطبيب لإظهار التجربة الأخيرة فقط
                Rating.objects.filter(
                    appointment__patient=request.user.patient, 
                    appointment__doctor=appointment.doctor
                ).delete()
                
                # حفظ التقييم وربطه بسياق الموعد الحالي
                serializer.save(appointment=appointment)
                
            return Response({"message": "Your smart rating has been submitted successfully."}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class RatingListView(generics.ListAPIView):
    """عرض مراجعات الطبيب مع دعم التقسيم (Pagination)"""
    serializer_class = RatingReadSerializer
    pagination_class = RatingPagination
    permission_classes = [IsAuthenticated, IsAccountActiveAndUnfrozen]

    def get_queryset(self):
        doctor_username = self.kwargs.get('doctor_username')

        # إذا لم يتم تمرير اسم مستخدم وكان المستخدم الحالي طبيباً، يعرض تقييماته الخاصة
        if not doctor_username and is_doctor(self.request.user):
            return Rating.objects.filter(
                appointment__doctor=self.request.user.doctor
            ).order_by('-created_at')
        
        # عرض مراجعات طبيب معين للعامة أو للمرضى بناءً على الـ username
        return Rating.objects.filter(
            appointment__doctor__user__username=doctor_username
        ).select_related('appointment__patient__user').order_by('-created_at')