"""
Structured logging utilities with category awareness.
"""

from .core.categories import Categories


class StructuredLogger:
    """Category-aware logger for application events with formatting."""
    
    def __init__(self, name, category=None):
        self.name = name
        self.category = category
        self.logger = Categories.get_logger(name, category)
    
    def log_user_action(self, user, action, resource=None, details=None):
        """Log user actions for audit trail."""
        user_id = getattr(user, 'id', 'anonymous')
        username = getattr(user, 'username', 'anonymous')
        
        message = f"User {username} (ID: {user_id}) performed {action}"
        if resource:
            message += f" on {resource}"
        if details:
            message += f" - Details: {details}"
        
        self.logger.info(message)
    
    def log_api_request(self, request, response=None, duration=None):
        """Log API requests and responses."""
        message = f"{request.method} {request.path}"
        if hasattr(request, 'user') and request.user.is_authenticated:
            message += f" by {request.user.username}"
        
        if response:
            message += f" - Status: {response.status_code}"
        
        if duration:
            message += f" - Duration: {duration:.4f}s"
        
        self.logger.info(message)
    
    def log_error(self, error, context=None):
        """Log errors with context."""
        message = f"Error: {str(error)}"
        if context:
            message += f" - Context: {context}"
        
        self.logger.error(message, exc_info=True)
    
    def log_performance(self, operation, duration, details=None):
        """Log performance metrics."""
        message = f"Performance: {operation} took {duration:.4f}s"
        if details:
            message += f" - {details}"
        
        self.logger.info(message)