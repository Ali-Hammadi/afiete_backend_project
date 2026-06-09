
def is_patient(user) -> str:
    return hasattr(user, 'patient')

def is_doctor(user) -> str:
    return hasattr(user, 'doctor')