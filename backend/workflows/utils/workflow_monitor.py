# workflows/monitoring.py
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class WorkflowMonitor:
    @classmethod
    def log_workflow_start(cls, workflow_id, input_data):
        """Log the start of a workflow execution"""
        logger.info(f"Workflow {workflow_id} started at {datetime.now()} with input: {input_data}")
    
    @classmethod
    def log_workflow_end(cls, workflow_id, status, output=None, execution_time=None):
        """Log the end of a workflow execution"""
        logger.info(f"Workflow {workflow_id} ended with status {status} at {datetime.now()}")
        if execution_time:
            logger.info(f"Workflow {workflow_id} execution time: {execution_time:.2f} seconds")
    
    @classmethod
    def log_node_execution(cls, workflow_id, node_id, input_data, output_data, execution_time):
        """Log the execution of a node in the workflow"""
        logger.info(f"Node {node_id} in workflow {workflow_id} executed in {execution_time:.2f} seconds")
    
    @classmethod
    def log_error(cls, workflow_id, node_id, error):
        """Log an error in the workflow execution"""
        logger.error(f"Error in workflow {workflow_id}, node {node_id}: {error}")