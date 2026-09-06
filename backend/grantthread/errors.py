class DomainError(Exception):
    def __init__(self, message, code="invalid_request", status=400):
        super().__init__(message)
        self.message, self.code, self.status = message, code, status


def require(condition, message, code="invalid_request", status=400):
    if not condition:
        raise DomainError(message, code, status)
