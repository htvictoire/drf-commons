"""
Bulk database operations for import processing.
"""

import logging
from typing import List, Dict, Any, Set, Tuple
from django.db.models import Model

logger = logging.getLogger(__name__)


class BulkOperations:
    """Handles bulk create and update operations for imported data."""
    
    def __init__(self, batch_size: int = 250):
        self.batch_size = batch_size
    
    def individual_create_instances(self, model_cls, to_create: List[Tuple[int, Model]], 
                                  created_objs: List[Dict[str, Model]], step_key: str) -> Dict[int, str]:
        """Create model instances individually to maintain object consistency for references.
        
        Returns:
            Dict mapping row_idx to error message for failed saves
        """
        if not to_create:
            return {}
            
        save_errors = {}
        created_count = 0
        for row_idx, instance in to_create:
            try:
                instance.save()
                created_objs[row_idx][step_key] = instance
                created_count += 1
            except Exception as save_error:
                error_msg = f"Failed to save {model_cls.__name__}: {str(save_error)}"
                logger.error("Failed to create individual %s instance at row %d: %s", model_cls.__name__, row_idx, save_error)
                save_errors[row_idx] = error_msg
                # Don't add to created_objs if save failed
        
        logger.debug("Individually created %d %s instances", created_count, model_cls.__name__)
        return save_errors

    def bulk_create_instances(self, model_cls, to_create: List[Tuple[int, Model]], 
                            created_objs: List[Dict[str, Model]], step_key: str) -> Dict[int, str]:
        """Bulk create model instances with fallback to individual creates.
        
        Returns:
            Dict mapping row_idx to error message for failed saves
        """
        if not to_create:
            return {}
            
        indices, instances = zip(*to_create)
        created = []
        save_errors = {}
        
        from django.db import transaction
        
        # Try bulk create with savepoint
        try:
            with transaction.savepoint():
                for i in range(0, len(instances), self.batch_size):
                    batch = instances[i:i + self.batch_size]
                    batch_indices = indices[i:i + self.batch_size]
                    
                    created_batch = model_cls.objects.bulk_create(batch, batch_size=self.batch_size)
                    
                    # Map created objects back to their original row indices immediately
                    for idx, obj in zip(batch_indices, created_batch):
                        created_objs[idx][step_key] = obj
                        
                    created.extend(created_batch)
                logger.debug("Bulk created %d %s instances", len(created), model_cls.__name__)
        except Exception as e:
            logger.warning("Bulk create failed for %s, falling back to individual creates: %s", model_cls.__name__, str(e))
            # Store the original bulk error for first row if individual saves also fail
            bulk_error_msg = str(e)
            
            # Individual fallback with proper index mapping
            for row_idx, instance in zip(indices, instances):
                try:
                    instance.save()
                    created_objs[row_idx][step_key] = instance
                except Exception as save_error:
                    # If this is the first error and looks like a transaction issue, 
                    # report the original bulk error instead
                    if ("atomic" in str(save_error).lower() or 
                        "transaction" in str(save_error).lower()):
                        error_msg = f"Failed to save {model_cls.__name__}: {bulk_error_msg}"
                    else:
                        error_msg = f"Failed to save {model_cls.__name__}: {str(save_error)}"
                    
                    logger.error("Failed to create individual %s instance at row %d: %s", model_cls.__name__, row_idx, save_error)
                    save_errors[row_idx] = error_msg
        
        return save_errors
    
    def bulk_update_instances(self, model_cls, to_update: List[Model], update_fields: Set[str]) -> None:
        """Bulk update model instances with fallback to individual saves."""
        if not to_update:
            return
            
        try:
            model_cls.objects.bulk_update(to_update, list(update_fields), batch_size=self.batch_size)
            logger.debug("Bulk updated %d %s instances", len(to_update), model_cls.__name__)
        except Exception as e:
            logger.warning("Bulk update failed for %s, falling back to individual saves: %s", model_cls.__name__, str(e))
            for obj in to_update:
                try:
                    obj.save(update_fields=list(update_fields))
                except Exception as save_error:
                    logger.error("Failed to save individual %s instance: %s", model_cls.__name__, save_error)
    
    def apply_updates(self, obj: Model, kwargs: Dict[str, Any]) -> None:
        """Apply field updates to existing model instance."""
        for k, v in kwargs.items():
            setattr(obj, k, v)