from employees.models import Employee

class EmployeeMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Kod wykonywany przed przetworzeniem widoku
        if request.user.is_authenticated and hasattr(request.user, 'is_employee') and request.user.is_employee:
            try:
                employee = Employee.objects.get(user=request.user)
                request.user.employee = employee
            except Employee.DoesNotExist:
                request.user.employee = None

        response = self.get_response(request)
        
        # Kod wykonywany po przetworzeniu widoku
        return response 